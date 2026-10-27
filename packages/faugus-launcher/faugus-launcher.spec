Name:           faugus-launcher
Version:        2.5.4
Release:        1%{?dist}
Summary:        A simple and lightweight app for running Windows games using UMU-Launcher

License:        MIT
URL:            https://github.com/Faugus/faugus-launcher
Source0:        %{url}/archive/refs/tags/%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  meson
BuildRequires:  python3-devel
BuildRequires:  gettext
BuildRequires:  gtk-update-icon-cache
BuildRequires:  desktop-file-utils

Requires:       python3-gobject
Requires:       python3-requests
Requires:       python3-pillow
Requires:       python3-vdf
Requires:       python3-psutil
Requires:       python3-icoextract
Requires:       gtk4
Requires:       libadwaita
Requires:       libmanette

%description
A simple and lightweight app for running Windows games using UMU-Launcher/UMU-Proton.

%prep
%autosetup -p1

%build
%meson
%meson_build

%install
%meson_install

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%files
%license LICENSE
%{_bindir}/faugus-launcher
%{python3_sitelib}/faugus/
%{_datadir}/applications/*.desktop
%{_datadir}/icons/hicolor/scalable/actions/*.svg
%{_datadir}/icons/hicolor/scalable/apps/*.svg
%{_datadir}/faugus-launcher/*
%{_datadir}/locale/*/LC_MESSAGES/*.mo
%{_metainfodir}/io.github.Faugus.faugus-launcher.metainfo.xml

%changelog
* Tue Oct 27 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 2.5.4-1
- Update to 2.5.4

* Thu Oct 22 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 2.5.1-1
- Update to 2.5.1

* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 2.5.0-1
- Initial package
