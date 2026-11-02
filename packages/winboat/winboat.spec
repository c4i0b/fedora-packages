# Electron payload: stripping corrupts the embedded snapshot; rpm 6 also
# fails on the empty debugsource list — see AGENTS.md
%define debug_package %{nil}
%global __strip /bin/true

# Bundled Electron must not leak into rpm provides/requires
%global __provides_exclude_from ^%{_libdir}/winboat/.*$
%global __requires_exclude_from ^%{_libdir}/winboat/.*$

ExclusiveArch:  x86_64

Name:           winboat
Version:        0.9.2
Release:        1%{?dist}
Summary:        Run Windows apps on Linux with seamless integration (Electron)

License:        MIT AND BSD-2-Clause AND BSD-3-Clause AND LGPL-2.1-or-later AND Apache-2.0 AND Zlib
URL:            https://github.com/winboat-org/winboat
Source0:        %{url}/releases/download/v%{version}/winboat-%{version}-x86_64.rpm

BuildRequires:  bsdtar
BuildRequires:  desktop-file-utils

Requires:       gtk3
Requires:       nss
Requires:       libsecret
Requires:       alsa-lib
Requires:       libXScrnSaver
Requires:       freerdp
# Windows VM runs in a container: either runtime satisfies (rich dep)
Requires:       (podman or docker)
Requires:       (podman-compose or docker-compose)

%description
WinBoat runs Windows applications on Linux with seamless desktop integration:
Windows runs as a VM inside a Docker/Podman container, apps are composited as
native windows via FreeRDP RemoteApp, and the home directory is shared between
both systems. Bundles its own Electron runtime and the WinBoat guest server.

%prep
%setup -T -q -c
bsdtar -xf %{SOURCE0}

%build

%install
appdir=%{buildroot}%{_libdir}/winboat
install -d "$appdir"
cp -a opt/winboat/. "$appdir"/
rm -f "$appdir"/resources/app-update.yml

install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/winboat <<EOF
#!/bin/sh
exec %{_libdir}/winboat/winboat "\$@"
EOF
chmod 755 %{buildroot}%{_bindir}/winboat

# Upstream desktop Exec points into /opt; rewrite to our wrapper
sed -i 's|^Exec=.*|Exec=winboat %U|' usr/share/applications/winboat.desktop
install -Dpm644 usr/share/applications/winboat.desktop \
  %{buildroot}%{_datadir}/applications/winboat.desktop

install -Dpm644 usr/share/icons/hicolor/scalable/apps/winboat.svg \
  %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/winboat.svg

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%files
%license opt/winboat/LICENSE.electron.txt opt/winboat/LICENSES.chromium.html
%{_bindir}/winboat
%{_libdir}/winboat/
%{_datadir}/applications/*.desktop
%{_datadir}/icons/hicolor/scalable/apps/*.svg

%changelog
* Mon Nov 02 2026 Caio Bruno <cbrunofb@gmail.com> - 0.9.2-1
- Initial package
