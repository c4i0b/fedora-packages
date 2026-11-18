#!/usr/bin/env python3
"""Latest-version resolver for the autoupdate job. Pure selection logic
(normalization, strict-first tag choice, JSON field extraction) is unit
tested in tools/tests; this module only adds network I/O and concurrency.
Emits the exact TSV contract the bash orchestration consumes:

  resolved/<pkg>   "latest\t<pkg>\t<version>"  (missing file = failure)
  stats file       "REQ\t<pkg>\t<code>\t<attempt>\t<rlrem>" and "RETRY"
  stderr           ::notice::[rate] / [tags-fallback] / ::warning::

stdlib only: python3 is present on every runner, and urllib's HTTP/1.1
sidesteps the CDN quirks that forced curl workarounds before.
"""

import concurrent.futures
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

SUCCESS_DELAY = float(os.environ.get("SUCCESS_DELAY", "0.3"))
RETRY_BASE = int(os.environ.get("RETRY_BASE", "3"))
WORKERS = 8

# plain "v1.2.3" / "1.2.3" tags (strict pass); component tags like
# "vscode-v1.0.0" or "rust-v0.163.0" only feed the fallback pass — a repo
# mixing component and plain tags must resolve a plain one (sibling-repo
# drift fix; anomalyco/opencode and jdx/mise are the live examples)
PLAIN_TAG = re.compile(r"^v?([0-9][A-Za-z0-9._+~-]*)$")
COMPONENT_TAG = re.compile(r"^.+-v([0-9][A-Za-z0-9._+~-]*)$")
PRERELEASE = re.compile(r"[-.](rc|beta|alpha|pre|dev|preview|b|a)\d*$", re.I)


# ---- pure helpers (unit tested) -------------------------------------------------

def normalize_tag(tag):
    """(version, strict) for a tag name, or None when it is not a version
    tag at all (junk like "_pr-attachments" or "v.1.5.5")."""
    m = PLAIN_TAG.match(tag)
    if m:
        return m.group(1), True
    m = COMPONENT_TAG.match(tag)
    if m:
        return m.group(1), False
    return None


def ver_key(version):
    """Total order over version strings: numeric segments compare as
    integers, letter suffixes sort after their base, and a prerelease
    suffix never outranks the release it belongs to."""
    m = PRERELEASE.search(version)
    core, penalty = (version[:m.start()], 0) if m else (version, 1)
    segs = []
    for seg in re.split(r"[._+~-]", core):
        sm = re.match(r"(\d*)([A-Za-z]*)", seg)
        segs.append((int(sm.group(1) or 0), sm.group(2)))
    return (tuple(segs), penalty)


def select_tag(tags):
    """Latest version from an unordered tag list, strict-first: plain
    v<version> tags win; component <prefix>-v<version> tags are only
    consulted when no plain version tag exists."""
    plain, comp = [], []
    for t in tags:
        n = normalize_tag(t)
        if not n:
            continue
        (plain if n[1] else comp).append(n[0])
    pool = plain or comp
    return max(pool, key=ver_key) if pool else None


def strip_release_tag(tag_name):
    """releases/latest tag_name to a version: drop a leading v, then a
    component prefix ("rust-v0.163.0" -> "0.163.0")."""
    v = tag_name[1:] if tag_name.startswith("v") else tag_name
    m = COMPONENT_TAG.match(tag_name)
    return m.group(1) if m else v


def json_field(body, field):
    """First occurrence of a key in compact or pretty JSON, recursing into
    arrays (None on any parse failure — the caller decides whether that is
    fatal)."""
    try:
        doc = json.loads(body)
    except (ValueError, TypeError):
        return None

    def walk(node):
        if isinstance(node, dict):
            if node.get(field) is not None:
                return node[field]
            for v in node.values():
                hit = walk(v)
                if hit is not None:
                    return hit
        elif isinstance(node, list):
            for v in node:
                hit = walk(v)
                if hit is not None:
                    return hit
        return None

    return walk(doc)


# ---- HTTP (auth, retry/backoff, rate stats) -------------------------------------

class Http:
    def __init__(self, stats_path):
        self.stats_path = stats_path
        self.lock = threading.Lock()

    def _stat(self, line):
        with self.lock:
            with open(self.stats_path, "a") as f:
                f.write(line + "\n")

    def get(self, pkg, url, headers=()):
        """200 body as text, else None. Retries 403/429 honoring
        Retry-After, exponential backoff otherwise (GitHub throttles
        bursts even when authenticated)."""
        for attempt in range(1, 6):
            req = urllib.request.Request(url, headers=dict(headers))
            t0 = time.monotonic()
            code, body, hdrs = 0, None, {}
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    code, body, hdrs = r.status, r.read(), r.headers
            except urllib.error.HTTPError as e:
                code, hdrs = e.code, e.headers or {}
            except Exception as e:  # noqa: BLE001 - any transport error
                print(f"::notice::[rate] pkg={pkg} transport error: {e}",
                      file=sys.stderr)
            elapsed = int((time.monotonic() - t0) * 1000)
            rlrem = hdrs.get("x-ratelimit-remaining", "-")
            self._stat(f"REQ\t{pkg}\t{code}\t{attempt}\t{rlrem}")
            if code == 200 and body is not None:
                print(f"::notice::[rate] pkg={pkg} attempt={attempt} "
                      f"status=200 wait={SUCCESS_DELAY} wait_src=success-delay "
                      f"elapsed={elapsed}ms rlrem={rlrem}", file=sys.stderr)
                time.sleep(SUCCESS_DELAY)
                return body.decode("utf-8", "replace")
            if code in (403, 429):
                wait = hdrs.get("retry-after")
                src = "retry-after" if wait else "computed"
                if not wait:
                    wait = RETRY_BASE * (1 << (attempt - 1))
                self._stat("RETRY")
                print(f"::notice::[rate] pkg={pkg} attempt={attempt} "
                      f"status={code} wait={wait} wait_src={src} "
                      f"elapsed={elapsed}ms rlrem={rlrem}", file=sys.stderr)
                time.sleep(float(wait))
            else:
                print(f"::notice::[rate] pkg={pkg} attempt={attempt} "
                      f"status={code} wait=0 wait_src=none "
                      f"elapsed={elapsed}ms rlrem={rlrem}", file=sys.stderr)
                return None
        return None


