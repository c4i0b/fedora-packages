#!/usr/bin/env bash
set -euo pipefail

project="${1:?usage: setup-project.sh <owner>/<project>}"

# Three latest stable Fedoras + rawhide, discovered at bootstrap; afterwards
# --follow-fedora-branching keeps the project rolling on its own. EPEL has no
# branching follow: the latest one is discovered here, so re-running after a
# major EPEL release adds its chroot (adding it does not rebuild anything —
# poke each package once afterwards).
args=()
for chroot in $(
  copr-cli list-chroots \
    | grep -E '^fedora-[0-9]+-x86_64$' \
    | sort -V | tail -3
  echo fedora-rawhide-x86_64
  copr-cli list-chroots \
    | grep -E '^epel-[0-9]+-x86_64$' \
    | sort -V | tail -1
); do
  args+=(--chroot "$chroot")
done

copr-cli create "$project" "${args[@]}" --unlisted-on-hp off >/dev/null 2>&1 || true
copr-cli modify "$project" \
  --follow-fedora-branching on \
  --fedora-review on \
  --appstream off \
  --auto-prune on \
  --enable-net on
