Name:           cloudflare-speed-cli
Version:        1.0.10
Release:        1%{?dist}
Summary:        Cloudflare-based internet speed test with optional TUI

License:        GPL-3.0-only
URL:            https://github.com/kavehtehrani/cloudflare-speed-cli
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

# aws-lc-sys jitterentropy errors on RPM's -O2; see AGENTS.md
%global build_cflags %(echo "%{build_cflags}" | sed 's/ *-O2//g')

%description
Internet speed test against Cloudflare's speed test endpoints: download and
upload throughput, idle and loaded latency, UDP quality (loss, jitter, MOS),
DNS and TLS timing, traceroute and proxy support. Renders a live ratatui TUI,
with headless --text/--json modes for scripting.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor

%build
%cargo_build

%install
%cargo_install

%check
%{buildroot}%{_bindir}/cloudflare-speed-cli --version

%files
%license LICENSE
%doc README.md
%{_bindir}/cloudflare-speed-cli

%changelog
* Mon Oct 19 2026 Caio Bruno <cbrunofb@gmail.com> - 1.0.10-1
- Initial package
