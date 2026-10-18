%global goipath         github.com/steveyegge/beads
Version:        1.3.1

%gometa -L -f

%bcond_with check

Name:           beads
Release:        1%{?dist}
Summary:        Memory upgrade for your coding agent

License:        MIT
URL:            https://github.com/gastownhall/beads
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2

BuildRequires:  go-vendor-tools
BuildRequires:  gcc
BuildRequires:  gcc-c++
# go-icu-regex (dolt backend) needs ICU headers
BuildRequires:  libicu-devel

%generate_buildrequires
%go_vendor_license_buildrequires

%description
Beads tracks every issue, decision and insight your coding agent touches and
feeds the right context back at the right moment, so agents stop re-reading
the whole repo and re-deciding solved problems. Ships the bd CLI.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
# Embedded Dolt backend requires CGO
CGO_ENABLED=1 %gobuild -o %{gobuilddir}/bin/bd %{goipath}/cmd/bd

%install
%go_vendor_license_install
install -m 0755 -vd %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/bd %{buildroot}%{_bindir}/

%{gobuilddir}/bin/bd completion bash > bd.bash
%{gobuilddir}/bin/bd completion fish > bd.fish
%{gobuilddir}/bin/bd completion zsh  > bd.zsh
install -Dpm644 bd.bash %{buildroot}%{bash_completions_dir}/bd
install -Dpm644 bd.fish %{buildroot}%{fish_completions_dir}/bd.fish
install -Dpm644 bd.zsh  %{buildroot}%{zsh_completions_dir}/_bd

%if %{with check}
%check
%gocheck2
%endif

%files -f %{go_vendor_license_filelist}
%doc README.md
%{_bindir}/bd
%{bash_completions_dir}/bd
%{fish_completions_dir}/bd.fish
%{zsh_completions_dir}/_bd

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 1.3.1-1
- Initial package
