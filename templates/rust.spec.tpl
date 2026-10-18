Name:           __NAME__
Version:        __VERSION__
Release:        1%{?dist}
Summary:        __SUMMARY__

License:        __LICENSE__
URL:            __URL__
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

# Uncomment if the dependency tree pulls aws-lc-sys (rustls/reqwest): its
# bundled jitterentropy errors on RPM's -O2 (see AGENTS.md)
#%global build_cflags %(echo "%{build_cflags}" | sed 's/ *-O2//g')

%description
__SUMMARY__

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor

%build
%cargo_build

%install
%cargo_install

%files
%license LICENSE
%{_bindir}/__NAME__

%changelog
* __DATE__ __PACKAGER__ - __VERSION__-1
- Initial package
