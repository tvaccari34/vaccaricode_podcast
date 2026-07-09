# Canonical specs

This tree is the **current source of truth** for what the system does, organized
by capability: `openspec/specs/<capability>/spec.md`. Each file has a `## Purpose`
and a `## Requirements` section of `### Requirement:` entries (with `#### Scenario:`
blocks) written as `SHALL` statements.

## Relationship to `changes/`

- `openspec/changes/<name>/specs/<capability>/spec.md` files are **deltas** —
  `## ADDED / MODIFIED / REMOVED / RENAMED Requirements` — describing how a change
  alters the canonical specs.
- When a change is archived, its deltas are **folded into this tree**: `ADDED`
  appends a requirement, `MODIFIED` replaces one in place, `REMOVED` deletes it,
  `RENAMED` re-keys it. Deltas are applied in the change's created-date order.
- These files were bootstrapped by folding all changes to date (see the
  `chore(openspec): bootstrap canonical specs` PR). Purpose lines are concise
  editorial summaries; the requirement/scenario text is copied verbatim from the
  deltas.

## Keeping it in sync

When you archive a completed change, apply its deltas here before (or as part of)
the move — the `/openspec-archive-change` skill's sync step handles this, or do it
by hand following the operations above.
