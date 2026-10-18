# vinceliuice-style icon theme (Tela/Qogir/WhiteSur/Colloid...): upstream
# install.sh assembles the theme from src/ + links/ (recoloring variants on
# the fly), the install section just runs it with -d into the buildroot.
# Upstream tags are dates: kept raw in the tag macro (Source0 references it);
# Version is the sanitized form and bump.sh keeps both in sync.
%define debug_package %{nil}
%global tag    2026-09-10

Name:           whitesur-icon-theme
Version:        2026.09.10
Release:        1%{?dist}
Summary:        WhiteSur icon theme (macOS style)
BuildArch:      noarch

License:        GPL-3.0-only
URL:            https://github.com/vinceliuice/WhiteSur-icon-theme
Source0:        https://github.com/vinceliuice/WhiteSur-icon-theme/archive/refs/tags/%{tag}.tar.gz

%description
WhiteSur icon theme (macOS style)

%prep
%setup -q -n WhiteSur-icon-theme-%{tag}

%build

%install
# install.sh calls gtk-update-icon-cache (absent from the buildroot; caches
# are rpm file triggers on user systems) and Qogir refuses a missing dest.
sed -i '/gtk-update-icon-cache/d' install.sh
mkdir -p %{buildroot}%{_datadir}/icons
./install.sh -d %{buildroot}%{_datadir}/icons

%files
%license COPYING
%{_datadir}/icons/WhiteSur*

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 2026.09.10-1
- Initial package
