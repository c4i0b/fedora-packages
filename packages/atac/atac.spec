Name:           atac
Version:        0.24.0
Release:        1%{?dist}
Summary:        Simple yet powerful API client TUI (terminal Postman)

License:        MIT
URL:            https://github.com/julien-cpsn/ATAC
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

%description
ATAC (Argument-Tree API Client) is a feature-rich API client that lives in
the terminal: collections, environments, keybind-driven requests, syntax
highlighted responses and curl import — a Postman/Insomnia experience
without leaving the keyboard.

%prep
%autosetup -n atac-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
%cargo_build

%install
%cargo_install

# 'atac completions <shell> <dir>' writes the file into <dir>
compdir="$(mktemp -d)"
%{buildroot}%{_bindir}/atac completions bash "$compdir"
install -Dpm644 "$compdir"/* %{buildroot}%{bash_completions_dir}/atac
rm -f "$compdir"/*
%{buildroot}%{_bindir}/atac completions zsh "$compdir"
install -Dpm644 "$compdir"/* %{buildroot}%{zsh_completions_dir}/_atac
rm -f "$compdir"/*
%{buildroot}%{_bindir}/atac completions fish "$compdir"
install -Dpm644 "$compdir"/* %{buildroot}%{fish_completions_dir}/atac.fish

%check
%{buildroot}%{_bindir}/atac --version

%files
%license LICENSE
%doc README.md
%{_bindir}/atac
%{bash_completions_dir}/atac
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{zsh_completions_dir}/_atac
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_completions.d
%{fish_completions_dir}/atac.fish

%changelog
* Thu Oct 29 2026 Caio Bruno <cbrunofb@gmail.com> - 0.24.0-1
- Initial package
