# Packaging quirks — .NET

- Toolchain per branch: Fedora ships `dotnet-sdk-X.Y`; EPEL has no dotnet
  package, so build there against the `dotnet-msft` repack — export
  `DOTNET_ROOT` accordingly (`%{_libdir}/dotnet` vs `%{_libdir}/dotnet-msft`)
  and prepend it to PATH per branch. MS binaries link OpenSSL 3 only and
  never run against rawhide's OpenSSL 4 — do not point Fedora builds at
  them.
- NuGet native assets (libSDL3, libSkiaSharp…) ship one
  `publish/runtimes/<rid>/native` tree per target rid — including musl,
  win and android builds whose sonames become unresolvable rpm requires.
  Set a per-arch rid (`linux-x64`/`linux-arm64` via `%ifarch`) and prune
  everything else: `find publish/runtimes -mindepth 1 -maxdepth 1
  ! -name '%{rid}' -exec rm -rf {} +` (quiver-launcher).
- Every installed ELF is prebuilt (Microsoft runtime, NuGet natives):
  carry `%global debug_package %{nil}` + `%global __strip /bin/true`
  (+ `%global _missing_build_ids_terminate_build 0` on rpm < 4.20/EPEL) —
  stripping prebuilt .NET runtime libraries corrupts them, and there is no
  debuginfo to collect anyway.
- P/Invoke-only deps are invisible to rpm autoreq (no DT_NEEDED on the
  apphost): list them manually — Avalonia's X11/OpenGL set (libX11,
  libXcursor, libXi, libXrandr, libglvnd, dbus-libs, libicu, …) — and
  re-check the set on every UI-stack major bump.
- Wrappers: rpm does not expand macros in Source files — generate them via
  heredoc in `%install` (see the general.md rule).
- `%build` hygiene: `export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1`
  (no first-run telemetry/noise in the build chroot).
- dotnet-msft updates stay manual: dotnet/sdk tags every major, feature
  band and preview (v8/v9/v10, previews), so tags-based tracking would
  mis-bump the pinned X.Y repack — and the SDK feature band is coupled to
  what consumers build against (the runtime ships inside the SDK tarball;
  patch tags can even point at the same commit).
