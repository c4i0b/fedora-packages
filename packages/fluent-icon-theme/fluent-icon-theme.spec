# vinceliuice-style icon theme (Tela/Qogir/WhiteSur/Colloid/Fluent...): upstream
# install.sh assembles the theme from src/ + links/ (recoloring variants on
# the fly), the install section just runs it with -d into the buildroot.
# Upstream tags are dates: kept raw in the tag macro (Source0 references it);
# Version is the sanitized form and bump.sh keeps both in sync.
%define debug_package %{nil}
%global tag    2026-07-27

Name:           fluent-icon-theme
Version:        2026.07.27
Release:        1%{?dist}
Summary:        Fluent icon theme
BuildArch:      noarch

License:        GPL-3.0-only
URL:            https://github.com/vinceliuice/Fluent-icon-theme
Source0:        https://github.com/vinceliuice/Fluent-icon-theme/archive/refs/tags/%{tag}.tar.gz

%description
Fluent icon theme

%prep
%setup -q -n Fluent-icon-theme-%{tag}

%build

%install
# install.sh calls gtk-update-icon-cache (absent from the buildroot; caches
# are rpm file triggers on user systems) and Qogir refuses a missing dest.
sed -i '/gtk-update-icon-cache/d' install.sh
mkdir -p %{buildroot}%{_datadir}/icons
./install.sh -d %{buildroot}%{_datadir}/icons

%files
%license COPYING
# The 2026 install.sh refactor gathers the shared content once into hidden
# .Fluent-* base dirs in the icons root (each theme dir is symlinks into
# them): without the dotfile glob every theme dir ships dangling links.
%{_datadir}/icons/Fluent*
%{_datadir}/icons/.Fluent*

%changelog
* Sat Oct 24 2026 Caio Bruno <cbrunofb@gmail.com> - 2026.07.27-1
- Initial package
