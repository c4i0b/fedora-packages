# Images install once into backgrounds/, every desktop entry points there.
# Upstream usually has no tagged releases: pin a commit snapshot (switch
# Source0 to tag form and keep Version in sync when upstream tags).
%global commit e34f05935c5b768f4c016b0893924d18ec1dba61

Name:           aesthetic-wallpapers
Version:        2025.06.17
Release:        1.20261024git%{?dist}
Summary:        D3Ext collection of aesthetic wallpapers
BuildArch:      noarch
BuildRequires:  python3

License:        MIT
URL:            https://github.com/D3Ext/aesthetic-wallpapers
Source0:        %{url}/archive/%{commit}/%{name}-%{commit}.tar.gz

%description
D3Ext collection of aesthetic wallpapers, installed in the layout desktop environments expect:
- %%{_datadir}/backgrounds/%{name}/ (raw path usable by every DE and picker
  wrappers like azote or nitrogen)
- chooser XMLs in gnome-, cinnamon- and mate-background-properties, so GNOME,
  Budgie, Cinnamon and MATE list every image in their built-in choosers
- one Plasma kpackage per image directly under %%{_datadir}/wallpapers
  (%%{name}-<image>/ as plasma-workspace-wallpapers does), so every card
  shows a working preview
- per-image symlinks under %%{_datadir}/xfce4/backdrops for xfdesktop
Portrait (phone-sized) images are skipped.

%prep
%setup -q -n %{name}-%{commit}
rm -f images/.gitkeep

%build

%install
# Choosers only list entries in their own dirs: GNOME/Budgie read
# gnome-background-properties, Cinnamon cinnamon-background-properties
# (cs_backgrounds.py scans that dir alone) and MATE
# mate-background-properties — never the raw backgrounds/ footprint
mkdir -p %{buildroot}%{_datadir}/gnome-background-properties \
  %{buildroot}%{_datadir}/cinnamon-background-properties \
  %{buildroot}%{_datadir}/mate-background-properties \
  %{buildroot}%{_datadir}/xfce4/backdrops
for dest in gnome-background-properties cinnamon-background-properties \
  mate-background-properties; do
  dtd=gnome-wp-list.dtd
  if [ "$dest" = mate-background-properties ]; then
    dtd=mate-wp-list.dtd
  fi
  {
    echo '<?xml version="1.0" encoding="UTF-8"?>'
    echo "<!DOCTYPE wallpapers SYSTEM \"$dtd\">"
    echo '<wallpapers>'
  } > %{buildroot}%{_datadir}/$dest/%{name}.xml
done

mkdir -p %{buildroot}%{_datadir}/backgrounds/%{name}

# Plasma only lists kpackages sitting directly under wallpapers/ (nested ones
# are skipped by packagefinder). Links are WxH-named because the chooser
# picks the preview by resolution; dims are sniffed from headers (upstreams
# mislabel extensions)
python3 - <<'PY' | while IFS='|' read -r stem ext wh; do
import re, struct, sys
from pathlib import Path


def dims_png(h):
    if h[12:16] != b'IHDR':
        return None
    return struct.unpack('>II', h[16:24])


def dims_gif(h):
    if not h.startswith(b'GIF8'):
        return None
    return struct.unpack('<HH', h[6:10])


def dims_webp(h):
    if h[8:12] != b'WEBP':
        return None
    if h[12:16] == b'VP8 ':
        w, hh = struct.unpack('<HH', h[26:30])
        return (w & 0x3FFF, hh & 0x3FFF)
    if h[12:16] == b'VP8L':
        if h[20] != 0x2F:
            return None
        bits = struct.unpack('<I', h[21:25])[0]
        return (1 + (bits & 0x3FFF), 1 + ((bits >> 14) & 0x3FFF))
    if h[12:16] == b'VP8X':
        return (int.from_bytes(h[24:27], 'little') + 1,
                int.from_bytes(h[27:30], 'little') + 1)
    return None


def dims_jpeg(b):
    # EXIF payloads break segment walking and embedded thumbnails add a
    # second small SOF: keep the largest sane match
    best = None
    for m in re.finditer(b'\xff[\xc0-\xc3\xc5-\xc7\xc9-\xcb\xcd-\xcf]', b):
        if m.end() + 7 > len(b):
            break
        hh, w = struct.unpack('>HH', b[m.end() + 3:m.end() + 7])
        if 64 < w < 16384 and 64 < hh < 16384:
            if best is None or w * hh > best[0] * best[1]:
                best = (w, hh)
    return best


def fmt(h):
    if h.startswith(b'\x89PNG'):
        return 'png'
    if h.startswith(b'\xff\xd8'):
        return 'jpeg'
    if h.startswith(b'GIF8'):
        return 'gif'
    if h[8:12] == b'WEBP':
        return 'webp'
    return None


PARSERS = {'png': dims_png, 'jpeg': dims_jpeg, 'gif': dims_gif, 'webp': dims_webp}

