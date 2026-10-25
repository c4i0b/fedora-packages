# Electron payload: stripping corrupts the embedded snapshot; rpm 6 also
# fails on the empty debugsource list — see AGENTS.md
%define debug_package %{nil}
%global __strip /bin/true

# Bundled Electron must not leak into rpm provides/requires
%global __provides_exclude_from ^%{_prefix}/lib/desktop-plus/.*$
%global __requires_exclude_from ^%{_prefix}/lib/desktop-plus/.*$

ExclusiveArch:  x86_64 aarch64

Name:           desktop-plus
Version:        3.6.8.1
Release:        1%{?dist}
Summary:        A GitHub Desktop fork with advanced functionality and improvements

License:        MIT
URL:            https://desktop-plus.org
Source0:        https://github.com/desktop-plus/desktop-plus/releases/download/v%{version}/DesktopPlus-v%{version}-linux-x86_64.rpm
Source1:        https://github.com/desktop-plus/desktop-plus/releases/download/v%{version}/DesktopPlus-v%{version}-linux-arm64.rpm
Source2:        org.desktop-plus.DesktopPlus.metainfo.xml

BuildRequires:  bsdtar
BuildRequires:  desktop-file-utils

Requires:       git
Requires:       gtk3
Requires:       nss
Requires:       libsecret
Recommends:     (gnome-keyring or kf6-kwallet)

%description
Desktop Plus is a community fork of GitHub Desktop with additional features:
commit search, multi-account support (GitHub, Bitbucket, GitLab, Codeberg),
commit graph, multiple stashes per branch, and more.

%prep
%setup -T -q -c
%ifarch x86_64
bsdtar -xf %{SOURCE0}
%else
bsdtar -xf %{SOURCE1}
%endif

%build

%install
cp -a usr %{buildroot}/
appdir=%{buildroot}%{_prefix}/lib/desktop-plus
rm -f "$appdir"/chrome-sandbox
# Upstream links libcurl-gnutls (Debian-built Electron); retarget to Fedora's
find "$appdir" -type f -executable -exec \
  sed -i 's/libcurl-gnutls\.so\.4/libcurl.so.4\x00\x00\x00\x00\x00\x00\x00/g' {} \;
chmod 0755 "$appdir"/resources/app/static/desktop-plus-cli
ln -sf %{_prefix}/lib/desktop-plus/resources/app/static/desktop-plus-cli \
  %{buildroot}%{_bindir}/desktop-plus-cli
rm -f %{buildroot}%{_datadir}/doc/desktop-plus/copyright

install -Dpm644 %{SOURCE2} %{buildroot}%{_metainfodir}/org.desktop-plus.DesktopPlus.metainfo.xml

# Upstream desktop file uses an unregistered Category; sanitize it
sed -i 's/^Categories=.*/Categories=Development;X-GitHub;/' \
  %{buildroot}%{_datadir}/applications/*.desktop
install -pm644 "$appdir"/LICENSE . 2>/dev/null || install -pm644 usr/share/doc/desktop-plus/copyright COPYING

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%files
%license LICENSE
%{_bindir}/desktop-plus
%{_bindir}/desktop-plus-cli
%{_prefix}/lib/desktop-plus/
%{_datadir}/applications/*.desktop
%{_datadir}/icons/hicolor/*/apps/*.png
%{_metainfodir}/org.desktop-plus.DesktopPlus.metainfo.xml

%changelog
* Sun Oct 25 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 3.6.8.1-1
- Update to 3.6.8.1

* Tue Oct 20 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 3.6.8.0-1
- Update to 3.6.8.0

* Sat Oct 17 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 3.6.7.2-1
- Update to 3.6.7.2

* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 3.6.7.1-1
- Initial package
