#!/usr/bin/env bash
set -euo pipefail

usage="usage: bump.sh <package> <version>"
pkg="${1:?$usage}"
ver="${2:?$usage}"

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
spec="$(ls "$root/packages/$pkg"/*.spec | head -1)"

# Date-style upstream tags (e.g. vinceliuice themes) carry '-', which RPM
# Version forbids: sanitize for Version, keep the raw tag in "%global tag"
# (Source0 URLs reference it) and keep both in sync on every bump.
raw_ver="$ver"
ver="$(printf '%s' "$ver" | sed 's/[- ]/./g')"
if grep -q '^%global tag ' "$spec"; then
  sed -i "s|^%global tag .*|%global tag    ${raw_ver}|" "$spec"
fi

# runner lacks rpmdev-bumpspec; this mimics its output
if command -v rpmdev-bumpspec >/dev/null; then
  rpmdev-bumpspec -n "$ver" -c "Update to $ver" "$spec"
else
  python3 - "$spec" "$ver" <<'PY'
import datetime as d
import re, subprocess, sys

spec, ver = sys.argv[1], sys.argv[2]
text = open(spec).read()
text = re.sub(r"^Version:\s+\S+", f"Version:        {ver}", text, flags=re.M)
text = re.sub(r"^Release:\s+\S+", r"Release:        1%{?dist}", text, flags=re.M)
who = subprocess.run(["git", "config", "user.name"],
                     capture_output=True, text=True).stdout.strip()
email = subprocess.run(["git", "config", "user.email"],
                       capture_output=True, text=True).stdout.strip()
date = d.datetime.now(d.UTC).strftime("%a %b %d %Y")
entry = f"* {date} {who} <{email}> - {ver}-1\n- Update to {ver}\n"
text = re.sub("%changelog\\n", f"%changelog\\n{entry}\\n", text, count=1)
open(spec, "w").write(text)
PY
fi
echo "bumped $pkg to $ver"
