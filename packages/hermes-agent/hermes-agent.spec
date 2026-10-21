# Bundled upstream-managed venv is the product: upstream ships no wheels
# (setup.py blocks non-Nix builds) and manages deps via its own uv/PM runtime
%global debug_package %{nil}
# manylinux wheels bundle auditwheel-hashed libs (libjpeg-<8hex>.so); RPM
# requires their versioned symbols but nothing (not even this package)
# provides them, making the rpm uninstallable
%global __requires_exclude ^lib.+-[0-9a-f]{8}\\.so

# Default python3 is 3.15 from F45 on, exceeding upstream's <3.15 pin;
# EL10's 3.12 falls under upstream's python_version >= '3.14' dep markers,
# which would silently install zero runtime deps into the venv
%if 0%{?fedora} >= 45 || 0%{?rhel} >= 10
%global py python3.14
%else
%global py python3
%endif

Name:           hermes-agent
Version:        0.22.3
Release:        1%{?dist}
Summary:        The self-improving AI agent by Nous Research

License:        MIT
URL:            https://github.com/NousResearch/hermes-agent
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  %{py}
BuildRequires:  %{py}-devel
BuildRequires:  gcc
ExclusiveArch:  %{ix86} x86_64 aarch64 ppc64le s390x

Requires:       %{py}

%description
Hermes Agent is a self-improving AI agent: it creates skills from experience,
improves them during use, and builds a persistent memory across sessions. It
runs locally on your own devices and answers on the channels you already use.

%prep
%autosetup -n hermes-agent-%{version}

%build

%install
%{py} -m venv %{buildroot}%{_libdir}/%{name}
# HERMES_NIX_BUILD bypasses upstream's "no wheels outside Nix" guard
HERMES_NIX_BUILD=1 %{buildroot}%{_libdir}/%{name}/bin/pip install \
    --no-cache-dir . >/dev/null
# Venv scripts and pyvenv.cfg carry the buildroot path
grep -rlZ '%{buildroot}' %{buildroot}%{_libdir}/%{name}/bin/ \
    | xargs -0 -r sed -i "s|%{buildroot}||g"
sed -i "s|%{buildroot}||g" %{buildroot}%{_libdir}/%{name}/pyvenv.cfg

install -d -m755 %{buildroot}%{_bindir}
for b in hermes hermes-agent hermes-acp; do
    ln -s %{_libdir}/%{name}/bin/$b %{buildroot}%{_bindir}/$b
done

install -d -m755 %{buildroot}%{_datadir}/%{name}
cp -a skills locales optional-mcps optional-skills plugin-catalog \
    cli-config.yaml.example %{buildroot}%{_datadir}/%{name}/

%check
# Run under a scratch HOME: hermes writes ~/.hermes on first run
mkdir -p "%{_builddir}/home"
# --version short-circuits before the full import chain: exercise it too,
# or missing venv deps (e.g. python_version markers skipping installs) pass
HOME="%{_builddir}/home" %{buildroot}%{_libdir}/%{name}/bin/python \
    -c "import hermes_cli.main"
HOME="%{_builddir}/home" %{buildroot}%{_libdir}/%{name}/bin/python \
    %{buildroot}%{_libdir}/%{name}/bin/hermes --version

%files
%license LICENSE
%doc README.md
%{_bindir}/hermes
%{_bindir}/hermes-agent
%{_bindir}/hermes-acp
%{_libdir}/%{name}/
%{_datadir}/%{name}/

%changelog
* Wed Oct 21 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.22.3-1
- Update to 0.22.3

* Sat Oct 17 2026 Caio Bruno <cbrunofb@gmail.com> - 0.22.2-1
- Initial package
