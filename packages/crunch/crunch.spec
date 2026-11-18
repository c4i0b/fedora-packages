Name:           crunch
Version:        3.6
Release:        1%{?dist}
Summary:        Wordlist generator where you can specify standard character sets

License:        GPL-2.0-only
URL:            https://github.com/crunchsec/crunch
# no tags/releases upstream (version comes from the binary): pinned commit,
# bump manually
%global commit 3bdc4a8941eb64e5c15086778df56af79d54e06b
Source0:        https://codeload.github.com/crunchsec/crunch/tar.gz/%{commit}#/crunch-%{commit}.tar.gz

BuildRequires:  gcc
BuildRequires:  make

%description
Crunch is a wordlist generator where you can specify a standard or custom
character set. It generates all possible combinations of the given charset,
with size and pattern constraints.

%prep
%autosetup -n crunch-%{commit}

%build
%make_build build

%install
%make_install PREFIX=%{_prefix} INSTALL=install INSTALL_OPTIONS=
rm %{buildroot}%{_docdir}/crunch/COPYING

%files
%license COPYING
%{_bindir}/crunch
%{_datadir}/crunch/charset.lst
%{_mandir}/man1/crunch.1*

%changelog
* Sun Oct 18 2026 Caio Bruno <cbrunofb@gmail.com> - 3.6-1
- Initial package
