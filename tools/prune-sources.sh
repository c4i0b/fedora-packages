#!/usr/bin/env bash
set -euo pipefail

# Keep the sources cache bounded by the live set: rpmbuild downloads tarballs
# into the package dir, so after a bump the old version would linger until
# LRU eviction (which also evicts the go/cargo module caches). The downloads
# are gitignored, so match by the same archive globs the CI cache carries and
# delete whatever no Source/Patch tag references. Sources are resolved with
# rpmspec -P because go/rust specs reference them via macros (%{gosource},
# %{archivename}-vendor.tar.bz2); the textual fallback only covers %{name}
# and %{version} (used when rpmspec is unavailable, e.g. a bare host).
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pruned=0
for dir in "$root"/packages/*/; do
  specs=("$dir"*.spec)
  [ -f "${specs[0]}" ] || continue
  refs=""
  volatile=""
  for spec in "${specs[@]}"; do
    names="$(rpmspec -P "$spec" 2>/dev/null | grep -E '^(Source|Patch)[0-9]*:' | awk '{print $2}' || true)"
    if [ -z "$names" ]; then
      name="$(awk '/^Name:/{print $2; exit}' "$spec")"
      version="$(awk '/^Version:/{print $2; exit}' "$spec")"
      names="$(grep -E '^(Source|Patch)[0-9]*:' "$spec" | awk '{print $2}' \
        | sed -e "s/%{name}/$name/g" -e "s/%{version}/$version/g")"
    fi
    refs+="$(while IFS= read -r ref; do basename "$ref"; done <<<"$names")"
    # "releases/latest" URLs keep a stable filename over changing content:
    # a cached copy would serve a stale payload forever, so always re-fetch
    # (names may be bare URLs already, rpmspec path has no Source prefix)
    volatile+="$(grep 'latest/download' <<<"$names" \
      | while IFS= read -r ref; do basename "$ref"; done || true)"
  done
  while IFS= read -r f; do
    base="$(basename "$f")"
    grep -qxF "$base" <<<"$refs" && continue
    rm -f "$f"
    pruned=$((pruned + 1))
  done < <(find "$dir" -maxdepth 2 -type f \
      \( -name '*.tar.*' -o -name '*.tgz' -o -name '*.zip' \) || true)
  if [ -n "$volatile" ]; then
    while IFS= read -r v; do
      rm -f "$dir/$v" "$dir"*/"$v" 2>/dev/null || true
      pruned=$((pruned + 1))
    done <<<"$volatile"
  fi
done
echo "pruned $pruned unreferenced file(s)"
