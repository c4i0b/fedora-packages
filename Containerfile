# Tooling image for the fedora-packages repo — the environment every `just`
# recipe runs in (see compose.yml). Fedora Rawhide to match the COPR project's
# top chroot.
FROM registry.fedoraproject.org/fedora:rawhide

# Full toolchain up front (the old distrobox ini + the SRPM/vendoring deps
# validate.sh used to dnf-install per run): deterministic, no network at
# recipe time beyond what the recipes themselves fetch.
RUN dnf -y --nodocs --setopt=install_weak_deps=0 install \
      copr-cli rpkg rpmdevtools rpmlint mock \
      git make curl \
      pyproject-rpm-macros cargo-rpm-macros \
      python3-specfile golang cargo rust-packaging go-vendor-tools \
    && dnf -y clean all

WORKDIR /app
