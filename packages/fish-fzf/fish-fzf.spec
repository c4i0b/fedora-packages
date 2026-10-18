# fish plugin installed into fish's vendor dirs — the same layout fisher
# uses under ~/.config/fish: conf.d/*.fish run at shell startup, functions/
# and completions/ autoload on demand. fzf.fish powers its key bindings
# with fzf; fd and bat are the README-recommended companions (directory
# search previews), pulled in so the bindings work out of the box.
Name:           fish-fzf
Version:        11.0
Release:        1%{?dist}
Summary:        fzf key bindings for the fish shell
BuildArch:      noarch

License:        MIT
URL:            https://github.com/patrickf1/fzf.fish
Source0:        https://github.com/patrickf1/fzf.fish/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  fish
Requires:       fish
Requires:       fzf
Requires:       fd-find
Requires:       bat

%description
fzf key bindings for the fish shell: fuzzy search of history, directory
contents, git status and log, processes and variables, with file previews.

%prep
%autosetup -n fzf.fish-%{version}

%build

%install
install -Dpm644 conf.d/fzf.fish %{buildroot}%{_datadir}/fish/vendor_conf.d/fzf.fish
for f in functions/*.fish; do
  install -Dpm644 "$f" "%{buildroot}%{_datadir}/fish/vendor_functions.d/$(basename "$f")"
done
install -Dpm644 completions/fzf_configure_bindings.fish \
  %{buildroot}%{_datadir}/fish/vendor_completions.d/fzf_configure_bindings.fish

%check
for f in conf.d/*.fish functions/*.fish completions/*.fish; do
  fish -n "$f"
done

%files
%license LICENSE.md
%doc README.md
%{_datadir}/fish/vendor_conf.d/fzf.fish
%{_datadir}/fish/vendor_functions.d/*.fish
%{_datadir}/fish/vendor_completions.d/fzf_configure_bindings.fish

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 11.0-1
- Initial package
