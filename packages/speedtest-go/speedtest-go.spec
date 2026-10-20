%global goipath         github.com/librespeed/speedtest-go
Version:        1.1.6

%gometa -L -f

Name:           speedtest-go
Release:        1%{?dist}
Summary:        LibreSpeed speed test server implemented in Go

License:        LGPL-3.0-only
URL:            https://github.com/librespeed/speedtest-go
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2
Source2:        speedtest-go.service

BuildRequires:  systemd-rpm-macros

%generate_buildrequires
%go_vendor_license_buildrequires

%description
LibreSpeed backend server: a lightweight, self-hosted internet speed test
with no Flash, Java or WebSockets. Serves the embedded web frontend (modern
and classic UIs), measures download/upload/ping/jitter, and can optionally
store telemetry results in SQLite, BoltDB, PostgreSQL, MySQL or MSSQL, with
IP/ISP detection, results sharing via PNG/JSON and proxy protocol support.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
%gobuild -o %{gobuilddir}/bin/speedtest-go %{goipath}

%install
%go_vendor_license_install
install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/
install -Dpm644 settings.toml       %{buildroot}%{_sysconfdir}/speedtest-go/settings.toml
install -Dpm644 %{SOURCE2}          %{buildroot}%{_unitdir}/speedtest-go.service

%post
%systemd_post speedtest-go.service

%preun
%systemd_preun speedtest-go.service

%files -f %{go_vendor_license_filelist}
%doc README.md
%license LICENSE
%config(noreplace) %{_sysconfdir}/speedtest-go/settings.toml
%{_bindir}/speedtest-go
%{_unitdir}/speedtest-go.service

%changelog
* Mon Oct 19 2026 Caio Bruno <cbrunofb@gmail.com> - 1.1.6-1
- Initial package
