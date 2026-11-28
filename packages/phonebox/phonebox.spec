Name:           phonebox
Version:        0.9.32
Release:        1%{?dist}
Summary:        Desktop agent that turns an old Android phone into a desk panel and touch control deck

License:        MIT
URL:            https://github.com/ersinkoc/phonebox
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
ExclusiveArch:  x86_64 aarch64

# not %{_userunitdir}: that macro needs systemd-rpm-macros in the buildroot
%global userunitdir %{_prefix}/lib/systemd/user

# Fedora ships the SDK; EPEL does not — the dotnet-msft repack provides it
# there (MS binaries link OpenSSL 3 and never run against rawhide)
%if 0%{?fedora}
BuildRequires:  dotnet-sdk-10.0
%else
BuildRequires:  dotnet-sdk-10.0-msft
%endif

# managed-only payload on Linux (QRCoder has no native assets), but the same
# dotnet rules apply: no debuginfo to collect, stripping corrupts the runtime
%global debug_package %{nil}
%global __strip /bin/true
%global _missing_build_ids_terminate_build 0

# The Linux agent is headless (settings live in the browser at
# http://127.0.0.1:8765; InvariantGlobalization=true needs no libicu), so
# besides the runtime there are no ELF/P/Invoke deps of our own
%if 0%{?fedora}
Requires:       dotnet-runtime-10.0
%else
Requires:       dotnet-runtime-10.0-msft
%endif
# Helper tools the agent shells out to when present (see upstream setup.sh):
# adb for USB, wpctl/playerctl for media and volume, xprintidle for X11 idle
Recommends:     android-tools
Recommends:     pipewire-utils
Recommends:     playerctl
Recommends:     xprintidle

%description
PhoneBox pairs a full-screen Android app with this small desktop agent: PC
stats, AI coding sessions, music and touch controls over USB or paired Wi-Fi.
Build the panel in a browser-based visual editor with 124 widgets and 30
templates. No root, PhoneBox account or cloud service required. This package
ships the agent only; the Android app is installed from the phone over USB or
from the upstream releases.

%prep
%autosetup -n %{name}-%{version} -p1

%build
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
%if 0%{?fedora}
export DOTNET_ROOT=%{_libdir}/dotnet
%else
export DOTNET_ROOT=%{_libdir}/dotnet-msft
%endif
export PATH="$DOTNET_ROOT:$PATH"

# net10.0 target only on Linux (the windows TFM needs targeting packs);
# the csproj embeds the panel assets from android/ so the full tarball is used
dotnet publish agent/PhoneBox.Agent/PhoneBox.Agent.csproj \
    -f net10.0 -c Release --self-contained false \
    -p:PublishTrimmed=false -p:PublishSingleFile=false \
    -o publish

%ifarch x86_64
%global rid linux-x64
%else
%global rid linux-arm64
%endif

%install
# NuGet native assets ship one runtimes/<rid> tree per target rid (musl,
# win, android...) whose sonames nothing provides: keep only the build arch
if [ -d publish/runtimes ]; then
  find publish/runtimes -mindepth 1 -maxdepth 1 -type d \
      ! -name '%{rid}' -exec rm -rf {} +
fi
install -d %{buildroot}%{_libdir}/%{name}
cp -a publish/. %{buildroot}%{_libdir}/%{name}/

# wrapper generated here on purpose: rpm does not expand macros in Source
# files, while in this heredoc they do expand (see packaging/general.md)
install -Dpm755 /dev/null %{buildroot}%{_bindir}/%{name}
cat > %{buildroot}%{_bindir}/%{name} <<'EOF'
#!/bin/sh
exec %{_libdir}/phonebox/PhoneBoxAgent "$@"
EOF

# Upstream autostart runs a user systemd unit named phonebox.service; ship
# the same unit (not enabled: the user opts in with
# `systemctl --user enable --now phonebox`)
install -Dpm644 /dev/null %{buildroot}%{userunitdir}/phonebox.service
cat > %{buildroot}%{userunitdir}/phonebox.service <<'EOF'
[Unit]
Description=PhoneBox desktop agent

[Service]
ExecStart=%{_libdir}/phonebox/PhoneBoxAgent
Restart=on-failure

[Install]
WantedBy=default.target
EOF

%files
%license LICENSE
%doc README.md
%{_bindir}/%{name}
%{_libdir}/%{name}/
%{userunitdir}/phonebox.service

%changelog
* Sat Nov 28 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.9.32-1
- Update to 0.9.32

* Fri Nov 27 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.9.31-1
- Update to 0.9.31

* Thu Nov 26 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.9.30-1
- Update to 0.9.30

* Wed Nov 25 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.9.29-1
- Update to 0.9.29

* Sun Nov 22 2026 Caio Bruno <cbrunofb@gmail.com> - 0.9.27-1
- Initial package
