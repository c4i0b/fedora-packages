# Automatic updates

Schedule slots are sized from measured bump yield per slot (90 days of
run history, catch-up runs excluded), not even spacing — method and
rationale: agent-skills `gh-actions-conventions` rule 14
(~/Projects/agent-skills/skills/foundations/gh-actions-conventions/SKILL.md).
The same slots apply repo-family-wide (opensuse-packages); badges run 2 h
behind each autoupdate slot.

- `packages/<name>/upstream` selects the tracker: `owner/repo` → GitHub
  Releases latest (leading `v` stripped), `tags:owner/repo` → latest git tag
  via `ls-remote` (tags-only repos, any forge, zero API quota) or
  `npm:<package>` → npm dist-tag `latest`.
- Resolution lives in `.github/scripts/resolve.py`; `autoupdate.sh` only
  orchestrates (branch, commits, gate). Tag selection is strict-first:
  plain `v<version>` tags win, component tags like `vscode-v1.0.0` or
  ghostty's `vt-1.0.0` only feed a fallback pass (mixed-tag repos:
  anomalyco/opencode, jdx/mise, Faugus/faugus-launcher). A downgrade guard
  (`sort -V` against the spec Version) blocks publish-ordered
  `releases/latest` surprises — never remove it without replacing it.
  The pure selection logic is unit-tested in `tools/tests/` (real tag
  lists as fixtures, no network); `tools/test.sh` runs the suite inside
  the gate because the SRPM gate alone would happily build a
  semantically wrong bump whose tarball exists.
- JSON responses are parsed with `json.loads` in the resolver (the old
  `grep -oE` trick died with the bash version; do not resurrect it).
- Scheduled multiple times per day (see `autoupdate.yml` for the cron); an
  in-script empty-commit keepalive (only after 45 idle days) defeats
  GitHub's 60-day inactivity rule — do not use keepalive-workflow actions
  (the popular one is ToS-blocked and breaks workflows).
- Renovate was evaluated and rejected — do not reintroduce without
  discussion.
- One push per bump: the COPR webhook fires on pushes of any ref, so the
  bump branch is never pushed pre-gate (the workflow publishes it only
  when the gate fails, for inspection). Pushing it would build every
  bumped package twice (branch push + merge push).
- To skip or downgrade a release: never add Epoch; push a commit message
  `autoupdate: override <version>` on the package (the bot respects it).
- No `upstream` file = manual pin. Legitimate when the forge has no
  parseable tags/releases or tracking would mis-bump (version-scheme
  mismatch, feature bands); say so in a leading spec comment. Current
  manual-update packages: asleap, ccze, cozette-fonts, crunch,
  press-start-2p-fonts, aesthetic-wallpapers, dotnet-msft, fish-hydro,
  fish-z, hostapd-wpe, unimatrix, wezterm. Floating branch-head URLs are
  never acceptable — pin a commit (`%global commit`).
