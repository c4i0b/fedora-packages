# Electron payload: stripping corrupts the embedded snapshot; rpm 6 also
# fails on the empty debugsource list — see AGENTS.md
%define debug_package %{nil}
%global __strip /bin/true

# Bundled Electron must not leak into rpm provides/requires
%global __provides_exclude_from ^%{_libdir}/__NAME__/.*$
%global __requires_exclude_from ^%{_libdir}/__NAME__/.*$

%ifarch x86_64
%global rpmarch x86_64
%elifarch aarch64
%global rpmarch aarch64
%endif

ExclusiveArch:  x86_64 aarch64

Name:           __NAME__
Version:        __VERSION__
Release:        1%{?dist}
Summary:        __SUMMARY__

License:        __LICENSE__
URL:            __URL__
Source0:        __SOURCE0__
Source1:        __SOURCE1__
Source2:        LICENSE

BuildRequires:  bsdtar
BuildRequires:  desktop-file-utils

Requires:       gtk3
Requires:       nss
Requires:       libsecret
Requires:       alsa-lib

%description
__SUMMARY__

%prep
%setup -T -q -c
%ifarch x86_64
bsdtar -xf %{SOURCE0}
%else
bsdtar -xf %{SOURCE1}
%endif

%build

%install
appdir=%{buildroot}%{_libdir}/__NAME__
install -d "$appdir"
cp -a __PAYLOAD_DIR__/. "$appdir"/
rm -f "$appdir"/resources/app-update.yml

install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/__NAME__ <<EOF
#!/bin/sh
exec %{_libdir}/__NAME__/__BIN__ "\$@"
EOF
chmod 755 %{buildroot}%{_bindir}/__NAME__

install -Dpm644 usr/share/applications/__APPID__.desktop \
  %{buildroot}%{_datadir}/applications/__APPID__.desktop
for png in usr/share/icons/hicolor/*/apps/*.png; do
  install -Dpm644 "$png" "%{buildroot}%{_datadir}/icons/hicolor/${png#*hicolor/}"
done

install -pm644 %{SOURCE2} LICENSE

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%files
%license LICENSE
%{_bindir}/__NAME__
%{_libdir}/__NAME__/
%{_datadir}/applications/*.desktop
%{_datadir}/icons/hicolor/*/apps/*.png

%changelog
* __DATE__ __PACKAGER__ - __VERSION__-1
- Initial package
