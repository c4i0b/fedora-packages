Name:           wifit3
Version:        0.6.0
Release:        1%{?dist}
Summary:        Wireless auditor TUI talking to USB Wi-Fi adapters from userland

License:        GPL-2.0-only
URL:            https://github.com/derv82/wifit3
Source0:        https://github.com/derv82/wifit3/archive/refs/tags/v%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-hatchling
BuildRequires:  python3-pip
BuildRequires:  pyproject-rpm-macros

Requires:       hashcat
Requires:       python3-libusb-package
Requires:       python3-platformdirs
Requires:       python3-pyusb
Requires:       python3-rich
Requires:       python3-textual

%description
Wifit3 talks to USB Wi-Fi adapters directly from userland with its own chip
drivers, so it needs no kernel drivers or airmon-ng. Captures handshakes and
feeds hashlines to hashcat.

%prep
%autosetup -n wifit3-%{version} -p1
# Windows-only installer; removing it pre-wheel keeps the RECORD valid
rm -rf src/wifit3/setup/bin
# Static.update(layout=) is textual>=5 (added 5.0.0); Fedora ships 4.x — drop the
# perf-only kwarg, update() then just does a full layout refresh
sed -i 's/, layout=False)/)/' \
    src/wifit3/ui/screens/focus_v2/{packet_dashboard,router_endpoint,clients_list,art}.py

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files -l wifit3

%check
export PYTHONPATH=%{buildroot}%{python3_sitelib}
%{buildroot}%{_bindir}/wifit3 --version

%files -f %{pyproject_files}
%doc README.md
%{_bindir}/wifit3

%changelog
* Sun Oct 25 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.6.0-1
- Update to 0.6.0

* Wed Oct 21 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.5.3-1
- Update to 0.5.3

* Mon Oct 19 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.5.2-1
- Update to 0.5.2

* Mon Oct 19 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.5.1-1
- Update to 0.5.1

* Sun Oct 18 2026 Caio Bruno <cbrunofb@gmail.com> - 0.5.0-1
- Initial package
