#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=host.sh
source "$root/tools/host.sh"

# Fetch recent CI run logs and aggregate key=value fields from
# lines matching a pattern, so new log fields need no changes here.
# usage: analyze-logs.sh [workflow=autoupdate] [days=7] [pattern=rate-summary]

workflow="${1:-autoupdate}"
days="${2:-7}"
pattern="${3:-rate-summary}"

repo="${GIT_SLUG:-}"
[ -n "$repo" ] && [ "$repo" != "/" ] && [[ "$repo" == */* && "${repo%%/*}" != "" ]] \
  || { echo "could not detect a valid OWNER/REPO from the origin remote (got '${repo:-empty}')" >&2; exit 1; }
since="$(date -u -d "$days days ago" +%Y-%m-%d)"

mapfile -t runs < <(gh run list -R "$repo" -w "$workflow" --created ">$since" \
  --json databaseId,createdAt --jq 'sort_by(.createdAt)[] | "\(.databaseId) \(.createdAt)"')

[ "${#runs[@]}" -gt 0 ] || { echo "no $workflow runs in the last $days days"; exit 0; }

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
matches="$tmp/matches"; : > "$matches"
errors=0

for run in "${runs[@]}"; do
  id="${run%% *}"; ts="${run#* }"
  # in-progress or expired logs have nothing to read yet; an API failure
  # (e.g. actions jobs 502s) is NOT "no data" and must be distinguishable,
  # or an outage reads as telemetry gone missing
  if ! gh run view "$id" -R "$repo" --log 2>"$tmp/err" > "$tmp/log"; then
    if grep -qE "HTTP [0-9]{3}|Server Error" "$tmp/err"; then
      errors=$((errors + 1)); continue
    fi
  fi
  grep -F "[${pattern}]" "$tmp/log" | sed "s/.*\[${pattern}\] //" \
    | sed "s/^/${ts%%T*} /" >> "$matches"
done

[ "$errors" -gt 0 ] && echo "warning: $errors/${#runs[@]} runs had log-fetch failures (API degraded?)" >&2
[ -s "$matches" ] || { echo "no [${pattern}] lines found in $((${#runs[@]} - errors)) readable runs"; exit 0; }

cat "$matches"
echo

awk '{
  for (i = 2; i <= NF; i++) {
    if ($i !~ /^[a-zA-Z_]+=[-0-9.]+$/) continue
    split($i, kv, "=")
    k = kv[1]; v = kv[2] + 0
    if (!(k in cnt) || v < mn[k]) mn[k] = v
    if (!(k in cnt) || v > mx[k]) mx[k] = v
    cnt[k]++; sum[k] += v
  }
}
END {
  printf "%-16s %6s %10s %8s %8s %7s\n", "field", "count", "sum", "min", "max", "avg"
  for (k in cnt)
    printf "%-16s %6d %10d %8d %8d %7.1f\n", k, cnt[k], sum[k], mn[k], mx[k], sum[k] / cnt[k]
}' "$matches" | sort
