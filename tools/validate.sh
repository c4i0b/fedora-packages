#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
# shellcheck source=lib.sh
source "$root/tools/lib.sh"

# args restrict SRPM builds to those packages (CI validates only what changed
# since the last green run); no args builds everything
pkgs=()
if [ "$#" -gt 0 ]; then
  for name in "$@"; do
    [ -f "packages/$name/$name.spec" ] || { echo "FAIL: no spec for $name" >&2; exit 1; }
    pkgs+=("packages/$name/")
  done
else
  for dir in packages/*/; do pkgs+=("$dir"); done
fi

# one dnf pass up front: parallel vendor phases must not race the dnf lock
# (vendor-sources.sh reinstalls only when the tool is absent); timed for the
# [phase-summary] telemetry (CI decides on a prebuilt image with this number)
t0=$(date +%s)
dnf -y install --nodocs --setopt=install_weak_deps=0 \
  git make rpmdevtools go-vendor-tools python3-specfile golang git-core \
  cargo rust-packaging >/dev/null 2>&1 \
  || sudo dnf -y install --nodocs --setopt=install_weak_deps=0 \
    git make rpmdevtools go-vendor-tools python3-specfile golang git-core \
    cargo rust-packaging
echo "dnf_toolchain=$(( $(date +%s) - t0 ))" >> "${GITHUB_ENV:-/dev/null}"

tools/lint.sh "$@" & lintpid=$!

# downloads = files rpmbuild had to fetch: on a healthy cache-hit run only
# the 'releases/latest' volatiles (pruned before every cache save); anything
# more without a spec change means a prune/cache bug
srcs_before="$(srcs_find | wc -l)"
t1=$(date +%s)
jobs=$(nproc); [ "$jobs" -gt 8 ] && jobs=8
printf '%s\n' "${pkgs[@]}" \
  | xargs -P "$jobs" -I{} make -f .copr/Makefile srpm "pkg={}" outdir=/tmp/srpm
echo "validate=$(( $(date +%s) - t1 ))" >> "${GITHUB_ENV:-/dev/null}"
echo "downloads=$(( $(srcs_find | wc -l) - srcs_before ))" >> "${GITHUB_ENV:-/dev/null}"
wait "$lintpid"

# Remove downloaded/generated build artifacts (legit files are tracked).
# CI sets KEEP_SOURCES=1 so the sources cache can save them after the prune;
# locally the default keeps the working tree clean.
if [ "${KEEP_SOURCES:-0}" != "1" ]; then
  find packages -maxdepth 2 -type f \( \
      -name '*.tar.gz' -o -name '*.tar.xz' -o -name '*.tgz' -o -name '*.zip' \
      -o -name 'vendor.tar.zst' -o -name '*-vendor.tar.bz2' -o -name 'COPYING' \
    \) -delete
  rm -rf packages/*/bun-linux-*
fi
