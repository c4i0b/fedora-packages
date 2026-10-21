# Self-contained venv: upstream needs dnspython >= 2.9 and cryptography < 51
# pins that Fedora's system python3-dns (2.8) cannot satisfy at runtime
%global debug_package %{nil}
# manylinux wheels bundle auditwheel-hashed libs (libcrypto-<8hex>.so); RPM
# requires their versioned symbols but nothing provides them, making the rpm
# uninstallable
%global __requires_exclude ^lib.+-[0-9a-f]{8}\\.so

Name:           dnsdiag
Version:        2.10.0
Release:        1%{?dist}
Summary:        DNS measurement, troubleshooting and security auditing toolset

License:        BSD-2-Clause
URL:            https://github.com/farrokhi/dnsdiag
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
# upstream server lists, not shipped in the wheel
Source1:        %{url}/raw/v%{version}/public-servers.txt
Source2:        %{url}/raw/v%{version}/public-v4.txt
Source3:        %{url}/raw/v%{version}/rootservers.txt
Source4:        dnseval-public

BuildRequires:  python3
BuildRequires:  python3-devel
BuildRequires:  python3-pip
BuildRequires:  gcc
ExclusiveArch:  x86_64 aarch64 ppc64le s390x

Requires:       python3

%description
dnsdiag is a toolset to measure, troubleshoot and audit DNS: dnsping measures
the response time of any DNS server (UDP, TCP, DoT, DoH, DoQ, DoH3),
dnstraceroute traces the path of DNS requests to detect interception, and
dnseval benchmarks a list of resolvers by latency and packet loss to help pick
the best one for the network.

%prep
%autosetup -n dnsdiag-%{version}

%build

%install
python3 -m venv %{buildroot}%{_libdir}/%{name}
%{buildroot}%{_libdir}/%{name}/bin/pip install --no-cache-dir . >/dev/null
# Venv scripts and pyvenv.cfg carry the buildroot path
grep -rlZ '%{buildroot}' %{buildroot}%{_libdir}/%{name}/bin/ \
    | xargs -0r sed -i "s|%{buildroot}||g"
sed -i "s|%{buildroot}||g" %{buildroot}%{_libdir}/%{name}/pyvenv.cfg

install -d -m755 %{buildroot}%{_datadir}/%{name}
install -m 0644 %{S:1} %{S:2} %{S:3} %{buildroot}%{_datadir}/%{name}/

install -d -m755 %{buildroot}%{_bindir}
install -m 0755 %{SOURCE4} %{buildroot}%{_bindir}/dnseval-public
for b in dnsping dnstraceroute dnseval; do
    ln -s %{_libdir}/%{name}/bin/$b %{buildroot}%{_bindir}/$b
done

%check
# console-script shebangs point at final installed paths: run them through
# the venv interpreter instead of executing the wrappers directly
for b in dnsping dnstraceroute dnseval; do
    %{buildroot}%{_libdir}/%{name}/bin/python \
        %{buildroot}%{_libdir}/%{name}/bin/$b --help >/dev/null
done

%files
%license LICENSE
%doc README.md CHANGELOG.md
%{_bindir}/dnsping
%{_bindir}/dnstraceroute
%{_bindir}/dnseval
%{_bindir}/dnseval-public
%{_libdir}/%{name}/
%{_datadir}/%{name}/

%changelog
* Mon Oct 19 2026 Caio Bruno <cbrunofb@gmail.com> - 2.10.0-1
- Initial package
