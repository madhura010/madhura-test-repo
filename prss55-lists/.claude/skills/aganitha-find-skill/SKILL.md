---
name: aganitha-find-skill
description: Finds the right skill or pack for a task across every skills-pack source visible to the current project, including vague or semantic requests that don't match any skill's name or description literally. Use this whenever someone asks "is there a skill for X", "what should I install for Y", or describes something they want to do and isn't sure a skill already covers it. Does not install anything — it only helps locate the right one.
---

# Aganitha Find Skill

`sp` is a shorter alias for `skills-pack` — either name works everywhere
below.

`skills-pack` searches the current source set: the built-in Aganitha registry,
project/global discovery sources, and repos already recorded in
`skills-pack.lock.json`. That means third-party or product-repo skills are
normal candidates, not edge cases.

`skills-pack search` does literal keyword matching against name, description,
and (with `--content`) full file bodies. That's fast and exact, but it can't
match a need that's described differently than the skill's own wording. For a
semantic pass over everything recommendable, use `skills-pack registry` and
judge the structured snapshot.

## Steps

1. **First pass — literal search.** Run `skills-pack search <keyword>` using
   the most obvious keyword(s) from what the user described. If that returns
   nothing useful, retry with `--content` (catches mentions that only appear
   in a skill's body, not its name/description) and/or try a different
   keyword guess.

2. **If the first pass is empty or ambiguous — use the registry snapshot.**
   Run `skills-pack registry` and inspect its JSON. Schema 2 has a `sources`
   list plus per-pack/per-skill source attribution. Only pack-reachable skills
   are included, so every skill in this snapshot is curated enough to
   recommend. Prefer each entry's printed `install` command if the user later
   asks to install; it already includes `--from`/`--from-pack` when needed.

3. **Read candidates when judgment needs more context.** Bare
   `skills-pack search` summarizes rather than listing every skill; run
   `skills-pack search --skills` to browse all of them individually, or
   `skills-pack search --json` for a lighter structured pass over search
   results. Read the full `SKILL.md` (or `.pack` file) of any candidate that
   seems plausible from its one-line description alone. `skills-pack info
   <pack>` shows a pack's full skill list with descriptions.

4. **Judge, don't just match substrings.** Decide which candidate(s) actually
   fit what the user described, even if the wording doesn't overlap. Prefer
   an existing skill/pack over suggesting something new — that's the whole
   point of the registry.

5. **Report back:**
   - The name of the best match (skill or pack) and *why* it fits — one or
     two sentences connecting the user's need to what the skill actually does.
   - The source, if it is not the built-in Aganitha registry or if multiple
     sources define similar names.
   - The exact install command from `registry`/`search`/`info`, if the user
     asked what to install. Do not reconstruct it by hand.
   - Any close-but-not-quite alternatives, briefly, if there's genuine
     ambiguity worth flagging.
   - If nothing in the registry fits, say so plainly rather than forcing a
     weak match — that's a real, useful answer too.

This skill only locates things. Installing is a separate, explicit step
(`skills-pack install ...`) — never install without the user confirming that's
what they want. Do not recommend direct `skills add` for ordinary use; it
bypasses packs, source resolution, and the `skills-pack.lock.json` workflow.
