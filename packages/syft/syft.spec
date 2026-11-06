%global goipath         github.com/anchore/syft
Version:        1.57.0

%gometa -L -f

%bcond_without check

Name:           syft
Release:        1%{?dist}
Summary:        CLI tool and library for generating a software SBOM

License:        Apache-2.0
URL:            https://github.com/anchore/syft
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

BuildRequires:  go-vendor-tools

%generate_buildrequires
%go_vendor_license_buildrequires

%description
Syft generates a Software Bill of Materials (SBOM) from container images
and filesystems, cataloging packages and dependencies in formats such as
SPDX and CycloneDX. It pairs with grype for vulnerability scanning of the
discovered packages.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
%gobuild -o %{gobuilddir}/bin/syft %{goipath}/cmd/syft

%install
%go_vendor_license_install
install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/

%if %{with check}
%check
# gocheck2 chokes on testdata corrupt go.mod fixtures; version smoke only
%{gobuilddir}/bin/syft version
%endif

%files -f %{go_vendor_license_filelist}
%doc README.md
%{_bindir}/syft

%changelog
* Fri Nov 06 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 1.57.0-1
- Update to 1.57.0

* Mon Nov 02 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 1.56.0-1
- Update to 1.56.0

* Thu Oct 29 2026 Caio Bruno <cbrunofb@gmail.com> - 1.55.0-1
- Initial package
