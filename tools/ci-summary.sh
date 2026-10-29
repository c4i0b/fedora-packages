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
# epoch covers source AND vendor archives plus the .vendor-ok stamps: a new
# vendor tar (fresh package, bump, toolchain change) must trigger a cache
# save just like a new source tarball
srcs_epoch="$(
  {
    srcs_find -printf '%P %s\n'
    find packages \( -name 'vendor.tar.zst' -o -name '*-vendor.tar.*' \
      -o -name 'zig-pkg.tar.*' -o -name '.vendor-ok' \) -printf '%P %s\n'
  } | sort | sha256sum | cut -c1-12
)"
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
  "vendor_runs=${vendor_runs:-na}"
  "vendor_skips=${vendor_skips:-na}"
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
