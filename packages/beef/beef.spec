Name:           beef
Version:        0.6.0.0
Release:        1%{?dist}
Summary:        Browser Exploitation Framework

License:        GPL-2.0-only
URL:            https://beefproject.com
Source0:        https://github.com/beefproject/beef/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  openssl-devel
BuildRequires:  patchelf
BuildRequires:  ruby-devel
BuildRequires:  rubygem-bundler
BuildRequires:  sqlite-devel

# vendored native gem extensions would trip the debug finder
%global debug_package %{nil}

Requires:       nodejs
Requires:       ruby

%description
BeEF is short for The Browser Exploitation Framework. It is a penetration
testing tool that focuses on the web browser: it hooks one or more browsers
and launches client-side attacks from a web UI.

%prep
%autosetup -n beef-%{version}

%install
d=%{buildroot}%{_datadir}/beef
install -d "$d"
cp -a . "$d"
pushd "$d"
bundle config set --local path vendor
# lockfile pins minitest to a ruby<4 only version: let bundler re-resolve
BUNDLE_FROZEN= bundle install
popd
# gem metadata embeds absolute buildroot paths; the wrapper cds into the app
grep -rlI "%{buildroot}" "$d" | xargs -r sed -i "s|%{buildroot}%{_datadir}/beef|%{_datadir}/beef|g"
# native extensions carry the buildroot path in debug info
find "$d" -name '*.so' -exec strip --strip-unneeded {} +
# precompiled sqlite3 gem ships rake-compiler runpaths that break check-rpaths
find "$d" -name '*.so' -exec patchelf --remove-rpath {} +

mkdir -p %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/beef <<'EOF'
#!/bin/sh
cd %{_datadir}/beef || exit 1
exec ruby beef "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/beef

%check
ruby -c beef

%files
%{_bindir}/beef
%config(noreplace) %{_datadir}/beef/config.yaml
%{_datadir}/beef/

%changelog
* Sun Oct 18 2026 Caio Bruno <caioibruno@gmail.com> - 0.6.0.0-1
- Initial package
- Ship config.yaml: a stray %exclude dropped it and the server
  could not start
