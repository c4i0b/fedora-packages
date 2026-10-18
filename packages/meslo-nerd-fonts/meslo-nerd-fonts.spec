# Nerd Fonts prebuilt family: patched .ttf set straight from a
# ryanoasis/nerd-fonts release tarball (patching at build time would drag
# fontforge plus the original font sources for zero gain).
# Per family: set Source0 to the release tarball and Source1 to the ORIGINAL
# font license under patched-fonts/<Family>/ in the nerd-fonts repo (the
# release tarballs ship .ttf files only, no license).
%define debug_package %{nil}

Name:           meslo-nerd-fonts
Version:        3.5.1
Release:        1%{?dist}
Summary:        Meslo typeface patched with Nerd Fonts symbols
BuildArch:      noarch

License:        Apache-2.0
URL:            https://github.com/ryanoasis/nerd-fonts/tree/master/patched-fonts/Meslo
Source0:        https://github.com/ryanoasis/nerd-fonts/releases/download/v%{version}/Meslo.tar.xz
Source1:        https://raw.githubusercontent.com/ryanoasis/nerd-fonts/v%{version}/patched-fonts/Meslo/L/LICENSE.txt

# %%_fontbasedir lives in fonts-srpm-macros
BuildRequires:  fonts-srpm-macros
Requires:       fontpackages-filesystem

%description
Meslo typeface patched with Nerd Fonts symbols

%prep
%setup -T -q -c -a 0 -n %{name}-%{version}
cp -a %{SOURCE1} LICENSE

%build

%install
install -m 0755 -d %{buildroot}%{_fontbasedir}/%{name}
install -m 0644 -p *.ttf %{buildroot}%{_fontbasedir}/%{name}/

%files
%license LICENSE
%dir %{_fontbasedir}/%{name}
%{_fontbasedir}/%{name}/*.ttf

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 3.5.1-1
- Initial package
