%global tag 20240203-110809-5046fc22

Name:           wezterm
Version:        0.r20240203_110809_5046fc22
Release:        1%{?dist}
Summary:        A GPU-accelerated cross-platform terminal emulator and multiplexer

License:        MIT
URL:            https://wezfurlong.org/wezterm/
Source0:        https://github.com/wez/wezterm/releases/download/%{tag}/wezterm-%{tag}-src.tar.gz

# plain cargo: the workspace has a git dependency (xcb-imdkit) and the COPR
# project builds with network enabled, so dependencies are fetched at build
# time instead of being vendored into the SRPM
BuildRequires:  cargo
BuildRequires:  rust
BuildRequires:  gcc-c++
BuildRequires:  desktop-file-utils
BuildRequires:  pkg-config
# vendored-openssl: system OpenSSL lacks engine.h (vendored libssh needs it)
# and rawhide's OpenSSL 4.x is too new for this vintage's openssl-sys
BuildRequires:  perl
BuildRequires:  perl-FindBin
BuildRequires:  openssl-devel
BuildRequires:  wayland-devel
BuildRequires:  egl-wayland-devel
BuildRequires:  xorg-x11-server-Xwayland-devel
BuildRequires:  libX11-devel
BuildRequires:  libxkbcommon-devel
BuildRequires:  libxkbcommon-x11-devel
BuildRequires:  xcb-util-devel
BuildRequires:  xcb-util-keysyms-devel
BuildRequires:  xcb-util-wm-devel
BuildRequires:  xcb-util-image-devel
BuildRequires:  libpng-devel
BuildRequires:  mesa-libEGL-devel
BuildRequires:  dbus-devel
BuildRequires:  fontconfig-devel

%global debug_package %{nil}

%description
WezTerm is a GPU-accelerated cross-platform terminal emulator and multiplexer
written in Rust. It supports ligatures, hyperlinks, multiplexing (with a
built-in client/server), scrollback search, and a configuration written in
Lua.

%prep
%autosetup -n %{name}-%{tag}
# time 0.3.31 predates rustc's stricter type inference (E0282); bump within 0.3.x
cargo update -p time

%build
# EPEL's rustc denies never-type-fallback patterns (deny-by-default rust_2024
# compat lint) that this vintage relies on via mlua's untyped .eval()
export RUSTFLAGS="-A dependency_on_unit_never_type_fallback"
cargo build --workspace --release \
    --features distro-defaults,wezterm-ssh/vendored-openssl

%install
install -Dm755 target/release/wezterm            %{buildroot}%{_bindir}/wezterm
install -Dm755 target/release/wezterm-gui        %{buildroot}%{_bindir}/wezterm-gui
install -Dm755 target/release/wezterm-mux-server %{buildroot}%{_bindir}/wezterm-mux-server
install -Dm755 target/release/strip-ansi-escapes %{buildroot}%{_bindir}/strip-ansi-escapes
install -Dm755 assets/open-wezterm-here          %{buildroot}%{_bindir}/open-wezterm-here

install -Dm644 assets/shell-completion/bash %{buildroot}%{_sysconfdir}/bash_completion.d/wezterm
install -Dm644 assets/shell-completion/zsh  %{buildroot}%{_datadir}/zsh/site-functions/_wezterm
install -Dm644 assets/shell-completion/fish %{buildroot}%{_datadir}/fish/vendor_completions.d/wezterm.fish
install -Dm644 assets/shell-integration/wezterm.sh %{buildroot}%{_sysconfdir}/profile.d/wezterm.sh

install -Dm644 assets/icon/terminal.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/org.wezfurlong.wezterm.png
install -Dm644 assets/wezterm.desktop   %{buildroot}%{_datadir}/applications/wezterm.desktop
install -Dm644 assets/wezterm.appdata.xml %{buildroot}%{_datadir}/metainfo/org.wezfurlong.wezterm.metainfo.xml
install -Dm644 assets/wezterm-nautilus.py %{buildroot}%{_datadir}/nautilus-python/extensions/wezterm-nautilus.py

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/wezterm.desktop
target/release/wezterm --version

%files
%license LICENSE.md
%doc README.md
%{_bindir}/wezterm
%{_bindir}/wezterm-gui
%{_bindir}/wezterm-mux-server
%{_bindir}/strip-ansi-escapes
%{_bindir}/open-wezterm-here
%{_sysconfdir}/bash_completion.d/wezterm
%{_sysconfdir}/profile.d/wezterm.sh
%{_datadir}/zsh/site-functions/_wezterm
%{_datadir}/fish/vendor_completions.d/wezterm.fish
%{_datadir}/icons/hicolor/128x128/apps/org.wezfurlong.wezterm.png
%{_datadir}/applications/wezterm.desktop
%{_datadir}/metainfo/org.wezfurlong.wezterm.metainfo.xml
%{_datadir}/nautilus-python/extensions/wezterm-nautilus.py

%changelog
* Sun Oct 18 2026 Caio Bruno <cbrunofb@gmail.com> - 0.r20240203_110809_5046fc22-1
- Initial package
