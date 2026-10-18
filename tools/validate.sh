#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

tools/lint.sh

for dir in packages/*/; do
    make -f .copr/Makefile srpm "pkg=$dir" outdir=/tmp/srpm
done

# Remove downloaded/generated build artifacts (legit files are tracked)
find packages -maxdepth 2 -type f \( \
    -name '*.tar.gz' -o -name '*.tar.xz' -o -name '*.tgz' -o -name '*.zip' \
    -o -name 'vendor.tar.zst' -o -name '*-vendor.tar.bz2' -o -name 'COPYING' \
  \) -delete
rm -rf packages/*/bun-linux-*
