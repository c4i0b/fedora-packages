# AGENTS.md — fedora-packages

RPM spec monorepo built server-side by COPR (Fedora stable + Rawhide). The
GitHub repo is the source of truth: COPR clones it, produces SRPMs via
`.copr/Makefile` (`make_srpm` contract) and rebuilds packages through a
webhook on every push. There is no CI-side building.

## Environment (mandatory)

- All development happens inside the `fedora-packages` distrobox (Fedora
  Rawhide). `just` runs on the **host** and is the only entrypoint: every
  recipe transparently prefixes `distrobox enter fedora-packages --`.
  `FEDORA_PACKAGES_DIRECT=1` runs commands directly instead (used by CI).
  Do not run `just` from inside the box (it would nest distrobox).
- Run `just box` once to create the box (from `.distrobox/fedora-packages.ini`,
  falling back to explicit flags on distrobox versions without `--config`);
  it also enables the versioned pre-commit hooks (`core.hooksPath`).
- The host has no copr-cli/ssh — never run rpmbuild or copr-cli on it.
- COPR token lives in `~/.config/copr` (home is bind-mounted into the box).
  Clear `~/.cache/copr` when switching COPR accounts (stale sessions 401).
- Git remote is HTTPS + gh credential helper (no ssh available).

## Identity split (a costly past mistake)

- GitHub and COPR owners are **different** (GitHub `c4i0b`, COPR/FAS
  `caiobruno`; defaults live in the justfile — check there, they may change).
  Package clone URLs must use the GitHub owner; COPR project paths use the FAS
  owner. Mixing them makes the SRPM build fail with
  `could not read Username for 'https://github.com'`.

## Commands

`just --list` for all. Key ones:

- `just new-package <name> [source|bin|go|rust|python|electron|bun]` — scaffold a spec from `templates/`
- `just srpm <name>` — build one SRPM with the same make_srpm contract COPR uses
- `just build-local <name> [chroot|all]` — full mock build (rawhide + oldest stable by
  default, with network); only for reproducing a COPR failure when its log is
  inconclusive
- `just status` — COPR build list; check it when finishing work if builds were left pending
- `just prune-builds [dry]` — delete old COPR builds, keeping only the newest
  per package
- `just watch [name] [interval]` — follow in-flight COPR builds until they finish (exits non-zero on any failure; interval in seconds, default 90)
- `just test` — package invariants + template rendering check (scaffolds can never drift from the standard)
- `just validate` — lint + SRPMs for all packages (identical to CI)
- `just bump <name> <version>` — Version + Release + changelog in one shot
- `just add-package <name>` — register a package in COPR (SCM + webhook rebuild)
- `just build <name>` — submit a COPR rebuild
- `just setup` — create or update the COPR project (idempotent); includes the
  latest EPEL chroot (no auto-branching there: re-run it after a major EPEL
  release, then poke builds once — adding a chroot rebuilds nothing).

Recipe logic lives in `tools/*.sh`; the justfile stays a thin dispatcher —
put new logic in a script, not inline in the justfile.

## COPR make_srpm contract

- COPR invokes `make -f .copr/Makefile srpm outdir=... spec=...` with cwd in
  the package directory and `spec=` pointing at the **subdirectory**, not the
  .spec file. The Makefile resolves both — do not simplify it away.
- The SRPM builder chroot has an **arbitrary architecture** (aarch64 observed).
  Source URLs must never depend on the build arch: ship one `Source` per arch
  and select with `%ifarch` in `%prep` (see any -bin package).
- `_disable_source_fetch 0` is what lets rpmbuild download URL sources
  (COPR sets it; the Makefile defines it for local parity).

## Webhook semantics (verified in COPR source code)

- A push rebuilds a package **only if the commit touches files under its
  `packages/<name>/` directory**. Empty commits trigger nothing.
- Pushes made with GITHUB_TOKEN trigger the COPR webhook but do NOT
  re-trigger GitHub Actions workflows.
- Webhook is push events only, `application/json`, obtained from COPR
  Settings → Integrations.

## Automatic updates

- `packages/<name>/upstream` selects the tracker: `owner/repo` → GitHub
  Releases latest (leading `v` stripped), `tags:owner/repo` → latest git tag
  via `ls-remote` (tags-only repos, any forge, zero API quota) or
  `npm:<package>` → npm dist-tag `latest`.
- Registry/GitHub API responses are **compact JSON (single line)**: extract
  fields with `grep -oE`, never with per-line `awk -F'"'`.
- Scheduled multiple times per day (see `autoupdate.yml` for the cron);
  an in-script empty-commit keepalive (only after 45 idle days) defeats
  GitHub's 60-day inactivity rule — do not use keepalive-workflow actions
  (the popular one is ToS-blocked and breaks workflows).
- Renovate was evaluated and rejected — do not reintroduce without discussion.

## Upstream quirks

General:
- `CFLAGS=...` on the make command line overrides every `+=` append in the
  Makefiles (breaking upstream feature detection): `export CFLAGS=...`
  before `%make_build` instead.
