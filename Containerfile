FROM registry.fedoraproject.org/fedora:rawhide

RUN dnf install -y --setopt=install_weak_deps=False \
      copr-cli rpkg rpmdevtools rpmlint make git curl sudo mock \
      pyproject-rpm-macros cargo-rpm-macros go-vendor-tools \
    && dnf clean all \
    && useradd -m -G mock,wheel -u 1000 builder \
    && echo 'builder ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/builder \
    && chmod 440 /etc/sudoers.d/builder

USER builder
WORKDIR /workspaces/fedora-packages
