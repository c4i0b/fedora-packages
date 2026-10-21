Name:           wordcraft
Version:        0.9.0
Release:        1%{?dist}
Summary:        Word processor with docx support, track changes and mail merge

License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/wordcraft
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst
Source2:        %{name}.desktop

BuildRequires:  cargo-rpm-macros
BuildRequires:  gcc
BuildRequires:  desktop-file-utils

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

# Release profile strips the binary and vendor sources trip the shebang BRP
%global debug_package %{nil}

# winit/wgpu dlopen these at runtime; Rust binaries declare no auto-deps
Requires:       libX11%{?_isa}
Requires:       libXcursor%{?_isa}
Requires:       libxkbcommon%{?_isa}
Requires:       libxkbcommon-x11%{?_isa}
Requires:       libwayland-client%{?_isa}
Requires:       vulkan-loader%{?_isa}

%description
WordCraft is an open-source, pure-Rust word processor with a familiar
workflow: the ribbon, styles, tables, track changes, references and mail
merge. It reads and writes .docx documents and runs natively on Linux.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
# git-sourced crates (craft-libs) need the source replacements cargo vendor
# printed; the prep macro only rewrites crates-io
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
# %%cargo_build cannot select a workspace member: its -n flag is
# --no-default-features and parametric macros reject other option letters
# zbus-lockstep's validate macro looks for ../xml relative to the crate
# being compiled: in a vendored tree that resolves to the vendored "xml"
# crate (whose extensionless LICENSE panics the macro) instead of
# atspi-common's D-Bus XML dir
[ -d vendor-deps/atspi-common/xml ] && export LOCKSTEP_XML_PATH="$(pwd)/vendor-deps/atspi-common/xml"
%{__cargo} build %{?_smp_mflags} -Z avoid-dev-deps --profile rpm -p %{name}

%install
# cargo install from a workspace member dir demands a local lock file
# offline; the binary is already built by the build section
install -Dm755 target/release/%{name} %{buildroot}%{_bindir}/%{name}

install -Dm644 %{SOURCE2} %{buildroot}%{_datadir}/applications/ai.storyteller.wordcraft.desktop

for size in 16x16 24x24 32x32 48x48 64x64 128x128 256x256 512x512; do
    install -Dm644 assets/app-icon/hicolor/$size/apps/ai.storyteller.wordcraft.png \
        %{buildroot}%{_datadir}/icons/hicolor/$size/apps/ai.storyteller.wordcraft.png
done
install -Dm644 assets/app-icon/hicolor/scalable/apps/ai.storyteller.wordcraft.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/ai.storyteller.wordcraft.svg

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/ai.storyteller.wordcraft.desktop

%files
%license LICENSE-APACHE LICENSE-MIT
%doc README.md
%{_bindir}/wordcraft
%{_datadir}/applications/ai.storyteller.wordcraft.desktop
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.wordcraft.*

%changelog
* Wed Oct 21 2026 Caio Bruno <cbrunofb@gmail.com> - 0.9.0-1
- Initial package
