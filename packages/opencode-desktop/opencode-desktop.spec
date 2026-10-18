# Electron payload: stripping corrupts the embedded snapshot; rpm 6 also
# fails on the empty debugsource list — see AGENTS.md
%define debug_package %{nil}
%global __strip /bin/true

# Bundled Electron must not leak into rpm provides/requires
%global __provides_exclude_from ^%{_libdir}/opencode-desktop/.*$
%global __requires_exclude_from ^%{_libdir}/opencode-desktop/.*$

ExclusiveArch:  x86_64 aarch64

Name:           opencode-desktop
Version:        1.19.3
Release:        1%{?dist}
Summary:        Desktop app for OpenCode, the open source AI coding agent (Electron)

License:        MIT
URL:            https://opencode.ai
Source0:        https://github.com/anomalyco/opencode/releases/download/v%{version}/opencode-desktop-linux-x86_64.rpm
Source1:        https://github.com/anomalyco/opencode/releases/download/v%{version}/opencode-desktop-linux-aarch64.rpm
Source2:        https://raw.githubusercontent.com/anomalyco/opencode/v%{version}/LICENSE

BuildRequires:  bsdtar
BuildRequires:  desktop-file-utils

Requires:       gtk3
Requires:       nss
Requires:       libsecret
Requires:       alsa-lib
Requires:       libXScrnSaver
Recommends:     opencode

%description
Official desktop application (beta) for OpenCode, the open source AI coding
agent. Bundles its own Electron runtime.

%prep
%setup -T -q -c
%ifarch x86_64
bsdtar -xf %{SOURCE0}
%else
bsdtar -xf %{SOURCE1}
%endif

%build

%install
appdir=%{buildroot}%{_libdir}/opencode-desktop
install -d "$appdir"
cp -a opt/OpenCode/. "$appdir"/
rm -f "$appdir"/resources/app-update.yml

install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/opencode-desktop <<EOF
#!/bin/sh
exec %{_libdir}/opencode-desktop/ai.opencode.desktop "\$@"
EOF
chmod 755 %{buildroot}%{_bindir}/opencode-desktop

# Upstream desktop Exec points into the bundle; rewrite to our wrapper
sed -i 's|^Exec=.*|Exec=opencode-desktop %U|' usr/share/applications/ai.opencode.desktop.desktop
install -Dpm644 usr/share/applications/ai.opencode.desktop.desktop \
  %{buildroot}%{_datadir}/applications/ai.opencode.desktop.desktop

for png in usr/share/icons/hicolor/*/apps/*.png; do
  install -Dpm644 "$png" "%{buildroot}%{_datadir}/icons/hicolor/${png#*hicolor/}"
done

# Upstream-shipped metainfo; validated upstream, not gated here
install -Dpm644 usr/share/metainfo/ai.opencode.desktop.metainfo.xml \
  %{buildroot}%{_datadir}/metainfo/ai.opencode.desktop.metainfo.xml

install -pm644 %{SOURCE2} LICENSE
cp -a opt/OpenCode/LICENSE.electron.txt opt/OpenCode/LICENSES.chromium.html .

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%files
%license LICENSE LICENSE.electron.txt LICENSES.chromium.html
%{_bindir}/opencode-desktop
%{_libdir}/opencode-desktop/
%{_datadir}/applications/ai.opencode.desktop.desktop
%{_datadir}/icons/hicolor/*/apps/ai.opencode.desktop.png
%{_datadir}/metainfo/ai.opencode.desktop.metainfo.xml

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 1.19.3-1
- Initial package
