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

Name:           opencode
Version:        2.2.4
Release:        1%{?dist}
Summary:        Open source AI coding agent for the terminal, IDE, and desktop

License:        MIT
URL:            https://opencode.ai
Source0:        https://github.com/anomalyco/opencode/archive/refs/tags/v%{version}.tar.gz
# Bun follows latest (project has build network); pin a version here if it ever breaks
Source1:        https://github.com/oven-sh/bun/releases/latest/download/bun-linux-x64.zip
Source2:        https://github.com/oven-sh/bun/releases/latest/download/bun-linux-aarch64.zip

BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  python3
BuildRequires:  nodejs-npm
BuildRequires:  unzip

%description
opencode is an open source AI coding agent that helps you write code in your
terminal, IDE, or desktop. It supports 75+ LLM providers (including local
models), LSP integration, multi-session workflows, GitHub Copilot and ChatGPT
login, and the Model Context Protocol (MCP).

%prep
%autosetup -n opencode-%{version} -p1
%ifarch x86_64
unzip -q %{SOURCE1}
%else
unzip -q %{SOURCE2}
%endif
chmod +x bun-linux-%{buna}/bun

%build
BUN=%{_builddir}/opencode-%{version}/bun-linux-%{buna}/bun
# Writable npm prefix (npm -g hits EACCES in /usr) + toolchain in PATH for
# postinstall scripts calling bare names
export npm_config_prefix=%{_builddir}/.npm-global
export PATH=$(dirname "$BUN"):%{_builddir}/.npm-global/bin:$PATH
npm install -g node-gyp

"$BUN" install
cd packages/cli
OPENCODE_VERSION=%{version} OPENCODE_CHANNEL=latest \
  "$BUN" run script/build.ts --single --skip-install

%install
export HOME=%{_builddir}/oc-home
mkdir -p "$HOME"

BIN=packages/cli/dist/cli-linux-%{a}/bin/opencode
install -Dpm755 "$BIN" %{buildroot}%{_bindir}/opencode

"$BIN" --completions bash > opencode.bash
"$BIN" --completions zsh  > _opencode
"$BIN" --completions fish > opencode.fish
install -Dpm644 opencode.bash %{buildroot}%{bash_completions_dir}/opencode
install -Dpm644 _opencode     %{buildroot}%{zsh_completions_dir}/_opencode
install -Dpm644 opencode.fish %{buildroot}%{fish_completions_dir}/opencode.fish

%check
%{buildroot}%{_bindir}/opencode --version

%files
%license LICENSE
%{_bindir}/opencode
%{bash_completions_dir}/opencode
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{zsh_completions_dir}/_opencode
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_completions.d
%{fish_completions_dir}/opencode.fish

%changelog
* Fri Oct 30 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 2.2.4-1
- Update to 2.2.4

* Fri Oct 30 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 2.2.3-1
- Update to 2.2.3

* Thu Oct 29 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 2.2.2-1
- Update to 2.2.2

* Thu Oct 29 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 2.2.1-1
- Update to 2.2.1

* Tue Oct 27 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 2.2.0-1
- Update to 2.2.0

* Fri Oct 23 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 2.1.4-1
- Update to 2.1.4

* Thu Oct 22 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 2.1.3-1
- Update to 2.1.3

* Wed Oct 21 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 2.1.2-1
- Update to 2.1.2

* Tue Oct 20 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 2.1.1-1
- Update to 2.1.1

* Fri Oct 16 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 2.0.32-1
- Update to 2.0.32

* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 2.0.31-1
- Initial package
