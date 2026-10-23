#!/usr/bin/env bash
# Refresh COPR status artifacts:
#   badges/*.json  — shields.io endpoint JSON (per-chroot semaphores, package
#                    count, highlighted package versions)
#   README.md      — the build-status block between the begin/end markers
# Data sources: api_3/monitor (per package x chroot state, attempted version)
# and the chroot repodata primary.xml (published = actually installable
# version; the last failed build never enters the repo).
set -euo pipefail

project="${1:?usage: update-badges.sh copr_owner/project [github_owner/project]}"
owner="${project%%/*}"
name="${project#*/}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=host.sh
source "$root/tools/host.sh"
# COPR owner/name and the repo identity differ in this repo: badges link to
# raw/web (repo owner) but to the COPR monitor (COPR owner).
github="${2:-${GIT_SLUG}}"
gowner="${github%%/*}"
gname="${github#*/}"

# pkg -> upstream homepage for the README badge links: the `upstream` file
# when it resolves (GitHub/GitLab/Codeberg/forgejo/npm/URL), else the spec's
# URL: tag, else nothing (the badge falls back to our package directory)
links_file="$(mktemp)"
trap 'rm -f "$links_file"' EXIT
for dir in "$root"/packages/*/; do
  pkg="$(basename "$dir")"
  spec=("$dir"/*.spec)
  link=""
  [ -f "$dir/upstream" ] && link="$(upstream_home "$(cat "$dir/upstream")")"
  if [ -z "$link" ] && [ -e "${spec[0]}" ]; then
    link="$(sed -n 's/^URL:[[:space:]]*//p' "${spec[0]}" | head -1 | tr -d '[:space:]')"
  fi
  [ -n "$link" ] && printf '%s\t%s\n' "$pkg" "$link" >>"$links_file"
done

python3 - "$root" "$owner" "$name" "$gowner" "$gname" "$GIT_RAW_BASE" "$GIT_WEB_BASE" "$links_file" <<'PY'
import json, gzip, os, re, sys, time, urllib.request

root, owner, project, gowner, gproject, git_raw_base, git_web_base, links_file = sys.argv[1:9]

links = {}
for line in open(links_file):
    pkg, url = line.rstrip("\n").split("\t", 1)
    links[pkg] = url
base = f"https://download.copr.fedorainfracloud.org/results/{owner}/{project}"
copr = f"https://copr.fedorainfracloud.org/coprs/{owner}/{project}"
raw = f"{git_raw_base}/{gowner}/{gproject}/main/badges"

BADGE_REV = 2  # bump to force GitHub camo to re-fetch every badge URL

def get(url, tries=3):
    # the results CDN (CloudFront -> packages.redhat.com/S3 redirects) drops
    # or mis-serves occasional requests; retry with growing backoff
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "update-badges"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception:
            if attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))

mon = json.loads(get(
    f"https://copr.fedorainfracloud.org/api_3/monitor?ownername={owner}&projectname={project}"
))["packages"]

def iter_cells():
    for pkg in mon:
        for chroot, c in pkg["chroots"].items():
            yield {"name": pkg["name"], "chroot": chroot, **c}

# ---- per-chroot semaphores -------------------------------------------------
chroots = {}
for cell in iter_cells():
    chroots.setdefault(cell["chroot"], []).append(cell)

def sort_key(c):
    m = re.match(r"fedora-(\d+)", c)
    return (0, int(m.group(1))) if m else ((1, 0) if "rawhide" in c else (2, 0))

# chroot naming is arch-aware: with a single arch per base, names/labels stay
# as today ("fedora 43"); once another arch joins, files and labels
# disambiguate ("fedora-43-aarch64" / "fedora 43 x86_64")
ARCH_RE = re.compile(r"-(x86_64|aarch64|ppc64le|s390x|riscv64)$")

def split_chroot(c):
    m = ARCH_RE.search(c)
    return (c[:m.start()], m.group(1)) if m else (c, "")

arches_by_base = {}
for c in chroots:
    # careful not to shadow the module-level `base` (the download URL):
    # published_versions() depends on it
    cbase, carch = split_chroot(c)
    arches_by_base.setdefault(cbase, set()).add(carch)

def bname(c):
    base, arch = split_chroot(c)
    return f"{base}-{arch}" if len(arches_by_base[base]) > 1 else base

def label(c):
    base, arch = split_chroot(c)
    txt = (base.replace("fedora-", "fedora ").replace("epel-", "epel ")
               .replace("fedora-rawhide", "rawhide"))
    return f"{txt} {arch}" if len(arches_by_base[base]) > 1 else txt

os.makedirs(f"{root}/badges", exist_ok=True)

