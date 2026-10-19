%global goipath         github.com/ramonvermeulen/whosthere
Version:        0.9.0

%gometa -L -f

%bcond_with check

Name:           whosthere
Release:        1%{?dist}
Summary:        LAN discovery tool with an interactive TUI

License:        Apache-2.0
URL:            https://github.com/ramonvermeulen/whosthere
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

Recommends:     bash-completion

BuildRequires:  go-vendor-tools

%generate_buildrequires
%go_vendor_license_buildrequires

%description
Local Area Network discovery tool with an interactive TUI, written in Go.
Whosthere performs unprivileged concurrent scans using mDNS and SSDP, sweeps
the local subnet to populate the ARP cache, and enriches discovered devices
with OUI manufacturer lookups. It can also scan TCP ports on found hosts, run
as a daemon with an HTTP API, and export scan results as JSON.

%prep
%goprep -p1
tar -xf %{S:1}
# upstream tracks its dev toolchain; deps only need go 1.26
sed -i 's/^go 1\.27\.[0-9]*/go 1.26/' go.mod

%build
%global gomodulesmode GO111MODULE=on
%gobuild -o %{gobuilddir}/bin/whosthere -ldflags "-X main.versionStr=%{version}" %{goipath}

%install
%go_vendor_license_install
install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/

%{gobuilddir}/bin/whosthere completion bash > whosthere.bash
%{gobuilddir}/bin/whosthere completion zsh  > _whosthere
%{gobuilddir}/bin/whosthere completion fish > whosthere.fish
install -Dpm644 whosthere.bash %{buildroot}%{bash_completions_dir}/whosthere
install -Dpm644 _whosthere     %{buildroot}%{zsh_completions_dir}/_whosthere
install -Dpm644 whosthere.fish %{buildroot}%{fish_completions_dir}/whosthere.fish

%if %{with check}
%check
%gocheck2
%endif

%files -f %{go_vendor_license_filelist}
%doc README.md
%{_bindir}/whosthere
%{bash_completions_dir}/whosthere
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{zsh_completions_dir}/_whosthere
%{fish_completions_dir}/whosthere.fish

%changelog
* Mon Oct 19 2026 Caio Bruno <cbrunofb@gmail.com> - 0.9.0-1
- Initial package
