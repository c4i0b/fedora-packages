#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

# one dnf pass up front: parallel vendor phases must not race the dnf lock
# (vendor-sources.sh reinstalls only when the tool is absent)
dnf -y install --nodocs --setopt=install_weak_deps=0 \
  git make rpmdevtools go-vendor-tools python3-specfile golang git-core \
  cargo rust-packaging >/dev/null 2>&1 \
  || sudo dnf -y install --nodocs --setopt=install_weak_deps=0 \
    git make rpmdevtools go-vendor-tools python3-specfile golang git-core \
    cargo rust-packaging

tools/lint.sh & lintpid=$!

jobs=$(nproc); [ "$jobs" -gt 8 ] && jobs=8
printf '%s\n' packages/*/ \
  | xargs -P "$jobs" -I{} make -f .copr/Makefile srpm "pkg={}" outdir=/tmp/srpm
wait "$lintpid"

# Remove downloaded/generated build artifacts (legit files are tracked)
find packages -maxdepth 2 -type f \( \
    -name '*.tar.gz' -o -name '*.tar.xz' -o -name '*.tgz' -o -name '*.zip' \
    -o -name 'vendor.tar.zst' -o -name '*-vendor.tar.bz2' -o -name 'COPYING' \
  \) -delete
rm -rf packages/*/bun-linux-*
