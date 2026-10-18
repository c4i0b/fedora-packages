Name:           zapzap
Version:        7.5.1
Release:        1%{?dist}
Summary:        WhatsApp desktop application written in PyQt6 + QtWebEngine

License:        GPL-3.0-or-later
URL:            https://github.com/rafatosta/zapzap
Source0:        %{url}/archive/refs/tags/%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-pip
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel
BuildRequires:  desktop-file-utils
BuildRequires:  pyproject-rpm-macros

Requires:       python3-pyqt6
Requires:       python3-pyqt6-webengine

%description
ZapZap is an unofficial WhatsApp desktop client that wraps WhatsApp Web in a
QtWebEngine window, adding tray integration, spell checking, themes and
per-window settings.

%prep
%autosetup -p1

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files -l zapzap

install -Dpm644 share/applications/com.rtosta.zapzap.desktop \
  %{buildroot}%{_datadir}/applications/com.rtosta.zapzap.desktop
for f in share/icons/*; do
  case "$f" in
    *.svg) install -Dpm644 "$f" %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/"$(basename "$f")" ;;
    *) size=$(basename "$(dirname "$f")")
       install -Dpm644 "$f" "%{buildroot}%{_datadir}/icons/hicolor/$size/apps/$(basename "$f")" ;;
  esac
done
for f in share/metainfo/*.xml; do
  install -Dpm644 "$f" "%{buildroot}%{_metainfodir}/$(basename "$f")"
done

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/com.rtosta.zapzap.desktop

%files -f %{pyproject_files}
%doc README.md
%{_bindir}/zapzap
%{_datadir}/applications/com.rtosta.zapzap.desktop
%{_datadir}/icons/hicolor/*/apps/*
%{_datadir}/icons/hicolor/scalable/apps/*
%{_metainfodir}/*.xml

%changelog
* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 7.5.1-1
- Initial package
