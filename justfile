set shell := ["bash", "-cu"]

repo := "fedora-packages"
owner := env_var_or_default("COPR_OWNER", "caiobruno")
github_owner := env_var_or_default("GITHUB_OWNER", "c4i0b")
project := owner + "/" + repo

# Recipes run inside the fedora-packages distrobox; CI sets FEDORA_PACKAGES_DIRECT=1
runner := `[ "${FEDORA_PACKAGES_DIRECT:-}" = 1 ] || printf 'distrobox enter fedora-packages --'`

@default:
    just --list

# Create and enter the development distrobox (mandatory environment)
box:
    tools/box.sh

# Lint all spec files (one rpmlint process per spec: no macro cross-leak)
lint:
    {{runner}} tools/lint.sh

# Build a package SRPM locally using the COPR make_srpm contract
srpm name:
    {{runner}} make -f .copr/Makefile srpm pkg=packages/{{name}}/ outdir=/tmp/srpm

# Check package invariants (naming, upstream syntax, changelog sync, arch-safe sources)
test:
    {{runner}} tools/test.sh

# Lint and build SRPMs for all packages (same as CI)
validate:
    {{runner}} tools/validate.sh

# Full mock build (rawhide + oldest stable, with network) — ONLY to reproduce
# an inconclusive COPR failure; never preemptively, COPR is the validator
build-local name chroot="default":
    {{runner}} tools/build-local.sh {{name}} {{chroot}}

# Bump a package version (Version, Release and changelog)
bump name version:
    {{runner}} tools/bump.sh {{name}} {{version}}

# Show COPR build status (check pending builds when finishing work)
status:
    {{runner}} copr-cli list-builds {{project}}

# Delete old COPR builds, keeping only the newest per package (dry = preview)
prune-builds dry="":
    {{runner}} tools/prune-builds.sh {{project}} {{dry}}

# Watch in-flight COPR builds until they finish; non-zero if any failed
watch name="" interval="90":
    {{runner}} tools/watch-build.sh {{project}} "{{name}}" {{interval}}

# Create or update the COPR project
setup:
    {{runner}} tools/setup-project.sh {{project}}

# Scaffold a new package from a template (source or bin)
new-package name kind="source":
    tools/new-package.sh {{name}} {{kind}}

# Register a package from packages/<name> as an SCM build with webhook rebuilds
add-package name:
    {{runner}} copr-cli add-package-scm {{project}} \
        --name {{name}} \
        --clone-url https://github.com/{{github_owner}}/{{repo}}.git \
        --type git \
        --method make_srpm \
        --subdir packages/{{name}} \
        --webhook-rebuild on

# Refresh COPR badges and the README build-status block (same as the badges workflow)
# Aggregate key=value fields from GitHub Actions logs of recent runs
analyze-logs workflow="autoupdate" days="7" pattern="rate-summary":
    tools/analyze-logs.sh {{workflow}} {{days}} {{pattern}}

badges:
    {{runner}} tools/update-badges.sh {{project}}

# Rebuild a package from its current source definition
build name:
    {{runner}} copr-cli build-package {{project}} --name {{name}} --nowait
