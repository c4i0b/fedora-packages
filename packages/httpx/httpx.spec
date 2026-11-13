%global goipath         github.com/projectdiscovery/httpx
Version:        1.12.0

%gometa -L -f

%bcond_with check

Name:           httpx
Release:        1%{?dist}
Summary:        Fast and multi-purpose HTTP toolkit

License:        MIT
URL:            https://github.com/projectdiscovery/httpx
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

BuildRequires:  go-vendor-tools

%generate_buildrequires
%go_vendor_license_buildrequires

%description
httpx is a fast and multi-purpose HTTP toolkit that allows running multiple
probes using the retryablehttp library. It is designed to maintain result
reliability with an increased number of threads, extracting titles, status
codes, response headers, technology fingerprints, CDN, IPs, ports and more
from lists of hosts or URLs.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
%gobuild -o %{gobuilddir}/bin/httpx %{goipath}/cmd/httpx

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
%license LICENSE.md
%{_bindir}/httpx

%changelog
* Fri Nov 13 2026 Caio Bruno <cbrunofb@gmail.com> - 1.12.0-1
- Initial package
