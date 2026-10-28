Name:           ghostty
Version:        1.4.0
Release:        1%{?dist}
Summary:        A fast, feature-rich terminal emulator

License:        MIT
URL:            https://ghostty.org
Source0:        https://github.com/ghostty-org/ghostty/archive/refs/tags/v%{version}.tar.gz
# Upstream ships no GitHub Release for stable tags (only the "tip" prerelease),
# so Source0 is the codeload archive; the autoupdate bot falls back to tags.
# zig is not in Fedora; ghostty pins 0.17.x and builds it with the official
# prebuilt toolchain (one Source per arch, SRPM builder arch is arbitrary).
Source1:        https://ziglang.org/download/0.17.0/zig-x86_64-linux-0.17.0.tar.xz
Source2:        https://ziglang.org/download/0.17.0/zig-aarch64-linux-0.17.0.tar.xz
# build.zig.zon dependency closure, pre-fetched at SRPM time into a
# zig build --system package store (vendor-sources.sh): zig's own downloader
# fails on the COPR builders
Source3:        zig-pkg.tar.zst
ExclusiveArch:  x86_64 aarch64

# zig produces no GNU build-id note; find-debuginfo fails on its binaries
%global debug_package %{nil}
# zig's staged install leaves hardlinked cache .o files under /usr/lib/<hash>
# that vanish mid brp-strip; zig binaries are shipped unstripped anyway
%global __strip /bin/true
%if 0%{?rhel}
# ...and rpm 4.19 aborts on the missing note without this
%global _missing_build_ids_terminate_build 0
%endif

BuildRequires:  blueprint-compiler
BuildRequires:  bzip2-devel
BuildRequires:  fontconfig-devel
BuildRequires:  freetype-devel
BuildRequires:  glib2-devel
BuildRequires:  gtk4-devel
BuildRequires:  harfbuzz-devel
BuildRequires:  libadwaita-devel
BuildRequires:  libpng-devel
BuildRequires:  mesa-libEGL-devel
BuildRequires:  oniguruma-devel
BuildRequires:  pixman-devel
BuildRequires:  pkg-config
BuildRequires:  wayland-protocols-devel
BuildRequires:  zstd
BuildRequires:  zlib-ng-devel
%if 0%{?rhel}
BuildRequires:  patchelf
%endif
# EPEL lacks pandoc-cli (man pages) and gtk4-layer-shell-devel; zig then
# builds and ships its own layer-shell lib (builds run with network)
%if 0%{?fedora}
BuildRequires:  gtk4-layer-shell-devel
BuildRequires:  pandoc-cli
%endif

%description
Ghostty is a fast, feature-rich, cross-platform terminal emulator that uses
platform-native UI toolkits (GTK4/libadwaita on Linux). It ships sensible
defaults while remaining fully configurable.

%package devel
Summary:        Development files for libghostty-vt
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
The %{name}-devel package contains the header files and pkg-config file
for libghostty-vt, Ghostty's standalone terminal emulation library.

%prep
%autosetup -n %{name}-%{version}
%if 0%{?rhel}
# EPEL's harfbuzz (8.4) predates HB_BUFFER_CLUSTER_LEVEL_GRAPHEMES; it equals
# CHARACTERS+1 in the newer harfbuzz the vendored binding links against
sed -i 's/c\.HB_BUFFER_CLUSTER_LEVEL_GRAPHEMES/c.HB_BUFFER_CLUSTER_LEVEL_CHARACTERS + 1/' pkg/harfbuzz/buffer.zig
# EL10 libadwaita is 1.6; the 1.7 floor is upstream's support policy, the
# blueprints (max declared 1.5) and code compile fine against 1.6. Same for
# blueprint-compiler 0.19 (floor says 0.20): all blueprints compile with it.
sed -i 's/\.minor = 7,/.minor = 6,/' src/apprt/gtk/build/gresource.zig
sed -i 's/\.minor = 20,/.minor = 19,/' src/apprt/gtk/build/blueprint.zig
sed -i 's/\.minor = 7,/.minor = 6,/' src/apprt/gtk/adw_version.zig
sed -i 's/\.minor = 18,/.minor = 16,/' src/apprt/gtk/gtk_version.zig
%endif
%ifarch x86_64
tar -xJf %{SOURCE1}
%else
tar -xJf %{SOURCE2}
%endif
tar --zstd -xf %{SOURCE3}

%install
%ifarch x86_64
export PATH="$PWD/zig-x86_64-linux-0.17.0:$PATH"
%else
export PATH="$PWD/zig-aarch64-linux-0.17.0:$PATH"
%endif
# Link the system fontconfig/freetype/harfbuzz rather than letting zig vendor
# them: without -fsys= the executable would interpose its own copies over the
# ones GTK4 uses, mixing symbol/state across library boundaries.
# Runs in the install section (rpmbuild's buildroot is only usable there).
DESTDIR=%{buildroot} zig build \
    --summary all \
    --system zig-pkg \
    --prefix "%{_prefix}" \
    -fsys=fontconfig \
    -fsys=freetype \
    %if 0%{?fedora}
    -fsys=harfbuzz \
    %endif
    -Dversion-string=%{version}-%{release} \
    -Doptimize=ReleaseFast \
    -Dcpu=baseline \
    -Dpie=true \
    -Dstrip=false \
    -Demit-themes=true \
    %if 0%{?rhel}
    -fno-sys=gtk4-layer-shell \
    %endif
    %if 0%{?fedora}
    -Demit-docs \
    %endif

