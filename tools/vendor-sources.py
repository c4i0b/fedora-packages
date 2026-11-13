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
import urllib.request
import zipfile
from pathlib import Path

GO = re.compile(r"^%goprep|^go-vendor-tools", re.M)
CARGO = re.compile(r"^%cargo_prep", re.M)
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


def pin_duplicate_git_crate(stderr_text, ws):
    """cargo vendor refuses the same crate+version coming from two git
    sources (an upstream lock can pin e.g. winprint at two revs), and a
    patch cannot point back at the same repository. Fetch the first
    source's rev into the tree and unify via a path [patch."<repo>"] entry
    appended to the workspace manifest; path-patched crates stay in-tree
    and are never vendored. The caller retries vendoring unlocked and
    repacks the tree. True when the manifest was patched."""
    m = re.search(
        r"found duplicate version of package `([A-Za-z0-9_.-]+) v\S+` "
        r"vendored from two sources:\s*\n\s*source 1: (\S+?rev=([0-9a-f]+))#",
        stderr_text)
    if not m:
        return False
    crate, src1, rev = m.group(1), m.group(2), m.group(3)
    repo = re.sub(r"\?rev=[0-9a-f]+$", "", src1)
    log(f"duplicate git sources for {crate}; pinning to {rev[:8]} via path patch")
    pindir = Path(ws) / "dup-pinned" / crate
    if not pindir.is_dir():
        pindir.parent.mkdir(parents=True, exist_ok=True)
        fetch_tarball(f"{repo}/archive/{rev}.tar.gz", strip=1, dest=pindir)
    manifest = Path(ws) / "Cargo.toml"
    with manifest.open("a") as f:
        f.write(f'\n[patch."{repo}"]\n'
                f'{crate} = {{ path = "dup-pinned/{crate}" }}\n')
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
    # vendor into a fresh dir name: some trees already carry a "vendor" dir
    r = subprocess.run(["cargo", "vendor", "--locked", "vendor-deps"],
                       cwd=ws, capture_output=True, text=True)
    if r.returncode != 0 and pin_duplicate_git_crate(r.stderr, ws):
        changed = True
        r = subprocess.run(["cargo", "vendor", "vendor-deps"],
                           cwd=ws, capture_output=True, text=True)
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
