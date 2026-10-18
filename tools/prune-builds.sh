#!/usr/bin/env bash
# Delete old COPR builds, keeping — per package — the newest finished build
# plus every build still in flight. An in-flight build never counts as the
# keeper: if it fails later, the previous good build is still around.
set -euo pipefail

project="${1:?usage: prune-builds.sh owner/project [dry]}"
dry="${2:-}"

# list-builds is newest-first
builds="$(copr-cli list-builds "$project" | awk -F'\t' 'NF>=3 {print $1, $2, $3}')"
inflight='^(running|starting|pending|importing)$'

keep_ids="$(awk -v re="$inflight" '$3 !~ re && !seen[$2]++ {print $1}' <<<"$builds")"
inflight_ids="$(awk -v re="$inflight" '$3 ~ re {print $1}' <<<"$builds")"

drop_ids="$(awk -v keep="$keep_ids $inflight_ids" \
  'BEGIN{split(keep,k); for(i in k) K[k[i]]=1} !($1 in K) {print $1}' <<<"$builds")"

echo "keeping $(wc -w <<<"$keep_ids") finished + $(wc -w <<<"$inflight_ids") in-flight builds"
count=$(wc -w <<<"$drop_ids")
[ "$count" -gt 0 ] || { echo "nothing to prune"; exit 0; }
echo "pruning $count builds"

for id in $drop_ids; do
  if [ -n "$dry" ]; then
    echo "would delete: $id"
  else
    copr-cli delete-build "$id" >/dev/null \
      || echo "WARN: failed to delete $id" >&2
  fi
done
