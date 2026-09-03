---
name: aganitha-publish-skill
description: Publishes a skill you have written so your group can discover and install it — a step-by-step flow with checklists that places the skill in the repo that owns it, bundles it into a pack, tests both the skill and the pack, adds the group's GitHub repo as a pack source, and publishes it (a group's own repo for special packs; the central aganitha/agent-skills only for org-wide common ones). Use when someone has a working skill and asks "how do I publish this", "make a pack", "share this with my group", "add it to the registry", or "how do people install my skill". Writing the skill itself is skill-creator; installing an existing one is aganitha-install-pack — this is the step in between that makes a written skill shareable.
---

# Aganitha Publish Skill

`sp` is a shorter alias for `skills-pack` — either name works everywhere
below.

This skill turns a written, locally-tested skill into something a group can
install by name. It assumes the skill already exists as a `SKILL.md`. If it
does not yet, write it with `skill-creator` first; if you only want to install
something that already exists, use `aganitha-install-pack`; if you are looking
for whether a skill exists at all, use `aganitha-find-skill`. This is the step
in between.

Work the steps in order; each ends in a checklist to confirm before moving on.
Publishing opens a pull request and can add committed configuration, so confirm
the placement and the pack with the user, and **do not open a PR or push
without their go-ahead.**

<!-- Two distinctions run through everything below. (1) A **repo** is a GitHub
org/repo (`my-group/pricing`) — where a skill's files live; it appears after
`--from`. A **pack** is a name chosen inside a `.pack` file (`group-flow`) — not
a repo, need not match one; it appears after `install pack`. (2) Where a skill
lives is an OWNERSHIP decision; where its pack lives is a DISCOVERY decision.
They are independent — a pack is only pointers and can list skills from many
repos. Keep both straight when talking to the user. -->

## 1. Place the skill where it is owned

A skill belongs in the git repo that owns the thing it teaches, so whoever
changes that tool changes the skill in the same commit. That is what keeps it
maintainable. This is an ownership decision, and it is separate from where the
pack will live.

**Verify before moving on:**

- [ ] The `SKILL.md` is in the repo that owns the tool/workflow it teaches.
- [ ] `name` in the frontmatter matches the folder exactly and carries the
      `aganitha-` prefix (an unscoped name silently clobbers others on install).
- [ ] The description says what it does *and* the real phrases that should
      trigger it — that is what makes it fire.

## 2. Test the skill locally

Before investing in a pack, confirm the skill itself works. Install it straight
from its repo with the underlying `skills` tool — the one tight loop where you
reach past `skills-pack`:

```bash
cd /path/to/its-repo
skills add . --skill aganitha-your-skill --agent claude-code universal --copy -y
```

Then say one of its trigger phrases and watch whether it fires. If it does not,
**fix the description, not the body** — a longer body never rescues a vague
trigger.

**Verify before moving on:**

- [ ] `skills add` reported the skill installed (`✓ ... (copied)`).
- [ ] A real trigger phrase actually activated the skill.
- [ ] Any misfire was fixed in the description, then re-tested.

## 3. Decide where the pack lives: common vs special

A pack is a list of pointers; its home is a discovery decision, not an
ownership one. There are exactly two homes — recommend the group-owned one
unless the skill is genuinely org-wide:

