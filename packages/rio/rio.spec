Name:           rio
Version:        0.5.28
Release:        1%{?dist}
Summary:        Hardware-accelerated terminal emulator built with Rust

License:        MIT
URL:            https://github.com/raphamorim/rio
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  desktop-file-utils
BuildRequires:  ncurses
# sugarloaf compiles its GLSL shaders to SPIR-V at build time
BuildRequires:  glslang
# font-kit probes the system libraries via pkg-config instead of bundling
BuildRequires:  pkg-config
BuildRequires:  fontconfig-devel
BuildRequires:  freetype-devel

# Bin-only workspace: do not install sources into the cargo registry
%global cargo_install_lib false

%description
Rio is a hardware-accelerated terminal emulator built on the wgpu graphics
API, focusing on performance and simplicity. It supports Wayland and X11,
ligatures, and configuration via TOML.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
# default features only: wayland + x11 backends; no --all-features (pulls
# audio deps via cpac/alsa not needed by a terminal)
%cargo_build

%install
# virtual workspace: cargo install cannot resolve a package at the root
install -Dm755 target/rpm/rio %{buildroot}%{_bindir}/rio

install -Dm644 misc/rio.desktop %{buildroot}%{_datadir}/applications/rio.desktop
install -Dm644 misc/com.rioterm.Rio.metainfo.xml %{buildroot}%{_datadir}/metainfo/com.rioterm.Rio.metainfo.xml
install -Dm644 misc/logo.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/rio.svg
tic -x -o %{buildroot}%{_datadir}/terminfo misc/rio.terminfo

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/rio.desktop
target/rpm/rio --version

%files
%license LICENSE
%doc README.md
%{_bindir}/rio
%{_datadir}/applications/rio.desktop
%{_datadir}/metainfo/com.rioterm.Rio.metainfo.xml
%{_datadir}/icons/hicolor/scalable/apps/rio.svg
%{_datadir}/terminfo/r/*
%{_datadir}/terminfo/x/xterm-rio

%changelog
* Sun Oct 18 2026 Caio Bruno <cbrunofb@gmail.com> - 0.5.28-1
- Initial package
