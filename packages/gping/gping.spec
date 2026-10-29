Name:           gping
Version:        1.21.0
Release:        1%{?dist}
Summary:        Ping tool with a real-time graph, TUI

License:        MIT
URL:            https://github.com/orf/gping
Source0:        %{url}/archive/refs/tags/gping-v%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

%description
gping is a ping tool that graphs the response time of hosts over time in
the terminal, and can plot the execution time of arbitrary commands
alongside. Supports multiple hosts, IPv4/IPv6 and adaptive graph scaling.

%prep
%autosetup -n gping-gping-v%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
# virtual workspace: cargo-rpm-macros cannot build a single member
%{__cargo} build %{?_smp_mflags} -Z avoid-dev-deps --profile rpm -p gping

%install
install -Dm755 target/release/gping %{buildroot}%{_bindir}/gping

%check
%{buildroot}%{_bindir}/gping --version

%files
%license LICENSE
%doc readme.md
%{_bindir}/gping

%changelog
* Thu Oct 29 2026 Caio Bruno <cbrunofb@gmail.com> - 1.21.0-1
- Initial package
