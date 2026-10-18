# Prebuilt single-family font shipped as final .ttf by google/fonts (OFL:
# the upstream source is a .glyphs file, not buildable here): raw files
# pinned to a commit — google/fonts has no tags/releases, so version bumps
# are manual (no upstream file: the autoupdate bot skips it).
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
* __DATE__ __PACKAGER__ - __VERSION__-1
- Initial package
