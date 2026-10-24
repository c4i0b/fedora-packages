# Prebuilt payload: rpm 6.1+ errors on the empty debugsource list that
# find-debuginfo emits for prebuilts, so always disable debuginfo.
# Only Bun/Electron payloads also need "%global __strip /bin/true" (stripping
# corrupts their embedded app data); Go/Rust prebuilts strip normally.
# Vendor repacks that carry upstream dev-machine rpaths need an export of
# the QA_RPATHS mask in install (check-rpaths would abort otherwise).
%define debug_package %{nil}

# Per-arch upstream assets: Source URLs must stay arch-agnostic (the COPR
# SRPM builder runs on an arbitrary arch); select the payload in prep.
%ifarch x86_64
%global a x64
%elifarch aarch64
%global a arm64
%endif

ExclusiveArch:  x86_64 aarch64

Name:           __NAME__
Version:        __VERSION__
Release:        1%{?dist}
Summary:        __SUMMARY__

License:        __LICENSE__
URL:            __URL__
Source0:        __SOURCE0__
Source1:        LICENSE

BuildRequires:  desktop-file-utils

%description
__SUMMARY__

%prep
%setup -T -q -b 0 -n package

%build

%install
install -Dpm755 bin/__NAME__ %{buildroot}%{_bindir}/__NAME__

# Optional: shell completions (drop what the binary does not generate)
__NAME__ --completions bash > __NAME__.bash
__NAME__ --completions zsh  > ___NAME__
__NAME__ --completions fish > __NAME__.fish
install -Dpm644 __NAME__.bash %{buildroot}%{bash_completions_dir}/__NAME__
install -Dpm644 ___NAME__     %{buildroot}%{zsh_completions_dir}/___NAME__
install -Dpm644 __NAME__.fish %{buildroot}%{fish_completions_dir}/__NAME__.fish

# Optional: desktop entry + icons + AppStream metainfo
#install -Dpm644 __NAME__.desktop %{buildroot}%{_datadir}/applications/__NAME__.desktop
#install -Dpm644 icon.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/__NAME__.png
#install -Dpm644 __APPID__.metainfo.xml %{buildroot}%{_metainfodir}/__APPID__.metainfo.xml

install -pm644 %{SOURCE1} LICENSE

%check
#desktop-file-validate %{buildroot}%{_datadir}/applications/__NAME__.desktop

%files
%license LICENSE
%{_bindir}/__NAME__
%{bash_completions_dir}/__NAME__
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{zsh_completions_dir}/___NAME__
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_completions.d
%{fish_completions_dir}/__NAME__.fish
#{_datadir}/applications/__NAME__.desktop
#{_datadir}/icons/hicolor/512x512/apps/__NAME__.png
#{_metainfodir}/__APPID__.metainfo.xml

%changelog
* __DATE__ __PACKAGER__ - __VERSION__-1
- Initial package
