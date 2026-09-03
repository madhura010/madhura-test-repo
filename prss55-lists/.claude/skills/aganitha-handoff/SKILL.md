---
name: aganitha-handoff
description: Create or update docs/handoff.md as a compact, shareable transfer summary for the next person or agent. Use when pausing work, handing a project to someone else, ending a session, or asking what the next operator needs to know; prune stale context and leave one actionable next step.
---

# Aganitha Handoff

Create a current transfer point, not a journal and not a dump of the
conversation. The handoff must let a new operator continue safely from the
repository without reconstructing the whole session.

## Inspect before writing

Read only the material needed to describe the current work:

- repository instructions (`AGENTS.md` and closer instructions);
- existing `docs/handoff.md`, if present;
- relevant design/status/TODO/progress docs;
- `git status`, the current branch, and recent commits;
- files and tests touched by the active work.

Separate observed facts from inferences. Do not claim a test passed unless you
ran it or can cite a recorded result.

## Write `docs/handoff.md`

Keep the document concise and update it in place. Use this structure:

```markdown
# Handoff

Updated: YYYY-MM-DD

## Objective
What outcome is being pursued and how success will be recognized.

## Current state
What is complete, in progress, and intentionally unchanged.

## Decisions and constraints
Only decisions that affect the next operator's choices.

## Evidence
Tests/checks run, relevant commits, and known unverified paths.

## Next action
One concrete next step, with the relevant file or command.

## Blockers and risks
External dependencies, uncertainty, or safe-to-avoid pitfalls.
```

Prefer links to repository files over copied paragraphs. Mention uncommitted
changes and their intended scope. Keep only context that changes what the next
operator should do; remove stale history, superseded options, and narration.

## Safety rules

- Do not rewrite project history or discard work to make the handoff tidy.
- Do not mark work complete when tests, review, or user decisions remain.
- If the objective is unclear, record the uncertainty and the smallest safe
  clarification needed.
- If `docs/handoff.md` does not exist, create it; do not stop merely because
  the project has no prior handoff.

The handoff is a disposable checkpoint. After the next operator makes
meaningful progress, it may be deleted or replaced; regenerate it before the
next transfer so it describes the new state.
