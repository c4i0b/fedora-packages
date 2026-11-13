# Packaging quirks — general

- `CFLAGS=...` on the make command line overrides every `+=` append in the
  Makefiles (breaking upstream feature detection): `export CFLAGS=...`
  before `%make_build` instead.
- EPEL chroots run one generation older toolchains than Fedora (rpm 4.19 on
  EPEL 10): macros in comments are expanded and executed silently on rpm < 4.20
  (test.sh rejects them) and ELF binaries without a GNU build-id note abort the
  build — non-GCC
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
  (`Source: zig-pkg.tar.*` via tools/vendor-sources.py) and build with
  `zig build --system zig-pkg` — zig's own http client fails on COPR
  builders, and only a dependency's *root* zon belongs to the graph
  (scanning fetched sub-zons pulls gigabytes of junk). Note `--system`
  implies zig's system package mode: install paths change (e.g. systemd
  units to `%{_prefix}/lib/systemd/user`) and upstream build defaults may
  flip (docs, vendored libs) — audit `%files` and build flags accordingly.
  A `#` comment inside the backslash-continued `zig build` command truncates
  it at that line — keep prose outside the command. New zig packages start
  from templates/zig.spec.tpl (zig pin, vendored store, guarded seds).
- GitHub tag archives omit git submodule contents. vendor-sources.py
  resolves each `.gitmodules` entry via the superproject's GitHub API (tag
  ref → pinned sha), overlays the submodule into the extracted tree and
  repacks Source0 — a spec never needs a Source per submodule. Rust specs
  may combine `%cargo_prep` with a `zig-pkg.tar` Source when an embedded
  build shells out to zig (herdr): serve the closure through a `ZIG` env
  shim that appends `--system <abs-path>` to `build` invocations only.
- Never hardcode upstream desktop-file/app-id names in %install/%files:
  upstreams rename them between releases — glob the desktop file and icons.
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
  in those (and all -bin) specs. Add `%global __strip /bin/true` for zig
  builds too (brp-strip chases zig's hardlinked cache .o files under
  /usr/lib/<hash> that vanish mid-strip) and for Bun/Electron payloads
  (stripping corrupts them).
