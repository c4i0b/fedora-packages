Name:           limusic
Version:        1.4.0
Release:        1%{?dist}
Summary:        Native desktop YouTube Music client (Rust + Tauri, no Electron)

License:        GPL-3.0-or-later
URL:            https://github.com/SimoHypers/limusic
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros
BuildRequires:  gcc-c++
BuildRequires:  desktop-file-utils
# Fedora only: webkit2gtk4.1 is not in EPEL (COPR chroots restricted to Fedora)
BuildRequires:  pkgconfig(webkit2gtk-4.1)
BuildRequires:  pkgconfig(gtk+-3.0)
BuildRequires:  pkgconfig(mpv)
BuildRequires:  librsvg2-devel
# frontend build: pnpm is not packaged in Fedora, pull it through npx (pinned
# major; deps themselves come from the frozen pnpm-lock.yaml)
BuildRequires:  /usr/bin/npm

# Bin-only workspace: do not install sources into the cargo registry
%global cargo_install_lib false
# V8 (rustypipe-botguard) + WebKitGTK tree sits at the COPR 5 h timeout edge
%global rustflags_codegen_units 16
%global rustflags_debuginfo 0
%global debug_package %{nil}

Requires:       mpv-libs%{?_isa}
# WebKitGTK plays music videos through gstreamer (Rust declares no auto-deps)
Recommends:     gstreamer1-plugins-good%{?_isa}
Recommends:     gstreamer1-plugins-bad-free%{?_isa}

%description
Limusic is a feature-rich, native desktop YouTube Music client built with
Rust and Tauri: no bundled browser runtime, no backend server, no ads in the
audio. It talks directly to YouTube's internal API, plays through libmpv with
gapless playback and loudness normalization, and ships synced lyrics, Discord
Rich Presence, Last.fm/ListenBrainz scrobbling and Listen Together rooms.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
# SvelteKit frontend first: tauri's codegen embeds ../ui/build at compile time
export npm_config_cache="$PWD/.npm"
(
  cd ui
  npx --yes --package=pnpm@10 pnpm install --frozen-lockfile
  npx --yes --package=pnpm@10 pnpm build
)
# %%cargo_build cannot select a workspace member: its -n flag is
# --no-default-features and parametric macros reject other option letters
%{__cargo} build %{?_smp_mflags} -Z avoid-dev-deps --profile rpm -p limusic-app

%install
# cargo install from a workspace member dir demands a local lock file
# offline; the binary is already built by the build section
install -Dm755 target/release/limusic-app %{buildroot}%{_bindir}/%{name}

install -d %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_datadir}/applications/%{name}.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Limusic
Comment=Native desktop YouTube Music client
Exec=%{name} %U
Icon=%{name}
Terminal=false
Categories=Audio;AudioVideo;
StartupWMClass=%{name}
EOF
for pair in 32x32:32x32 64x64:64x64 128x128:128x128 128x128@2x:256x256 icon.png:512x512; do
  src="${pair%%:*}"; size="${pair##*:}"
  install -Dpm644 "src-tauri/icons/$src" \
    "%{buildroot}%{_datadir}/icons/hicolor/$size/apps/%{name}.png"
done

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%files
%license LICENSE THIRD-PARTY-NOTICES.md
%doc README.md
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/*/apps/%{name}.png

%changelog
* Thu Nov 19 2026 Caio Bruno <cbrunofb@gmail.com> - 1.4.0-1
- Initial package
