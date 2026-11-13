#!/usr/bin/env bash
set -euo pipefail

# Merges the exact SHA the in-job gate validated (gh-actions-conventions
# rule 11). Never rebase-and-merge an ungated SHA — that recreates the red
# the gate caught (rea-agents 6.9.0 %check, pdfcraft 0.21.x vendoring).

usage="usage: autoupdate-merge.sh <branch> <sha>"
branch="${1:?$usage}"
sha="${2:?$usage}"

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
git config --global --add safe.directory "$root"

t0="$(date +%s)"

git -C "$root" fetch origin main

if [ "$(git -C "$root" rev-parse "$sha^{commit}")" = "$(git -C "$root" rev-parse origin/main)" ]; then
  echo "nothing to merge: $sha is already origin/main"
  echo "::notice::[merge-summary] sha=${sha:0:7} result=already-main elapsed=$(( $(date +%s) - t0 ))s"
  exit 0
fi

if ! git -C "$root" merge-base --is-ancestor origin/main "$sha"; then
  echo "::error::origin/main moved during the gate; ff-only to $sha is impossible. The next autoupdate cycle retries — refusing to rebase-and-merge an ungated SHA (branch $branch kept for inspection)."
  echo "::notice::[merge-summary] sha=${sha:0:7} result=refused-main-moved elapsed=$(( $(date +%s) - t0 ))s"
  exit 1
fi

git -C "$root" checkout -B main origin/main
git -C "$root" merge --ff-only "$sha"
# retry once on a lost race (a concurrent run merged first); the ancestor
# check above means the rebase can only sit us behind origin/main
git -C "$root" push --follow-tags origin main \
  || (sleep 15; git -C "$root" pull --rebase origin main && git -C "$root" push --follow-tags origin main)
echo "::notice::[merge-summary] sha=${sha:0:7} result=ff elapsed=$(( $(date +%s) - t0 ))s"
