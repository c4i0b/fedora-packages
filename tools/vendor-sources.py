#!/usr/bin/env python3
"""Vendor Go/Rust/zig dependencies at SRPM build time (network is available
in the COPR make_srpm step; the binary build afterwards uses the vendored
copy). Stdlib only: python3 is always present in the SRPM chroot (rpm itself
needs it). urllib speaks HTTP/1.1 only, which sidesteps the COPR egress
breakage that forced curl --http1.1 in the shell version."""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import tomllib
import urllib.request
import zipfile
from pathlib import Path

GO = re.compile(r"^%goprep|^go-vendor-tools", re.M)
CARGO = re.compile(r"^%cargo_prep", re.M)
# spec comment: `# cargo-update: -p <crate>` — stale lock pins bumped at
# vendor time so the fresh crate lands in vendor.tar.zst (E0282 class)
CARGO_UPDATE = re.compile(r"^#\s*cargo-update:\s*(.+?)\s*$", re.M)
ZIGSRC = re.compile(r"^Source[0-9]*:.*zig-pkg\.tar", re.M)
ZON_RE = re.compile(
    r'\.url\s*=\s*"((?:git\+)?https://[^"]+)",\s*\n\s*\.hash\s*=\s*"([^"]+)"')



def log(msg):
    print(f"vendor-sources: {msg}", file=sys.stderr, flush=True)


def die(msg):
    log(msg)
    sys.exit(1)


def stats(kind):
    p = os.environ.get("VENDOR_STATS")
    if p:
        with open(p, "a") as f:
            f.write(kind + "\n")


def dnf_install(pkgs):
    cmd = ["dnf", "-y", "install", "--nodocs", "--setopt=install_weak_deps=0", *pkgs]
    if os.geteuid() != 0:
        cmd.insert(0, "sudo")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def http_get(url, tries=4, timeout=600):
    # the results CDN drops occasional requests; retry with growing backoff
    last = None
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "vendor-sources"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001 - retry any transport error
            last = e
            log(f"GET {url} failed ({e}); attempt {attempt}/{tries}")
            if attempt < tries:
                time.sleep(10 * attempt)
    raise last


# ---- archives ----------------------------------------------------------------

def _extract_members(tf, dest, strip):
    members = tf.getmembers()
    if strip:
        kept = []
        for m in members:
            parts = m.name.split("/")
            if len(parts) > strip:
                m.name = "/".join(parts[strip:])
                kept.append(m)
        members = kept
    try:
        tf.extractall(dest, members=members, filter="tar")
    except TypeError:  # python < 3.12: no filter parameter
        tf.extractall(dest, members=members)


def untar(path, dest, strip=0):
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    try:
        with tarfile.open(path, "r:*") as tf:
            _extract_members(tf, dest, strip)
        return
    except tarfile.ReadError:
        pass
    # zstd & friends: system tar auto-detects every compressor
    cmd = ["tar", "-xf", str(path), "-C", str(dest)]
    if strip:
        cmd.append(f"--strip-components={strip}")
    subprocess.run(cmd, check=True)


def untar_strip_top(path, dest):
    # strip a single top-level dir like the shell `tar --strip-components=1`
    # conditional did (only when the archive has exactly one)
    try:
        with tarfile.open(path, "r:*") as tf:
            tops = {m.name.lstrip("./").split("/")[0]
                    for m in tf.getmembers() if m.name.strip("/")}
            strip = 1 if len(tops) == 1 else 0
            _extract_members(tf, dest, strip)
        return
    except tarfile.ReadError:
        pass
    out = subprocess.run(["tar", "-tf", str(path)],
                         capture_output=True, text=True, check=True).stdout
    tops = {l.lstrip("./").split("/")[0] for l in out.splitlines() if l.strip("/")}
    untar(path, dest, strip=1 if len(tops) == 1 else 0)


def strip_single_top(dest):
    entries = [p for p in Path(dest).iterdir() if p.name not in ("", ".")]
    if len(entries) == 1 and entries[0].is_dir():
        sole = entries[0]
        for child in list(sole.iterdir()):
            shutil.move(str(child), str(Path(dest) / child.name))
        sole.rmdir()


def repack_dir(dir_path, archive):
    # compression from the archive name (parity with the old tar -z/-J/-j)
    archive = Path(archive)
    name = archive.name
    if name.endswith((".tar.gz", ".tgz", ".crate")):
        mode = "w:gz"
    elif name.endswith(".tar.xz"):
        mode = "w:xz"
    elif name.endswith(".tar.bz2"):
        mode = "w:bz2"
    else:
        mode = "w"
    with tarfile.open(archive, mode) as tf:
        tf.add(str(dir_path), arcname=dir_path.name)


def tar_first_top(archive):
    try:
        with tarfile.open(archive, "r:*") as tf:
            ms = tf.getmembers()
    except tarfile.ReadError:
        out = subprocess.run(["tar", "-tf", str(archive)],
                             capture_output=True, text=True, check=True).stdout
        lines = [l for l in out.splitlines() if l.strip()]
        return lines[0].lstrip("./").split("/")[0] if lines else ""
    if not ms:
        return ""
    return ms[0].name.lstrip("./").split("/")[0]


def fetch_tarball(url, strip=0, dest=None):
    fd, name = tempfile.mkstemp(prefix="vendor-fetch-")
    os.close(fd)
    tmp = Path(name)
    try:
        tmp.write_bytes(http_get(url))
        if zipfile.is_zipfile(tmp):
            # zipfile restores modes from external_attr (nonzero ones only)
            with zipfile.ZipFile(tmp) as z:
                z.extractall(dest or ".")
            if strip:
                strip_single_top(dest or ".")
        else:
            untar(tmp, dest or ".", strip=strip)
    finally:
        tmp.unlink()


# ---- submodules ---------------------------------------------------------------

