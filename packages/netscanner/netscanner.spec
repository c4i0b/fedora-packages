Name:           netscanner
Version:        0.6.43
Release:        1%{?dist}
Summary:        Terminal network scanner and diagnostic tool with modern TUI

License:        MIT
URL:            https://github.com/Chleba/netscanner
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros
BuildRequires:  openssl-devel

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

# Not the unrelated Go port scanner R4yGM/netscanner shipped in Fedora

%description
Network scanner and diagnostic tool with a ratatui TUI: lists hardware
interfaces, scans WiFi networks with signal charts, pings IPv4 CIDRs with
hostname and OUI/MAC resolution, dumps TCP/UDP/ICMP/ARP packets, scans open
TCP ports, and exports results to CSV. Requires root at runtime.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
%cargo_build

%install
%cargo_install
install -Dpm644 debian/netscanner.manpage %{buildroot}%{_mandir}/man1/netscanner.1

%check
HOME=/tmp %{buildroot}%{_bindir}/netscanner --version

%files
%license LICENSE
%doc README.md
%{_bindir}/netscanner
%{_mandir}/man1/netscanner.1*

%changelog
* Mon Oct 19 2026 Caio Bruno <cbrunofb@gmail.com> - 0.6.43-1
- Initial package
