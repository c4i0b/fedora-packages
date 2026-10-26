Name:           topmatic
Version:        1.1.0
Release:        1%{?dist}
Summary:        User-level scheduled updates powered by topgrade

License:        MIT
URL:            https://github.com/c4i0b/topmatic
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

# Release profile strips the binary and vendor sources trip the shebang BRP
%define debug_package %{nil}

Requires:       topgrade

%description
Topmatic turns Topgrade into scheduled systemd jobs managed from a TUI,
updating user-level tools (flatpaks, cargo installs, npm globals, pipx apps)
without sudo, daemons or cron.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
%cargo_build

%install
%cargo_install

%check
%{buildroot}%{_bindir}/topmatic --version

%files
%license LICENSE
%doc README.md
%{_bindir}/topmatic

%changelog
* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 1.1.0-1
- Initial package