for p in sorted(Path('images').iterdir()):
    if p.is_dir() or p.name.startswith('.'):
        continue
    ext = p.suffix[1:].lower()
    h = p.open('rb').read(2 * 1024 * 1024)
    fn = PARSERS.get(fmt(h))
    try:
        wh = fn(h) if fn else None
    except Exception:
        wh = None
    if not wh or not (0 < wh[0] < 16384 and 0 < wh[1] < 16384):
        wh = (1920, 1080)
    # portrait = phone-sized: skipped once, for every consumer
    if wh[1] > wh[0]:
        continue
    print(f'{p.stem}|{ext}|{wh[0]}x{wh[1]}')
PY
  install -m644 "images/${stem}.${ext}" \
    %{buildroot}%{_datadir}/backgrounds/%{name}/
  for dest in gnome-background-properties cinnamon-background-properties \
    mate-background-properties; do
    printf '    <wallpaper deleted="false">\n        <name>%s</name>\n        <filename>%s/backgrounds/%s/%s</filename>\n        <options>zoom</options>\n        <shade_type>solid</shade_type>\n    </wallpaper>\n' \
      "$(echo "$stem" | sed 's/[-_]/ /g')" '%{_datadir}' '%{name}' "${stem}.${ext}" \
      >> %{buildroot}%{_datadir}/$dest/%{name}.xml
  done
  # xfdesktop lists whatever is in xfce4/backdrops; the symlink keeps the
  # payload single-copy
  ln -s "../../backgrounds/%{name}/${stem}.${ext}" \
    %{buildroot}%{_datadir}/xfce4/backdrops/%{name}-${stem}.${ext}
  kpkg=%{buildroot}%{_datadir}/wallpapers/%{name}-${stem}/contents/images
  mkdir -p "$kpkg"
  ln -s "../../../../backgrounds/%{name}/${stem}.${ext}" "$kpkg/${wh}.${ext}"
  {
    echo '{'
    echo '    "KPlugin": {'
    echo '        "Authors": ['
    echo '            {'
    echo '                "Name": "D3Ext"'
    echo '            }'
    echo '        ],'
    echo "        \"Id\": \"${stem}\","
    echo '        "License": "MIT",'
    echo "        \"Name\": \"$(echo "$stem" | sed 's/[-_]/ /g')\""
    echo '    }'
    echo '}'
  } > "$kpkg/../../metadata.json"
done
for dest in gnome-background-properties cinnamon-background-properties \
  mate-background-properties; do
  echo '</wallpapers>' >> %{buildroot}%{_datadir}/$dest/%{name}.xml
done

%check
# scriptlets do not share variables and the portrait skip shrinks the count
# below images/: recount everything here
bgc=$(find %{buildroot}%{_datadir}/backgrounds/%{name} -type f | wc -l)
gnomec=$(grep -c '<wallpaper ' \
  %{buildroot}%{_datadir}/gnome-background-properties/%{name}.xml)
cinnc=$(grep -c '<wallpaper ' \
  %{buildroot}%{_datadir}/cinnamon-background-properties/%{name}.xml)
matec=$(grep -c '<wallpaper ' \
  %{buildroot}%{_datadir}/mate-background-properties/%{name}.xml)
kroot=%{buildroot}%{_datadir}/wallpapers/%{name}-
pkgs=$(find "$kroot"* -name metadata.json | wc -l)
links=$(find "$kroot"* -type l | wc -l)
badres=$(find "$kroot"* -type l | awk -F/ '$NF !~ /[0-9]+x[0-9]+\./' | wc -l)
xfcel=$(find %{buildroot}%{_datadir}/xfce4/backdrops/%{name}-* -type l | wc -l)
dangling=$(find "$kroot"* %{buildroot}%{_datadir}/xfce4/backdrops \
  -type l ! -exec test -e {} \; -print | wc -l)
if [ "$bgc" -eq "$gnomec" ] && [ "$bgc" -eq "$cinnc" ] && \
   [ "$bgc" -eq "$matec" ] && [ "$bgc" -eq "$pkgs" ] && \
   [ "$bgc" -eq "$links" ] && [ "$bgc" -eq "$xfcel" ] && \
   [ "$dangling" -eq 0 ] && [ "$badres" -eq 0 ]; then
  :
else
  echo "inconsistent discovery data: bg=$bgc gnome=$gnomec cinnamon=$cinnc mate=$matec pkgs=$pkgs links=$links xfce=$xfcel dangling=$dangling badres=$badres" >&2
  exit 1
fi

%files
%license LICENSE
%doc README.md
%{_datadir}/backgrounds/%{name}/
%{_datadir}/gnome-background-properties/%{name}.xml
%{_datadir}/cinnamon-background-properties/%{name}.xml
%{_datadir}/mate-background-properties/%{name}.xml
%{_datadir}/xfce4/backdrops/%{name}-*
%{_datadir}/wallpapers/%{name}-*/

%changelog
* Sat Oct 24 2026 Caio Bruno <cbrunofb@gmail.com> - 2025.06.17-1.20261024git
- Initial package (commit snapshot)
