%global goipath         github.com/bcicen/ctop
Version:        0.7.7

%gometa -L -f

%bcond_without check

Name:           ctop
Release:        1%{?dist}
Summary:        Top-like interface for container metrics

License:        MIT
URL:            https://github.com/bcicen/ctop
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

BuildRequires:  go-vendor-tools

%generate_buildrequires
%go_vendor_license_buildrequires

%description
A concise command-line tool for monitoring container metrics in real time,
across docker and podman runtimes: CPU, memory, network and disk usage,
with filters, sorting and a log/actions view per container.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
%gobuild -o %{gobuilddir}/bin/ctop %{goipath}

%install
%go_vendor_license_install
install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/

%if %{with check}
%check
%gocheck2
%{gobuilddir}/bin/ctop -v
%endif

%files -f %{go_vendor_license_filelist}
%doc README.md
%{_bindir}/ctop

%changelog
* Thu Oct 29 2026 Caio Bruno <cbrunofb@gmail.com> - 0.7.7-1
- Initial package