- **Special (recommend by default)** — useful mainly to one group. The pack
  lives in **one repo per group** (the group's own `agent-skills`-shaped repo).
  Projects in the group add that repo as a source and install what they need.
  No central PR, no cross-group review; the group owns its curation.
- **Common (org-wide only)** — useful to every Aganitha project regardless of
  domain (the workflow lifecycle, the skills system itself). The pack goes into
  the central `aganitha/agent-skills` via PR.

Either way, the pack holds only pointers — the skill's content stays in the
repo that owns it (step 1). If it is unclear whether a skill is org-wide, it is
not: choose special. A special pack can be **promoted** later — move the
pointer into `aganitha/agent-skills`; the skill's content never moves.

**Verify before moving on:**

- [ ] Placement chosen and confirmed with the user: special (group repo) or
      common (central).
- [ ] The choice is about *discovery*, not ownership — the skill still lives in
      its own repo.

## 4. Write or extend the pack

A pack is a plain-text file under `packs/`, a list of pointers and nothing
more:

```text
# packs/group-flow.pack
# name: group-flow
# description: One sentence — who it is for and what installing it sets up.

git@github:aganitha/myproject@aganitha-pricing-report
git@github:aganitha/agent-skills@aganitha-standup-notes
https://github.com/anthropics/skills.git@skill-creator
```

Read each line as `<repo>@<skill>`: the repo the skill lives in, then the
skill's frontmatter `name`. Entries in one pack may point at different repos —
that is normal.

**Verify before moving on:**

- [ ] If a pack for the group already exists, a line was added to it rather
      than a new pack created.
- [ ] Every selector after `@` equals the target's frontmatter `name` exactly —
      a mismatch makes the install *silently* skip that skill.
- [ ] Entries are explicit `repo@skill` lines, not a bare repo line (a bare
      line installs *every* skill in the repo).

## 5. Test the pack

Exercise the pack from the repo holding the `.pack` file, before pushing. For a
fully-local check, temporarily use `.` as the repo in each line
(`.@aganitha-pricing-report`) so nothing is fetched:

```bash
sp list --from .
sp info group-flow --from .
sp preview group-flow --from .
```

`sp preview` prints the exact file each skill resolved to — a skill can sit
under any `skills/` directory at any depth (e.g.
`services/pricing/skills/aganitha-pricing-report/`), but not under `examples/`,
`test/`, `tests/`, `.claude/`, or `.agents/`. Then confirm the canonical remote
form once the skill's repo is pushed:

```bash
sp update --from github:my-group/agent-skills
sp preview group-flow --from github:my-group/agent-skills
```

**Verify before moving on:**

- [ ] `sp preview` resolved every skill the pack lists (none reported missing).
- [ ] Each skill resolved to the file path you expected.
- [ ] Every entry is back to its canonical `github:...` form — no `.` or local
      path left in a pack that will be committed.

## 6. Add the group repo as a source

For a **special** pack, this is how each project opts in to the group's
repo — the step that makes it discoverable without touching the central
registry. (Skip for a **common** pack; it comes from the built-in default.)

```bash
sp source add github:aganitha/myproject   # -g for this machine only
sp source list
```

A source only widens what discovery sees; it never sets precedence, and the
built-in default always stays in the set.

**Verify before moving on:**

- [ ] `sp source list` shows the group repo under the project's sources.
- [ ] `skills-pack.sources` is committed when the repo is part of the group's
      normal environment (use `-g` only for a single machine).

## 7. Publish

Confirm placement (step 3) and the tested pack with the user, then:

- **Special** — commit the `.pack` in the group's own repo (the skill's content
  is already committed in its owning repo).
- **Common** — commit the `SKILL.md` under `skills/` and the pack line in
  `aganitha/agent-skills`.

Run `make test` in whichever repo holds the pack, then open the PR:

```bash
make test        # validates pack metadata and that entries are well-formed
```

**Verify before moving on:**

- [ ] `make test` passed in the repo holding the pack.
- [ ] The user approved opening the PR / committing.
- [ ] Skill content and pack pointer are committed to the right repos (content
      never copied into the pack's repo).

## 8. Verify it is discoverable

After the pack merges (or the source is added):

```bash
sp update
sp info group-flow
sp search aganitha-your-skill
```

**Verify:**

- [ ] The skill appears with the expected source.
- [ ] `sp info` / `sp registry` prints a runnable `install` command for it —
      hand the user *that* command rather than reconstructing one; it already
      carries `--from`/`--from-pack` when a name collides.

## What to commit

Commit: the `SKILL.md` in the repo that owns it; the `.pack` pointer;
`skills-pack.sources` when sources are shared; `skills-pack.lock.json` after an
install.

Never commit: `.claude/skills/` or `.agents/skills/` (install artifacts, like
`node_modules`); local-path sources (`.`, `/Users/...`) in a shared `.pack` or
lock file.
