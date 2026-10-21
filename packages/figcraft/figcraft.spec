Name:           figcraft
Version:        0.8.0
Release:        1%{?dist}
Summary:        Interface design and prototyping tool with live collaboration

License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/figcraft
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
FigCraft is an open-source, pure-Rust interface design and prototyping tool.
It edits vector designs on an infinite canvas with components, variables,
auto layout and Smart Animate-style prototyping, opens SVG/PNG/JPG/WebP and
best-effort .fig documents, exports to PNG/JPG/WebP/SVG/PDF, generates code
(CSS, HTML, React, Leptos, SwiftUI, Compose) and shares live editing sessions
over the network. It works fully offline: no account, no telemetry, and no
server contact unless a file is explicitly shared.

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

install -Dm644 %{SOURCE2} %{buildroot}%{_datadir}/applications/ai.storyteller.figcraft.desktop

for size in 16x16 24x24 32x32 48x48 64x64 128x128 256x256 512x512; do
    install -Dm644 assets/app-icon/hicolor/$size/apps/ai.storyteller.figcraft.png \
        %{buildroot}%{_datadir}/icons/hicolor/$size/apps/ai.storyteller.figcraft.png
done
install -Dm644 assets/app-icon/hicolor/scalable/apps/ai.storyteller.figcraft.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/ai.storyteller.figcraft.svg

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/ai.storyteller.figcraft.desktop

%files
%license LICENSE-APACHE LICENSE-MIT
%doc README.md
%{_bindir}/figcraft
%{_datadir}/applications/ai.storyteller.figcraft.desktop
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.figcraft.*

%changelog
* Wed Oct 21 2026 Caio Bruno <cbrunofb@gmail.com> - 0.8.0-1
- Initial package
