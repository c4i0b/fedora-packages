# Repo conventions

## Adding a package

- Before adding, check it is not already in Fedora official repos or RPM
  Fusion — query the **oldest stable release**, not only rawhide (packages
  can be retired in rawhide while still shipped in stable); if absent, look
  at how existing COPRs, the AUR or other distros package it for reference
  (especially for source builds) — then adapt to this repo's conventions.
  The reverse also bites: a dependency shipped in stable can be retired from
  rawhide (ccze for hollywood) — check both ends before relying on one.
- Source builds are the priority: `just new-package <name> source|go|rust`
  (vendoring runs automatically at SRPM time, which has network). The COPR
  project also has build network enabled (`--enable-net on`, see
  `tools/setup-project.sh`), so builds may download self-contained
  toolchains at build time. When adding/converting, reference how existing
  COPRs/distros package the same app.

## `-bin` policy

- `-bin` marks a package we do not build from source (upstream binaries
  shipped as-is); never add it just because a same-named package exists in
  Fedora official.
- `-bin` is justified only by: a bundled runtime that IS the product (e.g.
  Electron apps) or root/hardware build steps (disk images, loop devices).
  State which in a one-line spec comment. If every other distro ships it as
  -bin, that is the signal.

## Specs

- BuildRequire every package providing the macros you use (pyproject macros,
  rust-packaging, go-vendor-tools...): an undefined macro reaches the shell
  literally and dies as "fg: no job control". Include build backends too
  (python3-setuptools/python3-wheel) — Fedora builds without isolation.
- When trimming comments from `.spec` files, never remove required headers
  (`Name:`, `Version:`, `Release:`, `Summary:`, `License:`, `URL:`). Some
  templates rely on those tags appearing early; stripping leading comment
  blocks blindly can drop them. Always run `just test` after bulk spec edits.
- Do not gate builds on upstream-shipped metadata quality (e.g.
  appstream/metainfo validation errors in upstream files): validate what we
  generate, not what upstream ships broken.
- Ship shell completions whenever the binary can generate them (see the
  templates); skip when upstream has none — never hand-write them.
- Ship upstream's `NOTICE` (or equivalent notices file) as `%license` when
  the source tree has one; smoke-run any headless CLI the package installs
  in `%check`.

## Repo hygiene

- Never commit archives (`*.tgz`, `*.tar.gz` gitignored) — sources are
  downloaded at build time.
- Never add Epoch (see [autoupdate.md](autoupdate.md) for overrides).
- Squash/amend + force-push to `main` is acceptable; keep a small clean
  history.
- English only, concise README. In any code (specs, scripts, tools):
  comments only for non-obvious workarounds — never the obvious; full
  context lives in these docs.
