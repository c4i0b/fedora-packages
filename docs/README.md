# fedora-packages docs

Evergreen reference. Start here; the lean rule list agents must follow every
session lives in [AGENTS.md](../AGENTS.md).

- [environment.md](environment.md) — ephemeral tooling container, credentials,
  the `just` runner, CI parity
- [copr.md](copr.md) — `make_srpm` contract, webhook semantics, build
  validation policy
- [autoupdate.md](autoupdate.md) — upstream trackers, cron, keepalive
- [conventions.md](conventions.md) — adding packages, `-bin` policy, spec and
  repo conventions
- [workflow.md](workflow.md) — optional beads task tracking and parallel
  orchestration of the bd task graph
- packaging quirks by ecosystem:
  [general](packaging/general.md) ·
  [python](packaging/python.md) ·
  [rust](packaging/rust.md) ·
  [npm](packaging/npm.md)
