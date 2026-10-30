Name:           quiver-launcher
Version:        3.5.1
Release:        1%{?dist}
Summary:        Launcher for downloading and playing static recompilation ports of classic games

License:        MIT
URL:            https://github.com/tgeorgiadis/quiver-launcher
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        quiver-launcher.wrapper

# Published framework-dependent: on Fedora the patched dotnet10.0 is used
# (MS binaries cannot run against rawhide's OpenSSL 4); EPEL has no dotnet
# package, so the dotnet-msft repack provides the toolchain there
%if 0%{?fedora}
BuildRequires:  dotnet-sdk-10.0
%else
BuildRequires:  dotnet-sdk-10.0-msft
%endif

# Avalonia app published self-contained: every installed ELF is prebuilt
# (Microsoft runtime, NuGet native assets) — no debuginfo to collect and
# stripping prebuilt .NET runtime libraries corrupts them
%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0
%global __strip /bin/true

BuildRequires:  curl
BuildRequires:  desktop-file-utils
BuildRequires:  libicu
BuildRequires:  tar

# Avalonia's X11/OpenGL backend P/Invokes these at runtime: invisible to rpm
# autoreq (no DT_NEEDED on our apphost)
Requires:       libX11
Requires:       libXcursor
Requires:       libXext
Requires:       libICE
Requires:       libXi
Requires:       libSM
Requires:       libXrandr
Requires:       libglvnd
Requires:       dbus-libs
Requires:       libicu
%if 0%{?fedora}
Requires:       dotnet-runtime-10.0
%else
Requires:       dotnet-runtime-10.0-msft
%endif
# optional backends/integration Avalonia probes at runtime
Recommends:     vulkan-loader
Recommends:     gtk3
# Quiver launches Windows-only recomp ports through Wine when the release
# ships no native Linux asset; EPEL has no wine (RPM Fusion only), so keep it
# soft or the package becomes uninstallable there
Recommends:     wine

%description
Quiver Launcher is a launcher for static recompilation and decompilation ports
of classic games. It downloads, installs, updates and runs those ports, with a
personal library, a community catalog, tag filtering, Windows-asset support
via Wine/Proton and mod management (Thunderstore, GameBanana).

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

dotnet publish QuiverLauncher.Desktop/QuiverLauncher.Desktop.csproj \
    -c Release --self-contained false \
    -p:PublishTrimmed=false -p:PublishSingleFile=false \
    -o publish

%install
install -Dm755 %{SOURCE1} %{buildroot}%{_bindir}/quiver-launcher
install -d %{buildroot}%{_libdir}/quiver-launcher
cp -a publish/. %{buildroot}%{_libdir}/quiver-launcher/

install -Dm644 packaging/flatpak/io.github.tgeorgiadis.QuiverLauncher.desktop \
    %{buildroot}%{_datadir}/applications/io.github.tgeorgiadis.QuiverLauncher.desktop
install -Dm644 packaging/flatpak/io.github.tgeorgiadis.QuiverLauncher.metainfo.xml \
    %{buildroot}%{_datadir}/metainfo/io.github.tgeorgiadis.QuiverLauncher.metainfo.xml
install -Dm644 Assets/quiver-icon.png \
    %{buildroot}%{_iconsdir}/hicolor/256x256/apps/io.github.tgeorgiadis.QuiverLauncher.png

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%files
%license LICENSE
%doc README.md
%{_bindir}/quiver-launcher
%{_libdir}/quiver-launcher/
%{_datadir}/applications/*.desktop
%{_datadir}/metainfo/*.metainfo.xml
%{_iconsdir}/hicolor/256x256/apps/*.png

%changelog
* Fri Oct 30 2026 Caio Bruno <cbrunofb@gmail.com> - 3.5.1-1
- Initial package
