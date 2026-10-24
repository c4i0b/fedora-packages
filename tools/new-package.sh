#!/usr/bin/env bash
set -euo pipefail

usage="usage: new-package.sh <name> [bin|source|go|rust|electron|bun|python|icon-theme|wallpaper]"
name="${1:?$usage}"
kind="${2:-bin}"

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=lib.sh
source "$root/tools/lib.sh"

template="$root/templates/$kind.spec.tpl"
[ -f "$template" ] || { echo "unknown template: $kind"; exit 1; }

dir="$root/packages/$name"
if [ -e "$dir" ]; then
  # An empty dir is scaffold debris; anything else must not be overwritten
  rmdir "$dir" 2>/dev/null || { echo "packages/$name already exists"; exit 1; }
fi
mkdir -p "$dir"
trap 'rm -rf "$dir"' ERR

render_spec "$template" "$dir/$name.spec" "$name"
trap - ERR

echo "created packages/$name/$name.spec"
echo "left to fill:"
grep -oE '__[A-Z]+__' "$dir/$name.spec" | sort -u | sed 's/^/  /'
echo "pending checks (must pass before push):"
check_package "$dir" || true
echo "next: just add-package $name"
echo "for automatic updates: echo 'owner/repo' > packages/$name/upstream"
