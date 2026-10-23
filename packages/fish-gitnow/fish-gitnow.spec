Name:           fish-gitnow
Version:        2.13.0
Release:        1%{?dist}
Summary:        Speed up your Git workflow with these few fish shell keybindings
BuildArch:      noarch

License:        MIT
URL:            https://github.com/joseluisq/gitnow
Source0:        %{url}/archive/refs/tags/%{version}.tar.gz

BuildRequires:  fish
Requires:       fish
Requires:       git

%description
Speed up your Git workflow with these few fish shell keybindings

%prep
%autosetup -n gitnow-%{version}

%build

%install
install_vendor() {
  # $2: vendor subdir; conf.d already ends in .d, the others do not
  [ -d "$1" ] || return 0
  for f in "$1"/*.fish; do
    install -Dpm644 "$f" "%{buildroot}%{_datadir}/fish/vendor_$2/$(basename "$f")"
  done
}
install -Dpm644 conf.d/gitnow.fish %{buildroot}%{_datadir}/fish/vendor_conf.d/gitnow.fish
install -Dpm644 conf.d/.gitnow %{buildroot}%{_datadir}/fish/vendor_conf.d/.gitnow
install_vendor functions functions.d
install_vendor completions completions.d


%check
for f in conf.d/*.fish functions/*.fish completions/*.fish; do
  if [ -f "$f" ]; then
    fish -n "$f"
  fi
done

%files
%license LICENSE.md
%doc README.md
%{_datadir}/fish/vendor_conf.d/gitnow.fish
%{_datadir}/fish/vendor_conf.d/.gitnow
%{_datadir}/fish/vendor_functions.d/*.fish
%{_datadir}/fish/vendor_completions.d/*.fish

%changelog
* Sat Oct 24 2026 Caio Bruno <cbrunofb@gmail.com> - 2.13.0-1
- Initial package