def badge(fname, lbl, message, color):
    with open(f"{root}/badges/{fname}.json", "w") as f:
        json.dump({"schemaVersion": 1, "label": lbl,
                   "message": message, "color": color}, f)
        f.write("\n")

for chroot, cell_list in sorted(chroots.items(), key=lambda kv: sort_key(kv[0])):
    ok = sum(c["state"] == "succeeded" for c in cell_list)
    bad = sum(c["state"] == "failed" for c in cell_list)
    inflight = len(cell_list) - ok - bad
    # the message keeps the succeeded count; only the color flags failures
    msg = str(ok)
    color = "red" if bad else ("yellow" if inflight else "brightgreen")
    badge(bname(chroot), label(chroot), msg, color)

packages = sorted({c["name"] for c in mon})
badge("packages", "packages", str(len(packages)), "blue")

expected = {bname(c) for c in chroots} | set(packages) | {"packages"}
d = f"{root}/badges"
for f in os.listdir(d):
    if f.endswith(".json") and f[:-len(".json")] not in expected:
        os.remove(os.path.join(d, f))
        print(f"pruned stale badge: {f}")

# ---- per-package version badges (any succeeded chroot wins) ----------------
# pkg_version is None for fresh/queued builds
latest, attempted, known, has_fail, inflight = {}, {}, {}, set(), set()

def published_versions(chroot):
    """name -> version of packages actually in the chroot binary repo.
    Returns None when the repodata cannot be fetched/parsed (so callers can
    tell 'fetch failed' from 'package not in repo'); the cache-buster works
    around the results CDN serving stale content."""
    url = f"{base}/{chroot}/repodata/repomd.xml?nc={time.time_ns()}"
    try:
        repomd = get(url).decode()
        href = re.search(r'href="(repodata/[^"]*primary\.xml\.gz)"', repomd).group(1)
        xml = gzip.decompress(
            get(f"{base}/{chroot}/{href}?nc={time.time_ns()}")).decode(errors="replace")
        return dict(re.findall(
            r'<name>([^<]+)</name>.*?<version[^>]*?ver="([^"]+)"', xml, re.S))
    except Exception as e:
        print(f"WARNING: repodata fetch failed for {chroot}: {e}")
        return None

pub_cache = {}
# name -> version actually installable; once a rebuild is submitted the
# monitor stops reporting the previous succeeded state, so the repodata is
# the only source for "last complete build" while one is in flight
published = {}
for chroot in chroots:
    pub_cache.setdefault(chroot, published_versions(chroot) or {})
    for pkg_name, ver in pub_cache[chroot].items():
        published.setdefault(pkg_name, ver)
for c in iter_cells():
    pkg, ver = c["name"], (c["pkg_version"] or "").rsplit("-", 1)[0]
    if c["state"] == "succeeded" and pkg not in latest:
        latest[pkg] = ver
    if c["state"] == "failed":
        has_fail.add(pkg)
        attempted.setdefault(pkg, ver)
    if c["state"] in ("waiting", "pending", "starting", "importing", "running"):
        inflight.add(pkg)
    if ver and pkg not in known:
        known[pkg] = ver
badge_lines = []
url = (f"https://img.shields.io/endpoint?url="
       + raw.replace(":", "%3A").replace("/", "%2F"))
for pkg in packages:
    # blue = published
    # yellow = build live in COPR (message keeps the last fully published
    # version, not the in-flight one)
    # red = failed, never published
    # grey = idle (canceled/never attempted, no failure)
    if pkg in latest:
        badge(pkg, pkg, f"v{latest[pkg]}", "blue")
    elif pkg in has_fail:
        badge(pkg, pkg, f"v{attempted.get(pkg, '?')} \u2717", "red")
    elif pkg in inflight:
        badge(pkg, pkg, f"v{published.get(pkg, known.get(pkg, '?'))}", "yellow")
    else:
        badge(pkg, pkg, f"v{known.get(pkg, '?')}", "lightgrey")
    ver = (latest.get(pkg) or attempted.get(pkg) or published.get(pkg)
           or known.get(pkg) or "?")
    gh_pkg_url = f"{git_web_base}/{gowner}/{gproject}/tree/main/packages/{pkg}"
    badge_lines.append(
        f"[![{pkg}]({url}"
        f"%2F{pkg}.json%3Fv%3D{ver}%2Er{BADGE_REV})"
        f"]({gh_pkg_url}/)")

# ---- failures table (published comes from chroot repodata) ----------------
DASH = "\u2014"
failed = {}
for c in iter_cells():
    if c["state"] == "failed":
        failed.setdefault(c["name"], []).append(c)

