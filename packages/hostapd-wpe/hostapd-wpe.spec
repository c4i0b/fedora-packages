Name:           hostapd-wpe
Version:        2.12
Release:        1%{?dist}
Summary:        hostapd fork facilitating AP impersonation attacks

License:        BSD-3-Clause
URL:            https://patches.aircrack-ng.org/wpe/hostapd-wpe/
Source0:        https://w1.fi/releases/hostapd-%{version}.tar.gz
Patch0:         https://patches.aircrack-ng.org/wpe/hostapd-wpe/hostapd-wpe.patch

BuildRequires:  gcc
BuildRequires:  libnl3-devel
BuildRequires:  make
BuildRequires:  openssl-devel
BuildRequires:  sqlite-devel

Requires:       openssl

%description
Hostapd-WPE (Wireless Pwn Edition) is hostapd patched to facilitate access
point impersonation attacks: it logs credentials of clients authenticating
against WPA/802.1X Enterprise networks (MSCHAPv2 hashes, EAP identities).

%prep
%setup -q -n hostapd-%{version}
# rejected hunks are superseded: banner/rename handled by the seds below,
# defconfig extras already present in 2.12
patch -p1 --fuzz=3 < %{PATCH0} ||:
# 2.12 dropped the locals the identity-logging block uses
sed -i 's|^/\* Print Response-Identity from STA\*/$|/* Print Response-Identity from STA*/\n\tconst u8 *identity;\n\tsize_t identity_len;|' src/ap/ieee802_1x.c
# airgeddon parses the banner as "hostapd-WPE v"
sed -i 's/hostapd v%s/hostapd-WPE v%s/' hostapd/main.c
# rejected getopt hunk: without it -k/-c/-s never reach their (applied) cases
sed -i 's/vg:G:qz:"/vg:G:qz:kcs:"/' hostapd/main.c

%build
cd hostapd
cp defconfig .config
%make_build

%install
install -Dpm755 hostapd/hostapd %{buildroot}%{_sbindir}/hostapd-wpe
# airgeddon's default certificate path
install -d %{buildroot}%{_sysconfdir}/hostapd-wpe/certs
cp -a hostapd/certs/. %{buildroot}%{_sysconfdir}/hostapd-wpe/certs/

%check
# guards the ||: on the patch: banner and WPE getopt must survive drift
# (-v exits 1, hence the || :)
out=$(%{buildroot}%{_sbindir}/hostapd-wpe -v 2>&1) || :
echo "$out" | grep -q "hostapd-WPE v%{version}"
%{buildroot}%{_sbindir}/hostapd-wpe -k 2>&1 | grep -q WPE

%files
%doc hostapd/hostapd-wpe.conf hostapd/hostapd-wpe.eap_user hostapd/certs/README.wpe
%{_sbindir}/hostapd-wpe
%{_sysconfdir}/hostapd-wpe/certs

%changelog
* Sun Oct 18 2026 Caio Bruno <caioibruno@gmail.com> - 2.12-1
- Initial package
