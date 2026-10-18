#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
packages="copr-cli rpkg rpmdevtools rpmlint make git curl pyproject-rpm-macros cargo-rpm-macros go-vendor-tools"
enter=1
[ "${1:-}" = "--no-enter" ] && enter=0

if ! distrobox list 2>/dev/null | grep -qw fedora-packages; then
  distrobox create --yes --config "$root/.distrobox/fedora-packages.ini" 2>/dev/null \
    || distrobox create --yes --name fedora-packages \
      --image registry.fedoraproject.org/fedora:rawhide \
      --additional-packages "copr-cli rpkg rpmdevtools rpmlint make git curl pyproject-rpm-macros cargo-rpm-macros go-vendor-tools"
fi

git -C "$root" config core.hooksPath .githooks

if [ "$enter" = 1 ]; then
  exec distrobox enter fedora-packages
fi
