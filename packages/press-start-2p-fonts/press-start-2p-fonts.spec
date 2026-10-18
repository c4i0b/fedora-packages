# Prebuilt single-family font shipped as final .ttf by google/fonts (OFL:
# the upstream source is a .glyphs file, not buildable here): raw files
# pinned to a commit — google/fonts has no tags/releases, so version bumps
# are manual (no upstream file: the autoupdate bot skips it).
%define debug_package %{nil}

Name:           press-start-2p-fonts
Version:        3.000
Release:        1%{?dist}
Summary:        Press Start 2P pixel 8-bit arcade display font
BuildArch:      noarch

License:        OFL-1.1
URL:            https://fonts.google.com/specimen/Press+Start+2P
Source0:        https://raw.githubusercontent.com/google/fonts/e06fe11c39051bddaef73ec338a9d1c8175723f1/ofl/pressstart2p/PressStart2P-Regular.ttf
Source1:        https://raw.githubusercontent.com/google/fonts/e06fe11c39051bddaef73ec338a9d1c8175723f1/ofl/pressstart2p/OFL.txt

# %%_fontbasedir lives in fonts-srpm-macros
BuildRequires:  fonts-srpm-macros
Requires:       fontpackages-filesystem

%description
Press Start 2P pixel 8-bit arcade display font

%prep
%setup -T -q -c
cp -a %{SOURCE1} LICENSE

%build

%install
install -m 0755 -d %{buildroot}%{_fontbasedir}/%{name}
install -m 0644 -p %{SOURCE0} %{buildroot}%{_fontbasedir}/%{name}/

%files
%license LICENSE
%dir %{_fontbasedir}/%{name}
%{_fontbasedir}/%{name}/*.ttf

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 3.000-1
- Initial package
