Name:           television
Version:        0.15.9
Release:        1%{?dist}
Summary:        A very fast and hackable fuzzy finder for the terminal

License:        MIT
URL:            https://github.com/alexpasmantier/television
Source0:        %{url}/archive/refs/tags/%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

%description
Television is a fast and portable fuzzy finder with a channel system: canned
selections (files, git, env, emojis, ...) each with their own source command,
preview command and keybindings.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
%cargo_build

%install
%cargo_install
ln -s tv %{buildroot}%{_bindir}/television

%{buildroot}%{_bindir}/tv completions bash > tv.bash
%{buildroot}%{_bindir}/tv completions zsh  > _tv
%{buildroot}%{_bindir}/tv completions fish > tv.fish
install -Dpm644 tv.bash  %{buildroot}%{bash_completions_dir}/tv
install -Dpm644 _tv      %{buildroot}%{zsh_completions_dir}/_tv
install -Dpm644 tv.fish  %{buildroot}%{fish_completions_dir}/tv.fish

install -Dpm644 man/tv.1 %{buildroot}%{_mandir}/man1/tv.1

%check
%{buildroot}%{_bindir}/tv --version

%files
%license LICENSE
%doc README.md
%{_bindir}/tv
%{_bindir}/television
%{bash_completions_dir}/tv
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{zsh_completions_dir}/_tv
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_completions.d
%{fish_completions_dir}/tv.fish
%{_mandir}/man1/tv.1*

%changelog
* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 0.15.9-1
- Initial package
