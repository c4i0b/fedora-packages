# Packaging quirks — Rust

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
- `aws-lc-sys` (common via rustls/reqwest) refuses RPM's `-O2`: drop it with
  `%global build_cflags %(echo "%{build_cflags}" | sed 's/ *-O2//g')` —
  plain `export CFLAGS` gets overridden by the %cargo macros.
