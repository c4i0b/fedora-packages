Name:           fish-abbreviation-tips
# __EXTRA*__ slots for subdirs, man pages or prompt conflicts.
Version:        0.7.0
Release:        1%{?dist}
Summary:        Help you remember your fish abbreviations and aliases
BuildArch:      noarch

License:        MIT
URL:            https://github.com/gazorby/fish-abbreviation-tips
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  fish
Requires:       fish


%description
Help you remember your fish abbreviations and aliases

%prep
%autosetup -n fish-abbreviation-tips-%{version}

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

%check
for f in conf.d/*.fish functions/*.fish; do
  fish -n "$f"
done

%files
%license LICENSE
%doc README.md
%{_datadir}/fish/vendor_conf.d/abbr_tips.fish
%{_datadir}/fish/vendor_functions.d/*.fish

%changelog
* Sat Oct 24 2026 Caio Bruno <cbrunofb@gmail.com> - 0.7.0-1
- Initial package
