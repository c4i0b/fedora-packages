# COPR integration

The GitHub repo is the source of truth: COPR clones it, produces SRPMs via
`.copr/Makefile` and rebuilds packages through a webhook on every push. There
is no CI-side building.

## CI workflow roles

The pipeline shape is bump → gate → (builder pulls) → report; workflow
names follow it (file name always equals `name:`):

- `autoupdate` — scheduled version bumps.
- `validate` — the git-side gate (PR/push): invariants, SRPM pre-flight.
- (delivery) — none: COPR pulls via webhook on push.
- `badges` — status-artifact refresh.
- (auto-merge — not used; no bot PRs).

Generic workflow conventions (pinned SHAs, bash-invoked scripts, timeouts,
concurrency, push-retry, GITHUB_TOKEN semantics) live in the
gh-actions-conventions skill.

## make_srpm contract

- COPR invokes `make -f .copr/Makefile srpm outdir=... spec=...` with cwd in
  the package directory and `spec=` pointing at the **subdirectory**, not the
  .spec file. The Makefile resolves both — do not simplify it away.
- The SRPM builder chroot has an **arbitrary architecture** (aarch64
  observed). Source URLs must never depend on the build arch: ship one
  `Source` per arch and select with `%ifarch` in `%prep` (see any -bin
  package).
- `_disable_source_fetch 0` is what lets rpmbuild download URL sources
  (COPR sets it; the Makefile defines it for local parity).

## Webhook semantics (verified in COPR source code)

- A push rebuilds a package **only if the commit touches files under its
  `packages/<name>/` directory**. Empty commits trigger nothing.
- Pushes made with GITHUB_TOKEN trigger the COPR webhook but do NOT
  re-trigger GitHub Actions workflows.
- Webhook is push events only, `application/json`, obtained from COPR
  Settings → Integrations.

## Build validation policy

- COPR is the only build validator: on new or changed packages, `just test`
  locally and push — the webhook builds.
- Never run `just build-local` preemptively; reserve it for when a COPR
  failure log is inconclusive and the build must be reproduced (mock runs
  with network, matching the project; rawhide + oldest stable by default).
- Do not block waiting for COPR builds. Continue working and check
  `just status` / `just watch` when finishing a task if any build is still
  unconfirmed.
- When a COPR build fails: follow the `diagnose-copr-failure` skill
  (`skills/diagnose-copr-failure/SKILL.md`) to fetch and read the builder
  log, fix, push. If the same class of failure bites twice, encode it as an
  invariant in `tools/test.sh`, a template, or a one-line comment — fix the
  class, not just the instance.
- When fixing a failed build, do not bump Release/changelog if that build
  never completed (a failed build never delivered the version).
- `just setup` (create/update the COPR project) includes the latest EPEL
  chroot; there is no auto-branching there — re-run it after a major EPEL
  release, then poke builds once (adding a chroot rebuilds nothing).
- When `fedora-review` is enabled on the project, builds run slower than
  usual — that is expected, not a hang.
