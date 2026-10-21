%global goipath         github.com/librespeed/speedtest-cli
Version:        1.0.14

%gometa -L -f

%bcond_with check

Name:           librespeed-cli
Release:        1%{?dist}
Summary:        Command line speed test tool using LibreSpeed servers

License:        LGPL-3.0-or-later
URL:            https://github.com/librespeed/speedtest-cli
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

BuildRequires:  go-vendor-tools

%generate_buildrequires
%go_vendor_license_buildrequires

%description
A command line client for testing internet bandwidth using LibreSpeed
servers, with server selection, upload/download/ping/jitter measurement
and CSV or JSON output.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
%gobuild -o %{gobuilddir}/bin/librespeed-cli -ldflags "-X github.com/librespeed/speedtest-cli/defs.ProgVersion=v%{version}" %{goipath}

%install
%go_vendor_license_install
install -m 0755 -vd                          %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/*      %{buildroot}%{_bindir}/

%if %{with check}
%check
%gocheck2
%endif

%files -f %{go_vendor_license_filelist}
%doc README.md
%{_bindir}/librespeed-cli

%changelog
* Wed Oct 21 2026 Caio Bruno <cbrunofb@gmail.com> - 1.0.14-1
- Initial package
