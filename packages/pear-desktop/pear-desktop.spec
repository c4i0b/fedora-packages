# Electron payload: stripping corrupts the embedded snapshot; rpm 6 also
# fails on the empty debugsource list — see AGENTS.md
%define debug_package %{nil}
%global __strip /bin/true

# Bundled Electron must not leak into rpm provides/requires
%global __provides_exclude_from ^%{_libdir}/pear-desktop/.*$
%global __requires_exclude_from ^%{_libdir}/pear-desktop/.*$

ExclusiveArch:  x86_64 aarch64

Name:           pear-desktop
Version:        3.12.0
Release:        1%{?dist}
Summary:        YouTube Music desktop app with plugins (Electron)

License:        MIT AND BSD-2-Clause AND BSD-3-Clause AND LGPL-2.1-or-later AND Apache-2.0 AND Zlib
URL:            https://github.com/pear-devs/pear-desktop
Source0:        https://github.com/pear-devs/pear-desktop/releases/download/v%{version}/youtube-music-%{version}.x86_64.rpm
Source1:        https://github.com/pear-devs/pear-desktop/releases/download/v%{version}/youtube-music-%{version}.aarch64.rpm
Source2:        https://raw.githubusercontent.com/pear-devs/pear-desktop/v%{version}/license

BuildRequires:  bsdtar
BuildRequires:  desktop-file-utils

Requires:       gtk3
Requires:       nss
Requires:       libsecret
Requires:       alsa-lib
Requires:       libXScrnSaver

%description
YouTube Music Desktop App — a feature-rich Electron client for YouTube Music
with plugins, from the pear-devs fork of th-ch/youtube-music. Bundles its own
Electron runtime.

%prep
%setup -T -q -c
%ifarch x86_64
bsdtar -xf %{SOURCE0}
%else
bsdtar -xf %{SOURCE1}
%endif

%build

%install
appdir=%{buildroot}%{_libdir}/pear-desktop
install -d "$appdir"
cp -a "opt/YouTube Music/." "$appdir"/
rm -f "$appdir"/resources/app-update.yml

install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/pear-desktop <<EOF
#!/bin/sh
exec %{_libdir}/pear-desktop/youtube-music "\$@"
EOF
chmod 755 %{buildroot}%{_bindir}/pear-desktop

# Upstream desktop Exec points into the bundle; rewrite to our wrapper
sed -i 's|^Exec=.*|Exec=pear-desktop %U|' usr/share/applications/com.github.th-ch.youtube-music.desktop
echo 'Keywords=pear;pear-desktop;music;player;' >> usr/share/applications/com.github.th-ch.youtube-music.desktop
install -Dpm644 usr/share/applications/com.github.th-ch.youtube-music.desktop \
  %{buildroot}%{_datadir}/applications/com.github.th-ch.youtube-music.desktop

for png in usr/share/icons/hicolor/*/apps/*.png; do
  install -Dpm644 "$png" "%{buildroot}%{_datadir}/icons/hicolor/${png#*hicolor/}"
done

install -pm644 %{SOURCE2} LICENSE
cp -a "opt/YouTube Music/LICENSE.electron.txt" "opt/YouTube Music/LICENSES.chromium.html" .

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%files
%license LICENSE LICENSE.electron.txt LICENSES.chromium.html
%{_bindir}/pear-desktop
%{_libdir}/pear-desktop/
%{_datadir}/applications/*.desktop
%{_datadir}/icons/hicolor/*/apps/*.png

%changelog
* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 3.12.0-1
- Initial package
