# Prebuilt vendor payload: rpm 6.1+ errors on the empty debugsource list that
# find-debuginfo emits for prebuilts — see AGENTS.md
%define debug_package %{nil}

# The bundle must not leak provides/requires: its bundled Qt/ICU/CEF sonames
# would resolve against nothing; every system lib it needs is declared below
%global __provides_exclude_from ^/opt/onlyoffice/.*$
%global __requires_exclude_from ^/opt/onlyoffice/.*$

ExclusiveArch:  x86_64 aarch64

Name:           onlyoffice-desktopeditors
Version:        10.0.0
Release:        1%{?dist}
Summary:        Offline office suite for documents, spreadsheets, presentations and PDFs

License:        AGPL-3.0-only
URL:            https://github.com/ONLYOFFICE/DesktopEditors
Source0:        %{url}/releases/download/v%{version}/onlyoffice-desktopeditors.x86_64.rpm
Source1:        %{url}/releases/download/v%{version}/onlyoffice-desktopeditors.aarch64.rpm

BuildRequires:  bsdtar
BuildRequires:  desktop-file-utils

# System libs the payload links against (ELF DT_NEEDED audit of v10.0.0);
# its Qt, ICU, CEF, hunspell and Vulkan are bundled and stay out of the deps
Requires:       gtk3
Requires:       alsa-lib
Requires:       cups-libs
Requires:       gstreamer1
Requires:       gstreamer1-plugins-base
Requires:       libglvnd-glx
Requires:       mesa-libgbm
Requires:       libSM
Requires:       libnotify
Requires:       libxcb
Requires:       libX11-xcb
Requires:       libXcomposite
Requires:       libXdamage
Requires:       libXext
Requires:       libXfixes
Requires:       libXi
Requires:       libXrandr
Requires:       libxkbcommon
Requires:       libxkbcommon-x11
Requires:       nss
Requires:       pulseaudio-libs
Requires:       xdg-utils
# Document rendering falls back to the system fonts family
Requires:       dejavu-fonts-all
Requires:       liberation-sans-fonts
Requires:       liberation-serif-fonts
Requires:       liberation-mono-fonts
Recommends:     gstreamer1-plugins-good

%description
ONLYOFFICE Desktop Editors: offline editor suite for documents, spreadsheets,
presentations and PDF forms, with DOCX/XLSX/PPTX round-trip fidelity. Ships
the prebuilt application bundle (with its own Qt, ICU, CEF and spellcheck
stack) under the upstream /opt/onlyoffice layout.

%prep
%setup -T -q -c
%ifarch x86_64
bsdtar -xf %{SOURCE0}
%else
bsdtar -xf %{SOURCE1}
%endif

%install
# Vendor ELFs keep upstream dev-machine rpaths (qt-5.9.9 build paths); the
# launcher resolves everything via LD_LIBRARY_PATH, so unused rpath entries
# are harmless — relax the brp rpath check for them
export QA_RPATHS=$(( 0x0001 | 0x0002 | 0x0008 | 0x0010 ))

# Keep the vendor /opt layout: upstream launch scripts carry the absolute
# bundle path (LD_LIBRARY_PATH + exec target are both /opt/onlyoffice-bound)
appdir=%{buildroot}/opt/onlyoffice/desktopeditors
install -d "$appdir"
cp -a opt/onlyoffice/desktopeditors/. "$appdir"/

# The launcher script also serves files via the new-document-templates hook
install -Dpm755 usr/bin/onlyoffice-desktopeditors \
  %{buildroot}%{_bindir}/onlyoffice-desktopeditors
ln -s onlyoffice-desktopeditors %{buildroot}%{_bindir}/desktopeditors

install -Dpm644 usr/share/applications/onlyoffice-desktopeditors.desktop \
  %{buildroot}%{_datadir}/applications/onlyoffice-desktopeditors.desktop
for png in usr/share/icons/hicolor/*/apps/onlyoffice-desktopeditors.png; do
  install -Dpm644 "$png" "%{buildroot}%{_datadir}/icons/hicolor/${png#*hicolor/}"
done

for lic in LICENSE 3DPARTYLICENSE LICENSE-CC.txt; do
  cp -p "usr/share/licenses/onlyoffice-desktopeditors/$lic" .
done

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%files
%license LICENSE 3DPARTYLICENSE LICENSE-CC.txt
%{_bindir}/onlyoffice-desktopeditors
%{_bindir}/desktopeditors
/opt/onlyoffice/desktopeditors/
%{_datadir}/applications/onlyoffice-desktopeditors.desktop
%{_datadir}/icons/hicolor/*/apps/onlyoffice-desktopeditors.png

%changelog
* Sat Oct 24 2026 Caio Bruno <cbrunofb@gmail.com> - 10.0.0-1
- Initial package
