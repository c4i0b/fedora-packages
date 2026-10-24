#!/usr/bin/env bash
set -euo pipefail

# Single emission point of the validate [phase-summary]: timing/counters
# arrive via GITHUB_ENV (dnf_toolchain/validate/downloads from validate.sh),
# cache states come from the workflow, and the "sources set" definition
# lives in lib.sh (srcs_find) next to the counters that use it.
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
# shellcheck source=lib.sh
source "$root/tools/lib.sh"

srcs_files="$(srcs_find | wc -l)"
srcs_epoch="$(srcs_find -printf '%P %s\n' | sort | sha256sum | cut -c1-12)"
srcs_mb="$(du -sm packages/*/ 2>/dev/null | awk '{s+=$1} END{print s+0}')"
[ -n "${GITHUB_ENV:-}" ] && echo "srcs_epoch=$srcs_epoch" >> "$GITHUB_ENV"

fields=(
  "scope=${SCOPE:-?}"
  "pkgs=${PKGS:-all}"
  "dnf=${dnf:-na}"
  "dnf_toolchain=${dnf_toolchain:-na}"
  "test=${test:-na}"
  "validate=${validate:-na}"
  "downloads=${downloads:-na}"
  "cache=${CACHE:-na}"
  "srcs_cache=${SRCS_CACHE:-na}"
  "srcs_files=$srcs_files"
  "srcs_mb=$srcs_mb"
  "total=$(( $(date +%s) - ${JOB_START:-$(date +%s)} ))"
)
line="[phase-summary] ${fields[*]}"
echo "::notice::$line"

if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  {
    echo "## validate"
    echo
    echo "| field | value |"
    echo "|---|---|"
    for f in "${fields[@]}"; do echo "| ${f%%=*} | \`${f#*=}\` |"; done
  } >> "$GITHUB_STEP_SUMMARY"
fi
