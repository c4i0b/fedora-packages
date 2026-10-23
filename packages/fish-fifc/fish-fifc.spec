Name:           fish-fifc
Version:        0.3.4
Release:        1%{?dist}
Summary:        Fzf powered fish history and tab completions
BuildArch:      noarch

License:        MIT
URL:            https://github.com/gazorby/fifc
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  fish
Requires:       fish
Requires:       fzf
Requires:       file
# optional upstream, required here for the full preview experience
Requires:       bat
Requires:       eza
Requires:       fd-find
Requires:       chafa
Requires:       hexyl
Requires:       ripgrep
# broot upgrades ctrl-o on a directory to an interactive tree; without it
# the shortcut falls back to eza above
Recommends:     broot

%description
Fzf powered fish history and tab completions

%prep
%autosetup -n fifc-%{version}
# late \t rebinders (autopair's --on-variable handler) clobber our TAB
# binding (fifc issue #81): re-apply on the same event, registered after
cat >> conf.d/fifc.fish <<'EOF'

function __fifc_rebind_tab --on-variable fish_key_bindings
    if status is-interactive
        for mode in default insert
            bind --mode $mode $fifc_keybinding _fifc
        end
    end
end
EOF

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
%{_datadir}/fish/vendor_completions.d/*.fish

%changelog
* Sat Oct 24 2026 Caio Bruno <cbrunofb@gmail.com> - 0.3.4-1
- Initial package
