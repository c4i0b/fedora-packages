# fedora-packages docs

Evergreen reference. Start here; the lean rule list agents must follow every
session lives in [AGENTS.md](../AGENTS.md). Trust labels: `live` documents
maintained truth, `reference` stable background.

- [environment.md](environment.md) — live: ephemeral tooling container,
  credentials, the `just` runner, CI parity
- [copr.md](copr.md) — live: `make_srpm` contract, webhook semantics, build
  validation policy
- [autoupdate.md](autoupdate.md) — live: upstream trackers, cron, keepalive
- [conventions.md](conventions.md) — live: adding packages, `-bin` policy,
  spec and repo conventions
- [workflow.md](workflow.md) — live: optional beads task tracking and
  parallel orchestration of the bd task graph
- packaging quirks by ecosystem — reference:
  [general](packaging/general.md) ·
  [python](packaging/python.md) ·
  [rust](packaging/rust.md) ·
  [npm](packaging/npm.md) ·
  [dotnet](packaging/dotnet.md)
