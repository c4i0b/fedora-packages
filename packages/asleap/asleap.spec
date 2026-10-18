Name:           asleap
Version:        2.3
Release:        1%{?dist}
Summary:        Actively recover LEAP passwords

License:        GPL-2.0-only
URL:            https://github.com/joswr1ght/asleap
Source0:        https://codeload.github.com/joswr1ght/asleap/tar.gz/refs/heads/master
# rawhide glibc dropped setkey()/encrypt(): DES via OpenSSL instead, and
# pcap-bpf.h no longer exists
Patch0:         des-openssl.patch

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  libpcap-devel
BuildRequires:  libxcrypt-devel
BuildRequires:  openssl-devel

%description
Asleap captures LEAP challenge/response exchanges and recovers weak LEAP
passwords offline, using a dictionary or a genkeys-generated hash file.

%prep
%autosetup -n asleap-master -p1

%build
# command-line CFLAGS fully replace the Makefile ones; -lcrypt, not -lxcrypt
%make_build CFLAGS="%{optflags} -Wno-error=incompatible-pointer-types -Wno-deprecated-declarations -pipe -Wall -D_LINUX -D_OPENSSL_MD4" LDLIBS="-lpcap -lcrypt -lcrypto"

%install
install -Dpm755 asleap %{buildroot}%{_bindir}/asleap
install -Dpm755 genkeys %{buildroot}%{_bindir}/genkeys

%files
%license COPYING
%{_bindir}/asleap
%{_bindir}/genkeys

%changelog
* Sun Oct 18 2026 Caio Bruno <caioibruno@gmail.com> - 2.3-1
- Initial package
