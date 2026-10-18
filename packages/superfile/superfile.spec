%global goipath         github.com/yorukot/superfile
Version:        1.6.0

%gometa -L -f

%bcond_with check

Name:           superfile
Release:        1%{?dist}
Summary:        Pretty fancy and modern terminal file manager

License:        MIT
URL:            https://github.com/yorukot/superfile
Source0:        %{gosource}
Source1:        %{archivename}-vendor.tar.bz2
Source3:        https://raw.githubusercontent.com/yorukot/superfile/v%{version}/cd_on_quit/cd_on_quit.sh
Source4:        https://raw.githubusercontent.com/yorukot/superfile/v%{version}/cd_on_quit/cd_on_quit.fish

BuildRequires:  go-vendor-tools

%generate_buildrequires
%go_vendor_license_buildrequires

%description
A pretty fancy and modern terminal file manager written in Go, with vim-like
keybindings, tabs, panels, themes, and an extensible plugin system.

%prep
%goprep -p1
tar -xf %{S:1}

%build
%global gomodulesmode GO111MODULE=on
%gobuild -o %{gobuilddir}/bin/spf %{goipath}

%install
%go_vendor_license_install
install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/
ln -s spf %{buildroot}%{_bindir}/superfile

install -Dpm755 %{SOURCE3} %{buildroot}%{_datadir}/%{name}/cd_on_quit.sh
install -Dpm644 %{SOURCE4} %{buildroot}%{_datadir}/%{name}/cd_on_quit.fish

%if %{with check}
%check
%gocheck2
%endif

%files -f %{go_vendor_license_filelist}
%doc README.md
%{_bindir}/spf
%{_bindir}/superfile
%{_datadir}/%{name}/

%changelog
* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 1.6.0-1
- Initial package
