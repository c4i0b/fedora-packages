%global goipath         github.com/DNSControl/dnscontrol/v5
Version:        5.8.2

%gometa -L -f

%bcond_with check

Name:           dnscontrol
Release:        1%{?dist}
Summary:        Compiler and DSL for managing DNS zones across providers

License:        MIT
URL:            https://github.com/DNSControl/dnscontrol
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

BuildRequires:  go-vendor-tools

%generate_buildrequires
%go_vendor_license_buildrequires

%description
DNSControl is an opinionated platform for seamlessly managing DNS configuration
across any number of DNS hosts, both in the cloud or in your own datacenter.
It uses a JS-based DSL to describe zones and a compiler that pushes changes to
100+ providers (Route53, Cloudflare, Google Cloud DNS, Azure, BIND, and many
more), enabling "DNS as code" with preview, push and check-creds workflows.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
# f43/f44 ship go 1.26 while go.mod requires 1.27; fetch the toolchain at build time (network is on)
export GOTOOLCHAIN=auto
%gobuild -o %{gobuilddir}/bin/dnscontrol -ldflags "-X 'github.com/DNSControl/dnscontrol/v5/pkg/version.version=%{version}'" %{goipath}

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
%{_bindir}/dnscontrol

%changelog
* Fri Nov 13 2026 Caio Bruno <cbrunofb@gmail.com> - 5.8.2-1
- Initial package
