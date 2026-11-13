Name:           rathole
Version:        0.5.0
Release:        1%{?dist}
Summary:        Lightweight and high-performance reverse proxy for NAT traversal

License:        Apache-2.0
URL:            https://github.com/rapiz1/rathole
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

# time 0.3.31 predates rustc's stricter type inference (E0282); bump within 0.3.x
# cargo-update: -p time
# openssl-sys < 0.9.114 rejects OpenSSL 4 (rawhide/f45); bump within 0.9.x/0.10.x
# cargo-update: -p openssl-sys -p openssl

BuildRequires:  cargo-rpm-macros
BuildRequires:  openssl-devel

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false
# debugsource trips brp-mangle-shebangs on vendored crate inner attrs (xh, atac)
%global debug_package %{nil}

%description
A secure, stable and high-performance reverse proxy for NAT traversal,
written in Rust and similar to frp and ngrok. It exposes services on
devices behind a NAT via a server with a public IP, with mandatory
per-service tokens and optional Noise Protocol or TLS encryption,
websocket transport and configuration hot-reloading.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
%cargo_build

%install
%cargo_install

%check
%{buildroot}%{_bindir}/rathole --version

%files
%license LICENSE
%doc README.md
%{_bindir}/rathole

%changelog
* Fri Nov 13 2026 Caio Bruno <cbrunofb@gmail.com> - 0.5.0-1
- Initial package
