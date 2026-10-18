# vinceliuice-style icon theme (Tela/Qogir/WhiteSur/Colloid...): upstream
# install.sh assembles the theme from src/ + links/ (recoloring variants on
# the fly); the install section just runs it with -d into the buildroot.
# Upstream tags are dates: kept raw in the tag macro (Source0 references it);
# Version is the sanitized form and bump.sh keeps both in sync.
%define debug_package %{nil}
%global tag    2026-07-07

Name:           tela-icon-theme
Version:        2026.07.07
Release:        1%{?dist}
Summary:        Tela icon theme
BuildArch:      noarch

License:        GPL-3.0-only
URL:            https://github.com/vinceliuice/Tela-icon-theme
Source0:        https://github.com/vinceliuice/Tela-icon-theme/archive/refs/tags/%{tag}.tar.gz

%description
Tela icon theme

%prep
%setup -q -n Tela-icon-theme-%{tag}

%build

%install
# install.sh calls gtk-update-icon-cache (absent from the buildroot; caches
# are rpm file triggers on user systems) and Qogir refuses a missing dest.
sed -i '/gtk-update-icon-cache/d' install.sh
mkdir -p %{buildroot}%{_datadir}/icons
./install.sh -d %{buildroot}%{_datadir}/icons

%files
%license COPYING
%{_datadir}/icons/Tela*

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 2026.07.07-1
- Initial package
