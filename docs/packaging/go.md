# Packaging quirks — Go

- Upstream tracks a newer Go than the distro ships: `export GOTOOLCHAIN=auto`
  in `%build` (downloads the toolchain the go.mod asks for at build time —
  net-on COPR only) plus `%global debug_package %{nil}` when the downloaded
  toolchain strips oddly (see crush/dnscontrol/nexttrace).
- Downgrade path when deps accept an older Go but the go.mod pins the dev
  toolchain: sed the `go` directive down and **guard it**
  (`grep -q '^go 1\.NN\.' go.mod || exit 1`) so a toolchain bump fails loud
  instead of no-oping (see whosthere).
- Version stamping: `-ldflags "-X <pkg>.<var>=%{version}"` on the `%gobuild`
  line is the repo idiom; `export GO_LDFLAGS` is the Fedora-canonical form —
  either works, keep per-spec usage consistent.
- Deliberate deviation from Fedora canonical (go-vendor-tools): this repo
  vendors at SRPM time via vendor-sources.py, ships no `go-vendor-tools.toml`
  (Source2) and no cumulative vendored-module `License:` — accepted for COPR;
  revisit if a package ever targets official Fedora.
