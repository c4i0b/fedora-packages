Name:           filmcraft
Version:        0.15.0
Release:        1%{?dist}
Summary:        Nonlinear video editor with timeline, color and audio tools

License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/filmcraft
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst
Source2:        %{name}.desktop

BuildRequires:  cargo-rpm-macros
BuildRequires:  gcc
# cpal -> alsa -> alsa-sys resolves libasound via pkg-config
BuildRequires:  pkgconfig(alsa)
BuildRequires:  desktop-file-utils

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

# rustls in this tree uses ring, not aws-lc-sys: keep RPM's -O2

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
FilmCraft is an open-source, native nonlinear video editor with a
multitrack timeline, trimming and ripple edits, color grading with scopes,
audio mixing and effects, titles and captions, and export to common video
formats via its own codec suite.

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

install -Dm644 %{SOURCE2} %{buildroot}%{_datadir}/applications/ai.storyteller.filmcraft.desktop

# ship whatever sizes upstream provides (they change between releases)
for icon in assets/app-icon/hicolor/*/apps/*; do
    install -Dm644 "$icon" "%{buildroot}%{_datadir}/icons/hicolor/${icon#assets/app-icon/hicolor/}"
done

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/ai.storyteller.filmcraft.desktop

%files
%license LICENSE-APACHE LICENSE-MIT NOTICE
%doc README.md
%{_bindir}/filmcraft
%{_datadir}/applications/ai.storyteller.filmcraft.desktop
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.filmcraft.*

%changelog
* Sat Oct 31 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.15.0-1
- Update to 0.15.0

* Wed Oct 28 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.14.0-1
- Update to 0.14.0

* Sun Oct 25 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.13.0-1
- Update to 0.13.0

* Fri Oct 23 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.12.0-1
- Update to 0.12.0

* Fri Oct 23 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.11.0-1
- Update to 0.11.0

* Wed Oct 21 2026 Caio Bruno <cbrunofb@gmail.com> - 0.10.0-1
- Initial package
