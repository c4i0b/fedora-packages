# Automatic updates

- `packages/<name>/upstream` selects the tracker: `owner/repo` → GitHub
  Releases latest (leading `v` stripped), `tags:owner/repo` → latest git tag
  via `ls-remote` (tags-only repos, any forge, zero API quota) or
  `npm:<package>` → npm dist-tag `latest`.
- Registry/GitHub API responses are **compact JSON (single line)**: extract
  fields with `grep -oE`, never with per-line `awk -F'"'`.
- Scheduled multiple times per day (see `autoupdate.yml` for the cron); an
  in-script empty-commit keepalive (only after 45 idle days) defeats
  GitHub's 60-day inactivity rule — do not use keepalive-workflow actions
  (the popular one is ToS-blocked and breaks workflows).
- Renovate was evaluated and rejected — do not reintroduce without
  discussion.
- To skip or downgrade a release: never add Epoch; push a commit message
  `autoupdate: override <version>` on the package (the bot respects it).
