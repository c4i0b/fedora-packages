# Packaging quirks — Python

- `%pyproject_wheel` needs `BuildRequires: python3-pip`. `%pyproject_save_files`
  `-l <name>` is assert-license **and** the module glob, and it validates the
  wheel RECORD — strip unwanted payload from the source tree in `%prep`,
  never from the buildroot. Smoke-testing an installed console script needs
  `PYTHONPATH=%{buildroot}%{python3_sitelib}` (and version flags can exit
  nonzero: guard substitutions with `|| :` under `sh -e`).
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
