Name:           photocraft
Version:        0.11.1
Release:        1%{?dist}
Summary:        Open-source native photo editor with layers, masks and PSD support

License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/photocraft
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst
Source2:        %{name}.desktop

BuildRequires:  cargo-rpm-macros
BuildRequires:  gcc
# aws-lc-sys (via rustls) and craft-print build C/C++ with cmake; pipewire-sys
# runs bindgen, which needs libclang
BuildRequires:  cmake
BuildRequires:  clang-devel
BuildRequires:  desktop-file-utils

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

# aws-lc-sys (via rustls) rejects RPM's -O2 (AGENTS.md)
%global build_cflags %(echo "%{build_cflags}" | sed 's/ *-O2//g')

# Release profile strips the binary and vendor sources trip the shebang BRP
%global debug_package %{nil}

%description
PhotoCraft is an open-source, native image editor with layers, masks,
adjustment layers, layer styles, type and brushes. It opens and saves layered
PSD/PSB documents, supports 8/16/32-bit float documents in RGB, grayscale,
CMYK and Lab, and a GPU compositor with multithreaded filters.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor
# git-sourced crates (craft-libs) need the source replacements cargo vendor
# printed; the prep macro only rewrites crates-io
cat git-sources.conf >> .cargo/config.toml

%build
# %%cargo_build cannot select a workspace member: its -n flag is
# --no-default-features and parametric macros reject other option letters
# zbus-lockstep's validate macro looks for ../xml relative to the crate
# being compiled: in a vendored tree that resolves to the vendored "xml"
# crate (whose extensionless LICENSE panics the macro) instead of
# atspi-common's D-Bus XML dir
[ -d vendor/atspi-common/xml ] && export LOCKSTEP_XML_PATH="$(pwd)/vendor/atspi-common/xml"
%{__cargo} build %{?_smp_mflags} -Z avoid-dev-deps --profile rpm -p %{name}

%install
# cargo install from a workspace member dir demands a local lock file
# offline; the binary is already built by the build section
install -Dm755 target/release/%{name} %{buildroot}%{_bindir}/%{name}

install -Dm644 %{SOURCE2} %{buildroot}%{_datadir}/applications/ai.storyteller.photocraft.desktop

for size in 16x16 24x24 32x32 48x48 64x64 128x128 256x256 512x512; do
    install -Dm644 assets/app-icon/hicolor/$size/apps/ai.storyteller.photocraft.png \
        %{buildroot}%{_datadir}/icons/hicolor/$size/apps/ai.storyteller.photocraft.png
done
install -Dm644 assets/app-icon/hicolor/scalable/apps/ai.storyteller.photocraft.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/ai.storyteller.photocraft.svg

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/ai.storyteller.photocraft.desktop

%files
%license LICENSE-APACHE LICENSE-MIT
%doc README.md
%{_bindir}/photocraft
%{_datadir}/applications/ai.storyteller.photocraft.desktop
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.photocraft.*

%changelog
* Wed Oct 21 2026 Caio Bruno <cbrunofb@gmail.com> - 0.11.1-1
- Initial package
