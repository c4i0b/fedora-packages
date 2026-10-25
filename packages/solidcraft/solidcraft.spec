Name:           solidcraft
Version:        0.22.0
Release:        1%{?dist}
Summary:        Parametric 3D CAD application with sketches, features and assemblies

License:        MIT OR Apache-2.0
URL:            https://github.com/tangency-labs/solidcraft
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

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
Requires:       libXi%{?_isa}
Requires:       libXrandr%{?_isa}
Requires:       libxkbcommon%{?_isa}
Requires:       libxkbcommon-x11%{?_isa}
Requires:       libwayland-client%{?_isa}
Requires:       vulkan-loader%{?_isa}

%description
SolidCraft is an open-source parametric 3D CAD application built in pure
Rust. Sketch on a plane, constrain and dimension the sketch, turn profiles
into solids on an editable feature timeline, and change a parameter to watch
the model rebuild. It reads and writes STEP, IGES, 3MF, STL, OBJ and glTF,
and ships a headless CLI with an MCP server for AI agents.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
# git-sourced crates need the source replacements cargo vendor printed;
# the prep macro only rewrites crates-io (empty when all deps are crates.io)
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
# %%cargo_build cannot select a workspace member: its -n flag is
# --no-default-features and parametric macros reject other option letters
# zbus-lockstep's validate macro looks for ../xml relative to the crate
# being compiled: in a vendored tree that resolves to the vendored "xml"
# crate (whose extensionless LICENSE panics the macro) instead of
# atspi-common's D-Bus XML dir
[ -d vendor-deps/atspi-common/xml ] && export LOCKSTEP_XML_PATH="$(pwd)/vendor-deps/atspi-common/xml"
%{__cargo} build %{?_smp_mflags} -Z avoid-dev-deps --profile rpm -p %{name} -p %{name}-cli

%install
# cargo install from a workspace member dir demands a local lock file
# offline; the binaries are already built by the build section
install -Dm755 target/release/%{name} %{buildroot}%{_bindir}/%{name}
install -Dm755 target/release/%{name}-cli %{buildroot}%{_bindir}/%{name}-cli

install -Dm644 assets/platforms/linux/ai.storyteller.%{name}.desktop \
    %{buildroot}%{_datadir}/applications/ai.storyteller.%{name}.desktop

# ship whatever sizes upstream provides (they change between releases)
for icon in assets/icons/app/linux/exports/hicolor/*/apps/*; do
    install -Dm644 "$icon" "%{buildroot}%{_datadir}/icons/hicolor/${icon#assets/icons/app/linux/exports/hicolor/}"
done

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/ai.storyteller.%{name}.desktop

%files
%license LICENSE-APACHE LICENSE-MIT
%doc README.md
%{_bindir}/solidcraft
%{_bindir}/solidcraft-cli
%{_datadir}/applications/ai.storyteller.solidcraft.desktop
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.solidcraft.*

%changelog
* Sat Oct 24 2026 Caio Bruno <cbrunofb@gmail.com> - 0.22.0-1
- Initial package
