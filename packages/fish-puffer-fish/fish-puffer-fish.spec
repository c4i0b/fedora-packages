# fish plugin installed into fish's vendor dirs — the same layout fisher
# uses under ~/.config/fish: conf.d/*.fish run at shell startup, functions/
# and completions/ autoload on demand. A plugin is plain fish source: there
# is nothing to build. Per-package: trim the vendor dirs the upstream
# actually ships (unmatched %%files globs fail the build) and fill the
# __EXTRA*__ slots for subdirs, man pages or prompt conflicts.
Name:           fish-puffer-fish
Version:        1.1.0
Release:        1%{?dist}
Summary:        Text objects and double-tap key bindings for the fish shell (puffer-fish)
BuildArch:      noarch

License:        MIT
URL:            https://github.com/nickeb96/puffer-fish
Source0:        https://github.com/nickeb96/puffer-fish/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  fish
Requires:       fish

%description
Text objects and double-tap key bindings for the fish shell (puffer-fish).

%prep
%autosetup -n puffer-fish-%{version}

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
%license LICENSE
%{_datadir}/fish/vendor_conf.d/*.fish
%{_datadir}/fish/vendor_functions.d/*.fish

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 1.1.0-1
- Initial package
