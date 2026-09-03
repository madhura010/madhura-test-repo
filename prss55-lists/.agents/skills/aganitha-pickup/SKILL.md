---
name: aganitha-pickup
description: Start work from a project's docs/handoff.md and verify the summary against the current repository before acting. Use when joining an existing project, resuming paused work, taking over from another person or agent, or asking what to do next.
---

# Aganitha Pickup

Turn the latest handoff into a verified working context. Treat it as a
compact, fallible checkpoint—not as unquestionable truth.

## Read the minimum context

1. Read `docs/handoff.md`. If it is missing, say so and recommend running
   `aganitha-handoff` before a non-trivial change; continue only with explicit
   evidence from the repository.
2. Read the repository's `AGENTS.md` instructions and the specific files or
   docs linked by the handoff.
3. Check the current branch, `git status`, and recent commits.
4. Run the smallest relevant status/test command needed to verify the
   handoff's claims.

Do not load unrelated project history or reproduce the entire prior session.

## Report the pickup

Return a concise summary with:

- objective and success criteria;
- completed versus active work;
- decisions and constraints that still apply;
- evidence that agrees or conflicts with the handoff;
- one immediate next action;
- blockers and risks.

When the repository disagrees with the handoff, lead with the discrepancy and
use current repository evidence. Do not silently continue from stale claims.

## Handoff lifecycle warning

Tell the operator that `docs/handoff.md` is a disposable snapshot. New work
can make it stale, and a later operator may delete or replace it as context is
reduced. After meaningful progress, regenerate it with `aganitha-handoff`.

Do not modify or delete the handoff during pickup unless the user explicitly
asks; pickup is primarily a read-and-verify operation.
