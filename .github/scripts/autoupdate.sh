#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
job_start="$(date +%s)"

git config --global --add safe.directory "$root"
git -C "$root" config user.name "github-actions[bot]"
git -C "$root" config user.email "41898282+github-actions[bot]@users.noreply.github.com"

# gate-in-job (gh-actions-conventions rule 11): a GITHUB_TOKEN push to main
# skips every GitHub-side workflow yet still fires the COPR webhook, so bumps
# commit to a branch; the workflow gates it there and merges the exact gated
# SHA into main (ff-only)
branch="bump/$(date -u +%Y%m%d-%H%M)"
git -C "$root" checkout -b "$branch"

# fetches are network-bound: resolve all latest versions in parallel, then
# apply bumps serially so git commits never race. Resolution (tag choice,
# JSON parsing) lives in resolve.py and is unit-tested by tools/test.sh;
# this script only orchestrates.
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
resolved="$tmp/resolved"; mkdir "$resolved"
stats="$tmp/stats"; : > "$stats"
bumps="$tmp/bumps"; : > "$bumps"
export resolved tmp stats root
# shellcheck source=/dev/null
[ -f "$root/tools/host.sh" ] && source "$root/tools/host.sh" >/dev/null 2>&1 || true

SUCCESS_DELAY=0.3
RETRY_BASE=3
export SUCCESS_DELAY RETRY_BASE

# a missing resolved/<pkg> is a per-package warning (::warning in the log),
# not a job failure — the run still bumps everything else
python3 "$root/.github/scripts/resolve.py" "$root" "$resolved" "$stats"

packages="$(mktemp)"
bumped=0
bumped_pkgs=""
keepalive=0
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
  # tags like jethrokuan/z's "<2.7.0" must never reach a spec, and neither
  # may a letter-leading one (a component tag resolved as "latest")
  if ! [[ "$latest_rpm" =~ ^[0-9][A-Za-z0-9._+]+$ ]]; then
    echo "::warning::$pkg: latest tag '$latest' has non-version characters, skipping"
    continue
  fi
  spec="$(ls "$root/packages/$pkg/"*.spec 2>/dev/null | head -1 || true)"
  if [ -z "$spec" ]; then
    echo "::warning::$pkg: no spec, skipping"
    continue
  fi
  current="$(awk '/^Version:/{print $2; exit}' "$spec")"
  # releases/latest is publish-ordered and the tags?per_page=1 fallback can
  # return an older or component tag: never bump down
  if [ "$latest_rpm" != "$current" ] \
     && [ "$(printf '%s\n%s\n' "$current" "$latest_rpm" | sort -V | head -1)" = "$latest_rpm" ]; then
    echo "::warning::$pkg: resolved $latest_rpm <= current $current, skipping (downgrade)"
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
  git -C "$root" add "packages/$pkg"
  git -C "$root" commit -m "chore($pkg): update to $latest"
  bumped=$((bumped + 1))
  bumped_pkgs="${bumped_pkgs:+$bumped_pkgs }$pkg"
  printf '| %s | %s | %s |\n' "$pkg" "$current" "$latest_rpm" >> "$bumps"
  git -C "$root" tag -f "$pkg/$latest"
done < "$packages"

# Keepalive: GitHub disables scheduled workflows after 60 idle days; an empty
# commit counts as activity and triggers no COPR rebuild (no files changed).
last_commit="$(git -C "$root" log -1 --format=%ct)"
now="$(date +%s)"
if [ $((now - last_commit)) -gt $((45 * 86400)) ]; then
  git -C "$root" commit --allow-empty -qm "chore: keepalive"
  keepalive=1
fi

packages_total="$(find "$root/packages" -name upstream -maxdepth 2 | wc -l)"
total_req="$(grep -c '^REQ' "$stats" || true)"
read -r c200 c403 c429 c404 minrl <<< "$(awk -F'\t' '$1=="REQ"{c[$3]++; if($5+0>0 && (m==0||$5+0<m)) m=$5+0} END{print c[200]+0, c[403]+0, c[429]+0, c[404]+0, m+0}' "$stats")"
cother=$(( total_req - c200 - c403 - c429 - c404 ))
retries="$(grep -c '^RETRY' "$stats" || true)"
# a failed request is not a failed package: the tags fallback 404s first
final_fail=$(( packages_total - $(find "$resolved" -type f | wc -l) ))
wall=$(( $(date +%s) - job_start ))
# a 404 on releases/latest is expected for tags-only repos (the fallback
# resolves them), so it gets its own bucket instead of polluting "other"
summary="packages=$packages_total bumped=$bumped requests=$total_req ok200=$c200 throttled403=$c403 throttled429=$c429 fallback404=$c404 other=$cother retries=$retries final_failures=$final_fail min_rlrem=$minrl wall=${wall}s"
echo "::notice::[rate-summary] $summary"

# The branch stays local: pushing it here would fire the COPR webhook on a
# non-main ref (it reacts to push events on any branch) and build every
# bumped package twice — once here, again on the merge push. The workflow
# pushes the branch for inspection only when the gate fails.

if [ -n "${GITHUB_OUTPUT:-}" ]; then
  {
    echo "branch=$branch"
    echo "sha=$(git -C "$root" rev-parse HEAD)"
    echo "pkgs=$bumped_pkgs"
    echo "count=$bumped"
    echo "keepalive=$keepalive"
  } >> "$GITHUB_OUTPUT"
fi

if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  {
    echo "## autoupdate"
    echo
    if [ -s "$bumps" ]; then
      echo "| package | from | to |"
      echo "|---|---|---|"
      cat "$bumps"
      echo
    else
      echo "no updates this run"
      echo
    fi
    echo '```'
    echo "$summary"
    echo '```'
  } >> "$GITHUB_STEP_SUMMARY"
fi
