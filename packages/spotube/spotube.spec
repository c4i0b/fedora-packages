# Bundled JVM/Skiko payload: stripping corrupts the embedded runtime; rpm 6
# also fails on the empty debugsource list — see docs/packaging/general.md
%global debug_package %{nil}
%global __strip /bin/true

# Bundled runtime must not leak into rpm provides/requires
%global __provides_exclude_from ^%{_libdir}/spotube/.*$
%global __requires_exclude_from ^%{_libdir}/spotube/.*$

# Bundled Compose Multiplatform/Skiko runtime IS the product (-bin policy)
ExclusiveArch:  x86_64 aarch64

Name:           spotube
Version:        6.0.0
Release:        3%{?dist}
Summary:        Spotify-compatible client that streams from YouTube Music

License:        AGPL-3.0-only
URL:            https://github.com/team-spotube/Spotube
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
# libskiko-linux-x64.so has a direct NEEDED on libharfbuzz.so.0 that
# freetype/fontconfig do not pull, and bundle requires are excluded
Requires:       harfbuzz
Requires:       libX11
Requires:       libXext
Requires:       libXi
Requires:       libXrender
Requires:       libXtst
Requires:       mesa-libGL
Requires:       vlc-libs
# vlc-plugins-base owns the native libopus (itag 251) + libfaad (itag 140)
# codec plugins and the ALSA output — the only ones vlcj (decode + audio)
# actually uses; the Qt UI / X vouts of the standalone player stay out
Requires:       vlc-plugins-base
Requires:       vlc-plugin-pulseaudio
# ffmpeg decode is only a fallback for exotic formats (base's native
# opus/faad cover YouTube Music); optional, not worth a hard pull
Recommends:     vlc-plugin-ffmpeg
# Fedora only: webkit2gtk4.1 is not in EPEL (COPR chroots restricted to Fedora)
Requires:       webkit2gtk4.1
# tray icon (mirrors the upstream .deb Recommends: libappindicator3-1)
Recommends:     libappindicator-gtk3

%description
Spotube is a lightweight Spotify-compatible client that streams audio from
YouTube Music, needing no Spotify Premium account. It is a Kotlin Compose
Multiplatform app that bundles its own JVM/Skiko runtime and plays through
the system VLC libraries.

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
* Fri Nov 20 2026 Caio Bruno <cbrunofb@gmail.com> - 6.0.0-3
- Require vlc-plugins-base (native opus/faad codecs + ALSA out) directly;
  demote vlc-plugin-ffmpeg to Recommends (fallback only)

* Fri Nov 20 2026 Caio Bruno <cbrunofb@gmail.com> - 6.0.0-2
- Require harfbuzz (direct NEEDED of libskiko, not pulled by freetype)
- Recommend libappindicator-gtk3 for the tray icon (mirrors upstream .deb)
- Fix runtime description: Kotlin Compose Multiplatform, not Flutter

* Thu Nov 19 2026 Caio Bruno <cbrunofb@gmail.com> - 6.0.0-1
- Initial package
