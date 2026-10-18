Name:           waydroid-helper
Version:        0.2.9
Release:        1%{?dist}
Summary:        A GUI application for Waydroid configuration and extension installation

License:        GPL-3.0-or-later
URL:            https://github.com/waydroid-helper/waydroid-helper
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  gcc
BuildRequires:  python3-devel
BuildRequires:  cairo-devel
BuildRequires:  gtk4-devel
BuildRequires:  libadwaita-devel
BuildRequires:  gobject-introspection-devel
BuildRequires:  dbus-devel
BuildRequires:  gettext
BuildRequires:  systemd
BuildRequires:  desktop-file-utils

Requires:       python3
Requires:       gtk4
Requires:       libadwaita
Requires:       vte291-gtk4
Requires:       waydroid
Requires:       fakeroot
Requires:       python3-aiofiles
Requires:       python3-httpx
Requires:       python3-cairo
Requires:       python3-gobject >= 3.50
Requires:       python3-pywayland
Requires:       python3-yaml
Requires:       python3-dbus
Requires:       android-tools

Recommends:     bindfs
Recommends:     hicolor-icon-theme

%description
Waydroid Helper is a graphical user interface application that provides
a user-friendly way to configure Waydroid and install extensions,
including Magisk, ARM translation, and various Google services alternatives.

%prep
%autosetup -p1

%build
%meson
%meson_build

%install
%meson_install

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/com.jaoushingan.WaydroidHelper.desktop

%files
%license COPYING
%doc README.md
%{_bindir}/waydroid-helper
%{_bindir}/waydroid-cli
%{_datadir}/waydroid-helper/
%{_datadir}/applications/com.jaoushingan.WaydroidHelper.desktop
%{_datadir}/icons/hicolor/scalable/apps/com.jaoushingan.WaydroidHelper.svg
%{_datadir}/icons/hicolor/symbolic/apps/com.jaoushingan.WaydroidHelper-symbolic.svg
%{_metainfodir}/com.jaoushingan.WaydroidHelper.metainfo.xml
%{_datadir}/glib-2.0/schemas/com.jaoushingan.WaydroidHelper.gschema.xml
%{_datadir}/polkit-1/actions/com.jaoushingan.WaydroidHelper.policy
%{_datadir}/locale/zh_CN/LC_MESSAGES/waydroid-helper.mo
%{_datadir}/locale/de/LC_MESSAGES/waydroid-helper.mo
%{_datadir}/locale/ru/LC_MESSAGES/waydroid-helper.mo
%{_datadir}/locale/zh_TW/LC_MESSAGES/waydroid-helper.mo
%{_datadir}/dbus-1/system.d/id.waydro.Mount.conf
%{_datadir}/dbus-1/system-services/id.waydro.Mount.service
%{_unitdir}/waydroid-mount.service
%{_userunitdir}/waydroid-monitor.service

%changelog
* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 0.2.9-1
- Initial package
