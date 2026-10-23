#!/usr/bin/env bash
set -euo pipefail

# Keep the sources cache bounded by the live set: rpmbuild downloads tarballs
# into the package dir, so after a bump the old version would linger until
# LRU eviction (which also evicts the go/cargo module caches). The downloads
# are gitignored, so match by the same archive globs the CI cache carries and
# delete whatever no Source/Patch tag references (macros %{name}/%{version}
# expanded; other macros are rare in Source basenames).
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pruned=0
for dir in "$root"/packages/*/; do
  specs=("$dir"*.spec)
  [ -f "${specs[0]}" ] || continue
  refs=""
  for spec in "${specs[@]}"; do
    name="$(awk '/^Name:/{print $2; exit}' "$spec")"
    version="$(awk '/^Version:/{print $2; exit}' "$spec")"
    refs+="$(grep -E '^(Source|Patch)[0-9]*:' "$spec" | awk '{print $2}' \
      | sed -e "s/%{name}/$name/g" -e "s/%{version}/$version/g" \
      | while IFS= read -r ref; do basename "$ref"; done)"
  done
  # "releases/latest" URLs keep a stable filename over changing content:
  # a cached copy would serve a stale payload forever, so always re-fetch
  volatile="$(cat "${specs[@]}" | grep -E '^Source[0-9]*:' | grep 'latest/download' \
    | awk '{print $2}' | while IFS= read -r ref; do basename "$ref"; done || true)"
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