pub_cache = {}
lines = []
for pkg in sorted(failed):
    cell_list = failed[pkg]
    ch_list = sorted((c["chroot"] for c in cell_list), key=sort_key)
    attempted = cell_list[0]["pkg_version"] or "?"
    build_id = max(c["build_id"] for c in cell_list)
    pub_parts = []
    for ch in ch_list:
        if ch not in pub_cache:
            pub_cache[ch] = published_versions(ch)
        pub_parts.append("?" if pub_cache[ch] is None else pub_cache[ch].get(pkg))
    if all(v == "?" for v in pub_parts):
        # every lookup failed: publishing "—" would claim the package was
        # never published; fail the run and keep the previous table instead
        sys.exit(f"repodata unfetchable for every failing chroot of {pkg}; "
                 "keeping the previous build-status block")
    if any(v and v != "?" for v in pub_parts):
        # per-chroot only when they diverge
        pub = pub_parts[0] if len(set(pub_parts)) == 1 and pub_parts[0] \
            else "<br>".join(f"{v or DASH} ({label(ch)})"
                             for v, ch in zip(pub_parts, ch_list))
    else:
        pub = DASH
    failed_in = "<br>".join(label(ch) for ch in ch_list)
    lines.append(f"| {pkg} | {pub} | {attempted} | {failed_in} "
                 f"| [#{build_id}]({copr}/build/{build_id}/) |")

from datetime import datetime, timezone
ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
if lines:
    body = ("### :x: build failures\n\n"
            "| package | published | attempted | failed in | build |\n"
            "|---|---|---|---|---|\n" + "\n".join(lines) + "\n")
    block = body + f"\n*Updated {ts} UTC automatically by GitHub Actions.*\n"
else:
    body = "**\u2705 all green**\n"
    block = f"**Updated {ts} UTC automatically by GitHub Actions.**\n"

rp = f"{root}/README.md"
readme = open(rp).read()
begin, end = "<!-- build-status begin -->", "<!-- build-status end -->"
import hashlib
def bust(path):
    with open(path, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()[:8]

chroot_lines = []
chroot_lines.append(
    f"[![packages]({url}"
    f"%2Fpackages.json%3Fv%3D{bust(f'{root}/badges/packages.json')}%2Er{BADGE_REV})"
    f"]({copr}/packages/)")
for chroot in sorted(chroots, key=sort_key):
    b = bname(chroot)
    chroot_lines.append(
        f"[![{label(chroot)}]({url}"
        f"%2F{b}.json%3Fv%3D{bust(f'{root}/badges/{b}.json')}%2Er{BADGE_REV})"
        f"]({copr}/monitor/)")

cbegin, cend = "<!-- chroot-badges begin -->", "<!-- chroot-badges end -->"
if cbegin not in readme or cend not in readme:
    sys.exit("README.md is missing the chroot-badges markers")
head, rest = readme.split(cbegin, 1)
_, tail = rest.split(cend, 1)
readme = f"{head}{cbegin}\n" + "\n".join(chroot_lines) + f"\n{cend}{tail}"

pbegin, pend = "<!-- package-badges begin -->", "<!-- package-badges end -->"
if pbegin not in readme or pend not in readme:
    sys.exit("README.md is missing the package-badges markers")
head, rest = readme.split(pbegin, 1)
_, tail = rest.split(pend, 1)
readme = f"{head}{pbegin}\n" + "\n".join(badge_lines) + f"\n{pend}{tail}"

if begin not in readme or end not in readme:
    sys.exit("README.md is missing the build-status markers")
head, rest = readme.split(begin, 1)
_, tail = rest.split(end, 1)
# the "updated" note is a last-STATE-CHANGE timestamp: only rewrite the block
# when the status itself changed, so refreshes with no change do not commit
current = rest.split(end, 1)[0]
def essence(t):
    t = re.sub(r"Updated [0-9-]+ [0-9:]+ UTC automatically by GitHub Actions", "", t)
    return "\n".join(l for l in t.split("\n") if l.strip()).strip()
# unchanged status keeps its existing timestamp; the chroot/package blocks are
# still rebuilt, so a plain file diff decides whether anything gets written
if essence(current) == essence(body):
    print("build-status unchanged; keeping the existing timestamp")
    readme = f"{head}{begin}\n{current.lstrip()}{end}{tail}"
else:
    readme = f"{head}{begin}\n{block.rstrip()}\n{end}{tail}"
if readme != open(rp).read():
    open(rp, "w").write(readme)
print(f"badges refreshed: {len(chroots)} chroots, {len(packages)} packages, "
      f"{len(failed)} failing")
PY
