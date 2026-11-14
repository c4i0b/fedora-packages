#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=lib.sh
source "$root/tools/lib.sh"

# args restrict linting to those packages (CI validates only what changed);
# no args lints everything
fail=0

# repo gate before per-spec lint: committable content here tops out ~35 KB,
# so anything over 5 MB under packages/ is a fetched payload that lost its
# ignored extension — a commit with it bounces at push (GH001 at 100 MB).
# Gitignored files can never be committed and are skipped.
while IFS= read -r -d '' f; do
  if [ "$(stat -c%s "$f")" -gt $((5*1024*1024)) ] \
     && ! git -C "$root" check-ignore -q "$f"; then
    echo "FAIL: oversize payload $f ($(($(stat -c%s "$f")/1024/1024)) MB, >5 MB ceiling, committable — GH001 at push)" >&2
    fail=1
  fi
done < <(find "$root/packages" -type f -print0)

if [ "$#" -gt 0 ]; then
  for name in "$@"; do
    for spec in "$root"/packages/"$name"/*.spec; do
      [ -f "$spec" ] || { echo "FAIL: no spec for $name" >&2; fail=1; continue; }
      lint_spec "$spec" || fail=1
    done
  done
  exit "$fail"
fi
for spec in "$root"/packages/*/*.spec; do
  lint_spec "$spec" || fail=1
done
exit "$fail"
