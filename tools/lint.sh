#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=lib.sh
source "$root/tools/lib.sh"

# args restrict linting to those packages (CI validates only what changed);
# no args lints everything
fail=0
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
