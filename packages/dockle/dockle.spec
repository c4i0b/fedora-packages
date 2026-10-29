%global goipath         github.com/goodwithtech/dockle
Version:        0.4.15

%gometa -L -f

%bcond_without check

Name:           dockle
Release:        1%{?dist}
Summary:        Container image linter for security and best practices

License:        Apache-2.0
URL:            https://github.com/goodwithtech/dockle
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

BuildRequires:  go-vendor-tools
# containers/storage cgo drivers (btrfs, devmapper) need their headers
BuildRequires:  btrfs-progs-devel
BuildRequires:  device-mapper-devel

%generate_buildrequires
%go_vendor_license_buildrequires

%description
Dockle scans container images for security issues and Dockerfile best
practices: credentials left in layers, suspicious files and permissions,
outdated packages, and checks from the CIS Benchmark — helping you build
secure images without a full vulnerability database.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
%gobuild -o %{gobuilddir}/bin/dockle %{goipath}/cmd/dockle

%install
%go_vendor_license_install
install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/

%if %{with check}
%check
%gocheck2
%{gobuilddir}/bin/dockle --version
%endif

%files -f %{go_vendor_license_filelist}
%doc README.md
%{_bindir}/dockle

%changelog
* Thu Oct 29 2026 Caio Bruno <cbrunofb@gmail.com> - 0.4.15-1
- Initial package
