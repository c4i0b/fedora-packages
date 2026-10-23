Name:           nvm-fish
Version:        2.2.17
Release:        1%{?dist}
Summary:        The Node.js version manager for fish
BuildArch:      noarch

License:        MIT
URL:            https://github.com/jorgebucaran/nvm.fish
Source0:        %{url}/archive/refs/tags/%{version}.tar.gz

BuildRequires:  fish
Requires:       fish
Requires:       curl
Requires:       git

%description
The Node.js version manager for fish

%prep
%autosetup -n nvm.fish-%{version}

%build

%install
install_vendor() {
  # $2: vendor subdir; conf.d already ends in .d, the others do not
  [ -d "$1" ] || return 0
  for f in "$1"/*.fish; do
    install -Dpm644 "$f" "%{buildroot}%{_datadir}/fish/vendor_$2/$(basename "$f")"
  done
}
install_vendor conf.d conf.d
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

%{_datadir}/fish/vendor_conf.d/*.fish
%{_datadir}/fish/vendor_functions.d/*.fish
%{_datadir}/fish/vendor_completions.d/*.fish

%changelog
* Sat Oct 24 2026 Caio Bruno <cbrunofb@gmail.com> - 2.2.17-1
- Initial package
