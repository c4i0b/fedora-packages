Name:           herdr
Version:        0.1.13
Release:        1%{?dist}
Summary:        Desktop app for terminals and coding agents

License:        Apache-2.0
URL:            https://github.com/herdrdev/herdr-app
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst
# zig is not in Fedora; the vendored ghostty-sys (terminal core) pins 0.16.
# One Source per arch: the SRPM builder chroot has an arbitrary architecture.
Source2:        https://ziglang.org/download/0.16.0/zig-x86_64-linux-0.16.0.tar.xz
Source3:        https://ziglang.org/download/0.16.0/zig-aarch64-linux-0.16.0.tar.xz
# ghostty's build.zig.zon closure, served to the embedded zig build via
# --system: zig's own http client fails on COPR builders (vendor-sources.sh)
Source4:        zig-pkg.tar.zst

BuildRequires:  cargo-rpm-macros
BuildRequires:  clang-devel
BuildRequires:  desktop-file-utils
BuildRequires:  fontconfig-devel
BuildRequires:  freetype-devel
BuildRequires:  libxcb-devel
BuildRequires:  libxkbcommon-devel
BuildRequires:  libxkbcommon-x11-devel
BuildRequires:  libzstd-devel
BuildRequires:  pkgconf-pkg-config
BuildRequires:  vulkan-loader-devel
BuildRequires:  wayland-devel

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false
# debugsource trips brp-mangle-shebangs on vendored crate inner attrs
%global debug_package %{nil}

%description
Herdr is a desktop app for terminals and coding agents: keep work in spaces,
see which agents need you, and leave terminals running when you close the
window. Built on GPUI with the Ghostty terminal emulation core.

%prep
%autosetup -n herdr-app-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
tar --zstd -xf %{SOURCE4}
%ifarch x86_64
tar -xJf %{SOURCE2}
zigbin="$PWD/zig-x86_64-linux-0.16.0/zig"
%else
tar -xJf %{SOURCE3}
zigbin="$PWD/zig-aarch64-linux-0.16.0/zig"
%endif
# ghostty-sys shells out to `zig build` itself; the shim serves its zon
# closure from the prefetched --system store instead of zig's downloader
mkdir _zig
cat > _zig/zig <<EOF
#!/bin/sh
[ "\$1" = build ] && set -- "\$@" --system "$PWD/zig-pkg"
exec "$zigbin" "\$@"
EOF
chmod +x _zig/zig
export ZIG="$PWD/_zig/zig"
%cargo_build

%install
# cargo install re-resolves and cannot use git deps against the vendor dir
# offline (no lock); the binary is already built by the build section
install -Dm755 target/release/herdr-app %{buildroot}%{_bindir}/herdr-app
install -Dm644 assets/icons/herdr-ui-icon-clean.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/herdr-app.svg
mkdir -p %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_datadir}/applications/herdr-app.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Herdr
Comment=Terminals and coding agents that keep running
Exec=herdr-app
Icon=herdr-app
Terminal=false
Categories=Development;
StartupWMClass=herdr-app
EOF

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/herdr-app.desktop
%{buildroot}%{_bindir}/herdr-app --version

%files
%license LICENSE THIRD-PARTY-NOTICES
%{_bindir}/herdr-app
%{_datadir}/applications/herdr-app.desktop
%{_datadir}/icons/hicolor/scalable/apps/herdr-app.svg

%changelog
* Fri Nov 06 2026 Caio Bruno <cbrunofb@gmail.com> - 0.1.13-1
- Initial package
