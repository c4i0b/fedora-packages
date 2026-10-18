# Cozette releases every consumer format known to man (bdf/otb/psf/fnt/
# dfont/woff...); only the Vector (scalable) ttf set is installed — the
# raster copies serve legacy bitmap consumers fontconfig does not touch.
# No upstream file: release tags are shaped "v.1.30.0" and the bot's v-strip
# would mangle that into an invalid version, so bumps are manual.
%define debug_package %{nil}

Name:           cozette-fonts
Version:        1.30.0
Release:        1%{?dist}
Summary:        Pixel-ish monospaced font designed for coding and small sizes
BuildArch:      noarch

License:        MIT
URL:            https://github.com/the-moonwitch/Cozette
Source0:        https://github.com/the-moonwitch/Cozette/releases/download/v.%{version}/CozetteVector.ttf
Source1:        https://github.com/the-moonwitch/Cozette/releases/download/v.%{version}/CozetteVectorBold.ttf
Source2:        https://github.com/the-moonwitch/Cozette/releases/download/v.%{version}/LICENSE

# %%_fontbasedir lives in fonts-srpm-macros
BuildRequires:  fonts-srpm-macros
Requires:       fontpackages-filesystem

%description
Pixel-ish monospaced font designed for coding and small sizes

%prep
%setup -T -q -c
cp -a %{SOURCE2} LICENSE

%build

%install
install -m 0755 -d %{buildroot}%{_fontbasedir}/%{name}
install -m 0644 -p %{SOURCE0} %{SOURCE1} %{buildroot}%{_fontbasedir}/%{name}/

%files
%license LICENSE
%dir %{_fontbasedir}/%{name}
%{_fontbasedir}/%{name}/*.ttf

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 1.30.0-1
- Initial package
