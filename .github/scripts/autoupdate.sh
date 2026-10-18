#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

git config --global --add safe.directory "$root"
git -C "$root" config user.name "github-actions[bot]"
git -C "$root" config user.email "41898282+github-actions[bot]@users.noreply.github.com"

# fetches are network-bound: resolve all latest versions in parallel, then
# apply bumps serially so git commits never race
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
resolved="$tmp/resolved"; mkdir "$resolved"
export resolved tmp

# curl with status tracking and progressive backoff: GitHub throttles
# bursts with 403/429 even when authenticated (Retry-After is honored)
get() {
  local url="$1" body headers code attempt wait
  shift
  body="$tmp/.body.$$"; headers="$tmp/.hdr.$$"
  for attempt in 1 2 3 4 5; do
    code="$(curl -s -o "$body" -D "$headers" -w '%{http_code}' "$@" "$url")" || true
    if [ "$code" = 200 ]; then
      cat "$body"
      return 0
    fi
    if [ "$code" = 403 ] || [ "$code" = 429 ]; then
      wait="$(tr -d '\r' < "$headers" | awk 'tolower($1)=="retry-after:"{print $2}' | head -1)"
      # 8...64s base, jittered so parallel workers spread their retries
      [ -n "$wait" ] || wait=$(( 8 * (1 << (attempt - 1)) + RANDOM % 4 ))
      sleep "$wait"
    else
      return 1
    fi
  done
  return 1
}

resolve() {
  upstream_file="$1"
  pkg="$(basename "$(dirname "$upstream_file")")"
  source="$(cat "$upstream_file")"

  auth=()
  [ -n "${GITHUB_TOKEN:-}" ] && auth=(-H "Authorization: Bearer $GITHUB_TOKEN")

  if [[ "$source" == npm:* ]]; then
    npm_pkg="${source#npm:}"
    npm_slug="$(echo "$npm_pkg" | sed 's|/|%2f|')"
    body="$(get "https://registry.npmjs.org/${npm_slug}/latest")" || true
    # with set -o pipefail an empty body must not abort before the fallback
    latest="$(grep -oE '"version": ?"[^"]*"' <<<"$body" | head -1 | cut -d'"' -f4)" || true
  else
    # repos without any GitHub Release (only prereleases) 404 here
    body="$(get "https://api.github.com/repos/${source}/releases/latest" "${auth[@]}")" || true
    latest="$(grep -oE '"tag_name": ?"[^"]*"' <<<"$body" | head -1 | cut -d'"' -f4)" || true
    latest="${latest#v}"
  fi
  if [ -z "$latest" ]; then
    # Tag-only repos (no GitHub Releases): fall back to the latest tag
    body="$(get "https://api.github.com/repos/${source}/tags?per_page=1" "${auth[@]}")" || true
    latest="$(grep -oE '"name": ?"[^"]*"' <<<"$body" | head -1 | cut -d'"' -f4)" || true
    latest="${latest#v}"
  fi

  if [ -z "$latest" ]; then
    echo "::warning::$pkg: could not resolve latest release of $source"
    return 0
  fi
  printf 'latest\t%s\t%s\n' "$pkg" "$latest" > "$resolved/$pkg"
}

find "$root/packages" -name upstream -maxdepth 2 \
  | xargs -P 8 -I{} bash -c "$(declare -f get resolve); resolve \"{}\""

packages="$(mktemp)"
for f in "$resolved"/*; do
  [ -f "$f" ] || continue
  cat "$f"
done | sort > "$packages"

while IFS=$'\t' read -r _ pkg latest; do
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
  spec="$(ls "$root/packages/$pkg/"*.spec 2>/dev/null | head -1 || true)"
  if [ -z "$spec" ]; then
    echo "::warning::$pkg: no spec, skipping"
    continue
  fi
  current="$(awk '/^Version:/{print $2; exit}' "$spec")"
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
  git -C "$root" add "packages/$pkg"
  git -C "$root" commit -m "chore($pkg): update to $latest"
  git -C "$root" tag -f "$pkg/$latest"
done < "$packages"

# Keepalive: GitHub disables scheduled workflows after 60 idle days; an empty
# commit counts as activity and triggers no COPR rebuild (no files changed).
last_commit="$(git -C "$root" log -1 --format=%ct)"
now="$(date +%s)"
if [ $((now - last_commit)) -gt $((45 * 86400)) ]; then
  git -C "$root" commit --allow-empty -qm "chore: keepalive"
fi
