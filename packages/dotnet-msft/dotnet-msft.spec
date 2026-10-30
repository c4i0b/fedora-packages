# Repack of Microsoft's official .NET 10 SDK/runtime binaries, for chroots
# where Fedora's dotnet10.0 is unavailable (EPEL): a true source build needs
# a previous SDK to bootstrap and ~100 distro patches — not worth it here.
# MS binaries link OpenSSL 3 (libssl.so.3) and only run on EPEL; Fedora
# chroots ship the patched dotnet10.0 and should use that instead.
%global debug_package %{nil}
%global __strip /bin/true
# bundled runtime must not leak sonames into rpm provides/requires
%global __provides_exclude_from ^%{_libdir}/dotnet-msft/.*$
%global __requires_exclude_from ^%{_libdir}/dotnet-msft/.*$

ExclusiveArch:  x86_64 aarch64

Name:           dotnet-msft
Version:        10.0.403
Release:        1%{?dist}
Summary:        Microsoft .NET 10 SDK and runtime binaries (repack)

License:        MIT
URL:            https://dotnet.microsoft.com/download/dotnet/10.0
# one Source per arch: the SRPM builder chroot has an arbitrary architecture
Source0:        https://builds.dotnet.microsoft.com/dotnet/Sdk/%{version}/dotnet-sdk-%{version}-linux-x64.tar.gz
Source1:        https://builds.dotnet.microsoft.com/dotnet/Sdk/%{version}/dotnet-sdk-%{version}-linux-arm64.tar.gz

%description
Repack of Microsoft's official .NET 10 binaries, installing under
/usr/lib64/dotnet-msft with a dotnet-msft launcher. Intended for
distributions or chroots without a native dotnet10.0 package (EPEL):
the binaries link OpenSSL 3 and will not run against OpenSSL 4.
Updates are manual: pin the SDK feature-band version, the bundled runtime
ships inside the SDK tarball.

%package -n dotnet-runtime-10.0-msft
Summary:        Microsoft .NET 10 runtime binaries
Requires:       libicu

%description -n dotnet-runtime-10.0-msft
The .NET 10 runtime (Microsoft.NETCore.App) from Microsoft's official SDK
tarball, installed under /usr/lib64/dotnet-msft.

%package -n dotnet-sdk-10.0-msft
Summary:        Microsoft .NET 10 SDK binaries
Requires:       dotnet-runtime-10.0-msft = %{version}-%{release}

%description -n dotnet-sdk-10.0-msft
The .NET 10 SDK (compiler toolchain, packs, templates) from Microsoft's
official tarball. Requires the matching dotnet-runtime-10.0-msft.

%prep
%setup -T -q -c
%ifarch x86_64
tar xf %{SOURCE0}
%else
tar xf %{SOURCE1}
%endif

%build

%install
install -d %{buildroot}%{_libdir}/dotnet-msft
cp -a ./{dotnet,host,shared,packs,sdk,sdk-manifests,templates,dnx,LICENSE.txt,ThirdPartyNotices.txt} \
    %{buildroot}%{_libdir}/dotnet-msft/
install -d %{buildroot}%{_bindir}
ln -s %{_libdir}/dotnet-msft/dotnet %{buildroot}%{_bindir}/dotnet-msft

%files -n dotnet-runtime-10.0-msft
%license %{_libdir}/dotnet-msft/LICENSE.txt
%{_bindir}/dotnet-msft
%{_libdir}/dotnet-msft/dotnet
%{_libdir}/dotnet-msft/host/
%{_libdir}/dotnet-msft/shared/Microsoft.NETCore.App/

%files -n dotnet-sdk-10.0-msft
%{_libdir}/dotnet-msft/ThirdPartyNotices.txt
%{_libdir}/dotnet-msft/sdk/
%{_libdir}/dotnet-msft/sdk-manifests/
%{_libdir}/dotnet-msft/packs/
%{_libdir}/dotnet-msft/templates/
# dnx ships as a single launcher script, not a directory
%{_libdir}/dotnet-msft/dnx
%{_libdir}/dotnet-msft/shared/Microsoft.AspNetCore.App/

%changelog
* Fri Oct 30 2026 Caio Bruno <cbrunofb@gmail.com> - 10.0.403-1
- Initial package
