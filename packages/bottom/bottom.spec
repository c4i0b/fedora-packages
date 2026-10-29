Name:           bottom
Version:        0.14.9
Release:        1%{?dist}
Summary:        Graphical process/system monitor with TUI (btm)

License:        MIT
URL:            https://github.com/ClementTsang/bottom
Source0:        %{url}/archive/refs/tags/%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

%description
A customizable cross-platform graphical process/system monitor with a TUI:
CPU, memory, network and disk usage, process list with search/filtering and
widgets reminiscent of htop, gtop and Mission Control.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
%cargo_build

%install
%cargo_install

%check
%{buildroot}%{_bindir}/btm --version

%files
%license LICENSE
%doc README.md
%{_bindir}/btm

%changelog
* Thu Oct 29 2026 Caio Bruno <cbrunofb@gmail.com> - 0.14.9-1
- Initial package
