Name:           angryoxide
Version:        0.9.2
Release:        1%{?dist}
Summary:        802.11 attack tool producing hashcat-ready hashlines

License:        GPL-3.0-only
URL:            https://github.com/Ragnt/AngryOxide
Source0:        https://github.com/Ragnt/AngryOxide/archive/refs/tags/v%{version}.tar.gz
# libwifi submodule pin from the release tag tree (upstream has no release
# tags); refresh on version bumps
%global libwifi_commit 71268e1898ad88b8b5d709e186836db417b33e81
Source1:        https://github.com/Ragnt/libwifi/archive/%{libwifi_commit}.tar.gz

# no cargo_prep vendoring (it can't assemble the submodule); crates fetch at
# build time
BuildRequires:  cargo
BuildRequires:  gcc

# release profile strips the binary (Cargo.toml): empty debugsource otherwise
%define debug_package %{nil}

Requires:       gpsd
Requires:       hashcat

%description
Single-interface 802.11 survey and attack tool with automated attacks that
result in valid hashcat hashlines. Heavily inspired by hcxdumptool.

%prep
%autosetup -n AngryOxide-%{version} -p1
mkdir -p libs/libwifi
tar -xf %{SOURCE1} --strip-components=1 -C libs/libwifi
%build
cargo build --release --locked

%install
install -Dpm755 target/release/angryoxide %{buildroot}%{_bindir}/angryoxide
install -Dpm644 completions/bash_angryoxide_completions %{buildroot}%{_datadir}/bash-completion/completions/angryoxide
install -Dpm644 completions/zsh_angryoxide_completions %{buildroot}%{_datadir}/zsh/site-functions/_angryoxide

%files
%license LICENSE
%doc README.md
%{_bindir}/angryoxide
%{_datadir}/bash-completion/completions/angryoxide
%{_datadir}/zsh/site-functions/_angryoxide

%changelog
* Sun Oct 18 2026 Caio Bruno <cbrunofb@gmail.com> - 0.9.2-1
- Initial package
