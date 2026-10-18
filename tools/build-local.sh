#!/usr/bin/env bash
set -euo pipefail

name="${1:?usage: build-local.sh <package> [chroot|all]}"
selection="${2:-default}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
project="${COPR_OWNER:-caiobruno}/fedora-packages"

command -v mock >/dev/null 2>&1 || sudo dnf -y install mock

arch="${MOCK_ARCH:-x86_64}"
project_chroots="$(copr-cli get "$project" 2>/dev/null \
  | grep -oE "fedora-(rawhide|[0-9]+)-$arch" | sort -u)"

case "$selection" in
  default)
    # Both ends of the project chroots: rawhide + oldest stable
    oldest="$(echo "$project_chroots" | grep -E 'fedora-[0-9]+' | sort -V | head -1)"
    chroots=(fedora-rawhide-"$arch")
    [ -n "$oldest" ] && chroots+=("$oldest")
    ;;
  all)
    mapfile -t chroots < <(echo "$project_chroots")
    ;;
  *)
    chroots=("$selection")
    ;;
esac

srpmdir=/tmp/srpm
rm -rf "$srpmdir" && mkdir -p "$srpmdir"
make -C "$root" -f "$root/.copr/Makefile" srpm "pkg=$root/packages/$name/" "outdir=$srpmdir"

srpm=$(ls "$srpmdir"/*.src.rpm | head -1)
for chroot in "${chroots[@]}"; do
  echo "rebuilding $srpm in mock ($chroot)"
  sudo mock --rebuild --no-bootstrap-chroot --uniqueext="fp$$" --enable-network -r "$chroot" "$srpm"
done
echo "OK: validated on ${chroots[*]}"