# ---- resolvers per upstream form ------------------------------------------------

def gh_headers():
    tok = os.environ.get("GITHUB_TOKEN")
    return [("Authorization", f"Bearer {tok}")] if tok else []


def gl_headers():
    tok = os.environ.get("GITLAB_TOKEN")
    return [("PRIVATE-TOKEN", tok)] if tok else []


def ls_remote_tags(url):
    """All tag names of a repo, any forge, zero API quota. None on
    transport failure (resolver treats it as unresolved)."""
    r = subprocess.run(["git", "ls-remote", "--tags", url],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return [l.split("\t")[1][len("refs/tags/"):]
            for l in r.stdout.splitlines()
            if "\trefs/tags/" in l and not l.endswith("^{}")]


def resolve_source(source, pkg, http):
    """Latest version string for one `upstream` declaration, or None."""
    if source.startswith("tags:"):
        # forge-agnostic tag listing (nested prefixes reuse their base)
        repo = source[len("tags:"):]
        if repo.startswith("gitlab:"):
            url = f"https://gitlab.com/{repo[len('gitlab:'):]}"
        elif repo.startswith("codeberg:"):
            url = f"https://codeberg.org/{repo[len('codeberg:'):]}"
        elif repo.startswith("forgejo:"):
            url = f"{os.environ.get('FORGEJO_HOME', 'https://codeberg.org')}/{repo[len('forgejo:'):]}"
        else:
            url = f"https://github.com/{repo}"
        tags = ls_remote_tags(url)
        return select_tag(tags) if tags else None

    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", source):
        # GitHub Releases; only-prerelease repos 404 here -> tags fallback
        body = http.get(pkg, f"https://api.github.com/repos/{source}/releases/latest",
                        gh_headers())
        tag = json_field(body, "tag_name") if body else None
        if tag:
            return strip_release_tag(tag)
        body = http.get(pkg, f"https://api.github.com/repos/{source}/tags?per_page=1",
                        gh_headers())
        tag = json_field(body, "name") if body else None
        if tag:
            print(f"::notice::[tags-fallback] pkg={pkg} source={source} "
                  f"(no GitHub Releases; releases/latest is re-checked every run)",
                  file=sys.stderr)
            return strip_release_tag(tag)
        return None

    if source.startswith("npm:"):
        slug = source[len("npm:"):].replace("/", "%2f")
        body = http.get(pkg, f"https://registry.npmjs.org/{slug}/latest")
        return json_field(body, "version") if body else None

    if source.startswith("gitlab:"):
        proj = source[len("gitlab:"):].replace("/", "%2f")
        body = http.get(pkg, f"https://gitlab.com/api/v4/projects/{proj}/releases",
                        gl_headers())
        tag = json_field(body, "tag_name") if body else None
        if not tag:
            body = http.get(pkg,
                            f"https://gitlab.com/api/v4/projects/{proj}/repository/tags?per_page=1",
                            gl_headers())
            tag = json_field(body, "name") if body else None
        return strip_release_tag(tag) if tag else None

    if source.startswith(("codeberg:", "forgejo:")):
        src = source.split(":", 1)[1]
        base = os.environ.get("FORGEJO_API", "https://codeberg.org/api/v1") \
            if source.startswith("forgejo:") else "https://codeberg.org/api/v1"
        body = http.get(pkg, f"{base}/repos/{src}/releases?limit=1", gh_headers())
        tag = json_field(body, "tag_name") if body else None
        if not tag:
            body = http.get(pkg, f"{base}/repos/{src}/tags?limit=1", gh_headers())
            tag = json_field(body, "name") if body else None
        return strip_release_tag(tag) if tag else None

    print(f"::warning::{pkg}: unrecognized upstream syntax: {source}",
          file=sys.stderr)
    return None


def main():
    if len(sys.argv) != 4:
        sys.exit(f"usage: resolve.py <repo-root> <resolved-dir> <stats-file>")
    root, resolved_dir, stats_path = sys.argv[1:]
    http = Http(stats_path)
    upstreams = []
    for dirpath, _, files in os.walk(os.path.join(root, "packages")):
        if "upstream" in files and os.path.dirname(dirpath) == os.path.join(root, "packages"):
            with open(os.path.join(dirpath, "upstream")) as f:
                upstreams.append((os.path.basename(dirpath), f.read().strip()))

    def work(item):
        pkg, source = item
        version = resolve_source(source, pkg, http)
        if not version:
            print(f"::warning::{pkg}: could not resolve latest release of {source}",
                  file=sys.stderr)
            return
        with open(os.path.join(resolved_dir, pkg), "w") as f:
            f.write(f"latest\t{pkg}\t{version}\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(ex.map(work, upstreams))


if __name__ == "__main__":
    main()
