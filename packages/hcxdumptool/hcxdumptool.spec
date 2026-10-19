Name:           hcxdumptool
Version:        7.1.2
Release:        1%{?dist}
Summary:        Small tool to capture packets from wireless interfaces

License:        MIT
URL:            https://github.com/ZerBea/hcxdumptool
Source0:        https://github.com/ZerBea/hcxdumptool/archive/refs/tags/%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  libnl3-devel
BuildRequires:  libpcap-devel
BuildRequires:  openssl-devel

%description
hcxdumptool is a small tool to capture packets from wireless
interfaces capable of packet injection: it turns a Wi-Fi interface
into a protocol analyzer capturing EAPOL and PMKID frames, feeding
the output to hashcat or wpa_supplicant for offline processing. It
is used by wifite for the PMKID capture attack.

%prep
%autosetup

%build
%make_build CFLAGS="%{build_cflags}"

%install
%make_install PREFIX=%{_prefix}
# the Makefile's install target ships binaries only
install -Dpm644 man/hcxdumptool.1 %{buildroot}%{_mandir}/man1/hcxdumptool.1

%files
%license license.txt
%doc README.md
%{_bindir}/hcxdumptool
# companion NMEA log tool built by the same Makefile
%{_bindir}/hcxnmealog
%{_mandir}/man1/hcxdumptool.1*

%changelog
* Sun Oct 18 2026 Caio Bruno <cbrunofb@gmail.com> - 7.1.2-1
- Initial package
