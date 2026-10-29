Name:           trippy
Version:        0.13.0
Release:        1%{?dist}
Summary:        Network diagnostic tool with a TUI (trip)

License:        Apache-2.0
URL:            https://github.com/fujiapple852/trippy
Source0:        %{url}/archive/refs/tags/%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false
# debugsource trips brp-mangle-shebangs on vendored crate inner attrs
%global debug_package %{nil}

%description
Trippy (trip) is a network diagnostic tool combining the functionality of
traceroute and ping in a TUI: per-hop latency and jitter stats, ASN/GeoIP
metadata, and multiple protocol support (ICMP, UDP, TCP). It runs without
root on most platforms.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
# virtual workspace: cargo-rpm-macros cannot build a single member
%{__cargo} build %{?_smp_mflags} -Z avoid-dev-deps --profile rpm -p trippy

%install
install -Dm755 target/release/trip %{buildroot}%{_bindir}/trip

%check
%{buildroot}%{_bindir}/trip --version

%files
%license LICENSE
%doc README.md
%{_bindir}/trip

%changelog
* Thu Oct 29 2026 Caio Bruno <cbrunofb@gmail.com> - 0.13.0-1
- Initial package
