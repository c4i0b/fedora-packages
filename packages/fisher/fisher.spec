Name:           fisher
Version:        4.4.8
Release:        1%{?dist}
Summary:        A plugin manager for the Fish shell

License:        MIT
URL:            https://github.com/jorgebucaran/fisher
Source0:        %{url}/archive/refs/tags/%{version}.tar.gz

BuildArch:      noarch

Requires:       fish

BuildRequires:  fish

%description
Fisher is a plugin manager for the Fish shell. It installs, updates and
removes fish plugins, managing functions, completions and key bindings
with a minimal footprint.

%prep
%autosetup -n fisher-%{version}

%build

%install
install -Dpm644 functions/fisher.fish %{buildroot}%{_datadir}/fish/vendor_functions.d/fisher.fish
install -Dpm644 completions/fisher.fish %{buildroot}%{fish_completions_dir}/fisher.fish

%check
fish -n functions/fisher.fish
fish -n completions/fisher.fish

%files
%license LICENSE.md
%doc README.md
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_functions.d
%{_datadir}/fish/vendor_functions.d/fisher.fish
%dir %{_datadir}/fish/vendor_completions.d
%{fish_completions_dir}/fisher.fish

%changelog
* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 4.4.8-1
- Initial package
