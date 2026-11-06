#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
packages="copr-cli rpkg rpmdevtools rpmlint make git curl pyproject-rpm-macros cargo-rpm-macros go-vendor-tools"
enter=1
[ "${1:-}" = "--no-enter" ] && enter=0

if ! distrobox list 2>/dev/null | grep -qw fedora-packages; then
  # container home inside the repo (gitignored), not the host's; the ini
  # stays path-free, DBX_CONTAINER_CUSTOM_HOME carries the absolute path
  mkdir -p "$root/.distrobox/home"
  DBX_CONTAINER_CUSTOM_HOME="$root/.distrobox/home" \
    distrobox assemble create --file "$root/.distrobox/fedora-packages.ini"
fi

git -C "$root" config core.hooksPath .githooks

# The COPR token stays in the HOST home; the container home is a separate
# dir, so link it in (host home is mounted at /run/host inside the box)
if [ -f "$HOME/.config/copr" ] && [ ! -e "$root/.distrobox/home/.config/copr" ]; then
  mkdir -p "$root/.distrobox/home/.config"
  ln -s "/run/host$HOME/.config/copr" "$root/.distrobox/home/.config/copr"
fi

if [ "$enter" = 1 ]; then
  exec distrobox enter fedora-packages
fi
