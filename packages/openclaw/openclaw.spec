# Same packaging as Fedora rawhide's openclaw (npm tarball, /usr/lib layout):
# this COPR copy only exists to be newer and to cover stable/EPEL chroots
Name:           openclaw
Version:        2026.10.5
Release:        1%{?dist}
Summary:        OpenClaw CLI, a personal AI assistant (npm bundle)

License:        MIT
URL:            https://github.com/openclaw/openclaw
Source0:        https://registry.npmjs.org/openclaw/-/openclaw-%{version}.tgz

BuildArch:      noarch

Requires:       nodejs24
BuildRequires:  nodejs24
BuildRequires:  nodejs24-npm

# The npm tarball is not self-contained; remaining deps install at build time.
# env-node shebangs would be mangled to nonexistent /usr/bin/node — skip that BRP.
%define __brp_mangle_shebangs %{nil}

%description
OpenClaw is a personal AI assistant you run on your own devices: one agent,
persistent memory, and the channels you already use. This package ships the
official npm bundle with the openclaw CLI.

%prep
%autosetup -n package

%build
# --legacy-peer-deps: mistralai pins a conflicting peerOptional; --omit=optional
# drops the arch-specific fs-safe native addon (noarch)
export npm_config_cache=%{_builddir}/.npm
%{_bindir}/npm-24 install --omit=dev --omit=optional --ignore-scripts \
    --no-audit --no-fund --legacy-peer-deps

# Complete the postinstall lifecycle marker in-tree so users never trigger it
HOME=%{_builddir} OPENCLAW_FS_SAFE_NATIVE_MODE=off \
    %{_bindir}/node-24 ./openclaw.mjs --version

%install
install -d -m755 %{buildroot}%{_prefix}/lib/node_modules/openclaw
cp -a . %{buildroot}%{_prefix}/lib/node_modules/openclaw/

# Upstream tree ships arch payloads: prebuilt binaries in skills/, wasm and
# per-platform dirs in node_modules; drop them all to keep the payload noarch
# (same hygiene as the Fedora rawhide package)
find %{buildroot}%{_prefix}/lib/node_modules/openclaw -type f \
    -exec sh -c 'file -b "$1" | grep -qE "ELF|Mach-O|PE32|WebAssembly" && rm -f "$1"' _ {} \;
for plat in linux-arm64 linux-x64 linux-ia32 darwin-arm64 darwin-x64 win32-arm64 win32-x64; do
    find %{buildroot}%{_prefix}/lib/node_modules/openclaw -type d -name "$plat" \
        -exec rm -rf {} +
done

install -Dpm755 /dev/null %{buildroot}%{_bindir}/openclaw
cat > %{buildroot}%{_bindir}/openclaw <<'EOF'
#!/bin/sh
exec /usr/bin/node-24 %{_prefix}/lib/node_modules/openclaw/openclaw.mjs "$@"
EOF

%check
# Invoke node-24 directly: the wrapper hardcodes the installed path
HOME=%{_builddir} OPENCLAW_FS_SAFE_NATIVE_MODE=off \
    %{_bindir}/node-24 \
    %{buildroot}%{_prefix}/lib/node_modules/openclaw/openclaw.mjs --version

%files
%license LICENSE
%doc README.md
%{_bindir}/openclaw
%{_prefix}/lib/node_modules/openclaw/

%changelog
* Sun Oct 18 2026 Caio Bruno <cbrunofb@gmail.com> - 2026.10.5-1
- Update to 2026.10.5; rename to openclaw (was openclaw-bin): same
  packaging as the Fedora rawhide package, so it upgrades it cleanly
  instead of conflicting

* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 2026.10.4-1
- Initial package
