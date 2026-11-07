# Packaging quirks — npm

- Yargs CLIs without a `completion` command still answer
  `--get-yargs-completions`: ship the canonical yargs bash shim (candidates
  come from the binary; never hand-write them) and smoke it in `%check`
  (see devcontainers-cli). Only yargs — openclaw/rea-agents style custom
  arg parsers have nothing to generate.
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
