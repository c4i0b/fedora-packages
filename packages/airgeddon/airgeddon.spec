Name:           airgeddon
Version:        12.02
Release:        1%{?dist}
Summary:        Multi-platform bash wireless auditing script

License:        GPL-3.0-only
URL:            https://github.com/v1s1t0r1sh3r3/airgeddon
Source0:        https://github.com/v1s1t0r1sh3r3/airgeddon/archive/refs/tags/v%{version}.tar.gz

BuildArch:      noarch

Requires:       aircrack-ng
Requires:       asleap
Requires:       bash
Requires:       beef
Requires:       bettercap
Requires:       bully
Requires:       ccze
Requires:       crunch
Requires:       curl
Requires:       dnsmasq
Requires:       ettercap
Requires:       ethtool
Requires:       gawk
Requires:       hashcat
Requires:       hcxdumptool
Requires:       hcxtools
Requires:       hostapd
Requires:       hostapd-wpe
Requires:       iproute
Requires:       iputils
Requires:       iw
Requires:       kea
Requires:       lighttpd
Requires:       mdk4
Requires:       nftables
Requires:       openssl
Requires:       pciutils
Requires:       pixiewps
Requires:       procps-ng
Requires:       reaver
Requires:       rfkill
Requires:       sox
Requires:       tcpdump
Requires:       usbutils
Requires:       wget
Requires:       wireshark-cli
Requires:       xprop
Requires:       xset
Requires:       xdpyinfo
Requires:       xterm

# Optional upstream (airgeddon blocks features when absent); pulled as
# Requires here by convenience so one install brings the full toolkit.

%description
Multi-platform bash script for wireless auditing: handshake capture, WPS and
WEP attacks, evil portal and more, orchestrating the installed toolset.

%prep
%autosetup -n airgeddon-%{version} -p1

%install
d=%{buildroot}%{_datadir}/airgeddon
install -Dpm755 airgeddon.sh "$d/airgeddon.sh"
install -Dpm644 language_strings.sh "$d/language_strings.sh"
install -Dpm644 known_pins.db "$d/known_pins.db"
install -Dpm644 pindb_checksum.txt "$d/pindb_checksum.txt"
cp -a plugins "$d/plugins"
# the script reads its rc only from its own folder
install -Dpm644 .airgeddonrc "$d/.airgeddonrc"
mkdir -p %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/airgeddon <<'EOF'
#!/bin/sh
exec bash %{_datadir}/airgeddon/airgeddon.sh "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/airgeddon

%check
bash -n airgeddon.sh

%files
%doc README.md CHANGELOG.md
%license LICENSE
%{_bindir}/airgeddon
%config(noreplace) %{_datadir}/airgeddon/.airgeddonrc
%{_datadir}/airgeddon/airgeddon.sh
%{_datadir}/airgeddon/language_strings.sh
%{_datadir}/airgeddon/known_pins.db
%{_datadir}/airgeddon/pindb_checksum.txt
%{_datadir}/airgeddon/plugins/

%changelog
* Sun Oct 18 2026 Caio Bruno <caioibruno@gmail.com> - 12.02-1
- Initial package
