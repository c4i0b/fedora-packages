# Upstream has no tags/releases (checked 2026-10): pinned commit snapshot,
# autoupdate tracker intentionally absent (same reasoning as unimatrix).
%global commit e34f05935c5b768f4c016b0893924d18ec1dba61

Name:           aesthetic-wallpapers
Version:        2025.06.17
Release:        1.20261024git%{?dist}
Summary:        D3Ext collection of aesthetic wallpapers

License:        MIT
URL:            https://github.com/D3Ext/aesthetic-wallpapers
Source0:        %{url}/archive/%{commit}/%{name}-%{commit}.tar.gz

BuildArch:      noarch

%description
Almost 400 aesthetic wallpapers (anime, landscapes, abstract) curated by D3Ext,
installed in the layout desktop environments expect:
- %%{_datadir}/backgrounds/aesthetic-wallpapers/ (raw path usable by every DE
  and picker wrappers like azote or nitrogen)
- a gnome-background-properties XML, so GNOME, Cinnamon and MATE list every
  image in their built-in wallpaper chooser
- a KDE kpackage under %%{_datadir}/wallpapers, so Plasma's chooser lists the
  collection too

%prep
%setup -q -n %{name}-%{commit}
rm -f images/.gitkeep

%build

%install
# Raw footprint: the images land once and every DE entry points at them
mkdir -p %{buildroot}%{_datadir}/backgrounds/%{name}
install -m644 images/* %{buildroot}%{_datadir}/backgrounds/%{name}/

# GNOME, Cinnamon and MATE discover wallpapers through
# gnome-background-properties XML listings only
mkdir -p %{buildroot}%{_datadir}/gnome-background-properties
{
  echo '<?xml version="1.0" encoding="UTF-8"?>'
  echo '<!DOCTYPE wallpapers SYSTEM "gnome-wp-list.dtd">'
  echo '<wallpapers>'
  for img in images/*; do
    base="$(basename "$img")"
    label="$(echo "$base" | sed 's/\.[^.]*$//; s/[-_]/ /g')"
    printf '    <wallpaper deleted="false">\n        <name>%s</name>\n        <filename>%s/backgrounds/%s/%s</filename>\n        <options>zoom</options>\n        <shade_type>solid</shade_type>\n    </wallpaper>\n' \
      "$label" '%{_datadir}' '%{name}' "$base"
  done
  echo '</wallpapers>'
} > %{buildroot}%{_datadir}/gnome-background-properties/%{name}.xml

# Plasma discovers wallpaper collections only under wallpapers/ as kpackages:
# per-file links inside contents/images avoid duplicating 650 MB of payload;
# no metadata screenshot file needed.
kpkg=%{buildroot}%{_datadir}/wallpapers/AestheticWallpapers/contents/images
mkdir -p "$kpkg"
for img in images/*; do
  ln -s "../../../../backgrounds/%{name}/$(basename "$img")" "$kpkg/$(basename "$img")"
done
# One level above contents/, as the Fedora wallpaper kpackages ship it
cat > "$kpkg/../../metadata.json" <<'EOF'
{
    "KPlugin": {
        "Authors": [
            {
                "Name": "D3Ext"
            }
        ],
        "Id": "AestheticWallpapers",
        "Name": "Aesthetic Wallpapers"
    }
}
EOF

%check
# the generated discovery data must cover exactly what got installed
imgs=$(find images -type f | wc -l)
xmlc=$(grep -c '<wallpaper ' \
  %{buildroot}%{_datadir}/gnome-background-properties/%{name}.xml)
links=$(find "$kpkg" -type l | wc -l)
dangling=0
for sym in "$kpkg"/*; do
  test -e "$sym" || dangling=$((dangling + 1))
done
test "$imgs" -eq "$xmlc" -a "$imgs" -eq "$links" -a "$dangling" -eq 0

%files
%license LICENSE
%doc README.md
%{_datadir}/backgrounds/%{name}/
%{_datadir}/gnome-background-properties/%{name}.xml
%{_datadir}/wallpapers/AestheticWallpapers/

%changelog
* Sat Oct 24 2026 Caio Bruno <cbrunofb@gmail.com> - 2025.06.17-1.20261024git
- Initial package (commit e34f059, 388 wallpapers)
