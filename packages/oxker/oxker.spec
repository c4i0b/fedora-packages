Name:           oxker
Version:        0.13.4
Release:        1%{?dist}
Summary:        TUI to view and control docker containers

License:        MIT
URL:            https://github.com/mrjackwills/oxker
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

%description
Oxker is a simple TUI for viewing and controlling docker containers, built
with ratatui: sort, restart, stop, and inspect containers with keyboard
shortcuts.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor

%build
%cargo_build

%install
%cargo_install

%check
%{buildroot}%{_bindir}/oxker --version

%files
%license LICENSE
%doc README.md
%{_bindir}/oxker

%changelog
* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 0.13.4-1
- Initial package
