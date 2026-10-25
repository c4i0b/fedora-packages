Name:           slimbrave
Version:        2.3.3
Release:        1%{?dist}
Summary:        Debloat and harden Brave Browser using Chromium enterprise policies

License:        GPL-3.0-only
URL:            https://github.com/ChaoticSi1ence/SlimBrave-Neo
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3

Requires:       python3

%description
SlimBrave applies Chromium enterprise policies to debloat and harden the Brave
browser: 79 policies across 6 presets, managed through a curses TUI with zero
runtime dependencies beyond Python's standard library.

%prep
%autosetup -n SlimBrave-Neo-%{version} -p1

%build

%install
install -Dpm755 slimbrave-linux.py %{buildroot}%{_bindir}/slimbrave

%check
python3 -m py_compile slimbrave-linux.py

%files
%license LICENSE
%{_bindir}/slimbrave

%changelog
* Sun Oct 25 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 2.3.3-1
- Update to 2.3.3

* Fri Oct 16 2026 Caio Bruno <cbrunofb@gmail.com> - 2.3.2-1
- Initial package
