#!/usr/bin/env bash
set -euo pipefail

# Vendor Go/Rust/zig dependencies at SRPM build time (network is available in
# the COPR make_srpm step; the binary build afterwards uses the vendored copy).
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
elif grep -q '^Source[0-9]*:.*zig-pkg.tar' "$spec"; then
  # zig: pre-fetch the build.zig.zon dependency closure into a --system package
  # store. zig's own http client is unreliable on some builders; curl+git are not.
  missing=""
  for bin in curl file git tar unzip zstd; do
    command -v "$bin" >/dev/null 2>&1 || missing="$missing $bin"
  done
  [ -n "${missing:-}" ] && dnfinstall git-core file zstd curl tar unzip
  command -v python3 >/dev/null 2>&1 || dnfinstall python3
  command -v spectool >/dev/null 2>&1 || dnfinstall rpmdevtools
  spectool -g "$(basename "$spec")"
  url="$(spectool --lf "$(basename "$spec")" | awk 'NR==1{print $2}')"
  src_file="$(basename "${url%%#*}")"
  tar -xf "$src_file"
  dir="$(tar -tf "$src_file" | head -1 | cut -d/ -f1 || true)"
  [ -d "$dir" ] || dir=.
  rm -rf zig-pkg && mkdir zig-pkg
  # zon files of a *package* declare its deps only at the root; nested ones
  # (examples/, docs sub-projects) are not part of the zig dep graph
  zon_urls() {
    local zons; zons="$(mktemp)"
    if [ "$2" = root ]; then
      cat "$1/build.zig.zon" > "$zons" 2>/dev/null || true
    else
      find "$1" -name build.zig.zon -not -path '*/zig-pkg/*' -exec cat {} + > "$zons" || true
    fi
    python3 - "$zons" <<'PY'
import re, sys
s = open(sys.argv[1]).read()
for m in re.finditer(r"\.url\s*=\s*\"((?:git\+)?https://[^\"]+)\",\s*\n\s*\.hash\s*=\s*\"([^\"]+)\"", s):
    u = m.group(1)
    if u.startswith("git+"):
        repo, _, commit = u[4:].partition("#")
        print(repo, commit or "-", m.group(2))
    else:
        print(u, "-", m.group(2))
PY
    rm -f "$zons"
  }
  : > zon-queue.txt
  zon_urls "$dir" tree >> zon-queue.txt
  declare -A zon_done
  while true; do
    sort -u zon-queue.txt > zon-work.txt
    new=0
    while read -r url commit hash; do
      [ -n "${zon_done[$url]:-}" ] && continue
      zon_done[$url]=1; new=1
      d="zig-pkg/$hash"
      [ -d "$d" ] && continue # same id reachable via several URLs
      mkdir -p "$d"
      if [ "$commit" != "-" ]; then
        repo="${url%%#*}"; repo="${repo%%\?*}"
        git init -q "$d/tmpg"
        (cd "$d/tmpg" &&
         git remote add origin "$repo" &&
         git fetch -q --depth 1 origin "$commit" &&
         git checkout -q FETCH_HEAD && rm -rf .git)
        shopt -s dotglob nullglob
        mv "$d/tmpg"/* "$d/"
        shopt -u dotglob nullglob
        rmdir "$d/tmpg"
      else
        f="zon-cache-$(basename "$url")"
        curl -sfL --max-time 300 --retry 3 -o "$f" "$url"
        ft=$(file -b "$f")
        if [[ "$ft" == *Zip* ]]; then
          unzip -q "$f" -d "$d"
          # strip a single top-level dir like the tar branch does
          shopt -s dotglob nullglob
          entries=("$d"/*)
          if [ "${#entries[@]}" = 1 ] && [ -d "${entries[0]}" ]; then
            mv "${entries[0]}"/* "$d/"
            rmdir "${entries[0]}"
          fi
          shopt -u dotglob nullglob
          rm -f "$f"
          zon_urls "$d" root >> zon-queue.txt
          continue
        fi
        case "$ft" in
          *Zstandard*) tarflag="--zstd" ;; *XZ*) tarflag="-J" ;;
          *gzip*) tarflag="-z" ;; *) tarflag="" ;;
        esac
        n=$(tar $tarflag -tf "$f" | cut -d/ -f1 | sort -u | wc -l)
        if [ "$n" = 1 ]; then tar $tarflag -xf "$f" -C "$d" --strip-components=1
        else tar $tarflag -xf "$f" -C "$d"; fi
        rm -f "$f"
      fi
      zon_urls "$d" root >> zon-queue.txt
    done < zon-work.txt
    [ "$new" = 0 ] && break
  done
  rm -f zon-queue.txt zon-work.txt
  [ -n "$(ls -A zig-pkg)" ] || { echo "vendor-sources: zig-pkg store is empty" >&2; exit 1; }
  tar --zstd -cf zig-pkg.tar.zst zig-pkg
  rm -rf zig-pkg "$dir"
  vendor_archive="zig-pkg.tar.zst"
fi

if [ -n "$vendor_archive" ] && [ ! -f "$vendor_archive" ]; then
  echo "vendor-sources: expected $vendor_archive in $srcdir but it is missing" >&2
  exit 1
fi
