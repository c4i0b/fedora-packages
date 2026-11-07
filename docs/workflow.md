# Task tracking & orchestration (optional — beads)

Activation is by availability: if `command -v bd` succeeds on the host,
prefer beads over ad-hoc TODO lists for multi-step work; if it fails,
proceed without it (no error, no setup attempt).

bd runs on the HOST (like gh) — it is not part of the tooling container.

## Tracking

- `bd prime` for full workflow context before starting
- claim with `bd update <id> --claim`, close with `bd close <id>`
- persistent memory goes in `bd remember` — no MEMORY.md, no markdown TODOs
- never commit, push or sync the beads database unless explicitly asked
  (`.beads/` is gitignored: task state is local, not repo source)

## Orchestration — parallel execution of the bd task graph

When more than one task is ready, the main session acts as orchestrator,
not sole implementer (this repo is highly parallelizable: package work is
independent per `packages/<name>/`, and concurrent tooling-container runs
are safe — the repo mount is `:z`-labeled for exactly that).

1. **Delegate everything ready**: `bd ready` → claim → spawn one background
   subagent per ready task. Each delegation carries the full task spec: bd
   description plus the relevant doc references (e.g. the packaging quirk
   page for its ecosystem) and the golden rules from `AGENTS.md`.
2. **Validate the agent's report, not redundantly**: agents return their
   command output (`just test`, `just srpm <name>`) as evidence; verify it
   and review the diff. Re-run yourself only when the report is incomplete
   or suspicious.
3. **Scoped work per agent**: one agent per package dir — concurrent agents
   never edit the same files. The repo-wide `just test`/`just validate` gate
   runs when the tree has no parallel WIP (before push), not as each
   agent's exit condition.
4. **Commit per task**, conventional message, then `bd close <id>`.
5. **Cascade immediately**: after each close, re-run `bd ready` and delegate
   newly unblocked tasks right away — don't batch waves.
6. **Loop** until nothing is ready; hand off with the status of open and
   blocked tasks.

Rules: only claim what you will actually work on now; never commit red —
if an agent's report fails validation, fix or re-delegate before moving on.
