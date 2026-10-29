Name:           xh
Version:        0.26.3
Release:        1%{?dist}
Summary:        Friendly and fast tool for sending HTTP requests (httpie clone)

License:        MIT
URL:            https://github.com/ducaale/xh
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false
# debugsource trips brp-mangle-shebangs on vendored crate inner attrs
%global debug_package %{nil}

%description
xh is a friendly and fast tool for sending HTTP requests: an improved
curl/httpie hybrid with sensible defaults, JSON support, syntax
highlighting, sessions and effortless downloads, in a single fast binary.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
%cargo_build

%install
%cargo_install

%{buildroot}%{_bindir}/xh --generate complete-bash > xh.bash
%{buildroot}%{_bindir}/xh --generate complete-zsh  > _xh
%{buildroot}%{_bindir}/xh --generate complete-fish > xh.fish
install -Dpm644 xh.bash %{buildroot}%{bash_completions_dir}/xh
install -Dpm644 _xh     %{buildroot}%{zsh_completions_dir}/_xh
install -Dpm644 xh.fish %{buildroot}%{fish_completions_dir}/xh.fish

%check
%{buildroot}%{_bindir}/xh --version

%files
%license LICENSE
%doc README.md
%{_bindir}/xh
%{bash_completions_dir}/xh
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{zsh_completions_dir}/_xh
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_completions.d
%{fish_completions_dir}/xh.fish

%changelog
* Thu Oct 29 2026 Caio Bruno <cbrunofb@gmail.com> - 0.26.3-1
- Initial package
