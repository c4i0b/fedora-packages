%global goipath         github.com/tantalor93/dnspyre/v3
Version:        3.12.0

%gometa -L -f

%bcond_with check

Name:           dnspyre
Release:        1%{?dist}
Summary:        High performance DNS benchmark tool

License:        MIT
URL:            https://github.com/Tantalor93/dnspyre
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

Recommends:     bash-completion

BuildRequires:  go-vendor-tools

%generate_buildrequires
%go_vendor_license_buildrequires

%description
dnspyre is a high performance DNS benchmark tool written in Go. It sends DNS
queries to a server at a configurable rate and reports latency percentiles,
throughput, timing and error statistics, with support for TCP, DoT, DoH and
DoQ transports and cached vs non-cached response measurement.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
%gobuild -o %{gobuilddir}/bin/dnspyre -ldflags "-X 'github.com/tantalor93/dnspyre/v3/cmd.Version=%{version}'" %{goipath}

%install
%go_vendor_license_install
install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/

%{gobuilddir}/bin/dnspyre completion bash > dnspyre.bash
%{gobuilddir}/bin/dnspyre completion zsh  > _dnspyre
%{gobuilddir}/bin/dnspyre completion fish > dnspyre.fish
install -Dpm644 dnspyre.bash %{buildroot}%{bash_completions_dir}/dnspyre
install -Dpm644 _dnspyre     %{buildroot}%{zsh_completions_dir}/_dnspyre
install -Dpm644 dnspyre.fish %{buildroot}%{fish_completions_dir}/dnspyre.fish

%if %{with check}
%check
%gocheck2
%endif

%files -f %{go_vendor_license_filelist}
%doc README.md
%{_bindir}/dnspyre
%{bash_completions_dir}/dnspyre
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{zsh_completions_dir}/_dnspyre
%{fish_completions_dir}/dnspyre.fish

%changelog
* Mon Oct 19 2026 Caio Bruno <cbrunofb@gmail.com> - 3.12.0-1
- Initial package
