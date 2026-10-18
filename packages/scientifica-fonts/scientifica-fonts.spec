# Prebuilt font straight from the GitHub release tarball (patching at
# build time would drag fontforge for zero gain); the tarball ships no
# license file, so Source1 is the OFL text from the tagged repo. Only the
# ttf set is installed: the bdf/otb copies serve legacy X11 bitmap apps
# that fontconfig does not consume.
%define debug_package %{nil}

Name:           scientifica-fonts
Version:        2.3
Release:        1%{?dist}
Summary:        Tall and condensed bitmap-style typeface based on creep
BuildArch:      noarch

License:        OFL-1.1
URL:            https://github.com/oppiliappan/scientifica
Source0:        https://github.com/oppiliappan/scientifica/releases/download/v%{version}/scientifica.tar
Source1:        https://raw.githubusercontent.com/oppiliappan/scientifica/v%{version}/LICENSE

# %%_fontbasedir lives in fonts-srpm-macros
BuildRequires:  fonts-srpm-macros
Requires:       fontpackages-filesystem

%description
Tall and condensed bitmap-style typeface based on creep

%prep
%setup -q -n scientifica
cp -a %{SOURCE1} LICENSE

%build

%install
install -m 0755 -d %{buildroot}%{_fontbasedir}/%{name}
install -m 0644 -p ttf/*.ttf %{buildroot}%{_fontbasedir}/%{name}/

%files
%license LICENSE
%dir %{_fontbasedir}/%{name}
%{_fontbasedir}/%{name}/*.ttf

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 2.3-1
- Initial package
