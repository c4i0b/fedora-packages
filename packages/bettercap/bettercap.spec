%global goipath         github.com/bettercap/bettercap/v2
Version:        2.42.0

%gometa -L -f

Name:           bettercap
Release:        1%{?dist}
Summary:        Swiss army knife for network attacks and monitoring

License:        GPL-3.0-only
URL:            https://github.com/bettercap/bettercap
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

BuildRequires:  gcc
BuildRequires:  go-vendor-tools
BuildRequires:  libpcap-devel
BuildRequires:  libusb1-devel

%generate_buildrequires
%go_vendor_license_buildrequires

%description
Bettercap is a powerful, modular and portable framework for MITM attacks,
network sniffing, Wi-Fi and HID reconnaissance and attacks.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
%gobuild -o %{gobuilddir}/bin/bettercap %{goipath}
%install
%go_vendor_license_install
install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/

%files -f %{go_vendor_license_filelist}
%doc README.md
%{_bindir}/bettercap

%changelog
* Sat Nov 21 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 2.42.0-1
- Update to 2.42.0

* Sun Oct 18 2026 Caio Bruno <cbrunofb@gmail.com> - 2.41.7-1
- Initial package
