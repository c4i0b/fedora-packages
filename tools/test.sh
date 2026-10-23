#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=lib.sh
source "$root/tools/lib.sh"

fail=0

# Never commit source archives or font binaries; they are downloaded at build time
while IFS= read -r archived; do
  echo "FAIL: committed archive: $archived"
  fail=1
done < <(git -C "$root" ls-files 'packages/*' | grep -E '\.(tgz|tar\.gz|tar\.xz|tar\.bz2|tar\.zst|zip|src\.rpm|ttf|otf|ttc|woff2)$' || true)

# rpmbuild downloads Source0 into the package dir when a local srpm build
# fails; the leftovers have no extension, so sniff tracked payload types
while IFS= read -r payload; do
  echo "FAIL: committed binary payload (extensionless): $payload"
  fail=1
done < <(git -C "$root" ls-files 'packages/*' | while IFS= read -r f; do
    case "$f" in *.*) continue ;; esac
    case "$(file -b --mime-type "$root/$f")" in
      application/*|font/*|image/*) echo "$f" ;;
    esac
  done)

# Wrapper/helper scripts shipped as package sources must parse
while IFS= read -r script; do
  if ! sh -n "$script" >/dev/null 2>&1; then
    echo "FAIL: sh -n $script" >&2
    fail=1
  fi
done < <(git -C "$root" ls-files 'packages/*' | grep -vE '\.(spec|patch|txt|md|toml|json|desktop|service|svg|png|metainfo.xml|appdata.xml)$' \
  | while IFS= read -r f; do
    head -c2 "$root/$f" 2>/dev/null | grep -q '#!' && echo "$f"
  done)

# host.sh must parse every remote syntax the repo may use (a past regression
# silently dropped the owner and every host-dependent tool died on "/repo")
# shellcheck source=host.sh
source "$root/tools/host.sh"
while IFS='|' read -r url host owner repo; do
  host_detect "$url"
  if [ "$GIT_HOST/$GIT_OWNER/$GIT_REPO" != "$host/$owner/$repo" ]; then
    echo "FAIL: host.sh parsed '$url' as $GIT_HOST/$GIT_OWNER/$GIT_REPO (expected $host/$owner/$repo)" >&2
    fail=1
  fi
done <<'EOF'
https://github.com/o/r.git|github.com|o|r
git@github.com:o/r.git|github.com|o|r
https://gitlab.com/group/sub/r.git|gitlab.com|sub|r
ssh://git@codeberg.org:2222/o/r.git|codeberg.org|o|r
https://github.com/o/r|github.com|o|r
EOF

for dir in "$root"/packages/*/; do
  check_package "$dir" || fail=1
done

# Templates must render into conforming packages: fill every placeholder with
# dummy values and run the same invariants over the rendered spec.
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
for template in "$root"/templates/*.spec.tpl; do
  kind="$(basename "$template" .spec.tpl)"
  mkdir -p "$tmp/$kind"
  render_spec "$template" "$tmp/$kind/$kind.spec" "$kind" 1
  if grep -q '__[A-Z]*__' "$tmp/$kind/$kind.spec"; then
    echo "FAIL: template $kind.tpl has unreplaced placeholders"
    fail=1
  fi
  # rendered templates must satisfy the same invariants and lint bar as real
  # packages, so scaffolds can never drift from the standard
  check_package "$tmp/$kind" || fail=1
  if ! lint_spec "$tmp/$kind/$kind.spec"; then
    echo "FAIL: template $kind.tpl renders with rpmlint errors"
    fail=1
  fi
done

[ "$fail" -eq 0 ] && echo "all package invariants OK" || exit 1
