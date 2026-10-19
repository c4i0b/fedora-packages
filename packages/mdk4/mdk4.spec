Name:           mdk4
Version:        4.2
Release:        1%{?dist}
Summary:        Proof-of-concept Wi-Fi testing tool for IEEE 802.11 networks

License:        GPL-3.0-only
URL:            https://github.com/aircrack-ng/mdk4
Source0:        https://github.com/aircrack-ng/mdk4/archive/refs/tags/%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  libnl3-devel
BuildRequires:  libpcap-devel
BuildRequires:  make

%description
MDK4 is a Wi-Fi testing tool that implements several Denial-of-Service and
beacon-flooding attacks against IEEE 802.11 networks, exploiting
weaknesses in the protocol itself.

%prep
%autosetup -n mdk4-%{version}

%build
# env CFLAGS keeps common.mak appends (libnl, -fcommon) working; -flto* and
# -j1 guard osdep's parallel-unsafe `ar cru` archive
export CFLAGS="$(echo "%{optflags} -Wno-error=int-conversion -Wno-error=implicit-function-declaration -Wno-error=return-mismatch -DTCPDUMP_MAGIC=0xa1b2c3d4 -DLINKTYPE_ETHERNET=1 -DLINKTYPE_IEEE802_11=105 -DLINKTYPE_PRISM_HEADER=119 -DLINKTYPE_RADIOTAP_HDR=127 -DLINKTYPE_PPI_HDR=192" | sed 's/ *-f[^ ]*lto[^ ]*//g')"
make -C src -j1

%install
install -Dpm755 src/mdk4 %{buildroot}%{_sbindir}/mdk4
install -Dpm644 man/mdk4.2 %{buildroot}%{_mandir}/man8/mdk4.8

%files
%license COPYING
%{_sbindir}/mdk4
%{_mandir}/man8/mdk4.8*

%changelog
* Sun Oct 18 2026 Caio Bruno <cbrunofb@gmail.com> - 4.2-1
- Initial package
