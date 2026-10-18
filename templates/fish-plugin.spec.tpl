# fish plugin installed into fish's vendor dirs — the same layout fisher
# uses under ~/.config/fish: conf.d/*.fish run at shell startup, functions/
# and completions/ autoload on demand. A plugin is plain fish source: there
# is nothing to build. Per-package: trim the vendor dirs the upstream
# actually ships (unmatched %%files globs fail the build) and fill the
# __EXTRA*__ slots for subdirs, man pages or prompt conflicts.
Name:           __NAME__
Version:        __VERSION__
Release:        1%{?dist}
Summary:        __SUMMARY__
BuildArch:      noarch

License:        __LICENSE__
URL:            __URL__
Source0:        __SOURCE0__

BuildRequires:  fish
Requires:       fish
__EXTRAREQ__

%description
__SUMMARY__

%prep
%autosetup -n __PAYLOADDIR__

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
__EXTRAINSTALL__

%check
for f in conf.d/*.fish functions/*.fish completions/*.fish; do
  if [ -f "$f" ]; then
    fish -n "$f"
  fi
done

%files
%license __LICENSEFILE__
__EXTRAFILES__
%{_datadir}/fish/vendor_conf.d/*.fish
%{_datadir}/fish/vendor_functions.d/*.fish
%{_datadir}/fish/vendor_completions.d/*.fish

%changelog
* __DATE__ __PACKAGER__ - __VERSION__-1
- Initial package
