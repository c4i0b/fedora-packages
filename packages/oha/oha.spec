Name:           oha
Version:        1.16.0
Release:        1%{?dist}
Summary:        HTTP load generator, ahaha-style (ab/wrk/hey successor)

License:        MIT
URL:            https://github.com/hatoo/oha
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

%description
oha is a tiny HTTP load generator inspired by ahaha: it fires requests as
fast as possible (tokio + HTTP/1, HTTP/2 and HTTP/3 support), reports
latency distribution, and supports dynamic URLs, timeouts, connection
limits and dynamic shutdown after N requests/duration.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
%cargo_build

%install
%cargo_install

%check
%{buildroot}%{_bindir}/oha --version

%files
%license LICENSE
%doc README.md
%{_bindir}/oha

%changelog
* Thu Oct 29 2026 Caio Bruno <cbrunofb@gmail.com> - 1.16.0-1
- Initial package
