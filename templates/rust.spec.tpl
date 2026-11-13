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
# debugsource trips brp-mangle-shebangs on vendored crate inner attrs (xh, atac)
%global debug_package %{nil}

# Uncomment if the dependency tree pulls aws-lc-sys (rustls/reqwest): its
# bundled jitterentropy errors on RPM's -O2 (see docs/packaging/rust.md)
#%global build_cflags %(echo "%{build_cflags}" | sed 's/ *-O2//g')

# Uncomment when the tree outgrows COPR's 5 h timeout (see
# docs/packaging/rust.md)
#%global rustflags_codegen_units 16
#%global rustflags_debuginfo 0

%description
__SUMMARY__

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
# zbus-lockstep resolves ../xml against the vendored "xml" crate otherwise
[ -d vendor-deps/atspi-common/xml ] && export LOCKSTEP_XML_PATH="$(pwd)/vendor-deps/atspi-common/xml"
%cargo_build

%install
%cargo_install

%files
%license LICENSE
%{_bindir}/__NAME__

%changelog
* __DATE__ __PACKAGER__ - __VERSION__-1
- Initial package
