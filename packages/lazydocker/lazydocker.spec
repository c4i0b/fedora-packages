%global goipath         github.com/jesseduffield/lazydocker
Version:        0.25.2

%gometa -L -f

%bcond_without check

Name:           lazydocker
Release:        1%{?dist}
Summary:        Simple terminal UI for docker and docker-compose

License:        MIT
URL:            https://github.com/jesseduffield/lazydocker
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

BuildRequires:  go-vendor-tools

%generate_buildrequires
%go_vendor_license_buildrequires

%description
A simple terminal UI for both docker and docker-compose, written in Go with
the gocui library. It shows container logs, restarts, removes containers and
services, and displays CPU/memory graphs and lazydocker's own environmental
info.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
%gobuild -o %{gobuilddir}/bin/lazydocker -ldflags "-X main.version=%{version}" %{goipath}

%install
%go_vendor_license_install
install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/

%if %{with check}
%check
%gocheck2
%endif

%files -f %{go_vendor_license_filelist}
%doc README.md
%{_bindir}/lazydocker

%changelog
* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 0.25.2-1
- Initial package
