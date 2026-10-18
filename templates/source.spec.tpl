Name:           __NAME__
Version:        __VERSION__
Release:        1%{?dist}
Summary:        __SUMMARY__

License:        __LICENSE__
URL:            __URL__
Source0:        __SOURCE0__

BuildRequires:  gcc

%description
__SUMMARY__

%prep
%autosetup -p1

%build
%set_build_flags
%configure
%make_build

%install
%make_install

%files
%license LICENSE
%doc README.md
%{_bindir}/__NAME__

%changelog
* __DATE__ __PACKAGER__ - __VERSION__-1
- Initial package
