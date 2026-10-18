Name:           hollywood
Version:        1.25
Release:        1%{?dist}
Summary:        Fill your console with Hollywood melodrama technobabble

License:        Apache-2.0
URL:            https://github.com/dustinkirkland/hollywood
Source0:        %{url}/archive/refs/tags/%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  ffmpeg-free
Requires:       bash
Requires:       tmux
Requires:       byobu
Requires:       util-linux
# Widget tools that exist on every chroot (Fedora + EPEL); ccze/jp2a/mpv come
# from this repo. cmatrix (no EPEL 10) and python3-pygments (EPEL: CRB only)
# stay Recommends so hollywood remains installable everywhere.
Requires:       apg atop bat bmon ccze figlet htop jp2a man-db moreutils
Requires:       mpv openssh-clients plocate pv tree
Recommends:     cmatrix python3-pygments

%package wallstreet
Summary:        Fill your console with Wall Street-like news and stats
Requires:       bash
Requires:       tmux
Requires:       byobu
Requires:       python3
Recommends:     caca-utils newsboat w3m wget

%description
This utility splits your terminal into multiple panes of genuine technobabble,
perfectly suitable for any Hollywood geek melodrama. It is particularly
suitable on any number of computer consoles in the background of any excellent
schlock technothriller.

%description wallstreet
This utility splits your terminal into multiple panes of news and statistics,
like any good computer screen on Wall Street.

%prep
%autosetup -n hollywood-%{version} -p1
# Fedora ships `bat`, not Debian's `batcat`
sed -i 's/batcat/bat/g' lib/hollywood/bat
# our mpv (ffmpeg-free build) replaces mplayer (RPM Fusion): null audio out
# and libcaca keep the widget silent and headless
sed -i 's/^command -v mplayer/command -v mpv/; s/DISPLAY= mplayer -vo caca -nosound -loop 0 -ss/DISPLAY= mpv --vo=libcaca --really-quiet --ao=null --loop-file=inf --start/' lib/hollywood/mplayer
# the bundled clip is h264, which ffmpeg-free cannot decode (buildroots have
# no fedora-cisco-openh264 repo either): regenerate a soundwave-style clip
# procedurally with lavfi, encoded as mpeg4, so the mpv widget stays
# patent-free
ffmpeg -y -v error -f lavfi -i "aevalsrc=0.3*sin(2*PI*200*t)*sin(2*PI*0.3*t)|0.3*sin(2*PI*300*t)*sin(2*PI*0.17*t):d=210:s=22050" \
  -filter_complex "[0:a]showwaves=s=128x96:mode=cline:rate=17[v]" \
  -map "[v]" -c:v mpeg4 -q:v 6 -pix_fmt yuv420p share/hollywood/soundwave.mp4

%build

%check
bash -n bin/hollywood bin/wallstreet

%install
install -Dpm755 bin/hollywood %{buildroot}%{_bindir}/hollywood
install -Dpm755 bin/wallstreet %{buildroot}%{_bindir}/wallstreet

# Scripts resolve their widget dir as dirname/../lib/<pkg>, keep /usr/lib
install -d -m755 %{buildroot}%{_prefix}/lib/hollywood
cp -a lib/hollywood/. %{buildroot}%{_prefix}/lib/hollywood/
install -d -m755 %{buildroot}%{_prefix}/lib/wallstreet
cp -a lib/wallstreet/. %{buildroot}%{_prefix}/lib/wallstreet/

install -d -m755 %{buildroot}%{_datadir}/hollywood
cp -a share/hollywood/. %{buildroot}%{_datadir}/hollywood/
install -d -m755 %{buildroot}%{_datadir}/wallstreet
cp -a share/wallstreet/. %{buildroot}%{_datadir}/wallstreet/

install -Dpm644 share/man/man1/hollywood.1 %{buildroot}%{_mandir}/man1/hollywood.1
install -Dpm644 share/man/man1/wallstreet.1 %{buildroot}%{_mandir}/man1/wallstreet.1

%files
%doc README.md
%{_bindir}/hollywood
%{_prefix}/lib/hollywood/
%{_datadir}/hollywood/
%{_mandir}/man1/hollywood.1*

%files wallstreet
%{_bindir}/wallstreet
%{_prefix}/lib/wallstreet/
%{_datadir}/wallstreet/
%{_mandir}/man1/wallstreet.1*

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 1.25-1
- Initial package
