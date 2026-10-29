# Packaging backlog

Candidate tools vetted on 2026-10-28: confirmed absent from Fedora rawhide and
not already in this repo. Work top to bottom; strike through when shipped.

## Tier 1 — high value, trivial build

- [x] **mise** — runtime/version manager (modern asdf). Go, single binary.
  Template: `go`. https://github.com/jdx/mise — *shipped 2026.10.23-1*
- [x] **dive** — Docker/OCI image layer and waste inspector. Go.
  Template: `go`. https://github.com/wagoodman/dive — *shipped 0.13.1-1*
- [x] **bottom** (binary `btm`) — TUI system monitor. Rust.
  Template: `rust`. https://github.com/ClementTsang/bottom — *shipped 0.14.9-1*
- [x] **xh** — HTTPie/curl hybrid HTTP client. Rust.
  Template: `rust`. https://github.com/ducaale/xh — *shipped 0.26.3-1*

## Tier 2 — network/TUI theme fit

- [x] **trippy** (binary `trip`) — TUI traceroute. Rust.
  Template: `rust`. https://github.com/fujiapple852/trippy — *shipped 0.13.0-1*
- [x] **gping** — ping TUI with graphs. Rust.
  Template: `rust`. https://github.com/orf/gping — *shipped 1.21.0-1*
- [x] **oha** — modern HTTP load tester. Rust.
  Template: `rust`. https://github.com/hatoo/oha — *shipped 1.16.0-1*
- [x] **atac** — TUI API client (terminal Postman). Rust.
  Template: `rust`. https://github.com/julien-cpsn/atac — *shipped 0.24.0-1*

## Container tools — podman/docker focus (Tier 1+2, CLI/TUI only)

- [x] **ctop** — `top` for containers (podman+docker); pairs with lazydocker/oxker.
  Go. Template: `go`. https://github.com/bcicen/ctop — *shipped 0.7.7-1*
- [x] **dockle** — container image linter (CVEs, Dockerfile best practices);
  companion to dive. Go. Template: `go`. https://github.com/goodwithtech/dockle — *shipped 0.4.15-1*
- [x] **syft** — SBOM generator for images; complements Fedora's grype.
  Go. Template: `go`. https://github.com/anchore/syft — *shipped 1.55.0-1*
- [x] **regclient** — registry surgery: copy, retag, inspect manifests,
  garbage ops; ships regctl+regsync+regbot. Go.
  Template: `go`. https://github.com/regclient/regclient — *shipped 0.11.7-1*
Replacements made (kept one tool per purpose):
- **ctop** replaces **dry** — both are container TUI managers (and lazydocker/
  oxker already ship); ctop is far more popular and covers podman.
- **regctl** replaces **crane** — both do daemonless image/registry ops;
  regclient ships regctl+regsync+regbot and a richer CLI.

Rejected for this batch: podman-desktop (GUI-only batch rule), cosign
(keeps the tier tight; candidate for a later batch), dry and crane (dropped
as duplicates of ctop and regctl respectively).

## Deferred (high value, high effort — discuss before starting)

- **deno** — JS/TS runtime; source build pulls V8 and a giant toolchain,
  likely `-bin` with bundled-runtime justification.
- **codex-cli** — AI agent (npm); repo already carries several AI agents.

## Workflow per package

1. `just new-package <name> go|rust` (vendoring runs at SRPM time)
2. Adapt spec; ship completions the binary can generate; smoke-run in `%check`
3. `just test`, then `just add-package <name>` + `just setup` if new chroots needed
4. Push — webhook builds; check `just status` when finishing
