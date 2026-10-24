# Wallpaper collection (D3Ext style): a flat images/ payload installed once
# into backgrounds/, with all DE picker entries pointing there — GNOME,
# Cinnamon and MATE through a gnome-background-properties XML, Plasma through
# a kpackage (metadata.json + per-file links in contents/images). Upstream
# collections usually have no tags/releases: the spec pins a commit snapshot
# (same reasoning as unimatrix); when an upstream does tag, switch Source0 to
# tag form and keep Version in sync.
%global commit __COMMIT__

Name:           __NAME__
Version:        __VERSION__
Release:        1.__SNAPSHOT__git%{?dist}
Summary:        __SUMMARY__
BuildArch:      noarch

License:        __LICENSE__
URL:            __URL__
Source0:        %{url}/archive/%{commit}/%{name}-%{commit}.tar.gz

%description
__SUMMARY__

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
# per-file links inside contents/images avoid duplicating the payload;
# no metadata screenshot file needed.
kpkg=%{buildroot}%{_datadir}/wallpapers/%{name}/contents/images
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
                "Name": "Upstream authors"
            }
        ],
        "Id": "Wallpapers",
        "Name": "Wallpapers"
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
%license __LICENSEFILE__
%{_datadir}/backgrounds/%{name}/
%{_datadir}/gnome-background-properties/%{name}.xml
%{_datadir}/wallpapers/%{name}/

%changelog
* __DATE__ __PACKAGER__ - __VERSION__-1.__SNAPSHOT__git
- Initial package (commit snapshot)
