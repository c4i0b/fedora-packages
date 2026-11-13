Name:           __NAME__
Version:        __VERSION__
Release:        1%{?dist}
Summary:        __SUMMARY__

License:        __LICENSE__
URL:            __URL__
Source0:        __SOURCE0__
# zig is not in Fedora; build with the official prebuilt toolchain pinned
# once by the zig_version macro (one Source per arch: the SRPM builder arch
# is arbitrary) — vendor-sources.py fails loud when upstream's
# minimum_zig_version outgrows the pin
%global zig_version 0.0.0
Source1:        https://ziglang.org/download/%{zig_version}/zig-x86_64-linux-%{zig_version}.tar.xz
Source2:        https://ziglang.org/download/%{zig_version}/zig-aarch64-linux-%{zig_version}.tar.xz
# build.zig.zon dependency closure, pre-fetched at SRPM time into a
# zig build --system package store (vendor-sources.py): zig's own downloader
# fails on the COPR builders
Source3:        zig-pkg.tar.zst
ExclusiveArch:  x86_64 aarch64

# zig produces no GNU build-id note; find-debuginfo fails on its binaries
%global debug_package %{nil}
# brp-strip chases zig's hardlinked cache .o files under /usr/lib/<hash>
# that vanish mid-strip; zig binaries are shipped unstripped anyway
%global __strip /bin/true
%if 0%{?rhel}
# ...and rpm 4.19 aborts on the missing note without this
%global _missing_build_ids_terminate_build 0
%endif

BuildRequires:  zstd

%description
__SUMMARY__

%prep
%autosetup -p1
%ifarch x86_64
tar -xJf %{SOURCE1}
%else
tar -xJf %{SOURCE2}
%endif
tar --zstd -xf %{SOURCE3}

%install
%ifarch x86_64
export PATH="$PWD/zig-x86_64-linux-%{zig_version}:$PATH"
%else
export PATH="$PWD/zig-aarch64-linux-%{zig_version}:$PATH"
%endif
# No comments inside the conditional — a hash truncates the
# backslash-continued zig build command at that line
DESTDIR=%{buildroot} zig build \
    --summary all \
    --system zig-pkg \
    --prefix "%{_prefix}" \
    -Doptimize=ReleaseFast \
    -Dstrip=false

# Guarded sed pattern: pair every sed on upstream files with a grep so a
# drifted pattern fails at the right line instead of silently no-oping:
# grep -q 'upstream-pattern' build.zig \
#   || { echo 'pattern drifted: build.zig' >&2; exit 1; }
# sed -i 's/upstream-pattern/replacement/' build.zig

%files
%license __LICENSEFILE__
%doc README.md
%{_bindir}/__NAME__

%changelog
* __DATE__ __PACKAGER__ - __VERSION__-1
- Initial package
