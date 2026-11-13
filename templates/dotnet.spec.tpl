Name:           __NAME__
Version:        __VERSION__
Release:        1%{?dist}
Summary:        __SUMMARY__

License:        __LICENSE__
URL:            __URL__
Source0:        __SOURCE0__
ExclusiveArch:  x86_64 aarch64

# Fedora ships the SDK; EPEL does not — the dotnet-msft repack provides it
# there (MS binaries link OpenSSL 3 and never run against rawhide)
%if 0%{?fedora}
BuildRequires:  dotnet-sdk-10.0
%else
BuildRequires:  dotnet-sdk-10.0-msft
%endif

# prebuilt payload (MS runtime, NuGet natives): no debuginfo to collect,
# stripping corrupts the .NET runtime libraries; on rpm < 4.20/EPEL the
# missing build-id note aborts the build without the third global
%global debug_package %{nil}
%global __strip /bin/true
%global _missing_build_ids_terminate_build 0

# P/Invoke-only runtime deps: invisible to rpm autoreq (no DT_NEEDED on the
# apphost) — re-check the set on UI-stack major bumps (Avalonia X11/OpenGL)
Requires:       libX11
Requires:       libXcursor
Requires:       libXi
Requires:       libXrandr
Requires:       libglvnd
Requires:       libicu
%if 0%{?fedora}
Requires:       dotnet-runtime-10.0
%else
Requires:       dotnet-runtime-10.0-msft
%endif

%description
__SUMMARY__

%prep
%autosetup -p1

%build
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
%if 0%{?fedora}
export DOTNET_ROOT=%{_libdir}/dotnet
%else
export DOTNET_ROOT=%{_libdir}/dotnet-msft
%endif
export PATH="$DOTNET_ROOT:$PATH"

dotnet publish -c Release --self-contained false \
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
find publish/runtimes -mindepth 1 -maxdepth 1 -type d \
    ! -name '%{rid}' -exec rm -rf {} +
install -d %{buildroot}%{_libdir}/%{name}
cp -a publish/. %{buildroot}%{_libdir}/%{name}/

# wrapper generated here on purpose: rpm does not expand macros in Source
# files, while in this heredoc they do expand (see packaging/general.md)
install -Dpm755 /dev/null %{buildroot}%{_bindir}/%{name}
cat > %{buildroot}%{_bindir}/%{name} <<'EOF'
#!/bin/sh
exec %{_libdir}/__NAME__/__NAME__ "$@"
EOF

%files
%license __LICENSEFILE__
%doc README.md
%{_bindir}/%{name}
%{_libdir}/%{name}/

%changelog
* __DATE__ __PACKAGER__ - __VERSION__-1
- Initial package
