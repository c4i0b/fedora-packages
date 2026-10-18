#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
job_start="$(date +%s)"

git config --global --add safe.directory "$root"
git -C "$root" config user.name "github-actions[bot]"
git -C "$root" config user.email "41898282+github-actions[bot]@users.noreply.github.com"

# fetches are network-bound: resolve all latest versions in parallel, then
# apply bumps serially so git commits never race
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
resolved="$tmp/resolved"; mkdir "$resolved"
stats="$tmp/stats"; : > "$stats"
export resolved tmp stats

# rate-limit tuning knobs
SUCCESS_DELAY=0.3
RETRY_BASE=3
export SUCCESS_DELAY RETRY_BASE

# GitHub throttles bursts with 403/429 even when authenticated; stats lines
# are single appends, safe across the xargs workers
get() {
  local pkg="$1" url="$2" body headers code attempt wait src t0 t1 elapsed
  shift 2
  body="$tmp/.body.$$"; headers="$tmp/.hdr.$$"
  for attempt in 1 2 3 4 5; do
    t0="$(date +%s%N)"
    code="$(curl -s -o "$body" -D "$headers" -w '%{http_code}' "$@" "$url")" || true
    t1="$(date +%s%N)"
    elapsed=$(( (t1 - t0) / 1000000 ))
    rlrem="$(tr -d '\r' < "$headers" | awk 'tolower($1)=="x-ratelimit-remaining:"{print $2}' | head -1)"
    printf 'REQ\t%s\t%s\t%s\n' "$pkg" "$code" "$attempt" >> "$stats"
    if [ "$code" = 200 ]; then
      echo >&2 "::notice::[rate] pkg=$pkg attempt=$attempt status=200 wait=$SUCCESS_DELAY wait_src=success-delay elapsed=${elapsed}ms rlrem=${rlrem:--}"
      sleep "$SUCCESS_DELAY"
      cat "$body"
      return 0
    fi
    if [ "$code" = 403 ] || [ "$code" = 429 ]; then
      wait="$(tr -d '\r' < "$headers" | awk 'tolower($1)=="retry-after:"{print $2}' | head -1)"
      if [ -n "$wait" ]; then
        src=retry-after
      else
        src=computed
        wait=$(( RETRY_BASE * (1 << (attempt - 1)) + RANDOM % 2 ))
      fi
      echo "RETRY" >> "$stats"
      echo >&2 "::notice::[rate] pkg=$pkg attempt=$attempt status=$code wait=$wait wait_src=$src elapsed=${elapsed}ms rlrem=${rlrem:--}"
      sleep "$wait"
    else
      echo >&2 "::notice::[rate] pkg=$pkg attempt=$attempt status=$code wait=0 wait_src=none elapsed=${elapsed}ms rlrem=${rlrem:--}"
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
    body="$(get "$pkg" "https://registry.npmjs.org/${npm_slug}/latest")" || true
    # with set -o pipefail an empty body must not abort before the fallback
    latest="$(grep -oE '"version": ?"[^"]*"' <<<"$body" | head -1 | cut -d'"' -f4)" || true
  else
    # repos without any GitHub Release (only prereleases) 404 here
    body="$(get "$pkg" "https://api.github.com/repos/${source}/releases/latest" "${auth[@]}")" || true
    latest="$(grep -oE '"tag_name": ?"[^"]*"' <<<"$body" | head -1 | cut -d'"' -f4)" || true
    latest="${latest#v}"
  fi
  if [ -z "$latest" ]; then
    # Tag-only repos (no GitHub Releases): fall back to the latest tag
    body="$(get "$pkg" "https://api.github.com/repos/${source}/tags?per_page=1" "${auth[@]}")" || true
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

packages_total="$(find "$root/packages" -name upstream -maxdepth 2 | wc -l)"
total_req="$(grep -c '^REQ' "$stats" || true)"
read -r c200 c403 c429 <<< "$(awk -F'\t' '$1=="REQ"{c[$3]++} END{print c[200]+0, c[403]+0, c[429]+0}' "$stats")"
cother=$(( total_req - c200 - c403 - c429 ))
retries="$(grep -c '^RETRY' "$stats" || true)"
# a failed request is not a failed package: the tags fallback 404s first
final_fail=$(( packages_total - $(find "$resolved" -type f | wc -l) ))
wall=$(( $(date +%s) - job_start ))
echo "::notice::[rate-summary] packages=$packages_total requests=$total_req ok200=$c200 throttled403=$c403 throttled429=$c429 other=$cother retries=$retries final_failures=$final_fail wall=${wall}s"