- EPEL chroots run one generation older toolchains than Fedora (rpm 4.19 on
  EPEL 10): macros in comments break the spec parse (test.sh rejects them)
  and ELF binaries without a GNU build-id note abort the build — non-GCC
  toolchain specs carry `%global _missing_build_ids_terminate_build 0` next
  to `%global debug_package %{nil}`. When a package needs something beyond
  base toolchains, verify it exists in EPEL + CS AppStream/CRB (repoquery)
  before counting on it.
- COPR runs rpmbuild unprivileged: scriptlets must never write outside
  %{buildroot} (test.sh rejects it); local mock runs as root and hides this.
- Upstream makefiles that build static archives with a plain `ar` lose
  symbols under partial LTO (undefined refs to symbols that ARE in the
  archive) — strip `-f*lto*` from CFLAGS in those specs. The same manual
  `ar` is often parallel-unsafe too: two sub-makes rebuild the same objects
  and the final archive lands truncated (mdk4 osdep) — build with `-j1`.
- zig packages vendor their `build.zig.zon` closure at SRPM time
  (`Source: zig-pkg.tar.*` via tools/vendor-sources.sh) and build with
  `zig build --system zig-pkg` — zig's own http client fails on COPR
  builders, and only a dependency's *root* zon belongs to the graph
  (scanning fetched sub-zons pulls gigabytes of junk). Note `--system`
  implies zig's system package mode: install paths and defaults change
  (ghostty moves systemd units to `%{_prefix}/lib/systemd/user` and flips
  `emit-docs` on) — audit `%files` and build flags accordingly.
- Never hardcode upstream desktop-file/app-id names in %install/%files:
  upstreams rename them between releases (solidcraft's
  ai.storyteller → io.tangencylabs) — glob the desktop file and icons.
- The Fedora meson macro forces `--auto-features=enabled` and cannot be
  overridden (argument concatenation): for minimal builds, call
  `meson setup %{_vpath_builddir} --auto-features=disabled ...` directly
  (the meson_build/meson_install helpers keep working) and disable the
  few non-auto defaults explicitly (mpv's `gl` defaults to enabled).
- Man pages get brp-compressed in the buildroot (`foo.1` becomes
  `foo.1.gz`): always glob `%files` entries as `%{_mandir}/man1/foo.1*`.
- mock's buildroot ships gcc but not g++: anything compiling C++ (CGO
  wrappers, build scripts falling back from cc) needs an explicit
  `BuildRequires: gcc-c++`.
- `%check` runs against `%{buildroot}`: invoke wrappers whose shebangs point
  at final installed paths via the real interpreter, and give first-run
  `~/` writers a scratch `HOME=` — otherwise check-buildroot/check-files
  fail on stray paths.
- Non-GCC toolchains (zig, elvish, …) emit no GNU build-id note, and empty
  debugsource lists break rpm 6.1+ — carry `%global debug_package %{nil}`
  in those (and all -bin) specs. Add `%global __strip /bin/true` **only**
  for Bun/Electron payloads (stripping corrupts them).

Python:
- `%pyproject_wheel` needs `BuildRequires: python3-pip`. `%pyproject_save_files`
  `-l <name>` is assert-license **and** the module glob, and it validates the
  wheel RECORD — strip unwanted payload from the source tree in `%prep`,
  never from the buildroot. Smoke-testing an installed console script needs
  `PYTHONPATH=%{buildroot}%{python3_sitelib}` (and version flags can exit
  nonzero: guard substitutions with `|| :` under `sh -e`).
- Venv/wheel installs bundle manylinux libs with auditwheel-hashed sonames
  (`libjpeg-31e2ca52.so.62.4.0`): RPM emits versioned requires nothing
  provides (not even the package itself), making the rpm uninstallable —
  carry `%global __requires_exclude ^lib.+-[0-9a-f]{8}\\.so` (see
  hermes-agent).

Rust:
- Old crates against the system OpenSSL: Fedora ships no `openssl/engine.h`
  and rawhide's OpenSSL major bumps are rejected by older openssl-sys —
  prefer the crate's `vendored-openssl` feature (`perl` + `perl-FindBin`)
  over patching version checks.
- Stale Cargo.lock pins breaking on new rustc (E0282 "type annotations
  needed" & friends): `cargo update -p <crate>` in %prep (builds run with
  network).
- Newer rustc denies old idioms outright (never-type-fallback via mlua's
  untyped `.eval()` etc): `export RUSTFLAGS="-A <lint-name>"` in %build
  rather than patching vintage code.
- zbus's `#[validate]` macro (zbus-lockstep) resolves its D-Bus XML dir as
  `../xml` relative to the crate being compiled: in a vendored build that
  lands on the vendored `xml` CRATE (its extensionless LICENSE panics the
  macro). Export `LOCKSTEP_XML_PATH=<builddir>/vendor/atspi-common/xml`
  in %build (see any craft spec).
- `cargo vendor` trees with git deps (e.g. storytold craft-libs) need the
  `[source."git+https://…"]` blocks cargo vendor prints appended to the
  config the cargo_prep macro writes; vendor-sources.sh ships them inside
  vendor.tar.zst as `git-sources.conf` — `cat` it onto `.cargo/config.toml`
  in %prep.
