Name:           mise
Version:        2026.10.23
Release:        1%{?dist}
Summary:        Polyglot runtime and tool version manager (modern asdf)

License:        MIT
URL:            https://github.com/jdx/mise
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros
BuildRequires:  gcc-c++
BuildRequires:  cmake
BuildRequires:  openssl-devel

# debug_package is nil and the workspace is huge: debuginfo + single
# codegen unit push the build past the COPR timeout on 2-vCPU builders
%global build_rustflags %(echo "%{build_rustflags}" | sed -e 's/-Cdebuginfo=[0-9]//' -e 's/-Ccodegen-units=1//')

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false
# debugsource trips brp-mangle-shebangs on vendored crate inner attrs
%global debug_package %{nil}

%description
Mise manages runtime and tool versions per project, directory or globally:
node, python, go, terraform and hundreds of other tools, plus environment
variables and tasks. A fast single-binary replacement for asdf, nvm, pyenv
and friends.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
%cargo_build

%install
%cargo_install

%{buildroot}%{_bindir}/mise completion bash > mise.bash
%{buildroot}%{_bindir}/mise completion zsh  > _mise
%{buildroot}%{_bindir}/mise completion fish > mise.fish
install -Dpm644 mise.bash %{buildroot}%{bash_completions_dir}/mise
install -Dpm644 _mise     %{buildroot}%{zsh_completions_dir}/_mise
install -Dpm644 mise.fish %{buildroot}%{fish_completions_dir}/mise.fish

%check
%{buildroot}%{_bindir}/mise --version

%files
%license LICENSE
%doc README.md
%{_bindir}/mise
%{bash_completions_dir}/mise
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{zsh_completions_dir}/_mise
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_completions.d
%{fish_completions_dir}/mise.fish

%changelog
* Thu Oct 29 2026 Caio Bruno <cbrunofb@gmail.com> - 2026.10.23-1
- Initial package
