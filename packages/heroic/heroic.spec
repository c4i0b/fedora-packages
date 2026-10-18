# Electron payload: stripping corrupts the embedded snapshot; rpm 6 also
# fails on the empty debugsource list — see AGENTS.md
%define debug_package %{nil}
%global __strip /bin/true

# Bundled Electron must not leak into rpm provides/requires
%global __provides_exclude_from ^%{_libdir}/heroic/.*$
%global __requires_exclude_from ^%{_libdir}/heroic/.*$

ExclusiveArch:  x86_64 aarch64

Name:           heroic
Version:        2.22.4
Release:        1%{?dist}
Summary:        Open source game launcher for GOG, Epic Games and Amazon Games

License:        GPL-3.0-only
URL:            https://github.com/Heroic-Games-Launcher/HeroicGamesLauncher
Source0:        %{url}/releases/download/v%{version}/Heroic-%{version}-linux-x86_64.rpm
Source1:        %{url}/releases/download/v%{version}/Heroic-%{version}-linux-aarch64.rpm
Source2:        %{url}/raw/refs/tags/v%{version}/COPYING

BuildRequires:  bsdtar
BuildRequires:  desktop-file-utils

Requires:       gtk3
Requires:       nss
Requires:       libsecret
Requires:       alsa-lib
Requires:       libXScrnSaver

%description
Heroic is an Open Source Game Launcher for Linux, Windows and macOS. It
launches GOG, Epic Games and Amazon Games titles (native and via Wine/Proton).
Bundles its own Electron runtime.

%prep
%setup -T -q -c
%ifarch x86_64
bsdtar -xf %{SOURCE0}
%else
bsdtar -xf %{SOURCE1}
%endif

%build

%install
appdir=%{buildroot}%{_libdir}/heroic
install -d "$appdir"
cp -a opt/Heroic/. "$appdir"/
rm -f "$appdir"/resources/app-update.yml

install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/heroic <<EOF
#!/bin/sh
exec %{_libdir}/heroic/heroic "\$@"
EOF
chmod 755 %{buildroot}%{_bindir}/heroic

# Upstream desktop Exec points into the bundle; rewrite to our wrapper
sed -i 's|^Exec=.*|Exec=heroic %U|' usr/share/applications/heroic.desktop
install -Dpm644 usr/share/applications/heroic.desktop \
  %{buildroot}%{_datadir}/applications/heroic.desktop

for png in usr/share/icons/hicolor/*/apps/*.png; do
  install -Dpm644 "$png" "%{buildroot}%{_datadir}/icons/hicolor/${png#*hicolor/}"
done

install -pm644 %{SOURCE2} COPYING
cp -a opt/Heroic/LICENSE.electron.txt opt/Heroic/LICENSES.chromium.html .

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%files
%license COPYING LICENSE.electron.txt LICENSES.chromium.html
%{_bindir}/heroic
%{_libdir}/heroic/
%{_datadir}/applications/heroic.desktop
%{_datadir}/icons/hicolor/*/apps/heroic.png

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 2.22.4-1
- Initial package
