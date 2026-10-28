# Official npm bundle, same packaging as openclaw: upstream publishes a fully
# bundled esbuild dist (the npm package.json ships with dependencies emptied),
# so the payload is plain JavaScript with no native addons and no build-time
# npm install — noarch.
Name:           devcontainers-cli
Version:        0.90.0
Release:        1%{?dist}
Summary:        Reference CLI for building and running Development Containers

License:        MIT
URL:            https://github.com/devcontainers/cli
Source0:        https://registry.npmjs.org/@devcontainers/cli/-/cli-%{version}.tgz

BuildArch:      noarch

BuildRequires:  nodejs24
Requires:       nodejs24
# OCI backend used by the up/build/exec commands (docker works too)
Recommends:     podman

# env-node shebang inside the payload tree; the /usr/bin wrapper is the entrypoint
%define __brp_mangle_shebangs %{nil}

%description
The Dev Container CLI takes a devcontainer.json and creates and configures a
dev container from it (build, up, exec, features and templates commands),
talking to a local Docker or Podman backend. This package ships the official
npm bundle of @devcontainers/cli.

%prep
%autosetup -n package

%build
# dist/spec-node/devContainersSpecCLI.js is upstream's production bundle:
# every dependency is inlined and only Node builtins are require()d

%install
install -d -m755 %{buildroot}%{_prefix}/lib/node_modules/%{name}
cp -a . %{buildroot}%{_prefix}/lib/node_modules/%{name}/

install -Dpm755 /dev/null %{buildroot}%{_bindir}/devcontainer
cat > %{buildroot}%{_bindir}/devcontainer <<'EOF'
#!/bin/sh
exec /usr/bin/node-24 %{_prefix}/lib/node_modules/devcontainers-cli/devcontainer.js "$@"
EOF

# Yargs has completion() enabled but no `completion` command (no script to
# print); ship the canonical yargs boilerplate — candidates are generated
# dynamically by the binary via --get-yargs-completions, nothing hand-written
install -Dpm644 /dev/null %{buildroot}%{_datadir}/bash-completion/completions/devcontainer
cat > %{buildroot}%{_datadir}/bash-completion/completions/devcontainer <<'EOF'
# canonical yargs completion shim
_devcontainer_completion() {
  local cur_word
  cur_word="${COMP_WORDS[COMP_CWORD]}"
  COMPREPLY=( $(COMP_CWORD=$((COMP_CWORD+1)) devcontainer --get-yargs-completions "${COMP_WORDS[@]:1}" "${cur_word}") )
}
complete -F _devcontainer_completion devcontainer
EOF

%check
# Scratch HOME per repo convention; call the interpreter directly since the
# wrapper hardcodes installed paths
HOME=%{_builddir} %{_bindir}/node-24 devcontainer.js --version
HOME=%{_builddir} %{_bindir}/node-24 devcontainer.js --help >/dev/null
# completion engine must answer both subcommands and per-command flags
# (tr: $(...) keeps the newlines, the comparison is space-separated)
test "$(HOME=%{_builddir} %{_bindir}/node-24 devcontainer.js --get-yargs-completions devcontainer '' | tr '\n' ' ')" = "up set-up build run-user-commands read-configuration outdated upgrade features templates exec "
HOME=%{_builddir} %{_bindir}/node-24 devcontainer.js --get-yargs-completions devcontainer up -- | grep -q -- --workspace-folder

%files
%license LICENSE.txt ThirdPartyNotices.txt
%doc README.md CHANGELOG.md
%{_bindir}/devcontainer
%{_prefix}/lib/node_modules/%{name}/

%changelog
* Wed Oct 28 2026 Caio Bruno <cbrunofb@gmail.com> - 0.90.0-1
- Initial package
