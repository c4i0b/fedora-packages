# Bun-compiled standalone binary; stripping corrupts its embedded app data.
%define debug_package %{nil}
%global __strip /bin/true

ExclusiveArch:  x86_64 aarch64

Name:           omo
Version:        5.1.66
Release:        1%{?dist}
Summary:        AI agent harness with multi-model orchestration and memory

License:        SUL-1.0
URL:            https://github.com/code-yeongyu/oh-my-openagent
Source0:        %{url}/raw/refs/tags/v%{version}/LICENSE.md
Source1:        %{url}/releases/download/v%{version}/omo-linux-x64
Source2:        %{url}/releases/download/v%{version}/omo-linux-arm64

%description
OmO turns prompts into finished work: one "omo" command with multi-model
orchestration, parallel agents, persistent memory and a large skill library.
Standalone binary embedding the Bun runtime and the senpi engine.

%prep
%setup -T -q -c

%build

%install
%ifarch x86_64
install -Dpm755 %{SOURCE1} %{buildroot}%{_bindir}/omo
%else
install -Dpm755 %{SOURCE2} %{buildroot}%{_bindir}/omo
%endif
install -Dpm644 %{SOURCE0} LICENSE

%check
# First run writes ~/.omo; keep it off the buildroot filesystem
HOME=%{_builddir}/omo-home %{buildroot}%{_bindir}/omo --version

%files
%license LICENSE
%{_bindir}/omo

%changelog
* Tue Nov 10 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 5.1.66-1
- Update to 5.1.66

* Mon Nov 09 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 5.1.65-1
- Update to 5.1.65

* Sat Nov 07 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 5.1.64-1
- Update to 5.1.64

* Sat Nov 07 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 5.1.63-1
- Update to 5.1.63

* Fri Nov 06 2026 Caio Bruno <cbrunofb@gmail.com> - 5.1.62-1
- Initial package
