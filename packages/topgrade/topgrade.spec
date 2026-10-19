Name:           topgrade
Version:        17.14.0
Release:        1%{?dist}
Summary:        Upgrade everything with one command

License:        GPL-3.0-or-later
URL:            https://github.com/topgrade-rs/topgrade
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

%description
Topgrade keeps your system fresh by detecting the tools you use and running
their appropriate package managers to update them all in one command.

# aws-lc-sys jitterentropy errors on RPM's -O2; see AGENTS.md
%global build_cflags %(echo "%{build_cflags}" | sed 's/ *-O2//g')

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor

%build
%cargo_build

%install
%cargo_install

%{buildroot}%{_bindir}/topgrade --gen-completion bash > topgrade.bash
%{buildroot}%{_bindir}/topgrade --gen-completion zsh  > _topgrade
%{buildroot}%{_bindir}/topgrade --gen-completion fish > topgrade.fish
%{buildroot}%{_bindir}/topgrade --gen-manpage > topgrade.1
install -Dpm644 topgrade.bash %{buildroot}%{bash_completions_dir}/topgrade
install -Dpm644 _topgrade     %{buildroot}%{zsh_completions_dir}/_topgrade
install -Dpm644 topgrade.fish %{buildroot}%{fish_completions_dir}/topgrade.fish
install -Dpm644 topgrade.1    %{buildroot}%{_mandir}/man1/topgrade.1*

%check
%{buildroot}%{_bindir}/topgrade --version

%files
%license LICENSE
%doc README.md
%{_bindir}/topgrade
%{bash_completions_dir}/topgrade
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{zsh_completions_dir}/_topgrade
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_completions.d
%{fish_completions_dir}/topgrade.fish
%{_mandir}/man1/topgrade.1*

%changelog
* Mon Oct 19 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 17.14.0-1
- Update to 17.14.0

* Sat Oct 17 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 17.13.1-1
- Update to 17.13.1

* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 17.13.0-1
- Initial package
