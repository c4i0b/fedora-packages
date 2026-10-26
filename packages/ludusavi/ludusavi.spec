Name:           ludusavi
Version:        0.31.0
Release:        1%{?dist}
Summary:        Game save backup tool

License:        MIT
URL:            https://github.com/mtkennerly/ludusavi
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(gtk+-3.0)
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(xkbcommon)

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

# Release profile strips the binary and vendor sources trip the shebang BRP
%define debug_package %{nil}

%description
Ludusavi backs up and restores game saves across multiple roots, mapping them
to a known game database (the ludusavi manifest) so files land in predictable
locations.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
%cargo_build

%install
%cargo_install

%{buildroot}%{_bindir}/ludusavi complete bash > ludusavi.bash
%{buildroot}%{_bindir}/ludusavi complete zsh  > _ludusavi
%{buildroot}%{_bindir}/ludusavi complete fish > ludusavi.fish
install -Dpm644 ludusavi.bash %{buildroot}%{bash_completions_dir}/ludusavi
install -Dpm644 _ludusavi     %{buildroot}%{zsh_completions_dir}/_ludusavi
install -Dpm644 ludusavi.fish %{buildroot}%{fish_completions_dir}/ludusavi.fish

%check
%{buildroot}%{_bindir}/ludusavi --version

%files
%license LICENSE
%doc README.md
%{_bindir}/ludusavi
%{bash_completions_dir}/ludusavi
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{zsh_completions_dir}/_ludusavi
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_completions.d
%{fish_completions_dir}/ludusavi.fish

%changelog
* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 0.31.0-1
- Initial package
