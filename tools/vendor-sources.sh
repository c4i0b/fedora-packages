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
    || dnfinstall cargo rust-packaging
  command -v spectool >/dev/null 2>&1 || dnfinstall rpmdevtools
  spectool -g "$(basename "$spec")"
  url="$(spectool --lf "$(basename "$spec")" | awk 'NR==1{print $2}')"
  src_file="$(basename "${url%%#*}")"
  tar -xf "$src_file"
  dir="$(tar -tf "$src_file" | head -1 | cut -d/ -f1 || true)"
  [ -d "$dir" ] || dir=.
  # workspace may live in a subdirectory (e.g. openai/codex keeps it in codex-rs/)
  ws="$dir"
  if [ ! -f "$ws/Cargo.toml" ]; then
    for d in "$dir"/*/; do
      if [ -f "${d}Cargo.toml" ] && [ -f "${d}Cargo.lock" ]; then ws="${d%/}"; break; fi
    done
  fi
  # absolute: the merge below cds around and would break relative paths
  ws="$(cd "$ws" && pwd)"
  # vendor into a fresh dir name: some trees already carry a "vendor" dir
  (cd "$ws" && cargo vendor --locked vendor-deps 2>/dev/null || cargo vendor vendor-deps 2>/dev/null) > vendor-cargo-config.toml
  # git-sourced crates (e.g. storytold craft-libs) need their own [source]
  # replacements appended to the config %cargo_prep generates
  awk 'BEGIN{RS=""; ORS="\n\n"} /\[source\."git\+/' vendor-cargo-config.toml > git-sources.conf
  rm -f vendor-cargo-config.toml
  # trees that ship their own vendor/ (patched crates via [patch.crates-io])
  # keep it for the patches: our vendored deps go to a SEPARATE dir — a merged
  # dir breaks (registry replacement demands checksums the patched copies
  # lack, and drops the vendored ones)
  mv "$ws/vendor-deps" vendor-deps
  mv git-sources.conf vendor-deps/
  tar --zstd -cf vendor.tar.zst vendor-deps
  rm -rf vendor-deps "$dir"
  vendor_archive="vendor.tar.zst"
fi

if [ -n "$vendor_archive" ] && [ ! -f "$vendor_archive" ]; then
  echo "vendor-sources: expected $vendor_archive in $srcdir but it is missing" >&2
  exit 1
fi
