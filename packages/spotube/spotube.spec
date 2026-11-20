# Flutter/Skiko payload: stripping corrupts the embedded runtime; rpm 6 also
# fails on the empty debugsource list — see docs/packaging/general.md
%global debug_package %{nil}
%global __strip /bin/true

# Bundled runtime must not leak into rpm provides/requires
%global __provides_exclude_from ^%{_libdir}/spotube/.*$
%global __requires_exclude_from ^%{_libdir}/spotube/.*$

# Bundled Flutter/Skiko engine IS the product (-bin policy)
ExclusiveArch:  x86_64 aarch64

Name:           spotube
Version:        6.0.0
Release:        1%{?dist}
Summary:        Spotify-compatible client that streams from YouTube Music

License:        AGPL-3.0-only
URL:            https://github.com/team-spotube/spotube
Source0:        %{url}/releases/download/v%{version}/Spotube-linux-x86_64.rpm
Source1:        %{url}/releases/download/v%{version}/Spotube-linux-aarch64.rpm
Source2:        %{url}/raw/refs/tags/v%{version}/LICENSE

BuildRequires:  desktop-file-utils

Requires:       alsa-lib
Requires:       dbus-libs
Requires:       fontconfig
Requires:       freetype
Requires:       glib2
Requires:       gtk3
Requires:       libX11
Requires:       libXext
Requires:       libXi
Requires:       libXrender
Requires:       libXtst
Requires:       mesa-libGL
Requires:       vlc-libs
Requires:       vlc-plugin-ffmpeg
Requires:       vlc-plugin-pulseaudio
# Fedora only: webkit2gtk4.1 is not in EPEL (COPR chroots restricted to Fedora)
Requires:       webkit2gtk4.1

%description
Spotube is a lightweight Spotify-compatible client that streams audio from
YouTube Music, needing no Spotify Premium account. It bundles its own
Flutter/Skiko runtime and plays through the system VLC libraries.

%prep
%setup -T -q -c
# libarchive/bsdtar cannot parse RPMv4 payloads and old (EL10) cpio
# misreads payload sizes; rpm2archive streams a tar on every rpm version
%ifarch x86_64
rpm2archive %{SOURCE0} > payload.tgz
%else
rpm2archive %{SOURCE1} > payload.tgz
%endif
tar -xzf payload.tgz

%build

%install
appdir=%{buildroot}%{_libdir}/spotube
install -d "$appdir"
cp -a opt/spotube/. "$appdir"/

install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/spotube <<EOF
#!/bin/sh
exec %{_libdir}/spotube/spotube "\$@"
EOF
chmod 755 %{buildroot}%{_bindir}/spotube

# Upstream desktop Exec points into the bundle; rewrite to our wrapper and
# fix the upstream-generic Name/Categories ("Packaged desktop application",
# Utility — no license text in the payload either, hence Source2)
desktop_file=usr/share/applications/spotube.desktop
sed -i -e 's|^Exec=.*|Exec=spotube %U|' \
       -e 's|^Name=.*|Name=Spotube|' \
       -e 's|^Comment=.*|Comment=Spotify-compatible client using YouTube Music|' \
       -e 's|^Categories=.*|Categories=Audio;AudioVideo;Music;|' "$desktop_file"
grep -q '^Exec=spotube' "$desktop_file" || exit 1
install -Dpm644 "$desktop_file" %{buildroot}%{_datadir}/applications/spotube.desktop

for png in usr/share/icons/hicolor/*/apps/*.png; do
  install -Dpm644 "$png" "%{buildroot}%{_datadir}/icons/hicolor/${png#*hicolor/}"
done

install -pm644 %{SOURCE2} LICENSE

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%files
%license LICENSE
%{_bindir}/spotube
%{_libdir}/spotube/
%{_datadir}/applications/spotube.desktop
%{_datadir}/icons/hicolor/*/apps/*.png

%changelog
* Thu Nov 19 2026 Caio Bruno <cbrunofb@gmail.com> - 6.0.0-1
- Initial package
