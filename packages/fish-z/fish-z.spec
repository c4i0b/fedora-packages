Name:           fish-z
Version:        2026.04.16
Release:        1%{?dist}
Summary:        Quick jumping between directories by frecent usage (z for fish)
BuildArch:      noarch

License:        MIT
URL:            https://github.com/jethrokuan/z
# No usable release tags (only "<2.7.0"/"pre27"/"1.1") and no GitHub
# releases: versioned snapshot of master, bumped manually.
Source0:        https://github.com/jethrokuan/z/archive/26a50962bc68f5cb60fc488ee008b3d4d5be75f4.tar.gz

BuildRequires:  fish
Requires:       fish

%description
Quick jumping between directories by frecent usage (z for fish).

%prep
%autosetup -n z-26a50962bc68f5cb60fc488ee008b3d4d5be75f4

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
install -Dpm644 man/man1/z.1 %{buildroot}%{_mandir}/man1/z.1

%check
for f in conf.d/*.fish functions/*.fish completions/*.fish; do
  if [ -f "$f" ]; then
    fish -n "$f"
  fi
done

%files
%license LICENSE
%{_mandir}/man1/z.1*
%{_datadir}/fish/vendor_conf.d/*.fish
%{_datadir}/fish/vendor_functions.d/*.fish

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 2026.04.16-1
- Initial package
