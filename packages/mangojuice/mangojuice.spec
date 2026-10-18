Name:           mangojuice
Version:        1.0.0
Release:        1%{?dist}
Summary:        A convenient alternative to GOverlay for configuring MangoHud

License:        GPL-3.0-or-later
URL:            https://github.com/radiolamp/mangojuice
Source0:        %{url}/archive/refs/tags/%{version}.tar.gz

BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  gcc
BuildRequires:  vala
BuildRequires:  libadwaita-devel
BuildRequires:  libgee-devel
BuildRequires:  gettext
BuildRequires:  desktop-file-utils

Requires:       mangohud
Requires:       hicolor-icon-theme

Recommends:     mesa-demos
Recommends:     vulkan-tools

%description
MangoJuice is a GTK4/libadwaita application for configuring MangoHud and
vkBasalt, intended as a convenient alternative to GOverlay.

%prep
%autosetup -p1

%build
%meson
%meson_build

%install
%meson_install

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/io.github.radiolamp.mangojuice.desktop

%files
%license LICENSE
%doc README.md
%{_bindir}/mangojuice
%{_datadir}/applications/io.github.radiolamp.mangojuice.desktop
%{_datadir}/icons/hicolor/scalable/apps/*.svg
%{_metainfodir}/io.github.radiolamp.mangojuice.metainfo.xml
%{_datadir}/locale/*/LC_MESSAGES/*.mo

%changelog
* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 1.0.0-1
- Initial package
