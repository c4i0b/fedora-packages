Name:           jp2a
Version:        1.3.3
Release:        1%{?dist}
Summary:        Converts JPG and PNG images to ASCII

License:        GPL-2.0-or-later
URL:            https://github.com/Talinx/jp2a
Source0:        %{url}/releases/download/v%{version}/jp2a-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  libcurl-devel
BuildRequires:  libexif-devel
BuildRequires:  libjpeg-devel
BuildRequires:  libpng-devel
BuildRequires:  libwebp-devel
BuildRequires:  ncurses-devel

%description
jp2a is a small utility that converts JPG and PNG images to ASCII (text)
using libjpeg and libpng. It can use ANSI colors and HTML in output, and
can download and convert images from the Internet via command line.

%prep
%autosetup

%build
%set_build_flags
%configure
%make_build

%install
%make_install

%files
%license COPYING
%doc README NEWS ChangeLog
%{_bindir}/jp2a
%{_sysconfdir}/bash_completion.d/jp2a
%{_datadir}/zsh/site-functions/_jp2a
%{_mandir}/man1/jp2a.1*

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 1.3.3-1
- Initial package
