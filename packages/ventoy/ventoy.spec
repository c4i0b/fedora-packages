# Upstream source build is impractical (cross grub/edk2 + root image steps)
%define debug_package %{nil}
# Bundle ships 32-bit ELFs whose sonames must not leak into requires
%global __requires_exclude_from ^/opt/ventoy/.*$
%global __provides_exclude_from ^/opt/ventoy/.*$
%global __strip /bin/true

ExclusiveArch:  x86_64

Name:           ventoy
Version:        1.1.18
Release:        1%{?dist}
Summary:        A new bootable USB solution

License:        GPL-3.0-or-later
URL:            https://www.ventoy.net
Source0:        https://github.com/ventoy/Ventoy/releases/download/v%{version}/ventoy-%{version}-linux.tar.gz
Source1:        https://raw.githubusercontent.com/ventoy/Ventoy/v%{version}/COPYING

BuildRequires:  desktop-file-utils

Requires:       bash
Requires:       dosfstools
Recommends:     parted
Recommends:     polkit

%description
Ventoy is an open source tool to create bootable USB drive for ISO/WIM/IMG/VHD(x)/EFI files.
You need to copy the ISO/WIM/IMG/VHD(x)/EFI files to the USB drive and boot from it.

%prep
%setup -T -q -b 0 -n ventoy-%{version}

%build

%install
install -d %{buildroot}/opt/ventoy
cp -a . %{buildroot}/opt/ventoy/
rm -f %{buildroot}/opt/ventoy/VentoyGUI.{aarch64,i386,mips64el}

install -d %{buildroot}%{_bindir}
for cmd in Ventoy2Disk VentoyWeb VentoyPlugson; do
  cat > %{buildroot}%{_bindir}/$(echo $cmd | tr 'A-Z' 'a-z') <<EOF
#!/bin/sh
cd /opt/ventoy || exit 1
exec ./$cmd.sh "\$@"
EOF
done
cat > %{buildroot}%{_bindir}/ventoygui <<EOF
#!/bin/sh
cd /opt/ventoy || exit 1
exec ./VentoyGUI.x86_64 "\$@"
EOF
cat > %{buildroot}%{_bindir}/ventoy-persistent <<EOF
#!/bin/sh
exec /opt/ventoy/CreatePersistentImg.sh "\$@"
EOF
cat > %{buildroot}%{_bindir}/ventoy-extend-persistent <<EOF
#!/bin/sh
exec /opt/ventoy/ExtendPersistentImg.sh "\$@"
EOF
chmod 755 %{buildroot}%{_bindir}/*

install -d %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_datadir}/applications/ventoy.desktop <<EOF
[Desktop Entry]
Type=Application
Icon=ventoy
Name=Ventoy
Exec=ventoygui --xdg
Terminal=false
Categories=Utility;
Comment=Ventoy2Disk GUI
EOF

install -Dpm644 WebUI/static/img/VentoyLogo.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/ventoy.png

install -pm644 %{SOURCE1} COPYING

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/ventoy.desktop

%files
%license COPYING
/opt/ventoy/
%{_bindir}/ventoy2disk
%{_bindir}/ventoygui
%{_bindir}/ventoyweb
%{_bindir}/ventoyplugson
%{_bindir}/ventoy-persistent
%{_bindir}/ventoy-extend-persistent
%{_datadir}/applications/ventoy.desktop
%{_datadir}/icons/hicolor/512x512/apps/ventoy.png

%changelog
* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 1.1.18-1
- Initial package
