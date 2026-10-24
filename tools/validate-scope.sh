#!/usr/bin/env bash
set -euo pipefail

# Decide what validate should build: only packages changed since the last
# SUCCESSFUL validate run, so a cancelled run's changes stay "pending" and are
# picked up by the next one (per-push diffs would bypass them). Any change
# outside packages/** affects every package; so do dispatch runs, a missing
# green history and unreachable shas after force-pushes. Every edge fails
# towards "full" — never towards validating less than needed.
# usage: validate-scope.sh [event_name]  ->  "full" | "subset <pkg>..."
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=host.sh
source "$root/tools/host.sh"

event="${1:-push}"
full() { echo "full"; exit 0; }

[ "$event" = workflow_dispatch ] && full

auth=()
[ -n "${GITHUB_TOKEN:-}" ] && auth=(-H "Authorization: Bearer $GITHUB_TOKEN")
# compact JSON: grep, never per-line awk (AGENTS.md)
last="$(curl -sf \
  "${GIT_API_BASE}/repos/${GIT_SLUG}/actions/workflows/validate.yml/runs?status=success&per_page=1" \
  "${auth[@]}" \
  | grep -oE '"head_sha": ?"[0-9a-f]{40}"' | head -1 | cut -d'"' -f4 || true)"
[ -n "$last" ] || full
git -C "$root" cat-file -e "$last^{commit}" 2>/dev/null || full

changed="$(git -C "$root" diff --name-only "$last"..HEAD)"
grep -qvE '^packages/' <<<"$changed" && full

pkgs=""
while IFS= read -r p; do
  [ -d "$root/packages/$p" ] && pkgs+=" $p"
done < <(cut -d/ -f2 <<<"$changed" | sort -u)
[ -n "$pkgs" ] || full
echo "subset$pkgs"
