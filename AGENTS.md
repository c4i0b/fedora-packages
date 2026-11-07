# AGENTS.md — fedora-packages

RPM spec monorepo built server-side by COPR (Fedora stable + Rawhide +
EPEL). The GitHub repo is the source of truth: a push to `main` rebuilds the
touched packages via webhook — there is no CI-side building. Keep this file
lean: behavioral rules an agent must follow every session. Detailed
policies live in `docs/` ([index](docs/README.md)); when adding rules here,
prefer extending a linked doc over growing this file.

## Environment

- The host provides only `just` + `podman`; every recipe runs in the
  ephemeral `tooling` container. Run `just image` once (and after
  `Containerfile` changes); `just shell` for interactive work.
  Full details: [docs/environment.md](docs/environment.md).
- GitHub and COPR owners are **different** (GitHub `c4i0b`, COPR/FAS
  `caiobruno`; defaults in the justfile — check there). Clone URLs use the
  GitHub owner; COPR project paths use the FAS owner. Mixing them fails the
  SRPM build with `could not read Username for 'https://github.com'`.

## Golden rules

- COPR is the only build validator: `just test` locally, push, let the
  webhook build. Never run `just build-local` preemptively (mock escape
  hatch for inconclusive COPR failure logs only).
- Never block waiting for COPR builds — keep working; check `just status`
  when finishing if builds are pending.
- On a COPR failure, follow the `diagnose-copr-failure` skill
  (`skills/diagnose-copr-failure/SKILL.md`). If the same class of failure
  bites twice, encode it as an invariant in `tools/test.sh`, a template, or
  a one-line comment — fix the class, not the instance.
- Before adding a package, check it is not in Fedora official or RPM Fusion
  **on the oldest stable release** (not only rawhide) — packages can be
  retired in rawhide while still shipped in stable, and vice versa.
- Never commit archives (sources are downloaded at build time); never add
  Epoch (`autoupdate: override <version>` commit instead); never bump
  Release/changelog for a build that never completed.
- Recipe logic lives in `tools/*.sh`; the justfile stays a thin dispatcher.
  English only; comments only for non-obvious workarounds.

## Reference

- COPR contract, webhook semantics, build policy: [docs/copr.md](docs/copr.md)
- Automatic updates: [docs/autoupdate.md](docs/autoupdate.md)
- Conventions (`-bin` policy, spec rules, repo hygiene):
  [docs/conventions.md](docs/conventions.md)
- Packaging quirks: [general](docs/packaging/general.md) ·
  [python](docs/packaging/python.md) ·
  [rust](docs/packaging/rust.md) ·
  [npm](docs/packaging/npm.md)
- Task tracking (optional): when the `bd` command is available on the host,
  organize multi-step work with it; when it is not, carry on without it.
  Details: [docs/workflow.md](docs/workflow.md)
