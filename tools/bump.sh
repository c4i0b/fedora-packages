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

rpmdev-bumpspec -n "$ver" -c "Update to $ver" "$spec"
echo "bumped $pkg to $ver"
