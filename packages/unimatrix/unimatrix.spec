# Upstream has no tags/releases (checked 2026-10): pinned commit snapshot,
# autoupdate tracker intentionally absent.
%global commit dff519f972103f91384f360f270614184de8aa92

Name:           unimatrix
Version:        0.1.0
Release:        1.20260520git%{?dist}
Summary:        Simulate the display from "The Matrix" in a terminal

License:        GPL-3.0-or-later
URL:            https://github.com/will8211/unimatrix
Source0:        %{url}/archive/%{commit}/%{name}-%{commit}.tar.gz

BuildArch:       noarch
BuildRequires:   python3-devel
Requires:        python3

%description
Python script to simulate the display from "The Matrix" in a terminal. Uses
half-width katakana unicode characters by default, but can use custom
character sets. Accepts keyboard controls while running.

%prep
%autosetup -n %{name}-%{commit}

%build

%install
install -Dpm755 unimatrix.py %{buildroot}%{_bindir}/unimatrix

%check
python3 -m py_compile unimatrix.py

%files
%license LICENSE
%doc README.md
%{_bindir}/unimatrix

%changelog
* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 0.1.0-1.20260520git
- Initial package (commit dff519f)
