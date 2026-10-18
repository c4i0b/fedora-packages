# Nerd Fonts prebuilt family: patched .ttf set straight from a
# ryanoasis/nerd-fonts release tarball (patching at build time would drag
# fontforge plus the original font sources for zero gain).
# Per family: set Source0 to the release tarball and Source1 to the ORIGINAL
# font license under patched-fonts/<Family>/ in the nerd-fonts repo (the
# release tarballs ship .ttf files only, no license).
%define debug_package %{nil}

Name:           __NAME__
Version:        __VERSION__
Release:        1%{?dist}
Summary:        __SUMMARY__
BuildArch:      noarch

License:        __LICENSE__
URL:            __URL__
Source0:        __SOURCE0__
Source1:        __SOURCE1__

# %%_fontbasedir lives in fonts-srpm-macros
BuildRequires:  fonts-srpm-macros
Requires:       fontpackages-filesystem

%description
__SUMMARY__

%prep
# flat tarball (no top dir): -c creates the dir, -a 0 extracts into it
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
* __DATE__ __PACKAGER__ - __VERSION__-1
- Initial package
