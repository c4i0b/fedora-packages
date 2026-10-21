# Official npm bundle (prebuilt dist) + build-time dependency install, same
# layout as openclaw. Archful: @lydell/node-pty ships prebuilt Linux ELF
# prebuilds for the process-capture feature, so the payload is not noarch.
%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           rea-agents
Version:        6.7.0
Release:        1%{?dist}
Summary:        Reverse-engineering CLI and MCP server for AI agents

License: MIT
URL:            https://github.com/morluto/rea
Source0:        https://registry.npmjs.org/rea-agents/-/rea-agents-%{version}.tgz

ExclusiveArch:  x86_64 aarch64

BuildRequires:  nodejs24
BuildRequires:  nodejs24-npm
Requires:       nodejs24

# env-node shebangs across the npm payload; the wrapper is the entrypoint
%define __brp_mangle_shebangs %{nil}

%description
REA (Reverse Engineer Anything) is one CLI and MCP server that lets agents
inspect native binaries, JavaScript and Electron apps, .NET assemblies and
websites, with evidence-backed results. Analysis runs locally; native
analysis can use an existing Hopper, Ghidra, IDA or Kuna installation.

%prep
%autosetup -n package

%build
export npm_config_cache=%{_builddir}/.npm
# --ignore-scripts: prebuilt payloads only; frida (root optionalDependency)
# is nonfunctional without its network install script and rea treats it as
# optional, so drop it after the install
%{_bindir}/npm-24 install --omit=dev --ignore-scripts --os=linux \
    --no-audit --no-fund
rm -rf node_modules/frida

# Windows-only native payload from the npm tarball
rm -f native/windows/build/rea-windows-x64.node
# foreign-platform leftovers, if any
for plat in darwin-arm64 darwin-x64 win32-arm64 win32-x64 linux-ia32; do
    find node_modules -type d -name "$plat" -exec rm -rf {} +
done

%install
install -d -m755 %{buildroot}%{_prefix}/lib/node_modules/%{name}
cp -a . %{buildroot}%{_prefix}/lib/node_modules/%{name}/

for b in rea rea-agents; do
    install -Dpm755 /dev/null %{buildroot}%{_bindir}/$b
    cat > %{buildroot}%{_bindir}/$b <<'EOF'
#!/bin/sh
exec /usr/bin/node-24 %{_prefix}/lib/node_modules/rea-agents/scripts/rea.mjs "$@"
EOF
done

%check
# Scratch HOME: first run writes user-level state
HOME=%{_builddir} %{_bindir}/node-24 scripts/rea.mjs --version
HOME=%{_builddir} %{_bindir}/node-24 scripts/rea.mjs --help >/dev/null

%files
%license LICENSE
%doc README.md DISCLAIMER.md
%{_bindir}/rea
%{_bindir}/rea-agents
%{_prefix}/lib/node_modules/%{name}/

%changelog
* Wed Oct 21 2026 Caio Bruno <cbrunofb@gmail.com> - 6.7.0-1
- Initial package
