%global goipath         github.com/wagoodman/dive
Version:        0.13.1

%gometa -L -f

%bcond_without check

Name:           dive
Release:        1%{?dist}
Summary:        Tool for exploring each layer of a Docker/OCI image

License:        MIT
URL:            https://github.com/wagoodman/dive
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

BuildRequires:  go-vendor-tools

%generate_buildrequires
%go_vendor_license_buildrequires

%description
A TUI for exploring a Docker or OCI image, layer contents, and discovering
ways to shrink the size of the image: it shows what files were added,
changed or removed per layer, estimates wasted space and can score a
Dockerfile against best practices.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
%gobuild -o %{gobuilddir}/bin/dive -ldflags "-X main.version=%{version}" %{goipath}

%install
%go_vendor_license_install
install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/

%if %{with check}
%check
%gocheck2
%{gobuilddir}/bin/dive --version
%endif

%files -f %{go_vendor_license_filelist}
%doc README.md
%{_bindir}/dive

%changelog
* Thu Oct 29 2026 Caio Bruno <cbrunofb@gmail.com> - 0.13.1-1
- Initial package
