# Archived OpenSpec changes

Completed changes live here once their implementation is **merged to `main` and
deployed**. This keeps `openspec/changes/` scoped to in-flight work while
preserving finished proposals as a historical record.

## Convention

- **Path:** `openspec/changes/archive/YYYY-MM-DD-<change-name>/`
  (the date is the day the change was archived).
- The change folder moves **verbatim** — `proposal.md`, `design.md`,
  `tasks.md`, and any `specs/` delta files travel with it.
- Archive a change only when **every task in its `tasks.md` is checked** and the
  work is live in production.

## How to archive

Use the repo's `/openspec-archive-change` skill (it applies this naming and
checks task completion). If the `openspec` CLI is unavailable, do it by hand:

```bash
mkdir -p openspec/changes/archive
git mv openspec/changes/<name> openspec/changes/archive/$(date +%F)-<name>
```

## Note on canonical specs

The canonical spec tree lives at [`openspec/specs/`](../../specs/) — the current
source of truth per capability. When archiving a change, **fold its `specs/`
deltas into that tree first** (`ADDED` appends, `MODIFIED` replaces in place,
`REMOVED` deletes), then move the change here. See `openspec/specs/README.md`.
