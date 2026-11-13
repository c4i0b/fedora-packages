Name:           bandwhich
Version:        0.23.1
Release:        1%{?dist}
Summary:        Terminal bandwidth utilization tool by process, connection and remote IP

License:        MIT
URL:            https://github.com/imsnif/bandwhich
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        vendor.tar.zst

BuildRequires:  cargo-rpm-macros
BuildRequires:  libpcap-devel

# Bin-only crate: do not install sources into the cargo registry
%global cargo_install_lib false
# debugsource trips brp-mangle-shebangs on vendored crate inner attrs (xh, atac)
%global debug_package %{nil}

%description
CLI utility for displaying current network utilization by process,
connection and remote IP/hostname. Sniffs packets on a network interface
(pnet/libpcap), resolves them to owning processes via /proc, and renders a
live ratatui TUI with upload/download rates per process, connection and
remote address. Requires root at runtime.

%prep
%autosetup -n %{name}-%{version} -p1 -a 1
%cargo_prep -v vendor-deps
cat vendor-deps/git-sources.conf >> .cargo/config.toml

%build
# build.rs writes manpage and shell completions here (OUT_DIR is a moving
# target); it never mkdirs the dir itself
export BANDWHICH_GEN_DIR="${PWD}/gen"
mkdir -p "${BANDWHICH_GEN_DIR}"
%cargo_build

%install
%cargo_install
install -Dpm644 gen/bandwhich.1 %{buildroot}%{_mandir}/man1/bandwhich.1
install -Dpm644 gen/bandwhich.bash %{buildroot}%{bash_completions_dir}/bandwhich
install -Dpm644 gen/_bandwhich %{buildroot}%{zsh_completions_dir}/_bandwhich
install -Dpm644 gen/bandwhich.fish %{buildroot}%{fish_completions_dir}/bandwhich.fish

%check
%{buildroot}%{_bindir}/bandwhich --help > /dev/null

%files
%license LICENSE.md
%doc README.md CHANGELOG.md
%{_bindir}/bandwhich
%{_mandir}/man1/bandwhich.1*
%{bash_completions_dir}/bandwhich
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{zsh_completions_dir}/_bandwhich
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_completions.d
%{fish_completions_dir}/bandwhich.fish

%changelog
* Fri Nov 13 2026 Caio Bruno <cbrunofb@gmail.com> - 0.23.1-1
- Initial package
