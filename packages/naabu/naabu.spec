%global goipath         github.com/projectdiscovery/naabu/v2
Version:        2.7.0

%gometa -L -f

%bcond_with check

Name:           naabu
Release:        1%{?dist}
Summary:        Fast port scanner with a focus on reliability and simplicity

License:        MIT
URL:            https://github.com/projectdiscovery/naabu
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

BuildRequires:  go-vendor-tools
# gopacket pcap bindings (SYN scanning) build against libpcap
BuildRequires:  libpcap-devel

%generate_buildrequires
%go_vendor_license_buildrequires

%description
naabu is a fast port scanner written in Go with a focus on reliability and
simplicity. It performs SYN and CONNECT scans (with CDN/WAF exclusion and
source IP/port control) and is designed to be combined with other tools for
attack surface discovery in bug bounties and pentests.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
%gobuild -o %{gobuilddir}/bin/naabu %{goipath}/cmd/naabu

%install
%go_vendor_license_install
install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/

%check
HOME=/tmp %{gobuilddir}/bin/naabu -version

%if %{with check}
%gocheck2
%endif

%files -f %{go_vendor_license_filelist}
%doc README.md
%{_bindir}/naabu

%changelog
* Fri Nov 13 2026 Caio Bruno <cbrunofb@gmail.com> - 2.7.0-1
- Initial package
