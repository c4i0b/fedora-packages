Name:           fish-pure
Version:        4.19.2
Release:        1%{?dist}
Summary:        Minimalistic, fast fish prompt (pure)
BuildArch:      noarch

License:        MIT
URL:            https://github.com/pure-fish/pure
Source0:        https://github.com/pure-fish/pure/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  fish
Requires:       fish

# Mutually exclusive with other prompts: they all own
# vendor_functions.d/fish_prompt.fish, and only one prompt can.
Provides:       fish-prompt = %{version}-%{release}
Conflicts:      fish-prompt

%description
Minimalistic, fast fish prompt (pure).

%prep
%autosetup -n pure-%{version}

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
for f in conf.d/*.fish functions/*.fish; do
  if [ -f "$f" ]; then
    fish -n "$f"
  fi
done

%files
%license LICENSE
%doc README.md
%{_datadir}/fish/vendor_conf.d/*.fish
%{_datadir}/fish/vendor_functions.d/*.fish

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 4.19.2-1
- Initial package
