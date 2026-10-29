%global goipath         github.com/regclient/regclient
Version:        0.11.7

%gometa -L -f

%bcond_without check

Name:           regclient
Release:        1%{?dist}
Summary:        Docker and OCI registry client (regctl, regsync, regbot)

License:        Apache-2.0
URL:            https://github.com/regclient/regclient
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

BuildRequires:  go-vendor-tools

%generate_buildrequires
%go_vendor_license_buildrequires

%description
Regclient provides interfaces for managing Docker and OCI registries
without a daemon. It ships three tools: regctl for inspecting, copying and
retagging images and manifests; regsync for mirroring registries on a
schedule; and regbot for scripting registry automation with Lua.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
%gobuild -o %{gobuilddir}/bin/regctl  %{goipath}/cmd/regctl
%gobuild -o %{gobuilddir}/bin/regsync %{goipath}/cmd/regsync
%gobuild -o %{gobuilddir}/bin/regbot  %{goipath}/cmd/regbot

%install
%go_vendor_license_install
install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/

%if %{with check}
%check
%gocheck2
%{gobuilddir}/bin/regctl version
%endif

%files -f %{go_vendor_license_filelist}
%doc README.md
%{_bindir}/regctl
%{_bindir}/regsync
%{_bindir}/regbot

%changelog
* Thu Oct 29 2026 Caio Bruno <cbrunofb@gmail.com> - 0.11.7-1
- Initial package
