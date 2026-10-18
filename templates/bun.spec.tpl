# Bun-compiled standalone binary; stripping corrupts its embedded app data.
%define debug_package %{nil}
%global __strip /bin/true

%ifarch x86_64
%global a x64
%global buna x64
%elifarch aarch64
%global a arm64
%global buna aarch64
%endif

ExclusiveArch:  x86_64 aarch64

Name:           __NAME__
Version:        __VERSION__
Release:        1%{?dist}
Summary:        __SUMMARY__

License:        __LICENSE__
URL:            __URL__
Source0:        __SOURCE0__
Source1:        https://github.com/oven-sh/bun/releases/latest/download/bun-linux-x64.zip
Source2:        https://github.com/oven-sh/bun/releases/latest/download/bun-linux-aarch64.zip
# Pin a bun version in the URLs above if latest ever breaks the build

BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  python3
BuildRequires:  nodejs-npm
BuildRequires:  unzip

%description
__SUMMARY__

%prep
%autosetup -p1
%ifarch x86_64
unzip -q %{SOURCE1}
%else
unzip -q %{SOURCE2}
%endif
chmod +x bun-linux-%{buna}/bun

%build
BUN=%{_builddir}/%{name}-%{version}/bun-linux-%{buna}/bun
# Writable npm prefix (npm -g hits EACCES in /usr) + toolchain in PATH for
# postinstall scripts calling bare names
export npm_config_prefix=%{_builddir}/.npm-global
export PATH=$(dirname "$BUN"):%{_builddir}/.npm-global/bin:$PATH
npm install -g node-gyp

"$BUN" install
__BUILD_CMD__

%install
BIN=__BUILD_OUTPUT__
install -Dpm755 "$BIN" %{buildroot}%{_bindir}/__NAME__

# Optional: shell completions (drop what the binary does not generate)
__NAME__ --completions bash > __NAME__.bash
__NAME__ --completions zsh  > ___NAME__
__NAME__ --completions fish > __NAME__.fish
install -Dpm644 __NAME__.bash %{buildroot}%{bash_completions_dir}/__NAME__
install -Dpm644 ___NAME__     %{buildroot}%{zsh_completions_dir}/___NAME__
install -Dpm644 __NAME__.fish %{buildroot}%{fish_completions_dir}/__NAME__.fish

%check
%{buildroot}%{_bindir}/__NAME__ --version

%files
%license LICENSE
%{_bindir}/__NAME__
%{bash_completions_dir}/__NAME__
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{zsh_completions_dir}/___NAME__
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_completions.d
%{fish_completions_dir}/__NAME__.fish

%changelog
* __DATE__ __PACKAGER__ - __VERSION__-1
- Initial package