def fetch_submodules(tree, source0_url):
    """GitHub tag archives carry .gitmodules but no submodule contents (herdr
    vendors ghostty that way). Fetch each submodule at the commit the tag
    pins (sha via the GitHub API) and overlay it into the tree; the caller
    must then repack the source tarball. True when anything changed."""
    tag = Path(source0_url.split("#")[0]).name
    for ext in (".tar.gz", ".tgz", ".tar.xz", ".zip"):
        if tag.endswith(ext):
            tag = tag[: -len(ext)]
            break
    gm = Path(tree) / ".gitmodules"
    if not gm.is_file():
        return False
    if shutil.which("git") is None:
        dnf_install(["git-core"])
    m = re.match(r"https://github.com/([^/]+/[^/]+)", source0_url)
    if not m:
        log("cannot resolve submodule pins: non-github Source0")
        return False
    super_repo = m.group(1)
    entries = subprocess.run(["git", "config", "-f", str(gm), "--list"],
                             capture_output=True, text=True, check=True).stdout
    changed = False
    for line in entries.splitlines():
        key, _, sm_url = line.partition("=")
        if not (key.startswith("submodule.") and key.endswith(".url") and sm_url):
            continue
        name = key[len("submodule."):-len(".url")]
        path = subprocess.run(
            ["git", "config", "-f", str(gm), "--get", f"submodule.{name}.path"],
            capture_output=True, text=True, check=True).stdout.strip()
        if not sm_url.startswith("https://github.com/"):
            log(f"skipping non-github submodule {path}")
            continue
        repo = sm_url[len("https://github.com/"):]
        repo = repo[:-len(".git")] if repo.endswith(".git") else repo
        # the pin lives in the superproject: ask ITS api about the path
        api = (f"https://api.github.com/repos/{super_repo}/contents/"
               f"{urllib.request.quote(path)}?ref={urllib.request.quote(tag)}")
        try:
            sha = json.loads(http_get(api)).get("sha", "")
        except Exception as e:  # noqa: BLE001
            die(f"no pinned sha for submodule {path} at {tag} ({e})")
        if not re.fullmatch(r"[0-9a-f]{40}", sha or ""):
            die(f"no pinned sha for submodule {path} at {tag}")
        log(f"fetching submodule {path} at {sha}")
        dest = Path(tree) / path
        shutil.rmtree(dest, ignore_errors=True)
        dest.mkdir(parents=True)
        fetch_tarball(f"https://github.com/{repo}/archive/{sha}.tar.gz",
                      strip=1, dest=dest)
        changed = True
    return changed


# ---- zig closure --------------------------------------------------------------

def zon_urls(scope_dir, mode):
    """(url, commit, hash) triples from build.zig.zon files. mode 'root':
    only the dir's own zon (only a dependency's ROOT zon belongs to the
    graph — scanning fetched sub-zons pulls gigabytes of junk); 'tree':
    every zon in the source tree."""
    if mode == "root":
        zons = [Path(scope_dir) / "build.zig.zon"]
    else:
        zons = [p for p in Path(scope_dir).rglob("build.zig.zon")
                if "zig-pkg" not in p.parts]
    out = []
    for z in zons:
        if not z.is_file():
            continue
        s = z.read_text(errors="replace")
        for m in ZON_RE.finditer(s):
            url = m.group(1)
            if url.startswith("git+"):
                repo, _, commit = url[4:].partition("#")
                out.append((repo, commit or "-", m.group(2)))
            else:
                out.append((url, "-", m.group(2)))
    return out


