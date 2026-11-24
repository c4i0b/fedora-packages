# Packaging quirks — Rust

- Old crates against the system OpenSSL: Fedora ships no `openssl/engine.h`
  and rawhide's OpenSSL major bumps are rejected by older openssl-sys —
  prefer the crate's `vendored-openssl` feature (`perl` + `perl-FindBin`)
  over patching version checks.
- Stale Cargo.lock pins breaking on new rustc (E0282 "type annotations
  needed" & friends): add a `# cargo-update: -p <crate>` comment to the
  spec — vendor-sources.py runs it before vendoring, so the fresh crate
  and the updated lock both land in the SRPM (a plain `cargo update` in
  %prep cannot work for vendored builds: the new version is not in
  vendor.tar.zst). wezterm (unvendored) does the %prep equivalent.
- When the broken pin has NO fixed version in its semver range
  (rustix 0.37.x via souvlaki -> zbus 3 -> async-io 1 vs rustc's reserved
  `rustc_*` attributes, limusic), `cargo-update` cannot help: force the
  crate's alternate backend instead — `%global build_rustflags
  %{build_rustflags} --cfg=rustix_use_libc` compiles the libc backend,
  which never touches the offending linux_raw code (any rustix 0.38+/1.x
  in the same tree ignores the cfg).
- Newer rustc denies old idioms outright (never-type-fallback via mlua's
  untyped `.eval()` etc): `export RUSTFLAGS="-A <lint-name>"` in %build
  rather than patching vintage code. When the rustc finally *stabilizes*
  the behavior the lint allow stops covering it (hard E0277): bump the
  crate in the lockfile instead (wezterm's `cargo update -p mlua` in
  %prep — the unvendored equivalent of the cargo-update comment).
- zbus's `#[validate]` macro (zbus-lockstep) resolves its D-Bus XML dir as
  `../xml` relative to the crate being compiled: in a vendored build that
  lands on the vendored `xml` CRATE (its extensionless LICENSE panics the
  macro). Export `LOCKSTEP_XML_PATH=<builddir>/vendor-deps/atspi-common/xml`
  in %build (see any craft spec).
- `cargo vendor` refuses the same crate+version pinned at two git revs
  (craft-libs revs drift between craft apps' locks): vendor-sources.py
  fetches a tree per lock rev into `dup-pinned/<repo>-<rev8>`, maps each
  crate to the rev the workspace manifests declare (falling back to the
  first lock rev for transitive crates), and adds a path
  `[patch."<repo>"]` entry per crate. **Never pick the first lock rev
  blindly**: a `[patch]` applies to every git edge for that crate, so an
  arbitrary rev leaks into consumers compiled against another rev
  (`craft_xml::El` vs `craft_xml::tree::El`, `wav::Reader` not implementing
  `ByteSource`). Two more traps make the naive patch fail: the repo root is
  a virtual workspace manifest (not a patch target), and cargo resolves a
  path target's `workspace = true` inheritance against the patching
  workspace, not the target's own — so vendor-sources *flattens* the
  fetched members into standalone manifests (inlining
  workspace.package/dependencies/lints, same-repo git refs become in-tree
  path deps, dangling dev-dep feature refs dropped). Each tree stays
  self-contained; crates whose canonical tree is another rev get version
  build metadata (`0.1.0+<rev8>`): semver-equal, but a distinct lockfile
  entry. Renamed duplicate deps get a physical copy named after the dep
  key; edits are journaled in `dup-pinned/.renamed-entries.json` and
  reverted on re-runs that extract a repacked Source0. Rewriting TOML
  requires scalars-before-subtables (see `_toml_dumps`), or a dep such as
  `quick-xml` silently lands inside `[dependencies.serde]`.
- `cargo vendor` trees with git deps (e.g. storytold craft-libs) need the
  `[source."git+https://…"]` blocks cargo vendor prints appended to the
  config the cargo_prep macro writes; vendor-sources.py ships them inside
  vendor.tar.zst as `git-sources.conf` — `cat` it onto `.cargo/config.toml`
  in %prep.
- A `[patch.crates-io]` entry for a crate nothing in the graph depends on is
  never vendored, yet cargo eagerly validates every patch entry against the
  directory source and aborts — vendor-sources.py drops unvendored **git**
  patch entries (and re-packs the source tarball) automatically at SRPM time;
  path patch entries are always kept (path-patched crates stay in-tree and
  are never vendored).
- `cargo-rpm-macros` cannot build a single workspace member (`-n` is
  `--no-default-features`, other flags rejected): invoke
  `%{__cargo} build %{?_smp_mflags} -Z avoid-dev-deps --profile rpm -p <crate>`
  in %build and `install -Dm755 target/release/<crate>` in %install (the
  prep macro symlinks target/release to the rpm profile); `%cargo_install`
  from a member dir demands a local Cargo.lock and dies offline.
- Heavy Rust trees that outgrow COPR's 5 h timeout: set
  `%global rustflags_codegen_units 16` + `%global rustflags_debuginfo 0`
  (see solidcraft/vectorcraft) instead of waiting out a second timeout.
  The cargo profile settings live in the config %cargo_prep writes:
  env `CARGO_PROFILE_RPM_*` outranks it, plain RUSTFLAGS does not (mise
  history, 6817333) — the %globals are the idiom because %cargo_prep
  expands them straight into [profile.rpm].
- Craft-style app ids churn across releases (ai.storyteller.* renames):
  never hardcode the app id in %files or the .desktop — glob the desktop
  file and icons instead (see solidcraft).
- GUI Rust apps: winit/wgpu dlopen their X11/Wayland/Vulkan/Xi/Xrandr
  client libs, which Rust binaries never auto-Require — list each one;
  re-check the set on every wgpu major bump.
- F43's rustc pairs an older backend with a newer stdarch: rten-gemm's
  avx512 VNNI fast path dies with "intrinsic signature mismatch" —
  pdfcraft carries a source carve keyed on a comment anchor; re-check
  which releases need it on each branch.
- `aws-lc-sys` (common via rustls/reqwest) refuses RPM's `-O2`: drop it with
  `%global build_cflags %(echo "%{build_cflags}" | sed 's/ *-O2//g')` —
  plain `export CFLAGS` gets overridden by the %cargo macros.
