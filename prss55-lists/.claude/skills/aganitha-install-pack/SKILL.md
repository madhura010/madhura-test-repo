---
name: aganitha-install-pack
description: Installs an approved skill pack or individual skill into the current project using skills-pack, including packs from non-default sources. Use when someone says to install, add, set up, get, or restore a skill or pack. Locates the right target first (delegating a vague request to aganitha-find-skill), confirms the exact pack or skill, source, and scope, then installs — and stops cleanly at a recommendation if all that was asked for was to find one. Prefer an existing skills-pack.lock.json restore for a project that already records its installs.
---

# Aganitha Install Pack

`sp` is a shorter alias for `skills-pack` — either name works everywhere
below.

Locate → confirm → install → verify, as one flow. This skill may change the
project's generated skill directories and `skills-pack.lock.json`, so do not
install anything until the user has confirmed *what* to install and *where*.
If the request was only "is there a skill for X" or "what would I install for
Y", stop after Locate with a recommendation — that is a complete outcome, not
a half-done install.

`skills-pack` resolves names across the current source set: built-in default,
project/global discovery sources, and sources already pinned in lock files.
The default registry is not a tie-breaker. If a name collides, use the exact
command printed by `skills-pack search`, `info`, or `registry`, or add
`--from <repo>` explicitly after confirming the source.

## 1. Locate the target

If the user already named a pack or skill and it is unambiguous, skip to
*Choose the source of truth*.

Otherwise the request is vague ("set me up with the docking tools", "what
should I use for X"): hand discovery to **`aganitha-find-skill`**. It searches
the full source set, broadens through `skills-pack registry` when a keyword
misses, judges fit, and reports the exact install command `skills-pack`
prints. Use its recommendation and that printed command — do not reconstruct
`--from`/`--from-pack` flags by hand. Prefer a curated pack over a single
direct skill unless the user explicitly wants only that one skill.

If the user only wanted a recommendation, stop here.

## 2. Choose the source of truth

1. If the project contains `skills-pack.lock.json`, offer the reproducible
   project setup first:

   ```bash
   skills-pack update && skills-pack upgrade
   ```

   This restores the recorded pack/skill recipes and materializes the
   gitignored `.claude/skills/` and `.agents/skills/` directories. Run both
   commands: `upgrade` resolves against the local registry cache and never
   fetches for a repo already cached, so on its own it can reinstall stale
   content. `update` is what refreshes that cache. The split mirrors `apt` —
   `apt upgrade` does not imply `apt update`.

2. **Add a group's repo as a source** when the project should discover that
   group's packs. A source is a GitHub repo `sp` searches alongside the
   built-in default — the consumer side of the group-owned model (see
   `aganitha-publish-skill` for the producer side). Configure it before
   installing:

   ```bash
   skills-pack source add github:<group>/agent-skills
   skills-pack source list
   skills-pack update
   ```

   Project-scoped sources live in `skills-pack.sources` and should be committed
   when the whole group works from the repo; `-g` makes it global to one
   machine only. A source only widens discovery — it never sets precedence, and
   the built-in default always stays in the set.

   Checklist:

   - [ ] `skills-pack source list` shows the group repo under the project's
         sources.
   - [ ] `skills-pack.sources` is committed (unless `-g`, which is machine-only).
   - [ ] The pack you want now shows up in `skills-pack list` / `search`.

## 3. Preview

For a named target, inspect the plan first — a bare name resolves to a pack
or skill automatically; the `pack`/`skill` prefix is only needed to
disambiguate a name that matches both:

```bash
skills-pack info <name>
skills-pack preview <name>
```

If `preview` asks for `--from` or a `pack`/`skill` prefix, stop and confirm the
intended source/target before continuing.

## 4. Confirm

Before running the mutating command, state:

- the pack or skill name;
- the source, if it is not the built-in Aganitha registry or if a collision
  requires `--from`;
- project-local or global scope;
- any non-default agent or forwarded options.

Ask for confirmation if any of those choices are unresolved. Do not infer
global installation from a casual request to "make it available".

## 5. Install

Project-local default:

```bash
skills-pack install <name>
```

Global:

```bash
skills-pack install <name> --global
```

Prefer the pack when it is a curated fit; a direct skill install is valid when
the user explicitly wants only that skill. Use `--from <repo>` for a
third-party or product repo when the command needs to narrow to one source.
Avoid recording local filesystem sources in a shared project lock file; they
are development only and cannot be restored portably.

If discovery printed a more specific command, use it exactly, for example:

```bash
skills-pack install pack <name> --from github:<org>/agent-skills
skills-pack install skill <name> --from-pack <pack> --from github:<org>/agent-skills
```

To remove a previously installed pack or skill, `skills-pack uninstall <name>`
mirrors this same target resolution and scope handling.

## 6. Verify

After installation, run:

```bash
skills-pack status
skills ls
```

Confirm that the expected skills are present and that the project lock file was
written. Never commit `.claude/skills/` or `.agents/skills/`; commit
`skills-pack.lock.json` instead.
