# Packaging quirks — Python

- `%pyproject_wheel` needs `BuildRequires: python3-pip`. `%pyproject_save_files`
  `-l <name>` is assert-license **and** the module glob, and it validates the
  wheel RECORD — strip unwanted payload from the source tree in `%prep`,
  never from the buildroot. Smoke-testing an installed console script needs
  `PYTHONPATH=%{buildroot}%{python3_sitelib}` (and version flags can exit
  nonzero: guard substitutions with `|| :` under `sh -e`).
- Seds against `setup.py`/`pyproject.toml`/sources are drift-prone (the
  setup.py → pyproject.toml migration makes this worse): guard them with
  `grep -q … || exit 1` like any pattern-matched workaround (wifite, wifit3).
- The repo lists build backends manually (`python3-setuptools`/`python3-wheel`,
  `python3-hatchling`, …) instead of Fedora's `%pyproject_buildrequires`
  generators — builds run without isolation on purpose (conventions.md);
  replace the backend BR when a scaffolded package's upstream moves off
  setuptools.
- Hand-installed modules (upstream's build unusable): craft the dist-info
  yourself but derive METADATA from `%{version}`, never a literal — bump.sh
  only rewrites the `Version:` tag (see python3-libusb-package).
## Venv packages

- Normalize `^#!/usr/bin/env python$` shebangs in vendored scripts (sed to
  an absolute interpreter) — brp-mangle-shebangs aborts on the ambiguous
  "env python" form (see hermes-agent).
- If upstream ships `[tool.uv] override-dependencies`, install with
  `uv pip --python <venv>/bin/python` — plain pip ignores the overrides
  and dies with ResolutionImpossible (hermes-agent cba9b46).

## Wheel builds

- Venv/wheel installs bundle manylinux libs with auditwheel-hashed sonames
  (`libjpeg-31e2ca52.so.62.4.0`): RPM emits versioned requires nothing
  provides (not even the package itself), making the rpm uninstallable —
  carry `%global __requires_exclude ^lib.+-[0-9a-f]{8}\\.so` (see
  hermes-agent).