def _git_shallow_fetch(repo, commit, dest):
    tmpg = Path(dest) / "tmpg"
    for attempt in range(1, 6):
        log(f"git fetch {repo} ({commit}), attempt {attempt}")
        tmpg.mkdir()
        subprocess.run(["git", "init", "-q", str(tmpg)], check=True)
        ok = subprocess.run(
            ["git", "-c", "http.version=HTTP/1.1", "fetch", "-q", "--depth", "1",
             repo, commit], cwd=tmpg,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        if ok:
            ok = subprocess.run(["git", "checkout", "-q", "FETCH_HEAD"], cwd=tmpg,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL).returncode == 0
        if ok:
            shutil.rmtree(tmpg / ".git")
            for child in list(tmpg.iterdir()):
                shutil.move(str(child), str(Path(dest) / child.name))
            tmpg.rmdir()
            return
        shutil.rmtree(tmpg, ignore_errors=True)
        time.sleep(10 * attempt)
    die(f"git fetch failed: {repo}")


def _fetch_zig_url(url, dest):
    for attempt in range(1, 6):
        log(f"fetching {url}, attempt {attempt}")
        try:
            data = http_get(url, tries=1, timeout=600)
            break
        except Exception as e:  # noqa: BLE001
            log(f"download failed: {url} ({e})")
            time.sleep(10 * attempt)
    else:
        die(f"download failed: {url}")
    fd, name = tempfile.mkstemp(prefix="zon-cache-")
    os.close(fd)
    tmp = Path(name)
    try:
        tmp.write_bytes(data)
        if zipfile.is_zipfile(tmp):
            with zipfile.ZipFile(tmp) as z:
                z.extractall(dest)
            strip_single_top(dest)
        else:
            untar_strip_top(tmp, dest)
    finally:
        tmp.unlink()


def _zig_ver(s):
    n = [int(p) for p in s.split("-")[0].split(".")]
    return (n + [0, 0, 0])[:3]


def check_zig_floor(src_tree, spec, spec_text):
    """The build.zig.zon minimum_zig_version is a hard floor; a spec pinning
    an older zig dies much later with cryptic compiler errors — abort here,
    naming the pin to bump. Cargo trees with an embedded zig build (herdr's
    vendored ghostty) carry no root zon: fall back to every zon in the
    source tree (the tree-mode scan zon_urls uses) and enforce the highest
    floor found."""
    zon = Path(src_tree) / "build.zig.zon"
    if zon.is_file():
        zons = [zon]
    else:
        zons = [p for p in Path(src_tree).rglob("build.zig.zon")
                if "zig-pkg" not in p.parts]
    floor = None
    for z in zons:
        if not z.is_file():
            continue
        m = re.search(r'\.minimum_zig_version\s*=\s*"([0-9][0-9.\-]*)',
                      z.read_text(errors="replace"))
        if m and (floor is None or _zig_ver(m.group(1)) > _zig_ver(floor)):
            floor = m.group(1)
    pin = re.search(r"^%global\s+zig_version\s+(\S+)", spec_text, re.M) \
        or re.search(r"ziglang\.org/download/([0-9][0-9.]*)", spec_text)
    if not (floor and pin):
        return
    if _zig_ver(floor) > _zig_ver(pin.group(1)):
        die(f"{spec.name}: upstream requires zig >= {floor} but the spec "
            f"pins {pin.group(1)} — bump the zig_version %global / Source URLs")


def fetch_zig_closure(src_tree, spec, spec_text):
    """Prefetch the build.zig.zon dependency closure into a `zig build
    --system` package store (zig-pkg.tar.zst in the cwd): zig's own http
    client is unreliable on some builders."""
    check_zig_floor(src_tree, spec, spec_text)
    missing = [b for b in ("git", "tar", "zstd") if shutil.which(b) is None]
    if missing:
        dnf_install(["git-core", "zstd", "tar"])
    store = Path("zig-pkg")
    shutil.rmtree(store, ignore_errors=True)
    store.mkdir()
    queue = zon_urls(src_tree, "tree")
    done = set()
    while True:
        new = False
        for url, commit, zhash in sorted(set(queue)):
            if url in done:
                continue
            done.add(url)
            new = True
            d = store / zhash
            if d.is_dir():
                continue  # same id reachable via several URLs
            d.mkdir()
            if commit != "-":
                _git_shallow_fetch(url, commit, d)
            else:
                _fetch_zig_url(url, d)
            queue += zon_urls(d, "root")
        if not new:
            break
    if not any(store.iterdir()):
        die("zig-pkg store is empty")
    subprocess.run(["tar", "--zstd", "-cf", "zig-pkg.tar.zst", "zig-pkg"], check=True)
    shutil.rmtree(store)


# ---- workspace flattening -------------------------------------------------------

_BARE = re.compile(r"^[A-Za-z0-9_-]+$")


def _toml_key(s):
    return s if _BARE.match(s) else '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _toml_val(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, list):
        return "[" + ", ".join(_toml_val(x) for x in v) + "]"
    raise TypeError(f"cannot serialize {type(v)}")


def _toml_dumps(m):
    """Minimal TOML writer (stdlib has no encoder): scalars/arrays inline,
    dicts as [table] sections, lists of dicts as [[array-of-tables]].
    Scalars of a table MUST precede its sub-tables or they would attach
    to the last open section — emit in passes, not in dict order."""
    out = []

    def emit(table, prefix):
        aots = {id(v) for k, v in table.items()
                if isinstance(v, list) and v and all(isinstance(x, dict) for x in v)}
        for k, v in table.items():
            if not isinstance(v, dict) and id(v) not in aots:
                out.append(f"{_toml_key(k)} = {_toml_val(v)}")
        for k, v in table.items():
            if isinstance(v, dict) and id(v) not in aots:
                name = f"{prefix}.{_toml_key(k)}" if prefix else _toml_key(k)
                if v:
                    out.append(f"\n[{name}]")
                    emit(v, name)
        for k, v in table.items():
            if id(v) in aots:
                name = f"{prefix}.{_toml_key(k)}" if prefix else _toml_key(k)
                for item in v:
                    out.append(f"\n[[{name}]]")
                    emit(item, name)
    emit(m, "")
    return "\n".join(out) + "\n"


def _dep_tables(m):
    for k in ("dependencies", "dev-dependencies", "build-dependencies"):
        if k in m:
            yield m[k]
    for tv in m.get("target", {}).values():
        for k in ("dependencies", "dev-dependencies", "build-dependencies"):
            if k in tv:
                yield tv[k]


def flatten_workspace_members(root, repo=None):
    """Inline `workspace = true` inheritance in every member manifest of the
    workspace at `root` (the fetched dup-pinned tree). Cargo resolves
    inheritance of a [patch] path target — and of everything it reaches via
    path deps — against the workspace doing the patching, so members of
    another workspace can never be patch targets as-is (craft-libs' root is
    a virtual manifest and every crate inherits heavily). With `repo`,
    git deps pointing back at that repository become in-tree path deps —
    they would otherwise reintroduce the duplicate git sources the pin is
    trying to eliminate. The tree stays self-contained: cross-tree
    duplicates are disambiguated by version build metadata instead (see
    pin_duplicate_git_crate). Manifests are rewritten only when something
    actually changes (inheritance inlined, a dev-dependency dropped, a
    dangling feature ref dropped)."""
    root = Path(root)
    rm = tomllib.loads((root / "Cargo.toml").read_text())
    wsp = rm.get("workspace", {})
    wpkg, wdeps = wsp.get("package", {}), wsp.get("dependencies", {})
    self_repo = re.sub(r"\.git$", "", repo.rstrip("/")) if repo else None
    for cm in sorted(root.rglob("Cargo.toml")):
        if cm.parent == root:
            continue  # the root itself keeps defining the workspace
        text = cm.read_text()
        m = tomllib.loads(text)
        if "package" not in m:
            continue  # nested virtual manifest: nothing to inline
        dirty = False
        # dev-deps of patch targets are never built, and the same dev-only
        # crate reachable from two trees ("two packages named X in this
        # workspace") aborts the resolve outright
        if "dev-dependencies" in m or any(
                "dev-dependencies" in tv for tv in m.get("target", {}).values()):
            m.pop("dev-dependencies", None)
            for tv in m.get("target", {}).values():
                tv.pop("dev-dependencies", None)
            dirty = True
            log(f"{cm}: dropped dev-dependencies (patch target)")
        if re.search(r"workspace\s*=\s*true", text):
            dirty = True  # rewritten even if only formatting changes
            pkg = m["package"]
            for k in list(pkg):
                if pkg[k] == {"workspace": True}:
                    if k not in wpkg:
                        die(f"{cm}: inherits package.{k}, root lacks it")
                    pkg[k] = wpkg[k]
            if m.get("lints") == {"workspace": True}:
                m["lints"] = {k.split(".", 1)[1]: v for k, v in wsp.items()
                              if k.startswith("lints.")}
            for tbl in _dep_tables(m):
                for name in list(tbl):
                    v = tbl[name]
                    if not isinstance(v, dict) or v.get("workspace") is not True:
                        continue
                    if name not in wdeps:
                        die(f"{cm}: inherits dependency '{name}', root lacks it")
                    # { workspace = true, optional/features/... }: merge the
                    # extras onto the root's spec (cargo allows both)
                    base = wdeps[name]
                    if isinstance(base, str):
                        base = {"version": base}
                    base = dict(base)
                    extra = {k: x for k, x in v.items() if k != "workspace"}
                    if "features" in extra and "features" in base:
                        extra["features"] = base["features"] + extra["features"]
                    base.update(extra)
                    v = tbl[name] = base
                    # same-repo git refs become in-tree path deps — the
                    # tree is self-contained (a git edge would reintroduce
                    # the duplicate sources the pin is eliminating)
                    if self_repo and isinstance(v.get("git"), str) \
                            and re.sub(r"\.git$", "", v["git"].rstrip("/")) == self_repo:
                        tgt = crate_member_dir(root, name)
                        v = {k: x for k, x in v.items()
                             if k not in ("git", "rev", "branch", "tag", "version")}
                        v["path"] = os.path.relpath(tgt.resolve(), cm.parent)
                        tbl[name] = v
                    elif "path" in v:  # root-relative -> member-relative
                        v["path"] = os.path.relpath(
                            (root / v["path"]).resolve(), cm.parent)
        # features referencing deps absent from the manifest (craft-libs
        # points `snapshot` at a dev-dependency): tolerated inside the
        # original workspace, eagerly rejected in a patch target — drop
        # the dangling references
        feats = m.get("features")
        if isinstance(feats, dict):
            # features may only reference normal/target dependencies —
            # dev-dependencies count as dangling (craft-libs' `snapshot`)
            depnames = set(m.get("dependencies", {}).keys())
            for tv in m.get("target", {}).values():
                depnames |= set(tv.get("dependencies", {}).keys())
            for fname, items in list(feats.items()):
                if not isinstance(items, list):
                    continue
                keep = []
                for it in items:
                    if not isinstance(it, str):
                        keep.append(it)
                        continue
                    ref = it[4:] if it.startswith("dep:") else it.split("/", 1)[0]
                    if ref in depnames or (not it.startswith("dep:")
                                           and "/" not in it and ref in feats):
                        keep.append(it)
                    else:
                        log(f"{cm}: dropping feature ref '{it}' "
                            f"(dep not in manifest)")
                        dirty = True
                feats[fname] = keep
        if dirty:
            cm.write_text(_toml_dumps(m))
            log(f"flattened workspace inheritance in {cm}")


# ---- cargo patch filtering -----------------------------------------------------

def drop_unvendored_git_patches(ws):
    """[patch.crates-io] GIT entries for crates nothing in the graph depends
    on are never vendored, yet cargo validates every patch entry against its
    source and aborts offline — drop them from the tree the binary build
    will extract (the extracted copy dies with the SRPM chroot, so the
    tarball gets re-packed too). PATH entries are always kept: path-patched
    crates stay in-tree and are never vendored. True when anything dropped."""
    dropped = False
    for cm in Path(ws).rglob("Cargo.toml"):
        if any(p.startswith("vendor") for p in cm.relative_to(ws).parts[:-1]):
            continue
        text = cm.read_text()
        if "\n[patch.crates-io]" not in text and not text.startswith("[patch.crates-io]"):
            continue
        lines = text.splitlines(keepends=True)
        out = []
        inpatch = False
        for line in lines:
            if line.startswith("[patch.crates-io]"):
                inpatch = True
            elif line.startswith("["):
                inpatch = False
            if inpatch:
                m = re.match(r"([A-Za-z0-9_-]+)\s*=\s*\{\s*git", line)
                if m:
                    crate = m.group(1)
                    vendored = (Path(ws) / "vendor-deps" / crate).is_dir() or \
                        bool(list((Path(ws) / "vendor-deps").glob(crate + "-[0-9]*")))
                    if not vendored:
                        log(f"dropping unvendored git patch entry: {crate} ({cm})")
                        dropped = True
                        continue
            out.append(line)
        new = "".join(out)
        if new != text:
            cm.write_text(new)
    return dropped


def crate_member_dir(root, crate):
    """Resolve the directory of the package manifest defining `crate`
    inside a fetched git tree. Many repos (craft-libs) keep a virtual
    workspace manifest at the root; a path [patch] entry must point at
    the member, not the root. Falls back to `root` when it itself is the
    package manifest or no member matches (the caller decides whether
    that is fatal)."""
    for cm in sorted(Path(root).rglob("Cargo.toml")):
        if re.search(rf'^name\s*=\s*"{re.escape(crate)}"\s*$',
                     cm.read_text(errors="replace"), re.M):
            return cm.parent
    return Path(root)


DUP_SOURCES_RE = re.compile(
    r"found duplicate version of package `([A-Za-z0-9_.-]+) v\S+` "
    r"vendored from two sources:\s*\n\s*source 1: (\S+?rev=([0-9a-f]+))#[0-9a-f]+"
    r"\s*\n\s*source 2: (\S+?rev=([0-9a-f]+))#[0-9a-f]+")


def lock_git_crates(ws):
    """From the lockfile: crate -> git repo, crate -> every rev it is
    pinned at IN ORDER (an upstream lock routinely mixes a dozen revs of
    one repo — each craft app pins whatever rev was current when it bumped
    each crate)."""
    lock = Path(ws) / "Cargo.lock"
    cmap, crevs = {}, {}
    if not lock.is_file():
        return cmap, crevs
    for blk in lock.read_text().split("[[package]]")[1:]:
        name = re.search(r'^name = "(.+)"$', blk, re.M)
        src = re.search(r'^source = "git\+(\S+?)\?rev=([0-9a-f]+)#', blk, re.M)
        if name and src:
            cmap.setdefault(name.group(1), src.group(1))
            crevs.setdefault(name.group(1), []).append(src.group(2))
    return cmap, crevs


def set_patch_entries(ws, repo, entries):
    """Write crate->path entries under [patch.\"repo\"], scoped to that
    repo's section: other repos' tagged entries (earlier pins) survive,
    upstream's own entries in the section are kept, and previously written
    entries for THIS repo are tagged so a repin replaces them cleanly."""
    manifest = Path(ws) / "Cargo.toml"
    text = manifest.read_text()
    header = f'[patch."{repo}"]'
    strip_re = re.compile(r"^# vendor-sources dup-pin\n"
                          r"[A-Za-z0-9_.-]+ = \{ path = \"[^\"]+\" \}(?:\n|\Z)", re.M)
    if header in text:
        before, rest = text.split(header, 1)
        cut = rest.find("\n[")
        body, after = (rest, "") if cut < 0 else (rest[:cut], rest[cut + 1:])
        body = strip_re.sub("", body)
        existing = set(re.findall(r"^([A-Za-z0-9_.-]+)\s*=", body, re.M))
    else:
        before, after, existing = text, "", set()
        body = ""
    block = "".join(f"# vendor-sources dup-pin\n"
                    f"{c} = {{ path = \"{p}\" }}\n"
                    for c, p in entries.items() if c not in existing)
    if header in text or block:
        manifest.write_text(before + header + "\n" + body + block + after)


def reset_dup_pin_state(ws):
    """A re-run may extract a Source0 that a previous run re-packed WITH
    our dup-pin patches (tagged Cargo.toml entries, renamed dep rewrites,
    dup-pinned trees, a lock resolved against them) — strip them so
    vendoring starts from the pristine upstream state and re-resolves."""
    journal = Path(ws) / "dup-pinned" / ".renamed-entries.json"
    if journal.is_file():
        for rel, entries in json.loads(journal.read_text()).items():
            cm = Path(ws) / rel
            if not cm.is_file():
                continue
            try:
                m = tomllib.loads(cm.read_text())
            except tomllib.TOMLDecodeError:
                continue
            for key, orig in entries.items():
                for tbl in _dep_tables(m):
                    if key in tbl:
                        tbl[key] = orig
                        break
            cm.write_text(_toml_dumps(m))
            log(f"restored renamed dep edits in {rel}")
    shutil.rmtree(Path(ws) / "dup-pinned", ignore_errors=True)
    manifest = Path(ws) / "Cargo.toml"
    if not manifest.is_file():
        return
    text = manifest.read_text()
    new = re.sub(r"^# vendor-sources dup-pin\n"
                 r"[A-Za-z0-9_.-]+ = \{ path = \"[^\"]+\" \}\n",
                 "", text, flags=re.M)
    new = re.sub(r'(?m)^\[patch\."[^"]+"\]\n(?=\[|\Z)', "", new)
    if new != text:
        manifest.write_text(new)
        log("stripped dup-pin patches re-extracted from a repacked Source0")


def manifest_declared_rev(ws, repo, crate):
    """The rev the workspace manifests themselves pin `crate` at from
    `repo` — the version upstream actually builds against, so the first
    candidate to try when unifying (lockfile rev counts drift once our
    own patches rewrite the lock). None when not declared."""
    for cm in Path(ws).rglob("Cargo.toml"):
        if any(p in ("dup-pinned", "vendor-deps", "vendor")
               for p in cm.relative_to(ws).parts[:-1]):
            continue
        try:
            m = tomllib.loads(cm.read_text())
        except tomllib.TOMLDecodeError:
            continue
        for tbl in _dep_tables(m):
            v = tbl.get(crate)
            if isinstance(v, dict) and v.get("git") \
                    and re.sub(r"\.git$", "", v["git"].rstrip("/")) \
                    == re.sub(r"\.git$", "", repo.rstrip("/")) \
                    and v.get("rev"):
                return v["rev"]
    return None


def dup_pin_dir(ws, repo, rev):
    key = re.sub(r"[^A-Za-z0-9.-]", "-", repo.rstrip("/").rsplit("/", 1)[-1]) \
        + "-" + rev[:8]
    return Path(ws) / "dup-pinned" / key


def _tree_member(ws, repo, rev, crate):
    """The member dir defining `crate` in the fetched tree at `rev`, or
    None when that rev does not carry it."""
    d = dup_pin_dir(ws, repo, rev)
    if not d.is_dir():
        return None
    pkg = crate_member_dir(d, crate)
    if re.search(rf'^name\s*=\s*"{re.escape(crate)}"\s*$',
                 (pkg / "Cargo.toml").read_text(errors="replace"), re.M):
        return pkg
    return None


def fix_renamed_dup_deps(ws, repo, crate_tree):
    """A manifest can depend on one repo crate under two keys — upstream
    pins an OLD rev under a renamed dep (effectcraft's craft-audio-markers
    = { package = "craft-audio", git ... }) alongside the workspace one.
    Once the repo is path-patched both edges collapse onto a single
    package and cargo rejects the duplicate ("depends on crate multiple
    times with different names"). Give every extra key its own physical
    copy of the canonical member so the instances stay distinct. Edits
    are recorded in dup-pinned/.renamed-entries.json so a re-run can
    restore the pristine manifests (the repacked Source0 carries them)."""
    norm = re.sub(r"\.git$", "", repo.rstrip("/"))
    journal = Path(ws) / "dup-pinned" / ".renamed-entries.json"
    undo = json.loads(journal.read_text()) if journal.is_file() else {}
    for cm in Path(ws).rglob("Cargo.toml"):
        if any(p in ("vendor-deps", "vendor") for p in cm.relative_to(ws).parts[:-1]):
            continue
        try:
            m = tomllib.loads(cm.read_text())
        except tomllib.TOMLDecodeError:
            continue
        if "package" not in m:
            continue
        by_pkg = {}
        for tbl in _dep_tables(m):
            for name, v in tbl.items():
                if not isinstance(v, dict):
                    continue
                pkg = v.get("package", name)
                git = v.get("git") and \
                    re.sub(r"\.git$", "", v["git"].rstrip("/")) == norm
                if git or pkg in crate_tree:
                    by_pkg.setdefault(pkg, {}).setdefault(name, []).append((tbl, v))
        dirty = False
        for pkg, names in by_pkg.items():
            # same dep name in several tables is NOT a rename: every
            # occurrence must share the canonical path or cargo rejects
            # the manifest ("different source paths depending on target")
            if len(names) < 2 or pkg not in crate_tree:
                continue
            canon = _tree_member(ws, repo, crate_tree[pkg], pkg)
            if canon is None:
                continue
            base = dup_pin_dir(ws, repo, crate_tree[pkg])
            preferred = pkg if pkg in names else sorted(names)[0]
            for name in sorted(n for n in names if n != preferred):
                # the copy RENAMES the package to the dep key: upstream code
                # already addresses it as <key>, and a distinct package name
                # keeps the lockfile unambiguous (same name+version from two
                # paths is a hard collision)
                copy = base.parent / (base.name + "-"
                                      + re.sub(r"[^A-Za-z0-9.-]", "-", name))
                src = None
                for _, v in names[name]:
                    if v.get("rev"):
                        src = _tree_member(ws, repo, v["rev"], pkg)
                        if src is not None:
                            break
                if src is None:
                    src = canon
                if not copy.is_dir():
                    shutil.copytree(src, copy)
                    cmk = copy / "Cargo.toml"
                    mm = tomllib.loads(cmk.read_text())
                    if "package" in mm:
                        mm["package"]["name"] = name
                        cmk.write_text(_toml_dumps(mm))
                    # copied manifests carry paths relative to the SOURCE
                    # location — re-anchor them at the copy or they dangle
                    for ccm in copy.rglob("Cargo.toml"):
                        try:
                            cmm = tomllib.loads(ccm.read_text())
                        except tomllib.TOMLDecodeError:
                            continue
                        moved = False
                        orig_parent = (src / ccm.relative_to(copy)).parent
                        for tbl in _dep_tables(cmm):
                            for nn, vv in tbl.items():
                                if isinstance(vv, dict) and "path" in vv:
                                    tgt = (orig_parent / vv["path"]).resolve()
                                    vv["path"] = os.path.relpath(
                                        tgt, ccm.parent.resolve())
                                    moved = True
                        if moved:
                            ccm.write_text(_toml_dumps(cmm))
                for tbl, v in names[name]:
                    nv = {k: x for k, x in v.items()
                          if k not in ("git", "rev", "branch", "tag", "version",
                                       "workspace", "package")}
                    nv["path"] = os.path.relpath(copy.resolve(), cm.parent)
                    tbl[name] = nv
                    undo.setdefault(cm.relative_to(ws).as_posix(), {})[name] = v
                dirty = True
                log(f"{cm}: duplicated {pkg} dep '{name}' gets its own "
                    f"renamed tree copy")
        if dirty:
            cm.write_text(_toml_dumps(m))
    if undo:
        journal.parent.mkdir(parents=True, exist_ok=True)
        journal.write_text(json.dumps(undo))


def pin_duplicate_git_crate(stderr_text, ws, tried):
    """cargo vendor refuses the same crate+version coming from two git
    revs, and a patch cannot point back at the same repository. Patch
    every crate the lock draws from that repo to a fetched tree of the
    rev THE LOCK PINNED IT AT — one canonical path per crate, identical to
    upstream's own resolution, so feature requirements keep holding (a
    single-rev unification cannot work: craft apps mix a dozen revs and no
    one rev carries every crate or feature). Cross-tree deps are
    redirected to each crate's canonical tree during flattening (see
    flatten_workspace_members), which is what keeps the lockfile
    collision-free. Only genuinely duplicated crates need a decision —
    first lock entry wins, and a "does not have that feature" failure
    flips that crate to its next rev via `tried`. Path-patched crates stay
    in-tree and are never vendored. True when a pin was (re)written."""
    cmap, crevs = lock_git_crates(ws)
    m = DUP_SOURCES_RE.search(stderr_text)
    sel = re.search(r"failed to select a version for `([A-Za-z0-9_.-]+)`",
                    stderr_text)
    feat = re.search(r"does not have (?:that feature|a feature)", stderr_text)
    if m:
        dup_crate = m.group(1)
        repo = re.sub(r"\?rev=[0-9a-f]+$", "", m.group(2))
    elif sel and feat and sel.group(1) in cmap:
        dup_crate = sel.group(1)
        repo = cmap[dup_crate]
    else:
        return False
    if dup_crate not in [c for c, r in cmap.items() if r == repo]:
        return False
    # duplicated crate stuck on a failing rev: flip to the next candidate
    if not m:
        alts = list(dict.fromkeys(crevs.get(dup_crate, [])))
        declared = manifest_declared_rev(ws, repo, dup_crate)
        if declared and declared not in alts:
            alts.append(declared)
        done = tried.setdefault(dup_crate, [])
        cands = [rv for rv in alts if rv not in done]
        if not cands:
            return False
        tried.setdefault("overrides", {})[dup_crate] = cands[0]
        done.append(cands[0])
        log(f"{dup_crate} pinned at a feature-incompatible rev; "
            f"flipping to {cands[0][:8]}")
    overrides = tried.get("overrides", {})
    crate_tree = {}
    for crate, r in cmap.items():
        if r != repo:
            continue
        crate_tree[crate] = overrides.get(crate, crevs[crate][0])
    tag = hashlib.md5(repr(sorted(crate_tree.items())).encode()).hexdigest()[:8]
    # fetch every needed tree first: flattening redirects cross trees.
    # A tree flattened for a different crate mapping carries stale
    # redirects (crate flipped to another rev) — refetch it pristine.
    revs = sorted(set(crate_tree.values()))
    for rev in revs:
        pindir = dup_pin_dir(ws, repo, rev)
        if pindir.is_dir():
            marks = list(pindir.glob(".flattened-*"))
            if marks and not (pindir / f".flattened-{tag}").is_file():
                log(f"refetching {pindir.name}: flattened for another mapping")
                shutil.rmtree(pindir)
        if not pindir.is_dir():
            pindir.parent.mkdir(parents=True, exist_ok=True)
            fetch_tarball(f"{repo}/archive/{rev}.tar.gz", strip=1, dest=pindir)
    entries = {}
    for crate, rev in sorted(crate_tree.items()):
        pkg = _tree_member(ws, repo, rev, crate)
        if pkg is None:
            log(f"dup-pinned {rev[:8]}: no member '{crate}', leaving it on git")
            continue
        entries[crate] = pkg.relative_to(ws).as_posix()
    if not entries:
        die(f"dup-pinned {repo}: no patchable members found")
    for rev in revs:
        pindir = dup_pin_dir(ws, repo, rev)
        if not (pindir / f".flattened-{tag}").is_file():
            flatten_workspace_members(pindir, repo)
            # crates whose canonical tree is another rev keep their own
            # instance here (self-contained tree): version build metadata
            # makes the lockfile entry distinct — same name+version from
            # two paths is an ambiguous-lock hard error, and metadata is
            # semver-equal so every ^/=0.1.0 requirement still matches
            for cm in sorted(pindir.rglob("Cargo.toml")):
                try:
                    mm = tomllib.loads(cm.read_text())
                except tomllib.TOMLDecodeError:
                    continue
                name = mm.get("package", {}).get("name")
                ver = mm.get("package", {}).get("version", "")
                if not name or crate_tree.get(name, rev) == rev \
                        or "+" in ver:
                    continue
                mm["package"]["version"] = f"{ver}+{rev[:8]}"
                cm.write_text(_toml_dumps(mm))
            (pindir / f".flattened-{tag}").touch()
    log(f"duplicate git sources from {repo}; patching its "
        f"{len(entries)} lock crates to per-crate rev trees")
    set_patch_entries(ws, repo, entries)
    fix_renamed_dup_deps(ws, repo, crate_tree)
    return True


def git_source_blocks(config_text):
    # [source."git+https://…"] replacement blocks cargo vendor printed (the
    # cargo_prep macro only rewrites crates-io); kept as-is inside the vendor
    # archive for the spec to append to .cargo/config.toml
    paras = [p for p in re.split(r"\n\s*\n", config_text.strip())
             if '[source."git+' in p] if config_text.strip() else []
    # trailing blank line preserved: the old awk RS="" ORS="\n\n" emitted one
    return "\n\n".join(paras) + "\n\n" if paras else ""


# ---- vendor branches -----------------------------------------------------------

def ensure_archive(src_file):
    # spectool saves whatever a forge returns (a 300/404 HTML or text error
    # page) under the tarball name; fail fast with the real cause instead of
    # a cryptic tarfile.ReadError from the vendoring tool
    magic = Path(src_file).read_bytes()[:5]
    if magic[:2] == b"\x1f\x8b" or magic[:3] == b"BZh" \
            or magic[:5] == b"\xfd7zXZ" or magic[:4] in (b"PK\x03\x04", b"ustar") \
            or magic[:4] == b"\x28\xb5\x2f\xfd":
        return
    head = Path(src_file).read_bytes()[:120].decode("utf-8", "replace").strip()
    die(f"{src_file} is not an archive (spectool saved an error page?): {head!r}")


def spectool_get(spec):
    subprocess.run(["spectool", "-g", spec.name], check=True)
    lf = subprocess.run(["spectool", "--lf", spec.name],
                        capture_output=True, text=True, check=True).stdout
    url = lf.splitlines()[0].split()[1]
    src_file = Path(url.split("#")[0]).name
    ensure_archive(src_file)
    return url, src_file


def extract_source0(src_file):
    untar(src_file, ".")
    top = tar_first_top(src_file)
    d = Path(top) if top else Path(".")
    return d if d.is_dir() else Path(".")


def check_prep_topdir(spec, top):
    # topdir-mismatch class bit three times (atac ATAC-*, gping
    # gping-gping-v*, herdr herdr-app-*): %autosetup then dies mid-rpmbuild
    # with a generic "cd: no such directory". The tarball is in hand here,
    # so compare its top against the -n argument (default name-version)
    # before the expensive vendoring even starts.
    spec_text = spec.read_text()
    top = str(top)
    m = re.search(r"^%(?:auto)?setup\b(.*)$", spec_text, re.M)
    if not m or top in (".", None) or "-c" in m.group(1).split():
        return
    # expand name/version and every %global (tag, commit, ...) the -n arg uses
    macros = {"name": spec.stem}
    for tag_name, tag_val in re.findall(r"^%global\s+(\w+)\s+(\S+)", spec_text, re.M):
        macros.setdefault(tag_name, tag_val)
    for tag_name in ("Version", "Name"):
        hit = re.search(rf"^{tag_name}:\s+(\S+)", spec_text, re.M)
        if hit:
            macros.setdefault(tag_name.lower(), hit.group(1))
    n = re.search(r"(?:^|\s)-n\s+(\S+)", m.group(1))
    want = n.group(1) if n else "%{name}-%{version}"
    want = re.sub(r"%\{(\w+)\}", lambda mm: macros.get(mm.group(1), mm.group(0)), want)
    if "%{" in want:  # unknown macro: cannot expand, do not guess
        return
    if want != top:
        die(f"Source0 topdir is '{top}' but %setup cds into '{want}' "
            f"— fix the -n argument (e.g. -n {top})")


def vendor_go(spec):
    if shutil.which("go_vendor_archive") is None:
        dnf_install(["go-vendor-tools", "python3-specfile", "golang",
                     "git-core", "rpmdevtools"])
    subprocess.run(["spectool", "-g", spec.name], check=True)
    lf = subprocess.run(["spectool", "--lf", spec.name],
                        capture_output=True, text=True, check=True).stdout
    ensure_archive(Path(lf.splitlines()[0].split()[1].split("#")[0]).name)
    check_prep_topdir(spec, tar_first_top(
        Path(lf.splitlines()[0].split()[1].split("#")[0]).name))
    cmd = ["go_vendor_archive", "create"]
    if Path("go-vendor-tools.toml").is_file():
        cmd += ["--config", "go-vendor-tools.toml"]
    env = {**os.environ, "GOTOOLCHAIN": "local+auto"}
    subprocess.run(cmd + [spec.name], check=True, env=env)
    matches = sorted(Path(".").glob("*-vendor.tar.*"))
    return matches[0].name if matches else ""


def vendor_cargo(spec, spec_text):
    if shutil.which("cargo") is None:
        dnf_install(["cargo", "rust-packaging"])
    if shutil.which("spectool") is None:
        dnf_install(["rpmdevtools"])
    url, src_file = spectool_get(spec)
    d = extract_source0(src_file)
    check_prep_topdir(spec, d if d != Path(".") else None)
    # submodules (gitlinked vendor trees) must be in place before vendoring
    # and before the zig closure scan
    changed = fetch_submodules(d, url)
    # zig closure for cargo trees whose (sub)builds invoke zig (herdr's
    # ghostty-sys); the spec opts in via a zig-pkg.tar Source
    if ZIGSRC.search(spec_text):
        fetch_zig_closure(d, spec, spec_text)
    # the workspace may live in a subdirectory (openai/codex keeps it in
    # codex-rs/)
    ws = d
    if not (ws / "Cargo.toml").is_file():
        for sub in sorted(ws.iterdir()):
            if (sub / "Cargo.toml").is_file() and (sub / "Cargo.lock").is_file():
                ws = sub
                break
    ws = ws.resolve()
    for upd in CARGO_UPDATE.findall(spec_text):
        subprocess.run(["cargo", "update"] + upd.split(), cwd=ws, check=True)
        changed = True
    # vendor into a fresh dir name: some trees already carry a "vendor" dir
    reset_dup_pin_state(ws)
    r = subprocess.run(["cargo", "vendor", "--locked", "vendor-deps"],
                       cwd=ws, capture_output=True, text=True)
    if r.returncode != 0:
        # a repacked Source0 may carry a lock resolved against our path
        # patches: --locked refuses it before any duplicate surfaces
        r = subprocess.run(["cargo", "vendor", "vendor-deps"],
                           cwd=ws, capture_output=True, text=True)
    # each pin unifies one git repo at one rev; a wrong rev choice surfaces
    # as a feature error and is retried with the next candidate
    tried = {}
    pins = 0
    while r.returncode != 0 and pins < 8 \
            and pin_duplicate_git_crate(r.stderr, ws, tried):
        pins += 1
        changed = True
        r = subprocess.run(["cargo", "vendor", "vendor-deps"],
                           cwd=ws, capture_output=True, text=True)
        if r.returncode != 0:
            cause = [l for l in r.stderr.splitlines()
                     if l.startswith(("error:", "  "))]
            log(f"attempt {pins} still failing: "
                + " | ".join(cause[:3][:3]))
    if r.returncode != 0:
        r = subprocess.run(["cargo", "vendor", "vendor-deps"],
                           cwd=ws, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        die("cargo vendor failed")
    if drop_unvendored_git_patches(ws):
        changed = True
    Path("git-sources.conf").write_text(git_source_blocks(r.stdout))
    # trees that ship their own vendor/ keep it for the patches: our vendored
    # deps go to a SEPARATE dir — a merged dir breaks (registry replacement
    # demands checksums the patched copies lack, and drops the vendored ones)
    shutil.rmtree("vendor-deps", ignore_errors=True)  # stale from a previous run
    shutil.move(str(ws / "vendor-deps"), "vendor-deps")
    shutil.move("git-sources.conf", "vendor-deps/git-sources.conf")
    if changed:
        # after the move: repacking earlier embeds vendor-deps in Source0
        repack_dir(d, src_file)
    subprocess.run(["tar", "--zstd", "-cf", "vendor.tar.zst", "vendor-deps"],
                   check=True)
    shutil.rmtree("vendor-deps")
    if d != Path("."):
        shutil.rmtree(d, ignore_errors=True)
    return "vendor.tar.zst"


def vendor_zig(spec):
    if shutil.which("spectool") is None:
        dnf_install(["rpmdevtools"])
    url, src_file = spectool_get(spec)
    d = extract_source0(src_file)
    check_prep_topdir(spec, d if d != Path(".") else None)
    fetch_submodules(d, url)
    fetch_zig_closure(d, spec, spec.read_text())
    if d != Path("."):
        shutil.rmtree(d, ignore_errors=True)
    return "zig-pkg.tar.zst"


# ---- entry point ----------------------------------------------------------------

def expected_archives(spec_text):
    if GO.search(spec_text):
        return ["*-vendor.tar.*"]
    if CARGO.search(spec_text):
        exp = ["vendor.tar.zst"]
        if ZIGSRC.search(spec_text):
            exp.append("zig-pkg.tar.zst")
        return exp
    if ZIGSRC.search(spec_text):
        return ["zig-pkg.tar.*"]
    return []


def _is_source_archive(p):
    # what the old `find -name '*.tar.*' -o -name '*.tgz' -o -name '*.zip'` matched
    name = p.name
    return name.endswith((".tar.gz", ".tgz", ".zip")) or ".tar." in name


def _is_vendor_archive(p):
    name = p.name
    return (name == "vendor.tar.zst" or name.startswith("zig-pkg.tar.")
            or re.search(r"-vendor\.tar\.", name) is not None)


def vendor_fingerprint(spec, script):
    # every input that determines the vendor archive: spec bytes, this
    # script, the (non-vendor) source archives and the toolchain packages.
    # A matching .vendor-ok stamp + present archive skips re-vendoring.
    h = hashlib.sha256()
    for p in (spec, script):
        try:
            h.update(p.read_bytes())
        except OSError:
            pass
    paths = sorted(
        p for p in list(Path(".").glob("*")) + list(Path(".").glob("*/*"))
        if p.is_file() and _is_source_archive(p) and not _is_vendor_archive(p))
    for p in paths:
        h.update(f"{p} {p.stat().st_size}\n".encode())
    r = subprocess.run(
        ["rpm", "-q", "golang", "go-vendor-tools", "cargo", "rust-packaging"],
        capture_output=True, text=True)
    h.update(r.stdout.encode())
    return h.hexdigest()[:16]


def main():
    if len(sys.argv) != 3:
        die("usage: vendor-sources.py <source-dir> <spec>")
    srcdir = Path(sys.argv[1]).resolve()
    spec = Path(sys.argv[2]).parent.resolve() / Path(sys.argv[2]).name
    script = Path(__file__).resolve()
    os.chdir(srcdir)
    spec_text = spec.read_text()

    expected = expected_archives(spec_text)
    if expected:
        ok = Path(".vendor-ok")
        if ok.is_file():
            fp = vendor_fingerprint(spec, script)
            present = all(any(Path(".").glob(g)) for g in expected)
            if fp == ok.read_text().strip() and present:
                log(f"inputs unchanged, reusing {next(iter(sorted(Path('.').glob(expected[0]))))}")
                stats("skip")
                return

    if GO.search(spec_text):
        vendor_archive = vendor_go(spec)
    elif CARGO.search(spec_text):
        vendor_archive = vendor_cargo(spec, spec_text)
    elif ZIGSRC.search(spec_text):
        vendor_archive = vendor_zig(spec)
    else:
        return

    if vendor_archive and not Path(vendor_archive).is_file():
        die(f"expected {vendor_archive} in {srcdir} but it is missing")
    if expected:
        Path(".vendor-ok").write_text(vendor_fingerprint(spec, script) + "\n")
        stats("run")


if __name__ == "__main__":
    main()
