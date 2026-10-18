# fish plugin installed into fish's vendor dirs — the same layout fisher
# uses under ~/.config/fish: conf.d/*.fish run at shell startup, functions/
# and completions/ autoload on demand. A plugin is plain fish source: there
# is nothing to build. Per-package: trim the vendor dirs the upstream
# actually ships (unmatched %%files globs fail the build) and fill the
# __EXTRA*__ slots for subdirs, man pages or prompt conflicts.
# No upstream tags/releases: version is a pinned commit snapshot (manual bumps).
Name:           fish-hydro
Version:        2026.02.23
Release:        1%{?dist}
Summary:        Fast async git prompt for fish (hydro)
BuildArch:      noarch

License:        MIT
URL:            https://github.com/jorgebucaran/hydro
Source0:        https://github.com/jorgebucaran/hydro/archive/f130b55ee3eaf099eccf588e2a62e5447068d120.tar.gz

BuildRequires:  fish
Requires:       fish

# Mutually exclusive with other prompts: they all own
# vendor_functions.d/fish_prompt.fish, and only one prompt can.
Provides:       fish-prompt = %{version}-%{release}
Conflicts:      fish-prompt

%description
Fast async git prompt for fish (hydro).

%prep
%autosetup -n hydro-f130b55ee3eaf099eccf588e2a62e5447068d120

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
%license LICENSE.md
%doc README.md
%{_datadir}/fish/vendor_conf.d/*.fish
%{_datadir}/fish/vendor_functions.d/*.fish

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 2026.02.23-1
- Initial package
