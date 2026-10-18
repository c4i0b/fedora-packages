#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=lib.sh
source "$root/tools/lib.sh"

fail=0
for spec in "$root"/packages/*/*.spec; do
  lint_spec "$spec" || fail=1
done
exit "$fail"
