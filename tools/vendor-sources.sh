#!/usr/bin/env bash
set -euo pipefail

# Vendor Go/Rust dependencies at SRPM build time (network is available in the
# COPR make_srpm step; the binary build afterwards runs offline).
srcdir="${1:?usage: vendor-sources.sh <source-dir> <spec>}"
spec="${2:?usage: vendor-sources.sh <source-dir> <spec>}"
# Normalize to absolute before changing directories
spec="$(cd "$(dirname "$spec")" && pwd)/$(basename "$spec")"
cd "$srcdir"

dnfinstall() { dnf -y install --nodocs --setopt=install_weak_deps=0 "$@" >/dev/null 2>&1; }
[ "$(id -u)" = 0 ] || dnfinstall() { sudo dnf -y install --nodocs --setopt=install_weak_deps=0 "$@" >/dev/null 2>&1; }

vendor_archive=""
if grep -qE '^%goprep|go-vendor-tools' "$spec"; then
  command -v go_vendor_archive >/dev/null 2>&1 \
    || dnfinstall go-vendor-tools python3-specfile golang git-core rpmdevtools
  spectool -g "$(basename "$spec")"
  config=()
  [ -f go-vendor-tools.toml ] && config=(--config go-vendor-tools.toml)
  GOTOOLCHAIN=local+auto go_vendor_archive create "${config[@]}" "$(basename "$spec")"
  vendor_archive="$(ls ./*-vendor.tar.* 2>/dev/null | head -1 || true)"
elif grep -q '^%cargo_prep' "$spec"; then
  command -v cargo >/dev/null 2>&1 \
    || dnfinstall cargo rust-packaging rpmdevtools
  spectool -g "$(basename "$spec")"
  url="$(spectool --lf "$(basename "$spec")" | awk 'NR==1{print $2}')"
  src_file="$(basename "${url%%#*}")"
  tar -xf "$src_file"
  dir="$(tar -tf "$src_file" | head -1 | cut -d/ -f1 || true)"
  [ -d "$dir" ] || dir=.
  (cd "$dir" && cargo vendor --locked >/dev/null 2>&1 || cargo vendor >/dev/null)
  [ -d "$dir/vendor" ] && mv "$dir/vendor" vendor
  tar --zstd -cf vendor.tar.zst vendor
  rm -rf vendor "$dir"
  vendor_archive="vendor.tar.zst"
fi

if [ -n "$vendor_archive" ] && [ ! -f "$vendor_archive" ]; then
  echo "vendor-sources: expected $vendor_archive in $srcdir but it is missing" >&2
  exit 1
fi
