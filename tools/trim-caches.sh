#!/usr/bin/env bash
set -euo pipefail

# Keep only the newest sources-v* cache entry. The 10GB repo quota with a
# ~6GB payload means every epoch change transiently holds two entries and
# the LRU can evict the live one (a full repopulation run); deleting the
# stale entry right after a successful save makes the quota deterministic.
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=host.sh
source "$root/tools/host.sh"

api="${GITHUB_API_URL:-https://api.github.com}"
slug="${GITHUB_REPOSITORY:-${GIT_SLUG:-}}"
auth=(-H "Authorization: Bearer ${GITHUB_TOKEN:?}" -H "Accept: application/vnd.github+json")

stale="$(python3 - "$api" "$slug" <<'PY'
import json, os, sys, urllib.request
api, slug = sys.argv[1], sys.argv[2]
req = urllib.request.Request(f"{api}/repos/{slug}/actions/caches?per_page=100",
                             headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"})
entries = json.load(urllib.request.urlopen(req))["actions_caches"]
mine = [e for e in entries if e["key"].startswith("sources-v")]
if len(mine) > 1:
    newest = max(e["created_at"] for e in mine)
    for e in mine:
        if e["created_at"] != newest:
            print(e["id"])
PY
)"
[ -z "$stale" ] || while IFS= read -r id; do
  curl -s -X DELETE "${api}/repos/${slug}/actions/caches/${id}" "${auth[@]}" || true
  echo "deleted stale cache entry $id"
done <<<"$stale"