# zig bakes DESTDIR into the pc files' prefix; check-buildroot aborts
sed -i 's@^prefix=.*@prefix=%{_prefix}@' \
    %{buildroot}%{_datadir}/pkgconfig/libghostty-vt*.pc
# static artifacts shipped nowhere: drop them
rm -f %{buildroot}%{_prefix}/lib/libghostty-vt.a \
      %{buildroot}%{_datadir}/pkgconfig/libghostty-vt-static.pc

# rpm's own terminfo owns this entry on fedora >= 42
%if 0%{?fedora} >= 42
rm -f "%{buildroot}%{_datadir}/terminfo/g/ghostty"
%endif
%if 0%{?rhel}
# zig leaves an rpath pointing into its cache for the vendored layer-shell
# lib (installed into /usr/lib, on the default linker path)
patchelf --remove-rpath %{buildroot}%{_bindir}/ghostty
%endif

%check
%if 0%{?rhel}
# vendored layer-shell lib lives in the buildroot's /usr/lib until installed
LD_LIBRARY_PATH=%{buildroot}%{_prefix}/lib \
%endif
%{buildroot}%{_bindir}/ghostty +version

%files
%license LICENSE
%{_bindir}/ghostty
%{_datadir}/applications/com.mitchellh.ghostty.desktop
%{_datadir}/bash-completion/completions/ghostty.bash
%{_datadir}/bat/syntaxes/ghostty.sublime-syntax
%{_datadir}/fish/vendor_completions.d/ghostty.fish
%{_datadir}/ghostty
%{_datadir}/icons/hicolor/1024x1024/apps/com.mitchellh.ghostty.png
%{_datadir}/icons/hicolor/128x128/apps/com.mitchellh.ghostty.png
%{_datadir}/icons/hicolor/128x128@2/apps/com.mitchellh.ghostty.png
%{_datadir}/icons/hicolor/16x16/apps/com.mitchellh.ghostty.png
%{_datadir}/icons/hicolor/16x16@2/apps/com.mitchellh.ghostty.png
%{_datadir}/icons/hicolor/256x256/apps/com.mitchellh.ghostty.png
%{_datadir}/icons/hicolor/256x256@2/apps/com.mitchellh.ghostty.png
%{_datadir}/icons/hicolor/32x32/apps/com.mitchellh.ghostty.png
%{_datadir}/icons/hicolor/32x32@2/apps/com.mitchellh.ghostty.png
%{_datadir}/icons/hicolor/512x512/apps/com.mitchellh.ghostty.png
%{_datadir}/kio/servicemenus/com.mitchellh.ghostty.desktop
%if 0%{?fedora}
%{_mandir}/man1/ghostty.1*
%{_mandir}/man5/ghostty.5*
%endif
%{_datadir}/nautilus-python/extensions/ghostty.py
%{_datadir}/nvim/site/compiler/ghostty.vim
%{_datadir}/nvim/site/ftdetect/ghostty.vim
%{_datadir}/nvim/site/ftplugin/ghostty.vim
%{_datadir}/nvim/site/syntax/ghostty.vim
%{_datadir}/vim/vimfiles/compiler/ghostty.vim
%{_datadir}/vim/vimfiles/ftdetect/ghostty.vim
%{_datadir}/vim/vimfiles/ftplugin/ghostty.vim
%{_datadir}/vim/vimfiles/syntax/ghostty.vim
%{_datadir}/zsh/site-functions/_ghostty
%{_datadir}/dbus-1/services/com.mitchellh.ghostty.service
%{_datadir}/locale/*/LC_MESSAGES/com.mitchellh.ghostty.mo
%{_datadir}/metainfo/com.mitchellh.ghostty.metainfo.xml
%{_datadir}/systemd/user/app-com.mitchellh.ghostty.service
# zig installs libraries into /usr/lib regardless of the arch-specific libdir
%{_prefix}/lib/libghostty-vt.so.0
%{_prefix}/lib/libghostty-vt.so.0.1.0
# EPEL: zig builds its own layer-shell (no gtk4-layer-shell-devel there)
%if 0%{?rhel}
%{_prefix}/lib/libgtk4-layer-shell.so*
%endif
%{_datadir}/terminfo/x/xterm-ghostty
%if 0%{?fedora} < 42
%{_datadir}/terminfo/g/ghostty
%endif

%files devel
%{_includedir}/ghostty/vt.h
%{_includedir}/ghostty/vt/
%{_prefix}/lib/libghostty-vt.so
%{_datadir}/pkgconfig/libghostty-vt.pc
%if 0%{?rhel}
%{_includedir}/gtk4-layer-shell.h
%{_includedir}/gtk4-session-lock.h
%endif

%changelog
* Tue Oct 27 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 1.4.0-1
- Update to 1.4.0

* Sun Oct 18 2026 Caio Bruno <cbrunofb@gmail.com> - 1.3.1-1
- Initial package
