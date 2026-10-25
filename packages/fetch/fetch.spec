Name:           fetch
Version:        2.3.0
Release:        1%{?dist}
Summary:        Animated 3D fetch tool for your terminal

License:        ISC
URL:            https://github.com/areofyl/fetch
Source0:        %{url}/archive/refs/tags/v%{version}/fetch-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make

%description
A donut.c-inspired fetch tool that spins your distro logo in 3D with
live-updating system info. Takes any ASCII/Unicode distro logo, turns each
character into a point cloud based on its visual density, and renders it as a
rotating 3D relief with Blinn-Phong shading. System info is gathered natively
from /proc, /sys and GTK config — no external dependencies beyond libm.

%prep
%autosetup -n fetch-%{version}

%build
%set_build_flags
%make_build

%install
%make_install DESTDIR=%{buildroot} PREFIX=%{_prefix}

%files
%license LICENSE
%doc README.md
%{_bindir}/fetch

%changelog
* Sun Oct 25 2026 Caio Bruno <cbrunofb@gmail.com> - 2.3.0-1
- Initial package
