#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
name="fedora-packages"
image="localhost/$name"
devhome="/tmp/devhome-$name"  # host tmpfs: container home is wiped on reboot by design

ensure() {
  mkdir -p "$devhome"
  podman build -q -t "$image" "$root" >/dev/null
  if ! podman container exists "$name" 2>/dev/null; then
    # --privileged stays bounded by the rootless userns: the upstream-documented
    # way to run mock inside a container (label=disable keeps host files unlabeled)
    podman run -d --name "$name" \
      --userns=keep-id --privileged \
      --security-opt label=disable \
      --init \
      -e HOME=/home/builder \
      -v "$devhome:/home/builder" \
      -v "$root:/workspaces/$name" \
      -v "$HOME/.config/copr:/home/builder/.config/copr:ro" \
      -v "$name-mock-cache:/var/cache/mock" \
      -w "/workspaces/$name" \
      "$image" sleep infinity
  elif [ "$(podman inspect -f '{{.State.Running}}' "$name")" != true ]; then
    podman start "$name" >/dev/null
  fi
  # the home bind hides the image-layer ~/rpmbuild
  podman exec "$name" rpmdev-setuptree 2>/dev/null || true
}

git -C "$root" config core.hooksPath .githooks

case "${1:-}" in
  --no-enter) ensure ;;
  exec)
    shift
    [ "${1:-}" = -- ] && shift
    ensure
    exec podman exec -i "$name" bash -lc "$*"
    ;;
  *) ensure; exec podman exec -it "$name" bash -l ;;
esac
