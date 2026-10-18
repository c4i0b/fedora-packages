# vinceliuice-style icon theme (Tela/Qogir/WhiteSur/Colloid...): upstream
# install.sh assembles the theme from src/ + links/ (recoloring variants on
# the fly), the install section just runs it with -d into the buildroot.
# Upstream tags are dates: kept raw in the tag macro (Source0 references it);
# Version is the sanitized form and bump.sh keeps both in sync.
%define debug_package %{nil}
%global tag    __TAG__

Name:           __NAME__
Version:        __VERSION__
Release:        1%{?dist}
Summary:        __SUMMARY__
BuildArch:      noarch

License:        __LICENSE__
URL:            __URL__
Source0:        __SOURCE0__

%description
__SUMMARY__

%prep
%setup -q -n __PAYLOAD_DIR__-%{tag}

%build

%install
# install.sh calls gtk-update-icon-cache (absent from the buildroot; caches
# are rpm file triggers on user systems) and Qogir refuses a missing dest.
sed -i '/gtk-update-icon-cache/d' install.sh
mkdir -p %{buildroot}%{_datadir}/icons
./install.sh -d %{buildroot}%{_datadir}/icons

%files
%license __LICENSEFILE__
%{_datadir}/icons/__THEMEPREFIX__*

%changelog
* __DATE__ __PACKAGER__ - __VERSION__-1
- Initial package
