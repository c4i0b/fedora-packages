Name:           artcraft
Version:        0.41.0
Release:        1%{?dist}
Summary:        AI image and video creation studio with 2D and 3D scene staging

License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/artcraft
Source0:        %{url}/archive/refs/tags/artcraft-v%{version}.tar.gz
Source1:        vendor.tar.zst
Source2:        %{name}.desktop

BuildRequires:  cargo-rpm-macros
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  cmake
# a -sys crate in the graph runs bindgen at build time
BuildRequires:  clang-devel
BuildRequires:  desktop-file-utils
# native webview used by the desktop shell
BuildRequires:  pkgconfig(webkit2gtk-4.1)
BuildRequires:  pkgconfig(javascriptcoregtk-4.1)
BuildRequires:  pkgconfig(gtk+-3.0)
BuildRequires:  pkgconfig(libsoup-3.0)
# the React frontend is compiled with Nx during %%build
BuildRequires:  nodejs
# Fedora: npm; EL10 ships it as nodejs-npm
BuildRequires:  /usr/bin/npm

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

# aws-lc-sys (via rustls) rejects RPM's -O2 (AGENTS.md)
%global build_cflags %(echo "%{build_cflags}" | sed 's/ *-O2//g')

# Release profile strips the binary and vendor sources trip the shebang BRP
%global debug_package %{nil}

%description
ArtCraft is an open-source desktop studio for interactive AI image and video
creation. It composes in 2D, stages characters, cameras and props in 3D, and
turns a prompt into image, video, audio, 3D-mesh and world assets with the
models of your choice. Generation runs in the cloud, so the app needs an
account with the provider you pick; the editing and scene tools run locally.

%prep
%autosetup -n %{name}-artcraft-v%{version} -p1 -a 1
%cargo_prep -v vendor-deps

%build
export SQLX_OFFLINE=true VITE_ENVIRONMENT_TYPE=production NX_DAEMON=false
cd frontend
npm ci --no-audit --no-fund
npx nx run artcraft:build
cd ..
# %%cargo_build cannot select a workspace member (its -n is
# --no-default-features): build the desktop app directly
%{__cargo} build %{?_smp_mflags} -Z avoid-dev-deps --profile rpm -p %{name}

%install
install -Dm755 target/release/%{name} %{buildroot}%{_bindir}/%{name}
install -Dm644 %{SOURCE2} %{buildroot}%{_datadir}/applications/ai.artcraft.app.desktop

install -Dm644 crates/desktop/artcraft/icons/32x32.png %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/ai.artcraft.app.png
install -Dm644 crates/desktop/artcraft/icons/64x64.png %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/ai.artcraft.app.png
install -Dm644 crates/desktop/artcraft/icons/128x128.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/ai.artcraft.app.png
install -Dm644 crates/desktop/artcraft/icons/128x128@2x.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/ai.artcraft.app.png
install -Dm644 crates/desktop/artcraft/icons/icon.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/ai.artcraft.app.png

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/ai.artcraft.app.desktop

%files
%license LICENSE-APACHE LICENSE-MIT NOTICE
%doc README.md
%{_bindir}/artcraft
%{_datadir}/applications/ai.artcraft.app.desktop
%{_datadir}/icons/hicolor/*/apps/ai.artcraft.app.png

%changelog
* Fri Oct 23 2026 Caio Bruno <cbrunofb@gmail.com> - 0.41.0-1
- Initial package
