---
description: Use when a COPR build of a package in this repo fails and the builder log is needed to diagnose it. Covers fetching logs, the CDN cache trap, and where errors hide.
name: diagnose-copr-failure
---

# Diagnosing a failed COPR build

Project: `<COPR_OWNER>/fedora-packages` (default `caiobruno/fedora-packages`).
Find the build id with `just status`.

## Fetch the right log

Builds have two stages, each with its own log location under
`https://download.copr.fedorainfracloud.org/results/<owner>/fedora-packages/`:

- **SRPM stage**: `srpm-builds/<build-id>/builder-live.log.gz` — contains the
  make_srpm/vendor output. A failure here never reaches the chroots.
- **Binary stage**: `<chroot>/<build-id>-<pkg-name>/builder-live.log.gz` where
  `<chroot>` is e.g. `fedora-rawhide-x86_64`, `fedora-43-x86_64`. Not every
  chroot has the directory; list the parent index first to see which chroots
  ran, and compare a passing chroot against a failing one when only some fail.
  `root.log.gz` (mock setup) and `build.log.gz` sit alongside.

```sh
curl -sH 'Cache-Control: no-cache' \
  "https://download.copr.fedorainfracloud.org/results/<owner>/fedora-packages/<chroot>/<id>-<pkg>/builder-live.log.gz?nc=$(date +%s)" \
  | gunzip | less
```

**CDN cache trap**: plain curls have returned a *different build's* log (bad
CloudFront cache). Always send the cache-buster above and sanity-check the
spec/SRPM name in the output matches the package you are diagnosing.

## Where the error hides

- rpmbuild failures are near the end: grep for `Bad exit status`, `RPM build
  errors`, `Installed (but unpackaged)` and read ~30 lines of context above.
- `go build -v` failures are buried: the failing package prints **before** the
  hundreds of succeeding package lines (e.g. an `exec: "g++" not found` at
  line ~2500 of a log whose tail looks like a silent OOM). Grep the whole log
  for `exec:|fatal error:|error:` before concluding a silent kill/OOM.
- A noarch package failing every chroot with `Arch dependent binaries in
  noarch package` means ELFs/wasm/platform dirs in the payload — strip them in
  `%install` (see openclaw).

## If the log is still inconclusive

Reproduce locally with `just build-local <name> <chroot>` (mock with network).
Results land in `/var/lib/mock/<cfg>/result/` (read from inside the box). If
the local build gets further than COPR, suspect missing BuildRequires in the
minimal mock buildroot (e.g. gcc-c++) or builder memory limits.

## After fixing

`just test`, commit, push — the webhook rebuilds only the touched
`packages/<name>/`. Register new packages with `just add-package` **before**
pushing, or the first push triggers nothing and `just build <name>` is needed.

## Watching the rebuild

Don't sit on `just status` or poll by hand: run `just watch [name] [interval]`
(no name watches every in-flight build; interval is the poll period in
seconds, default 90). It locks the in-flight set on the
first poll, prints one status line per build every ~90s and exits non-zero
as soon as all watched builds have finished with at least one failure —
then come back here and fetch the log. Run it in the background if you have
other work to do meanwhile.
