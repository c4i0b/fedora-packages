#!/usr/bin/env bash
# Central host detection for the packages repo. Derive git host/owner/repo
# and the web/raw/api bases from the origin remote so scripts don't hardcode
# github.com. Falls back to github.com when the remote doesn't parse cleanly.
host_detect() {
  local url="${1:-}"
  [ -n "$url" ] || url="$(git -C "${root:-$(pwd)}" remote get-url origin 2>/dev/null || true)"
  GIT_URL="$url"
  GIT_HOST=""
  GIT_OWNER=""
  GIT_REPO=""
  # accepts https://host/owner/repo.git, git@host:owner/repo.git and bare
  # forms; nested groups (gitlab) keep only the last path segment as owner
  if [[ "$url" =~ ^[a-zA-Z][a-zA-Z0-9+.-]*://([^/]+)/(.+)/([^/]+?)(\.git)?/?$ ]]; then
    GIT_HOST="${BASH_REMATCH[1]}"
    GIT_OWNER="${BASH_REMATCH[2]##*/}"
    GIT_REPO="${BASH_REMATCH[3]}"
  elif [[ "$url" =~ ^([^@]+@)?([^:/]+):(.+)/([^/]+?)(\.git)?/?$ ]]; then
    GIT_HOST="${BASH_REMATCH[2]}"
    GIT_OWNER="${BASH_REMATCH[3]##*/}"
    GIT_REPO="${BASH_REMATCH[4]}"
  fi
  GIT_HOST="${GIT_HOST##*@}"
  GIT_HOST="${GIT_HOST%%:*}"
  GIT_REPO="${GIT_REPO%.git}"
  [ -n "$GIT_HOST" ] || GIT_HOST="github.com"
  [ -n "$GIT_OWNER" ] || GIT_OWNER=""
  [ -n "$GIT_REPO" ] || GIT_REPO=""
  GIT_REPO_CLEAN="${GIT_REPO%.git}"
  GIT_SLUG="${GIT_OWNER}/${GIT_REPO_CLEAN}"
  case "$GIT_HOST" in
    github.com)
      GIT_WEB_BASE="https://github.com"
      GIT_RAW_BASE="https://raw.githubusercontent.com"
      GIT_API_BASE="https://api.github.com"
      ;;
    gitlab.com)
      GIT_WEB_BASE="https://gitlab.com"
      GIT_RAW_BASE="https://gitlab.com"
      GIT_API_BASE="https://gitlab.com/api/v4"
      ;;
    codeberg.org)
      GIT_WEB_BASE="https://codeberg.org"
      GIT_RAW_BASE="https://codeberg.org"
      GIT_API_BASE="https://codeberg.org/api/v1"
      ;;
    *)
      GIT_WEB_BASE="https://$GIT_HOST"
      GIT_RAW_BASE="https://$GIT_HOST"
      GIT_API_BASE="https://$GIT_HOST/api/v1"
      ;;
  esac
}
# no "$@" here: sourcing scripts must not leak their own positional args
# in as a URL (host_detect defaults to the origin remote when argless)
host_detect
