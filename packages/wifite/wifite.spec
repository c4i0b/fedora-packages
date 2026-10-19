Name:           wifite
Version:        2.2.5
Release:        1%{?dist}
Summary:        Automated wireless attack tool

License:        GPL-2.0-only
URL:            https://github.com/derv82/wifite2
Source0:        https://github.com/derv82/wifite2/archive/refs/tags/%{version}.tar.gz
Source1:        wifite-completion

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-pip
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel
BuildRequires:  pyproject-rpm-macros

# No runtime Python deps: wifite shells out to external tools (soft
# Dependency wrappers in wifite/tools/, warns when one is missing)
Requires:       aircrack-ng
# net-tools provides ifconfig
Requires:       net-tools
Requires:       python3
# iproute provides ip
Requires:       iproute
Requires:       iw
# feeds reaver's pixie-dust attack (wifite never calls it directly)
Requires:       pixiewps

# Optional upstream (wifite warns and skips when absent); pulled as Requires
# here by convenience so one install brings the full toolkit.
# ships the tshark binary
Requires:       wireshark-cli
Requires:       reaver
Requires:       bully
Requires:       cowpatty
Requires:       hashcat
Requires:       john
# ships the hcxpcaptool binary
Requires:       hcxtools
Requires:       hcxdumptool
# used by the --random-mac flag
Requires:       macchanger
# pyrit (handshake detection) is dead upstream (Python 2) — skip

%description
Wifite is an automated wireless attack tool. It wraps the auditing
toolchain (aircrack-ng, reaver/bully, hashcat, hcxtools and friends),
scanning for networks and running the supported attacks (WPS
pixie-dust and brute-force, WPA handshake and PMKID capture, WEP
attacks) with sensible defaults and a single interface.

%prep
%autosetup -p1 -n wifite2-%{version}
# console_scripts names a nonexistent module; real entry is wifite.__main__
sed -i 's/wifite\.wifite:entry_point/wifite.__main__:entry_point/' setup.py

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files -l wifite

export PYTHONPATH=%{buildroot}%{python3_sitelib}
export PATH=%{buildroot}%{_bindir}:$PATH
%{buildroot}%{_bindir}/wifite --help > wifite-help.txt 2>&1
install -Dpm755 %{SOURCE1} %{buildroot}%{_datadir}/bash-completion/completions/wifite

%check
export PYTHONPATH=%{buildroot}%{python3_sitelib}
%{buildroot}%{_bindir}/wifite --help > /dev/null

%files -f %{pyproject_files}
%doc README.md
%doc wifite-help.txt
%{_bindir}/wifite
%{_datadir}/bash-completion/completions/wifite
# bundled probable-password wordlist (data_files in setup.py)
%{_datadir}/dict/wordlist-top4800-probable.txt

%changelog
* Sun Oct 18 2026 Caio Bruno <cbrunofb@gmail.com> - 2.2.5-1
- Initial package
