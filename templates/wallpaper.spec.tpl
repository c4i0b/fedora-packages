# Wallpaper collection: a flat images/ payload installed once into
# backgrounds/, with all DE picker entries pointing there — GNOME, Cinnamon
# and MATE through a gnome-background-properties XML, Plasma through one
# kpackage per image (as plasma-workspace-wallpapers does). Upstream
# collections usually have no tags/releases: the spec pins a commit snapshot
# (same reasoning as unimatrix); when an upstream does tag, switch Source0 to
# tag form and keep Version in sync.
%global commit __COMMIT__

Name:           __NAME__
Version:        __VERSION__
Release:        1.__SNAPSHOT__git%{?dist}
Summary:        __SUMMARY__
BuildArch:      noarch
BuildRequires:  python3

License:        __LICENSE__
URL:            __URL__
Source0:        %{url}/archive/%{commit}/%{name}-%{commit}.tar.gz

%description
__SUMMARY__, installed in the layout desktop environments expect:
- %%{_datadir}/backgrounds/%{name}/ (raw path usable by every DE and picker
  wrappers like azote or nitrogen)
- a gnome-background-properties XML, so GNOME, Cinnamon and MATE list every
  image in their built-in wallpaper chooser
- one Plasma kpackage per image under %%{_datadir}/wallpapers, as
  plasma-workspace-wallpapers does, so every card shows a working preview
Portrait (phone-sized) images are skipped.

%prep
%setup -q -n %{name}-%{commit}
rm -f images/.gitkeep

%build

%install
# Every desktop entry is driven by one python listing of the landscape
# (published) wallpapers: raw footprint, GNOME XML and KDE kpackages

# GNOME, Cinnamon and MATE discover wallpapers through
# gnome-background-properties XML listings only; the file is opened here and
# closed by the </wallpapers> line appended after the listing loop
mkdir -p %{buildroot}%{_datadir}/gnome-background-properties
{
  echo '<?xml version="1.0" encoding="UTF-8"?>'
  echo '<!DOCTYPE wallpapers SYSTEM "gnome-wp-list.dtd">'
  echo '<wallpapers>'
} > %{buildroot}%{_datadir}/gnome-background-properties/%{name}.xml

# Raw footprint: the images land once and every DE entry points at them
mkdir -p %{buildroot}%{_datadir}/backgrounds/%{name}

# Plasma discovers wallpaper collections only under wallpapers/ as kpackages,
# one per image (plasma-workspace-wallpapers ships Altai, Autumn, ... that
# way). It picks the card preview and the applied image by a WxH-encoded
# filename, so every link is named with the image's real resolution, sniffed
# from file headers (upstreams sometimes mislabel extensions).
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
    # portrait images are phone-sized (1080x2340, ...): skip them so every
    # consumer (raw footprint, GNOME XML, KDE kpackages) filters in one place
    if wh[1] > wh[0]:
        continue
    print(f'{p.stem}|{ext}|{wh[0]}x{wh[1]}')
PY
  install -m644 "images/${stem}.${ext}" \
    %{buildroot}%{_datadir}/backgrounds/%{name}/
  printf '    <wallpaper deleted="false">\n        <name>%s</name>\n        <filename>%s/backgrounds/%s/%s</filename>\n        <options>zoom</options>\n        <shade_type>solid</shade_type>\n    </wallpaper>\n' \
    "$(echo "$stem" | sed 's/[-_]/ /g')" '%{_datadir}' '%{name}' "${stem}.${ext}" \
    >> %{buildroot}%{_datadir}/gnome-background-properties/%{name}.xml
  # images -> contents -> <stem> -> <name> -> wallpapers -> share, then backgrounds
  kpkg=%{buildroot}%{_datadir}/wallpapers/%{name}/${stem}/contents/images
  mkdir -p "$kpkg"
  ln -s "../../../../../backgrounds/%{name}/${stem}.${ext}" "$kpkg/${wh}.${ext}"
  {
    echo '{'
    echo '    "KPlugin": {'
    echo '        "Authors": ['
    echo '            {'
    echo '                "Name": "__AUTHOR__"'
    echo '            }'
    echo '        ],'
    echo "        \"Id\": \"${stem}\","
    echo '        "License": "__LICENSE__",'
    echo "        \"Name\": \"$(echo "$stem" | sed 's/[-_]/ /g')\""
    echo '    }'
    echo '}'
  } > "$kpkg/../../metadata.json"
done
echo '</wallpapers>' >> %{buildroot}%{_datadir}/gnome-background-properties/%{name}.xml

%check
# the generated discovery data must cover exactly what got published
# (scriptlets do not share variables: paths must be recomputed here; the
# portrait skip makes the published count differ from the raw images/)
bgc=$(find %{buildroot}%{_datadir}/backgrounds/%{name} -type f | wc -l)
xmlc=$(grep -c '<wallpaper ' \
  %{buildroot}%{_datadir}/gnome-background-properties/%{name}.xml)
kroot=%{buildroot}%{_datadir}/wallpapers/%{name}
pkgs=$(find "$kroot" -name metadata.json | wc -l)
links=$(find "$kroot" -type l | wc -l)
# link filenames must encode a resolution (KDE picks the preview by it)
badres=$(find "$kroot" -type l | awk -F/ '$NF !~ /[0-9]+x[0-9]+\./' | wc -l)
dangling=$(find "$kroot" -type l ! -exec test -e {} \; -print | wc -l)
if [ "$bgc" -eq "$xmlc" ] && [ "$bgc" -eq "$pkgs" ] && \
   [ "$bgc" -eq "$links" ] && [ "$dangling" -eq 0 ] && [ "$badres" -eq 0 ]; then
  :
else
  echo "inconsistent discovery data: bg=$bgc xml=$xmlc pkgs=$pkgs links=$links dangling=$dangling badres=$badres" >&2
  exit 1
fi

%files
%license __LICENSEFILE__
%{_datadir}/backgrounds/%{name}/
%{_datadir}/gnome-background-properties/%{name}.xml
%{_datadir}/wallpapers/%{name}/

%changelog
* __DATE__ __PACKAGER__ - __VERSION__-1.__SNAPSHOT__git
- Initial package (commit snapshot)
