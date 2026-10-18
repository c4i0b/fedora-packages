Name:           __NAME__
Version:        __VERSION__
Release:        1%{?dist}
Summary:        __SUMMARY__

License:        __LICENSE__
URL:            __URL__
Source0:        __SOURCE0__

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-pip
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  desktop-file-utils

%description
__SUMMARY__

%prep
%autosetup -p1

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files -l __NAME__

# Desktop entry / icons / metainfo if upstream ships them (explicit file paths:
# install -D does not accept directory destinations)
#install -Dpm644 __APPID__.desktop %{buildroot}%{_datadir}/applications/__APPID__.desktop
#for f in share/icons/*; do
#  case "$f" in
#    *.svg) install -Dpm644 "$f" %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/"$(basename "$f")" ;;
#  esac
#done

%check
#desktop-file-validate %{buildroot}%{_datadir}/applications/__APPID__.desktop

%files -f %{pyproject_files}
%doc README.md
%{_bindir}/__NAME__

%changelog
* __DATE__ __PACKAGER__ - __VERSION__-1
- Initial package
