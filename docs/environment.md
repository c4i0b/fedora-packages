# Development environment

The host provides only `just` + `podman` (same model as the finance repo):
every recipe transparently prefixes `podman compose run --rm tooling`, an
**ephemeral** container (Fedora Rawhide) defined by `Containerfile` +
`compose.yml`. No state survives a run; anything the environment needs must
be in the image — if it is not in the `Containerfile`, it does not exist.
`FEDORA_PACKAGES_DIRECT=1` runs commands directly instead (used by CI).

## Lifecycle

- `just image` builds the image and enables the versioned pre-commit hooks
  (`core.hooksPath`) — re-run after `Containerfile` changes; layer cache makes
  rebuilds near-instant unless a layer changed.
- `just shell` opens an interactive bash in the container with the repo
  bind-mounted at `/app`.
- `just --list` lists every recipe.

The container runs as uid 0 (maps to the unprivileged host user in rootless
podman — no host privilege gained; it is the only uid that can write the
bind mount). Repo mount uses `:z` (shared SELinux label) so concurrent runs
keep access.

## Credentials

- The COPR token (`~/.config/copr` in the host home) is mounted read-only
  into the container.
- git push / gh are HOST-side only: the gh token lives in the host system
  keyring, unreachable from containers. Do not require gh inside the
  container.
- The container HOME is `/tmp` and dies with each run, so the copr-cli
  session cache (`~/.cache/copr`) can never go stale.
- The host has no copr-cli/ssh — never run rpmbuild or copr-cli on it.

## Hooks

`.githooks/pre-commit` is a thin wrapper: it runs `tools/pre-commit.sh`
wherever the rpm toolchain lives — directly inside the container (`just
shell`), or through `podman compose run` when invoked by host git.

## Recipe logic

Recipe logic lives in `tools/*.sh`; the justfile stays a thin dispatcher —
put new logic in a script, not inline in the justfile.
