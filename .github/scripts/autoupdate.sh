#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

git config --global --add safe.directory "$root"
git -C "$root" config user.name "github-actions[bot]"
git -C "$root" config user.email "41898282+github-actions[bot]@users.noreply.github.com"

auth=()
if [ -n "${GITHUB_TOKEN:-}" ]; then
  auth=(-H "Authorization: Bearer $GITHUB_TOKEN")
fi

for upstream_file in "$root"/packages/*/upstream; do
  [ -f "$upstream_file" ] || continue
  pkg_dir="$(dirname "$upstream_file")"
  pkg="$(basename "$pkg_dir")"
  spec="$(ls "$pkg_dir"/*.spec 2>/dev/null | head -1 || true)"
  # a missing spec must never abort the whole run (plain ls dies on it)
  if [ -z "$spec" ]; then
    echo "::warning::$pkg: no spec in $pkg_dir, skipping"
    continue
  fi

  current="$(awk '/^Version:/{print $2; exit}' "$spec")"
  source="$(cat "$upstream_file")"

  if [[ "$source" == npm:* ]]; then
    npm_pkg="${source#npm:}"
    npm_slug="$(echo "$npm_pkg" | sed 's|/|%2f|')"
    # || true: with set -o pipefail a 404 from the registry (or an empty
    # grep) must not abort the script before the tag fallback below
    latest="$(curl -fsSL "https://registry.npmjs.org/${npm_slug}/latest" \
      | grep -oE '"version": ?"[^"]*"' | head -1 | cut -d'"' -f4)" || true
  else
    # repos without any GitHub Release (only prereleases) 404 here
    latest="$(curl -fsSL "${auth[@]}" "https://api.github.com/repos/${source}/releases/latest" \
      | grep -oE '"tag_name": ?"[^"]*"' | head -1 | cut -d'"' -f4)" || true
    latest="${latest#v}"
  fi

  if [ -z "$latest" ]; then
    # Tag-only repos (no GitHub Releases): fall back to the latest tag
    latest="$(curl -fsSL "${auth[@]}" "https://api.github.com/repos/${source}/tags?per_page=1" \
      | grep -oE '"name": ?"[^"]*"' | head -1 | cut -d'"' -f4)" || true
    latest="${latest#v}"
  fi
  if [ -z "$latest" ]; then
    echo "::warning::$pkg: could not resolve latest release of $source"
    continue
  fi
  # Manual pin: a commit message "autoupdate: override <version>" on the
  # package dir keeps the bot from re-bumping to an unwanted release
  if git -C "$root" log -1 --format=%B -- "packages/$pkg" \
    | grep -qiE "^autoupdate: override .*$latest"; then
    echo "$pkg: $latest manually overridden, skipping"
    continue
  fi
  # RPM forbids '-' in Version; bump.sh sanitizes, so compare sanitized
  latest_rpm="$(printf '%s' "$latest" | sed 's/[- ]/./g')"
  # tags like jethrokuan/z's "<2.7.0" must never reach a spec
  if ! [[ "$latest_rpm" =~ ^[A-Za-z0-9._+]+$ ]]; then
    echo "::warning::$pkg: latest tag '$latest' has non-version characters, skipping"
    continue
  fi
  if [ "$latest_rpm" = "$current" ]; then
    echo "$pkg: up to date ($current)"
    continue
  fi

  echo "$pkg: $current -> $latest"
  # one broken package must not abort the whole run (the push step only
  # runs on success, so an abort would throw away every bump made so far)
  if ! "$root/tools/bump.sh" "$pkg" "$latest"; then
    echo "::warning::$pkg: bump to $latest failed, skipping"
    continue
  fi
  git -C "$root" add "$pkg_dir"
  git -C "$root" commit -m "chore($pkg): update to $latest"
  git -C "$root" tag -f "$pkg/$latest"
done

# Keepalive: GitHub disables scheduled workflows after 60 idle days; an empty
# commit counts as activity and triggers no COPR rebuild (no files changed).
last_commit="$(git -C "$root" log -1 --format=%ct)"
now="$(date +%s)"
if [ $((now - last_commit)) -gt $((45 * 86400)) ]; then
  git -C "$root" commit --allow-empty -qm "chore: keepalive"
fi
