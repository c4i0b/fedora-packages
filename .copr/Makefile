selfdir := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

pkg ?=
spec ?= $(if $(pkg),$(firstword $(wildcard $(pkg)*.spec)),$(firstword $(wildcard *.spec)))
specfile := $(if $(wildcard $(spec)/*.spec),$(firstword $(wildcard $(spec)/*.spec)),$(spec))
srcdir := $(dir $(abspath $(specfile)))

.PHONY: srpm vendor
# source payloads are (already compressed) tarballs: rpm's default zstd-19
# burns ~9x the CPU for zero size win — level 1 is size-identical
srpm: vendor
	rpmbuild -bs \
		--define "_sourcedir $(srcdir)" \
		--define "_srcrpmdir $(abspath $(outdir))" \
		--define "_disable_source_fetch 0" \
		--define "_source_payload w1T.zstdio" \
		$(specfile)

vendor:
	@if grep -qE '^%goprep|go-vendor-tools' $(specfile) || grep -q '^%cargo_prep' $(specfile) || grep -q '^Source[0-9]*:.*zig-pkg.tar' $(specfile); then \
		command -v python3 >/dev/null 2>&1 || dnf -y --nodocs --setopt=install_weak_deps=0 install python3 >/dev/null 2>&1; \
		python3 $(selfdir)../tools/vendor-sources.py $(srcdir) $(specfile); \
	fi
