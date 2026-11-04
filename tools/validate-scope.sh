#!/usr/bin/env bash
set -euo pipefail

# Decide what validate should build: only packages changed since the last
# SUCCESSFUL validate run, so a cancelled run's changes stay "pending" and are
# picked up by the next one (per-push diffs would bypass them). Files outside
# packages/ are mostly CI artifacts (README, badges/) and are ignored; only
# build-affecting paths force a full run. Every edge fails towards "full" —
# never towards validating less than needed — with the reason reported so the
# weekly telemetry can show what forced it.
# usage: validate-scope.sh [event_name]
#   ->  "full <reason>"  |  "subset <pkg>..."
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=host.sh
source "$root/tools/host.sh"

event="${1:-push}"
full() { echo "full $1"; exit 0; }

[ "$event" = workflow_dispatch ] && full dispatch

auth=()
[ -n "${GITHUB_TOKEN:-}" ] && auth=(-H "Authorization: Bearer $GITHUB_TOKEN")
# compact JSON: grep, never per-line awk (AGENTS.md). Diagnostics MUST go to
# stderr: stdout is command-substituted by the caller, and a ::warning:: that
# lands there poisons the scope parse
url="${GIT_API_BASE}/repos/${GIT_SLUG}/actions/workflows/validate.yml/runs?status=success&per_page=1"
body="$(mktemp)"
fetch_last() {
  curl -s -o "$body" -w '%{http_code}' "$@" "$url" || true
}
# the GITHUB_TOKEN 404s this endpoint from inside a job (integration
# masking) while the same URL answers unauthenticated (public repo): try
# with, then without; only both-failing falls back to full
http="$(fetch_last "${auth[@]}")"
last="$(grep -oE '"head_sha": ?"[0-9a-f]{40}"' "$body" | head -1 | cut -d'"' -f4 || true)"
if [ -z "$last" ]; then
  http="$(fetch_last)"
  last="$(grep -oE '"head_sha": ?"[0-9a-f]{40}"' "$body" | head -1 | cut -d'"' -f4 || true)"
fi
if [ -z "$last" ]; then
  echo >&2 "::warning::[scope] last-green lookup empty (http=$http url=$url msg=$(grep -oE '"message": ?"[^"]*"' "$body" | head -1))"
  rm -f "$body"
  full no-green-history
fi
rm -f "$body"
git -C "$root" cat-file -e "$last^{commit}" 2>/dev/null || full orphaned-sha

changed="$(git -C "$root" diff --name-only "$last"..HEAD)"
force="$(grep -vE '^packages/' <<<"$changed" \
  | grep -E '^(tools/|templates/|\.copr/|justfile$|\.github/workflows/validate\.yml$)' || true)"
[ -z "$force" ] || full "${force%%/*}"

pkgs=""
while IFS= read -r p; do
  [ -n "$p" ] && [ -d "$root/packages/$p" ] && pkgs+=" $p"
done < <(cut -d/ -f2 <<<"$changed" | sort -u)
[ -n "${pkgs// /}" ] || full nothing-changed
echo "subset$pkgs"