- `cargo-rpm-macros` cannot build a single workspace member (`-n` is
  `--no-default-features`, other flags rejected): invoke
  `%{__cargo} build %{?_smp_mflags} -Z avoid-dev-deps --profile rpm -p <crate>`
  in %build and `install -Dm755 target/release/<crate>` in %install (the
  prep macro symlinks target/release to the rpm profile); `%cargo_install`
  from a member dir demands a local Cargo.lock and dies offline.
- `aws-lc-sys` (common via rustls/reqwest) refuses RPM's `-O2`: drop it with
  `%global build_cflags %(echo "%{build_cflags}" | sed 's/ *-O2//g')` —
  plain `export CFLAGS` gets overridden by the %cargo macros.

npm:
- Apps may ship no GitHub Releases: the `upstream` file supports
  `npm:<package>` tracking. A bundled-`node_modules` tarball is **not
  necessarily complete** (regular `dependencies` may be missing) and can
  carry prebuilt arch binaries/wasm that break a noarch payload —
  smoke-run the CLI from the buildroot in `%check` to catch both.
- Tauri source builds (artcraft) need the frontend compiled in `%build`
  before cargo — `npx nx run <app>:build` writes the `frontendDist` the
  tauri-build script embeds — plus `pkgconfig(webkit2gtk-4.1)`, gtk3 and
  libsoup-3. BuildRequire `/usr/bin/npm`, not `npm`: EL10 only ships
  nodejs-npm. npm 11 blocks postinstall scripts, but esbuild/swc pull their
  platform binaries as optional deps, so the Vite build still works; export
  `NX_DAEMON=false` so Nx does not fork a daemon into the build chroot.

## Repo conventions

- Before adding a package, check it is not already in Fedora official repos
  or RPM Fusion — query the **oldest stable release**, not only rawhide
  (packages can be retired in rawhide while still shipped in stable);
  if absent, look at how existing COPRs, the AUR or other distros package it
  for reference (especially for source builds) — then adapt to this repo's
  conventions. The reverse also bites: a dependency shipped in stable can be
  retired from rawhide (ccze for hollywood) — check both ends before
  relying on one.
- Do not block waiting for COPR builds. Continue working and check
  `just status` when finishing a task if any build is still unconfirmed.
- COPR is the only build validator: on new or changed packages, `just test`
  locally and push — the webhook builds. Never run `just build-local`
  preemptively; reserve it for when a COPR failure log is inconclusive and the
  build must be reproduced (mock runs with network, matching the project).
- When a COPR build fails: follow the `diagnose-copr-failure` skill
  (`skills/diagnose-copr-failure/SKILL.md`) to fetch and read the builder
  log, fix, push. If the same class of failure bites twice, encode it as an
  invariant in tools/test.sh, a template, or a one-line comment — fix the
  class, not just the instance.
- Do not gate builds on upstream-shipped metadata quality (e.g.
  appstream/metainfo validation errors in upstream files): validate what we
  generate, not what upstream ships broken.
- Ship shell completions whenever the binary can generate them (see the
  templates); skip when upstream has none — never hand-write them.
- Ship upstream's `NOTICE` (or equivalent notices file) as `%license` when
  the source tree has one; smoke-run any headless CLI the package installs
  in `%check`.
- Squash/amend + force-push to `main` is acceptable; keep a small clean history.
- Never commit archives (`*.tgz`, `*.tar.gz` gitignored) — sources are
  downloaded at build time.
- When trimming comments from `.spec` files, never remove required headers (`Name:`, `Version:`, `Release:`, `Summary:`, `License:`, `URL:`). Some templates rely on those tags appearing early; stripping leading comment blocks blindly can drop them. Always run `just test` after bulk spec edits.
- Source builds are the priority: `just new-package <name> source|go|rust`
  (vendoring runs automatically at SRPM time, which has network). The COPR
  project also has build network enabled (`--enable-net on`, see
  tools/setup-project.sh), so builds may download self-contained toolchains
  at build time. When adding/converting, reference how existing
  COPRs/distros package the same app.
- `-bin` is justified only by: a bundled runtime that IS the product
  (e.g. Electron apps) or root/hardware build steps (disk images, loop
  devices). State which in a one-line spec comment. If every other distro
  ships it as -bin, that is the signal.
- `-bin` marks a package we do not build from source (upstream binaries
  shipped as-is); never add it just because a same-named package exists in
  Fedora official.
- BuildRequire every package providing the macros you use (pyproject macros,
  rust-packaging, go-vendor-tools...): an undefined macro reaches the shell
  literally and dies as "fg: no job control". Include build backends too
  (python3-setuptools/python3-wheel) — Fedora builds without isolation.
- Never add Epoch; if a release must be skipped or downgraded, push a commit
  message `autoupdate: override <version>` on the package (the bot respects it).
  When fixing a failed build, do not bump Release/changelog if that build never
  completed (a failed build never delivered the version).
- English only, concise README. In any code (specs, scripts, tools): comments
  only for non-obvious workarounds — never the obvious; full context lives here.
- When `fedora-review` is enabled on the project, builds run slower than
  usual — that is expected, not a hang.
