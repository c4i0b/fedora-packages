#!/usr/bin/env bash
# Shared helpers for package scaffolding and validation.

# Map an `upstream` source to the project homepage; empty when unmappable.
# Formats must stay in sync with resolve() in autoupdate.sh and check_package.
upstream_home() {
  local src="$1"
  # prefixed forms also match */*, so they must come first; GitHub (the most
  # frequent) is the fallthrough
  case "$src" in
    # tags-only repo on any forge: same homepage as its bare form
    tags:*) upstream_home "${src#tags:}" ;;
    npm:*) echo "https://www.npmjs.com/package/${src#npm:}" ;;
    gitlab:*) echo "https://gitlab.com/${src#gitlab:}" ;;
    codeberg:*) echo "https://codeberg.org/${src#codeberg:}" ;;
    forgejo:*)
      echo "${FORGEJO_HOME:-https://codeberg.org}/${src#forgejo:}" ;;
    http://*|https://*) echo "$src" ;;
    */*) echo "https://github.com/$src" ;;
  esac
}

# The "downloaded sources set": what rpmbuild fetches into the package dirs,
# minus the vendor archives that are regenerated (not fetched) each run.
# Single definition shared by the CI counters, the content epoch and the
# cache paths commentary — keep them from drifting apart.
srcs_find() {
  find packages -type f \
    \( -name '*.tar.*' -o -name '*.tgz' -o -name '*.zip' \) \
    -not \( -name '*-vendor.tar.bz2' -o -name 'vendor.tar.zst' \) "$@"
}

# Shared rpmlint invocation (kept in one place so packages and rendered
# templates are held to the exact same standard)
lint_spec() {
  # lint_spec <spec-file>; prints rpmlint output, returns non-zero on errors
  local spec="$1" out
  # vendor archives are local files by design; the invalid-url noise is expected
  out="$(rpmlint "$spec" 2>/dev/null)" || true
  grep -v 'invalid-url Source[0-9]*: .*vendor\.tar' <<<"$out" || true
  # rpmlint exit code is unreliable across configs; re-derive it from the
  # error count so filtered noise cannot mask real findings
  [ "$(grep -c 'E: ' <<<"$out")" -eq 0 ]
}

render_spec() {
  # render_spec <template> <outfile> <name> [full]
  local template="$1" out="$2" name="$3" full="${4:-0}"
  local values=()
  local key val
  while read -r key val; do
    if [ "$full" = 1 ]; then
      values+=(-e "s|$key|$val|g")
    fi
  done <<EOF
__VERSION__ 0.0.1
__SUMMARY__ Template check
__LICENSE__ MIT
__URL__ https://example.com
__SOURCE0__ https://example.com/$name-%{version}.tar.gz
__TAG__ 1970-01-01
__COMMIT__ 0123456789abcdef0123456789abcdef0123456789ab
__SNAPSHOT__ 19700101
__LICENSEFILE__ LICENSE
__AUTHOR__ Upstream authors
__THEMEPREFIX__ Payload
__APPID__ org.example.$name
__GOIPATH__ github.com/example/$name
__SOURCE1__ https://example.com/$name-%{version}-extra.tar.gz
__PAYLOAD_DIR__ payload
__PAYLOADDIR__ payload-dir
__BIN__ $name
__EXTRAREQ__
__EXTRAINSTALL__
__EXTRAFILES__
__SKIP__
__DATE__ $(date '+%a %b %d %Y')
__PACKAGER__ Template Check <check@localhost>
EOF
  # ___NAME__ must be replaced before __NAME__ (it contains it)
  sed -e "s|___NAME__|_$name|g" \
    -e "s|__NAME__|$name|g" \
    "${values[@]}" "$template" > "$out"
}

check_package() {
  # check_package <pkg-dir>; prints FAIL lines, returns non-zero on failure
  local dir="$1" fail=0
  local name
  name="$(basename "$dir")"
  local specs=("$dir"/*.spec)
  local spec="${specs[0]}"

  if [ ${#specs[@]} -ne 1 ] || [ ! -f "$spec" ]; then
    echo "FAIL: $name: exactly one .spec file is required"
    return 1
  fi

  local spec_name version release changelog
  spec_name="$(awk '/^Name:/{print $2; exit}' "$spec")"
  if [ -z "$spec_name" ]; then
    echo "FAIL: $name: missing Name: tag"
    fail=1
  elif [ "$spec_name" != "$name" ]; then
    echo "FAIL: $name: spec Name '$spec_name' != directory name"
    fail=1
  fi

  version="$(awk '/^Version:/{print $2; exit}' "$spec")"
  release="$(awk '/^Release:/{print $2; exit}' "$spec" | sed 's/%{.*//')"
  changelog="$(awk '/^%changelog/{getline; print $NF; exit}' "$spec")"
  [ "$changelog" = "${version}-${release}" ] \
    || { echo "FAIL: $name: changelog entry '$changelog' != Version-Release '${version}-${release}'"; fail=1; }

  # macros from external packages reach the shell literally in mock and die
  # as "fg: no job control" (AGENTS.md): BuildRequire their providers
  if grep -q '%go_vendor_license' "$spec" && ! grep -q '^BuildRequires:.*go-vendor-tools' "$spec"; then
    echo "FAIL: $name: uses %go_vendor_license_* without BuildRequires: go-vendor-tools"
    fail=1
  fi
  if grep -q '^%cargo_' "$spec" && ! grep -q '^BuildRequires:.*cargo-rpm-macros' "$spec"; then
    echo "FAIL: $name: uses %cargo_* without BuildRequires: cargo-rpm-macros"
    fail=1
  fi
  if grep -q '%pyproject_' "$spec" && ! grep -q '^BuildRequires:.*pyproject-rpm-macros' "$spec"; then
    echo "FAIL: $name: uses %pyproject_* without BuildRequires: pyproject-rpm-macros"
    fail=1
  fi
  # uv applies upstream's [tool.uv] override-dependencies where pip cannot
  # (hermes-agent's Pillow/browser-harness ResolutionImpossible)
  if grep -q 'uv pip install' "$spec" && ! grep -q '^BuildRequires:.*\<uv\>' "$spec"; then
    echo "FAIL: $name: uses 'uv pip install' without BuildRequires: uv"
    fail=1
  fi

  # pip/venv into the buildroot bundles manylinux libs with hashed sonames
  # whose versioned requires nothing provides: uninstallable rpm (AGENTS.md)
  if grep -Eq '(-m venv|pip +install)' "$spec"; then
    grep -q '__requires_exclude' "$spec" \
      || { echo "FAIL: $name: pip/venv install without __requires_exclude for hashed manylinux sonames"; fail=1; }
  fi

  # rpm rejects a changelog date whose weekday doesn't match ("bogus date")
  local centry wk cdate real
  centry="$(awk '/^%changelog/{getline; print; exit}' "$spec")"
  wk="$(awk '{print $2}' <<<"$centry")"
  cdate="$(awk '{print $3, $4, $5}' <<<"$centry")"
  real="$(LC_ALL=C date -d "$cdate" +%a 2>/dev/null || true)"
  if [ -n "$real" ] && [ "$wk" != "$real" ]; then
    echo "FAIL: $name: changelog weekday '$wk' != actual '$real' for '$cdate'"
    fail=1
  fi

  # Undefined macros pass through to scriptlets as literal text (the %__npm /
  # %pyproject_build_wheel failures): expand the spec fully, then flag
  # own-line %tokens that are not sections of THIS spec (sections are the
  # column-0 %lines in the source, so custom sections never false-positive)
  local expanded sections undefined
  expanded="$(rpmspec -P "$spec" 2>/dev/null || true)"
  sections="$(grep -oE '^%[a-zA-Z_][a-zA-Z0-9_]*' "$spec" | tr -d '%' || true)"
  undefined="$(echo "$expanded" | grep -oE '^[[:space:]]+%[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*$' \
    | tr -d ' %' | sort -u | { grep -vxF -f <(echo "$sections") || true; })"
  if [ -n "$undefined" ]; then
    echo "FAIL: $name: undefined macro in scriptlet: $(echo "$undefined" | head -1)"
    fail=1
  fi

  # rpm < 4.20 (EPEL) expands macros inside comments: a commented-out
  # %install/%files/... breaks the whole spec parse ("Name field must be
  # present") and parameterized macros (%meson et al) inject their entire
  # body as spec text — spell names out in prose instead. %{braced} forms
  # expand harmlessly and are allowed.
  if grep -qE '^\s*#.*[[:space:](>]%[a-zA-Z_][a-zA-Z0-9_]*([^a-zA-Z0-9_{]|$)' "$spec"; then
    echo "FAIL: $name: comment mentions a bare macro token (breaks rpm < 4.20/EPEL parse)"
    fail=1
  fi

  # install -D requires a FILE destination; a trailing slash fails at build time
  if grep -qE 'install +-([a-zA-Z]*D[a-zA-Z]*|D) +.*[^ ]/ *$' "$spec"; then
    echo "FAIL: $name: install -D with directory destination (needs explicit file path)"
    fail=1
  fi

  # Upstream theme install.sh scripts end with gtk-update-icon-cache, which
  # is absent from the minimal buildroot (caches are rpm file triggers).
  if grep -qE '^\s*\./install\.sh' "$spec" && ! grep -q 'gtk-update-icon-cache/d' "$spec"; then
    echo "FAIL: $name: runs ./install.sh but does not strip gtk-update-icon-cache"
    fail=1
  fi

  # Wallpaper collections are blind in a desktop unless its picker finds the
  # payload: GNOME/Budgie list gnome-background-properties XML only, Cinnamon
  # lists cinnamon-background-properties only, MATE lists
  # mate-background-properties only, xfdesktop lists xfce4/backdrops only,
  # Plasma lists kpackages under wallpapers/ only, everything else reads the
  # raw backgrounds/ footprint. All five consumers must ship together.
  if grep -q 'backgrounds/' "$spec" \
    || grep -q 'gnome-background-properties' "$spec" \
    || grep -q '%{_datadir}/wallpapers/' "$spec"; then
    grep -q '%{_datadir}/backgrounds/' "$spec" \
      || { echo "FAIL: $name: wallpaper without a backgrounds/ raw footprint"; fail=1; }
    for consumer in gnome-background-properties cinnamon-background-properties \
      mate-background-properties 'xfce4/backdrops'; do
      grep -q "%{_datadir}/$consumer" "$spec" \
        || { echo "FAIL: $name: wallpaper without %{_datadir}/$consumer entries (invisible in that DE)"; fail=1; }
    done
    # Plasma's chooser only lists kpackages sitting directly under wallpapers/
    # (proven against real packagefinder.cpp findAll: a metadata-less parent
    # dir enqueues its children but marks them in `folders` during the root
    # enumeration, so addPackage() skips them — kpackages nested under a
    # collection dir never appear). One kpackage per image, prefix-named
    # %{name}-<image>/, as plasma-workspace-wallpapers does
    if grep -qE '%\{_datadir\}/wallpapers/%\{name\}/(contents|metadata)' "$spec"; then
      echo "FAIL: $name: nested Plasma kpackage (chooser does not list them; use prefix-named wallpapers/%{name}-<image>/)"
      fail=1
    fi
    grep -q '%{_datadir}/wallpapers/%{name}-' "$spec" \
      || { echo "FAIL: $name: Plasma kpackages not as prefix-named wallpapers/%{name}-<image>/"; fail=1; }
    if ! grep -qE '[0-9]+x[0-9]+' "$spec"; then
      echo "FAIL: $name: KDE kpackage links without WxH resolution names (broken previews)"
      fail=1
    fi
  fi

  # fish plugin installs: vendor dirs are vendor_conf.d/vendor_functions.d/
  # vendor_completions.d — the bare name (a forgotten .d) silently installs
  # to a dead path that %files globs then miss
  if grep -qE 'vendor_(conf|functions|completions)($|[^d.])' "$spec"; then
    echo "FAIL: $name: fish vendor dir without .d suffix"
    fail=1
  fi

  if grep -qE '^Source[0-9]*:.*%(\{_?target_cpu\}|{_?arch\}|npm_arch)' "$spec"; then
    echo "FAIL: $name: Source URLs must not depend on build arch (SRPM builder arch is arbitrary)"
    fail=1
  fi

  # Scriptlets run in a minimal chroot: every interpreter they invoke must be
  # BuildRequired; bash/sh are always present (they run the scriptlet itself).
  local scriptlets tools tool
  scriptlets="$(awk '/^%(build|check|install)$/{f=1;next} /^%[a-zA-Z]/{f=0} f' "$spec")"

  # COPR runs rpmbuild unprivileged: writing to system paths outside
  # %{buildroot} dies with permission denied (the ghostty harfbuzz header case)
  if echo "$scriptlets" \
    | grep -E '(>>>?|(^|[[:space:];&])(install|cp|mv) +|mkdir +-[dp] +)[^|]*[[:space:]]/(usr|etc|opt|var)([[:space:]/]|$)' \
    | grep -qv buildroot; then
    echo "FAIL: $name: scriptlet writes outside the buildroot"
    fail=1
  fi

  tools="$(echo "$scriptlets" | grep -oE '(^|[;&|[:space:]])(python3|node|npm|cargo|go) ' | grep -oE '(python3|node|npm|cargo|go)' | sort -u || true)"
  for tool in $tools; do
    grep -qE "^BuildRequires:.*${tool}\b" "$spec" \
      || { echo "FAIL: $name: '$tool' used in scriptlet but not BuildRequired"; fail=1; }
  done

  if [ -f "$dir/upstream" ]; then
    local src
    src="$(cat "$dir/upstream")"
    [[ "$src" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ || "$src" == npm:* \
       || "$src" == gitlab:* || "$src" == codeberg:* || "$src" == forgejo:* \
       || "$src" == tags:* \
       || "$src" =~ ^https?:// ]] \
      || { echo "FAIL: $name: invalid upstream '$src' (expected 'owner/repo', '<forge>:owner/repo', 'npm:<package>' or an URL)"; fail=1; }
    [ -n "$(upstream_home "$src")" ] \
      || { echo "FAIL: $name: upstream '$src' has no mappable homepage"; fail=1; }
  fi

  return "$fail"
}
