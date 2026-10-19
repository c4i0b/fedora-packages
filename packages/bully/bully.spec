Name:           bully
Version:        1.2
Release:        1%{?dist}
Summary:        WPS brute-force attack tool

License:        GPL-3.0-or-later
URL:            https://github.com/aanarchyy/bully
Source0:        https://codeload.github.com/aanarchyy/bully/tar.gz/refs/tags/%{version}

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  libpcap-devel

%description
Bully is an implementation of the WPS brute-force attack, written in
C. It references the original Reaver code, but is a standalone project.
Given a AP's pin, it can retrieve the WPA/WPA2 key — it is also used
by wifite for WPS attacks and to fetch the PSK once the PIN is known.

%prep
%autosetup -n bully-%{version}

%build
# Env (not command-line) CFLAGS/LDFLAGS so the Makefile's += keeps the
# internal crypto defines and -lpcap on top of the RPM flags
cd src
export CFLAGS="%{build_cflags}"
export LDFLAGS="%{build_ldflags}"
make %{?_smp_mflags}

%install
# Cleanup helper from Kali's packaging: removes WPS session files
# (--restore/--p2c) left by bully runs.
cat > bully-cleanup << 'EOF'
#!/bin/sh
rm -f ./bully.*.run ./bully.*.pin ./bully.*.p2c 2>/dev/null || true
EOF
install -Dpm755 bully-cleanup %{buildroot}%{_bindir}/bully-cleanup

make -C src prefix=%{_prefix} bindir=%{_bindir} DESTDIR=%{buildroot} install

%files
%license LICENSE.md
%{_bindir}/bully
%{_bindir}/bully-cleanup

%changelog
* Sun Oct 18 2026 Caio Bruno <cbrunofb@gmail.com> - 1.2-1
- Initial package
