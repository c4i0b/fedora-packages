# Prebuilt release zip: ttf set plus web formats (eot/svg/woff/woff2) that
# fontconfig does not consume — only the ttf set is installed. The zip
# carries no license file, so Source1 is the OFL text from the tagged repo.
# Selawik is the Segoe UI metric-compatible open typeface by Microsoft.
%define debug_package %{nil}

Name:           selawik-fonts
Version:        1.01
Release:        1%{?dist}
Summary:        Open Segoe UI metric-compatible typeface by Microsoft
BuildArch:      noarch

License:        OFL-1.1
URL:            https://github.com/microsoft/Selawik
Source0:        https://github.com/microsoft/Selawik/releases/download/%{version}/Selawik_Release.zip
Source1:        https://raw.githubusercontent.com/microsoft/Selawik/%{version}/LICENSE.txt

# %%_fontbasedir lives in fonts-srpm-macros
BuildRequires:  fonts-srpm-macros
BuildRequires:  unzip
Requires:       fontpackages-filesystem

%description
Open Segoe UI metric-compatible typeface by Microsoft

%prep
# flat zip (no top dir): -c creates the dir, -a 0 extracts into it
%setup -T -q -c -a 0
cp -a %{SOURCE1} LICENSE.txt

%build

%install
install -m 0755 -d %{buildroot}%{_fontbasedir}/%{name}
install -m 0644 -p *.ttf %{buildroot}%{_fontbasedir}/%{name}/

%files
%license LICENSE.txt
%dir %{_fontbasedir}/%{name}
%{_fontbasedir}/%{name}/*.ttf

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 1.01-1
- Initial package
