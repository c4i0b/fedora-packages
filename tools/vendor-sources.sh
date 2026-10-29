#!/usr/bin/env bash
set -euo pipefail

# Vendor Go/Rust/zig dependencies at SRPM build time (network is available in
# the COPR make_srpm step; the binary build afterwards uses the vendored copy).
srcdir="${1:?usage: vendor-sources.sh <source-dir> <spec>}"
spec="${2:?usage: vendor-sources.sh <source-dir> <spec>}"
# Normalize to absolute before changing directories
spec="$(cd "$(dirname "$spec")" && pwd)/$(basename "$spec")"
cd "$srcdir"

# Fingerprint of every input that determines the vendor archive: spec bytes,
# this script, the (non-vendor) source archives, and toolchain packages. A
# matching .vendor-ok stamp + present archive skips re-vendoring entirely —
# CI restores both from the sources cache; COPR builders start clean and
# never hit this path.
vendor_fingerprint() {
  {
    sha256sum "$spec" "${BASH_SOURCE[0]}" 2>/dev/null
    find . -maxdepth 2 \( -name '*.tar.*' -o -name '*.tgz' -o -name '*.zip' \) \
      ! -name '*-vendor.tar.*' ! -name 'vendor.tar.zst' ! -name 'zig-pkg.tar.*' \
      -printf '%p %s\n' | sort
    rpm -q golang go-vendor-tools cargo rust-packaging 2>/dev/null || true
  } | sha256sum | cut -c1-16
}

vendor_kind() {
  if grep -qE '^%goprep|go-vendor-tools' "$spec"; then printf '*-vendor.tar.*'
  elif grep -q '^%cargo_prep' "$spec"; then printf 'vendor.tar.zst'
  elif grep -q '^Source[0-9]*:.*zig-pkg.tar' "$spec"; then printf 'zig-pkg.tar.*'
  else printf ''; fi
}

kind="$(vendor_kind)"
if [ -n "$kind" ] && [ -f .vendor-ok ]; then
  fp="$(vendor_fingerprint)"
  if [ "$fp" = "$(cat .vendor-ok)" ] && ls $kind >/dev/null 2>&1; then
    echo "vendor-sources: inputs unchanged, reusing $(ls $kind | head -1)"
    if [ -n "${VENDOR_STATS:-}" ]; then echo skip >> "$VENDOR_STATS"; fi
    exit 0
  fi
fi

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
  # [patch.crates-io] GIT entries for crates nothing in the graph depends on
  # are never vendored, yet cargo validates every patch entry against its
  # source and aborts offline — drop them from the tree the binary build will
  # extract (the extracted copy dies with the SRPM chroot, so re-pack the
  # tarball too). PATH entries must be kept: path-patched crates (pdfcraft's
  # vendor/hayro) stay local and never appear in the vendor dir, yet the
  # build resolves them from the tree itself.
  dropped=0
  while IFS= read -r -d '' cm; do
    grep -q '^\[patch\.crates-io\]' "$cm" || continue
    tmp="$cm.tmp"; : > "$tmp"; inpatch=0
    while IFS= read -r line || [ -n "$line" ]; do
      case "$line" in
        '[patch.crates-io]'*) inpatch=1 ;;
        '['*) inpatch=0 ;;
      esac
      if [ "$inpatch" = 1 ] && [[ "$line" =~ ^[A-Za-z0-9_-]+[[:space:]]*=[[:space:]]*\{[[:space:]]*git ]]; then
        crate="${line%%=*}"; crate="${crate//[[:space:]]/}"
        if [ ! -d "$ws/vendor-deps/$crate" ] \
           && ! ls "$ws/vendor-deps/$crate"-[0-9]* >/dev/null 2>&1; then
          echo "vendor-sources: dropping unvendored git patch entry: $crate ($cm)" >&2
          dropped=1
          continue
        fi
      fi
      printf '%s\n' "$line" >> "$tmp"
    done < "$cm"
    mv "$tmp" "$cm"
  done < <(find "$ws" -name Cargo.toml -not -path '*/vendor*' -print0)
  if [ "$dropped" = 1 ]; then
    case "$src_file" in
      *.tar.gz|*.tgz|*.crate) zflag=-z ;;
      *.tar.xz) zflag=-J ;;
      *.tar.bz2) zflag=-j ;;
      *) zflag="" ;;
    esac
    tar $zflag -cf "$src_file" "$dir"
  fi
  # git-sourced crates (e.g. storytold craft-libs) need their own [source]
  # replacements appended to the config %cargo_prep generates
  awk 'BEGIN{RS=""; ORS="\n\n"} /\[source\."git\+/' vendor-cargo-config.toml > git-sources.conf
  rm -f vendor-cargo-config.toml
  # trees that ship their own vendor/ (patched crates via [patch.crates-io])
  # keep it for the patches: our vendored deps go to a SEPARATE dir — a merged
  # dir breaks (registry replacement demands checksums the patched copies
  # lack, and drops the vendored ones)
  # a stale vendor-deps from a previous local run would nest as
  # vendor-deps/vendor-deps inside the mv below
  rm -rf vendor-deps
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
      # COPR builder egress breaks HTTP/2 to several forges (curl exit 92) and
      # flaps mid-transfer; force HTTP/1.1 and retry hard, verbosely.
      if [ "$commit" != "-" ]; then
        repo="${url%%#*}"; repo="${repo%%\?*}"
        git init -q "$d/tmpg"
        ok=0
        for attempt in 1 2 3 4 5; do
          echo "vendor-sources: git fetch $repo ($commit), attempt $attempt" >&2
          if (cd "$d/tmpg" &&
              git -c http.version=HTTP/1.1 fetch -q --depth 1 "$repo" "$commit" &&
              git checkout -q FETCH_HEAD && rm -rf .git); then ok=1; break; fi
          rm -rf "$d/tmpg"; git init -q "$d/tmpg"
          sleep $((attempt * 10))
        done
        [ "$ok" = 1 ] || { echo "vendor-sources: git fetch failed: $repo" >&2; exit 1; }
        shopt -s dotglob nullglob
        mv "$d/tmpg"/* "$d/"
        shopt -u dotglob nullglob
        rmdir "$d/tmpg"
      else
        f="zon-cache-$(basename "$url")"
        ok=0
        for attempt in 1 2 3 4 5; do
          echo "vendor-sources: fetching $url, attempt $attempt" >&2
          if curl --http1.1 -sfL --connect-timeout 30 --max-time 600 \
               --retry 3 --retry-delay 10 --retry-all-errors -o "$f" "$url"; then
            ok=1; break
          fi
          sleep $((attempt * 10))
        done
        [ "$ok" = 1 ] || { echo "vendor-sources: download failed: $url" >&2; exit 1; }
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

if [ -n "$kind" ]; then
  vendor_fingerprint > .vendor-ok
  if [ -n "${VENDOR_STATS:-}" ]; then echo run >> "$VENDOR_STATS"; fi
fi
