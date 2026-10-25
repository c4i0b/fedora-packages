Name:           pdfcraft
Version:        0.14.0
Release:        1%{?dist}
Summary:        PDF reader and editor with annotations, forms and signing

License:        MIT OR Apache-2.0
URL:            https://github.com/storytold/pdfcraft
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst
Source2:        %{name}.desktop

BuildRequires:  cargo-rpm-macros
BuildRequires:  gcc
# aws-lc-sys (via rustls, from pdfcraft-sign) builds C with cmake; no bindgen
# users in the app's tree, so no clang-devel needed
BuildRequires:  cmake
BuildRequires:  python3
BuildRequires:  desktop-file-utils

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false

# aws-lc-sys (via rustls) rejects RPM's -O2 (AGENTS.md)
%global build_cflags %(echo "%{build_cflags}" | sed 's/ *-O2//g')

# Release profile strips the binary and vendor sources trip the shebang BRP
%global debug_package %{nil}

# winit/wgpu dlopen these at runtime; Rust binaries declare no auto-deps
Requires:       libX11%{?_isa}
Requires:       libXcursor%{?_isa}
Requires:       libXi%{?_isa}
Requires:       libXrandr%{?_isa}
Requires:       libxkbcommon%{?_isa}
Requires:       libxkbcommon-x11%{?_isa}
Requires:       libwayland-client%{?_isa}
Requires:       vulkan-loader%{?_isa}

%description
PdfCraft is a pure-Rust PDF reader and editor with an egui-based workspace.
It opens and edits PDF documents with page organize (merge, split, rotate),
annotations, form filling, redaction, digital signing and certification,
OCR, preflight audits, and encryption with granular permissions.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
# git-sourced crates (craft-libs) need the source replacements cargo vendor
# printed; the prep macro only rewrites crates-io
cat vendor-deps/git-sources.conf >> .cargo/config.toml
%if 0%{?fedora} == 43
# F43's rustc pairs a pre-LLVM-19 backend with a newer stdarch: any use of
# the avx512 VNNI intrinsic dies with "intrinsic signature mismatch"
# (reproduced with a plain rustc probe, toolchain-wide). Drop rten-gemm's
# VNNI fast path there and re-stamp the vendor checksum.
python3 - <<'PYEOF'
import json, hashlib, pathlib
p = pathlib.Path("vendor-deps/rten-gemm/src/i8dot.rs")
s = p.read_text()
block = s[s.index("            // Base ISA features"):s.index("            // Base ISA features (no extensions required)")]
s = s.replace(block, "")
p.write_text(s)
cj = pathlib.Path("vendor-deps/rten-gemm/.cargo-checksum.json")
d = json.loads(cj.read_text())
d["files"]["src/i8dot.rs"] = hashlib.sha256(p.read_bytes()).hexdigest()
cj.write_text(json.dumps(d))
PYEOF
%endif

%build
# %%cargo_build cannot select a workspace member: its -n flag is
# --no-default-features and parametric macros reject other option letters
# zbus-lockstep's validate macro looks for ../xml relative to the crate
# being compiled: in a vendored tree that resolves to the vendored "xml"
# crate (whose extensionless LICENSE panics the macro) instead of
# atspi-common's D-Bus XML dir
[ -d vendor-deps/atspi-common/xml ] && export LOCKSTEP_XML_PATH="$(pwd)/vendor-deps/atspi-common/xml"
%{__cargo} build %{?_smp_mflags} -Z avoid-dev-deps --profile rpm -p %{name}

%install
# cargo install from a workspace member dir demands a local lock file
# offline; the binary is already built by the build section
install -Dm755 target/release/%{name} %{buildroot}%{_bindir}/%{name}

install -Dm644 %{SOURCE2} %{buildroot}%{_datadir}/applications/ai.storyteller.pdfcraft.desktop

# ship whatever sizes upstream provides (they change between releases)
for icon in assets/app-icon/hicolor/*/apps/*; do
    install -Dm644 "$icon" "%{buildroot}%{_datadir}/icons/hicolor/${icon#assets/app-icon/hicolor/}"
done

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/ai.storyteller.pdfcraft.desktop

%files
%license LICENSE-APACHE LICENSE-MIT NOTICE
%doc README.md
%{_bindir}/pdfcraft
%{_datadir}/applications/ai.storyteller.pdfcraft.desktop
%{_datadir}/icons/hicolor/*/apps/ai.storyteller.pdfcraft.*

%changelog
* Sun Oct 25 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.14.0-1
- Update to 0.14.0

* Fri Oct 23 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.13.0-1
- Update to 0.13.0

* Fri Oct 23 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.12.0-1
- Update to 0.12.0

* Wed Oct 21 2026 github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> - 0.11.0-1
- Update to 0.11.0

* Wed Oct 21 2026 Caio Bruno <cbrunofb@gmail.com> - 0.10.1-1
- Initial package
