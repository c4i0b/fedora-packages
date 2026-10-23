Name:           broot
Version:        1.61.0
Release:        1%{?dist}
Summary:        Interactive tree file manager with fuzzy search and previews

License:        MIT
URL:            https://github.com/Canop/broot
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

# Uncomment if the dependency tree pulls aws-lc-sys (rustls/reqwest): its
# bundled jitterentropy errors on RPM's -O2 (see AGENTS.md)
#%global build_cflags %(echo "%{build_cflags}" | sed 's/ *-O2//g')

%description
File browser and launcher: navigates as an interactive tree, fuzzy-searches names and contents, previews files and launches commands directly from the tree.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps

%build
%cargo_build

%install
%cargo_install
# without the br function broot shows a first-run "install it now?" prompt
target/release/broot --print-shell-function fish > br.fish
install -Dpm644 br.fish %{buildroot}%{_datadir}/fish/vendor_functions.d/br.fish

%files
%license LICENSE
%{_bindir}/broot
%{_datadir}/fish/vendor_functions.d/br.fish

%changelog
* Sat Oct 24 2026 Caio Bruno <cbrunofb@gmail.com> - 1.61.0-1
- Initial package
