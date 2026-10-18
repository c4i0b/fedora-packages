selfdir := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

pkg ?=
spec ?= $(if $(pkg),$(firstword $(wildcard $(pkg)*.spec)),$(firstword $(wildcard *.spec)))
specfile := $(if $(wildcard $(spec)/*.spec),$(firstword $(wildcard $(spec)/*.spec)),$(spec))
srcdir := $(dir $(abspath $(specfile)))

.PHONY: srpm vendor
srpm: vendor
	rpmbuild -bs \
		--define "_sourcedir $(srcdir)" \
		--define "_srcrpmdir $(abspath $(outdir))" \
		--define "_disable_source_fetch 0" \
		$(specfile)

vendor:
	@if grep -qE '^%goprep|go-vendor-tools' $(specfile) || grep -q '^%cargo_prep' $(specfile); then \
		$(selfdir)../tools/vendor-sources.sh $(srcdir) $(specfile); \
	fi
