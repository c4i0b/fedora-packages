%global goipath         github.com/nxtrace/NTrace-core
Version:        1.7.6

%gometa -L -f

# the build-time downloaded Go toolchain is not annobin-instrumented: an empty
# debugsource list aborts the build
%global debug_package %{nil}

%bcond_with check

Name:           nexttrace
Release:        1%{?dist}
Summary:        Open source visual route tracking CLI tool

License:        GPL-3.0-only
URL:            https://github.com/nxtrace/NTrace-core
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

BuildRequires:  go-vendor-tools

%generate_buildrequires
%go_vendor_license_buildrequires

%description
NextTrace is an open source visual route tracking CLI tool. It enhances
traceroute with IP geolocation, ASN and routing information for every hop,
supports ICMP/TCP/UDP probes, MTR-style continuous mode, map generation,
DN42 lookups and a web console with an MCP endpoint.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
# f43/f44 ship go 1.26 while go.mod requires 1.27; fetch the toolchain at build time (network is on)
export GOTOOLCHAIN=auto
%gobuild -o %{gobuilddir}/bin/nexttrace -ldflags "-X github.com/nxtrace/NTrace-core/config.Version=v%{version}" %{goipath}

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
%{_bindir}/nexttrace

%changelog
* Fri Nov 13 2026 Caio Bruno <cbrunofb@gmail.com> - 1.7.6-1
- Initial package
