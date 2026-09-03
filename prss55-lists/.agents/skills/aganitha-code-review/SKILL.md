---
name: aganitha-code-review
description: Review code before it ships. Use whenever the user asks for a code review, says "review this", "check my code", "review my changes", "before I commit", "is this safe to merge", pastes a PR URL, a commit, or a diff, or points at a file or directory. Reports what will break, then what is structurally wrong, then what is merely untidy — and says, for each finding, whether it can be applied here, needs a decision, or needs someone with access. Works on a change in flight, a commit that already landed, or a standing body of code.
---

# Code Review

Two passes. First the big picture, then the detail. The report inverts that —
what breaks goes first.

---

## What a review is looking for

Five questions sit under everything below. The checklists are **examples** of
them, not substitutes for them — when something is wrong and no bullet names it,
the finding is still real; when a bullet matches but nothing is actually wrong,
there is no finding. Most of the best findings come from the questions, not the
lists.

- **Correctness** — does it do the right thing, including when the input is
  empty, hostile, or concurrent?
- **Coherence** — does it hold together as one idea: the right thing owning the
  right job, names matching reality?
- **Consistency** — does it match the decisions this project has already made?
- **Simplicity** — is this the least code that solves the problem?
- **Flexibility and longevity** — when one requirement changes, does one thing
  change or five? What does this look like in a year, once the assumptions it
  makes about the outside world have shifted?

**How much to report — and the rule that governs everything below.** Report
every finding that meets the bar and would change what someone does. Do not trim
to a number: the reader can decide what to act on, but cannot act on what you
never showed them.

Meeting the bar is necessary, not sufficient. An unused variable and a cosmetic
banner both pass it — you can name the concrete change — and neither earns a row.
Group that kind of thing into a single `Dropped` line rather than reporting it
individually or hiding it. The rule above exists so that *real* findings never get
cut for length; it is not a licence to list everything nameable.

What you owe them instead is a filter they can run themselves. Say what you
verified, name the input that triggers each failure, and mark anything that is
conditional. That is what makes a long review usable and a short one trustworthy.

**Never suppress silently.** If you set aside something you believed was real —
for length, because another finding covers it, because a rule below told you not
to report it — say so, with the category and the reason. A finding you drop
without a trace is indistinguishable to the reader from one you never found.

A review that finds nothing real says so in one line and stops; that is a valid
outcome, not a failure to look hard enough. And a long list of located defects is
not padding — padding is category names with no scenario, which the bar already
forbids.

---

## Step 0 — What am I reviewing?

Resolve the target before reading any code, and say which one you picked.

| Given | Do this |
|---|---|
| **PR URL or number** | `gh pr view <ref>` for title, description, and CI status; `gh pr diff <ref>` for the change. |
| **A commit hash or range** | `git show <sha>` (or `git diff A..B`). If the subject ends in `(#123)` — the squash-merge convention — or `gh pr list --search <sha>` resolves one, follow the PR row as well for the description and checks. |
| **A branch name** | `git diff $(git merge-base HEAD <branch>)..<branch>` |
| **A pasted diff or `.patch` file** | Review as given. You have no surrounding code — say so, and flag what you could not verify rather than assuming it. |
| **A file or directory path** | Standing review of the code as it stands. No diff, so "what changed" questions do not apply. |
| **Nothing** | `git diff HEAD` plus untracked files. If empty, fall back to `git show`. If still empty or ambiguous, ask — do not guess. |

The target path and the repository root are often not the same directory. Find
the root (`git rev-parse --show-toplevel`) before resolving paths in a diff.

### Gathering context

Walk **from the target directory up to the repository root**, collecting at each
level; nearest wins on conflict. Look **sideways** too — a sibling directory
holding another copy of what you are reading often carries the only written
account of why it exists.

- `AGENTS.md` / `CLAUDE.md` and any convention skills they name.
- `docs/design.md`, `docs/vision.md`, decision records, ADRs, a `DESIGN.md`
  beside the code. Whatever the project uses to record decisions — a long
  explanatory comment block in a source file counts, and on some codebases it is
  the only place decisions live.
- For a PR or a merged commit: the description and any linked ticket.

Two things this produces:

- **A recorded decision the code contradicts is a finding — but establish which
  one changed last before you file it.** A document can be the authority the code
  violated, or it can be stale prose describing a decision the code has since
  reversed for a better reason. `git log` on both settles it in minutes. Filing
  against correct code because a document lagged is the most expensive mistake
  available here.
- **A target with no context of its own is itself worth reporting.** A directory
  with no README, no owner, and no docs, whose nearest `AGENTS.md` is four levels
  up and about something else, is a finding on the standing review.

Read a red CI run before writing findings the tests already report. CI that
passes while running no tests proves nothing — say so rather than leaning on it.

**Before reading any test failure as a defect, establish that the toolchain is
installed and the suite is meant to run here.** A fresh clone with no dependencies
fails wholesale, and that failure looks exactly like the finding you are hunting
for.

---

## Target modes

The passes below are the same in every mode. What changes is what you read first,
what the header says, and what a verdict is allowed to conclude.

| Mode | Read first | Header carries | Verdict chooses between |
|---|---|---|---|
| **Change in flight** — PR, branch, working diff | the diff, then every changed file whole | files, `+N/-N` | safe to commit · needs changes first · needs discussion |
| **Already landed** — a commit, a merged PR, released code | `git show`, then every changed file whole | commit, files, `+N/-N` | leave it · fix forward · revert |
| **Standing review** — a path, a package, a subsystem | the build manifest and entry points, then the published surface, then outward along the import graph | files, lines, and **what you read in full versus surveyed** | it is fine · plan the work · stop and decide |
| **Raw diff, no repo** | the diff as given | what you were handed | what you would need to check to be sure |

**Code that acts beyond its own process.** Installers, bootstrap scripts,
migrations and deploy tooling change machines. Services execute other people's
work, hold other people's credentials, and answer to callers with different
privileges. Clients spend someone else's quota under someone else's key. All of
these are reviewed in whichever mode fits, with one addition — ask not only "is
this correct" but:

- What does this do to a machine, an account, or a budget that is not mine?
- Who can make it do that, and is that the same set of people who are supposed to?
- Can it be undone, and by whom?

**Which Fit checks are live.** Disproportion and Scope creep need a stated
requirement. A PR description, a ticket, a commit body, or a design doc all
count. Only when there is genuinely none — a bare working diff in a repo with no
records — skip those two, and say you skipped them. Never infer the requirement
from the code you are reviewing; that is circular and it produces confident
nonsense.

---

## Scope

**Read whole files, not hunks.** A clean diff can sit inside a function that
should not exist. Read the full text of every file the change touches.

On a standing review there is no change to bound the reading. Follow the mode's
order — manifest and entry points, then the published surface, then outward along
the import graph — and stop when new files stop changing findings you already
have. Then say in the header what you read in full and what you only surveyed, so
the reader knows where the review is thin.

Widen when any of these hold:

- The code touches a core or domain layer, a port, or an interface.
- It is a refactor rather than an addition.
- It crosses layers or modules.
- **Most of its work is delegated elsewhere.** Three thin files over a library
  are unreviewable without the library.
- **The same filename or the same responsibility appears elsewhere in the repo.**
  Sweep for siblings and forks — nothing else here will surface them. Check
  whether the copies have actually diverged, and whether the duplication was
  bought deliberately, before deciding it is a defect.
- Something feels structurally off even in a small diff.

Say so when you widen, and say how far. **Stop when new files stop changing
findings you already have** — not when you run out of files.

**When the surroundings are the problem** — if the code under review is sound but
what it sits in is not, that is a finding, not a second review. This applies in
every mode, including a standing review of one file inside a larger mess:

> `src/importers/csv.ts` — the change is sound, but this file has three
> overlapping parse paths and no tests. That needs a standing review, not a diff
> review — run `aganitha-system-health` on this module.

Two things this does **not** cover. When the dependency is fine and only the
caller's assumption about it is wrong, report it here — the evidence lives
elsewhere but the defect is in scope. And when the problem is a convention
spanning the whole repository rather than this module, say that plainly instead
of handing off; no single module is the right destination.

---

## Pass 1 — Architecture & Design

Structural problems compound over time. Four questions, in this order: does this
code belong here, is it structured right, does it hold at the edges, and does it
account for everything it claims to. Most reviews start at the second and never
ask the first.

### Fit — does this code belong here, at this size?

Ask this before anything else. There is no point critiquing the layering of code
that should not have been written. The best review outcome is less code.

- **Reinvention** — does a maintained package already do this? Retry and backoff,
  date arithmetic, structured parsing, schema validation, path manipulation are
  usually solved. Name the package, and weigh it — a dependency is not free.
  Thirty lines of hand-rolled backoff, yes; eight lines of glue, no. And check
  the language first: what is a missing library in one ecosystem is the plain
  idiom in another.

- **Disproportion** — is the solution larger than the problem? Four classes and an
  interface for a one-line requirement; a value wrapped in an object; an interface
  added before a second implementation exists; indirection introduced before the
  pattern is clear. YAGNI, and the characteristic LLM failure mode — where the
  shape isn't known yet, the code should be flat and concrete. Name the simpler
  shape: "this could be simpler" is taste, "these four classes are a dict lookup"
  is a finding.

- **Inconsistency** — does this match how the project already does things? A new
  HTTP client where every other module uses the shared one; a config read that
  bypasses the established path; a pattern that contradicts a recorded decision.
  If the decision is wrong that is a separate conversation, not a silent
  divergence. This is the check no linter can make.

- **Claim mismatch** — does the change do what its description says it does?
  Overclaimed work misleads every future reader of the history, and the claim most
  worth checking is the one about a safeguard: a description asserting that
  something now prevents recurrence, where the mechanism cannot actually fail.
  Check the mechanism; do not match the wording.

- **Scope creep** — does it do more than it was asked to? An unrequested refactor
  bundled into a feature commit is hard to review and hard to revert.

### Inside the boundaries

- **Leaky abstractions** — implementation details bleeding across layer boundaries; callers knowing too much about internals.
- **Needless re-validation** — an intermediate layer re-validating, re-typing, or re-narrowing a structure it only forwards (doesn't branch on, transform, or read a field of). Passing through a typed value is not a use of it. This duplicates the producer's contract in a second place, coupling that layer to changes on both ends.
- **Improper boundaries** — layers doing each other's work; wrong dependency direction (inner depending on outer). On code with no formal layers, keep the question and drop the words: what does this file know that it should not, and who breaks when it changes?
- **Structural replication** — DRY read properly: not duplicate lines, but duplicate concepts, responsibilities, or logic paths. Similar-looking code with different reasons to change is not a violation. Duplication that was bought deliberately — to hold a boundary the project defends in writing — is a decision, not a defect; report what keeps the copies honest, not that they exist.
- **Broken mental model** — names, structures, or concepts that no longer reflect what the code actually does.
- **Cohesion** — things that change together should live together. Flag logic scattered across files, or a module split so finely that one operation takes several files to follow.

### At the edges — where the code meets something it doesn't control

Only where the code actually touches one of these — do not invent a hypothetical
external system to review against.

- **Untrusted input** — anything arriving from a user, a file, an upload, or a
  request body. Is it validated before use, or does invalid shape reach logic
  that assumes it's clean?
- **An external call** — another service, a database, a filesystem, a queue. What
  happens when it's slow, errors, returns the wrong shape, or times out? Does the
  caller notice, or does the failure disappear?
- **A trust or auth boundary** — does the code check the caller is *allowed* to do
  this, or only that the request is well-formed? Those are different questions.
- **A secret or credential** — where does it come from, and could this change
  cause it to be logged, returned in a response, or committed?

The question at every one of these is the same: **what does this code assume
about the world outside it, and what happens the moment that assumption is
wrong?** Ask it even where no bullet above matches — that question finds more
than the list does.

### Completeness — every enumeration is a claim about the world

Wherever code says "these specific things are allowed" or "these are the cases" —
an allowlist, a hash set, an enum, a validation whitelist, a switch over known
states, a set of registered handlers — **enumerate what actually exists and check
the list covers all of it.**

This matters most when a change tightens a permission that used to be open, since
whatever falls outside the new list stops working silently. But it applies to any
standing enumeration: the set was true when it was written and the world has been
moving since.

Two things make this hard, and they are why it is worth doing deliberately. The
missing member usually lives in a different module or a different package, so the
diff will not show it to you. And a set can be incomplete but safe — if the
fall-through case does nothing harmful, an unlisted member is not a finding. Say
which of the two you found.

---

## Pass 2 — Code

Four groups. **Breakage** reports in its own section; **Waste**, **Shape**, and
**Surface** report together under **Quality**.

### Breakage — what fails at runtime

**No scenario, no finding.**

- **Edge cases** — empty, absent, zero, negative, single element, maximum size, malformed, unicode. Which of these reaches this code?
- **Error handling** — is a failure swallowed, logged and continued, or surfaced to a caller that can act on it? Two shapes to watch: a handler that hides the cause, and a caller reading a status the callee never meaningfully sets.
- **Assertions standing in for checks** — a cast that asserts rather than verifies; a value used without the guard its type demands; a name bound on only one branch and read on all of them; a status trusted that was never set; a type test that answers the wrong question.
- **Concurrency** — two things running at once over shared state: check-then-act, a missing transaction or lock, ordering assumed rather than enforced, races over files and temporary paths.
- **Bounds and arithmetic** — loop bounds, indices, offsets, counters, retry limits, timeouts that ignore the time the work itself takes.
- **Resource lifecycle** — files, connections, handles, subscriptions, temporary files and directories opened but not reliably released on the error path.
- **Unbounded work** — work that grows with input the caller controls; a query with no limit; repeated work inside a loop that could be done once; a collection that grows with the dataset.
- **Data becoming code** — a query, a shell command, a template, a deserializer, a dynamic evaluation. Ask what the source is and who can influence it. Ask this wherever it appears, not only where untrusted input was already found.
- **Idempotence** — does re-running this do the same thing twice? Anything claiming to be safe to re-run, resume, or retry — an installer, a migration, a queue consumer, a sync — needs that claim checked.
- **Portability** — what does this assume about the platform, shell, filesystem, locale, or installed tooling, and where does that assumption not hold?

These bullets do not name the characteristic failure modes of your language or
runtime. They exist, they are usually where the real bugs are, and they are yours
to know — name each one concretely when you find it.

### Waste — code that shouldn't be there

- **Dead code and magic values** — a branch nothing reaches, an unused export, a literal that should be named.
- **Hacks and workarounds** — code patching around a root cause instead of fixing it: special-casing one bad input because upstream sends wrong data, silencing an error instead of handling it, a shim compensating for a broken API. Each hack makes the next more likely; the fix belongs at the source.

### Shape — whether the abstraction fits what's actually known

- **Abstraction & function size** — functions doing too much; logic that should be named and extracted. The test: if you can't describe what a function does in one short phrase, it's doing too much. But don't extract speculatively — the Rule of Three: once, inline it; twice, leave it; three times, abstract it.

- **Minimal knowledge (Law of Demeter)** — each function or module should know only what it needs to. Watch for functions receiving objects but using one field; logic reaching across layers for data; callers that must understand a function's internals to use it. Two tells. The first is a chain of dots:

  ```typescript
  // Smell — processor knows how tax is structured inside Customer
  const tax = order.customer.address.region.taxRate * order.total

  // Better — Order knows its own rules
  const tax = order.calculateTax()
  ```

  The second is **re-derived structure**: a caller rebuilding a path, a key, a
  filename, or a URL that some other module already owns and often already
  exports. It reads as ordinary local code and is easy to scan past, so look for
  the same fact spelled two ways in one file — once by importing the owner, once
  by hand.

- **Under-committed decisions** — defer when you genuinely don't know yet, commit when you do. Over-deferring is caught above under Fit. The opposite failure belongs here: hardcoding something clearly configurable, a machine-specific path, one developer's hostname as a production default, or a structure left loose when the decision is already made.

  ```typescript
  // Smell — the base URL is a known config value, not a magic string
  const url = "https://api.internal.co/v2/reports"  // copy-pasted in 4 places

  // Better
  const url = `${config.get("API_BASE_URL")}/v2/reports`
  ```

- **Pure functions** — flag functions that could be pure but aren't: mutating a passed-in object, reading or writing shared state, doing I/O inside logic that doesn't need it. If a function can be pure at no real cost, it should be.

- **Separation of concerns for evolvability** — not reuse for others, but reuse as your own code evolves. Watch for one module mixing concerns that change at different rates. The test: if the CSV format changes, should the classification logic change too? If yes, they're tangled.

  ```typescript
  // Smell — format change and rule change both touch the same function
  function processCSV(filePath: string): Summary {
    return parse(filePath).reduce((acc, [name, amount]) => {
      if (parseFloat(amount) > 1000) acc.highValue.push(name)
      else acc.normal.push(name)
      return acc
    }, { highValue: [], normal: [] })
  }

  // Better — each piece can change without touching the other
  function parseCSV(filePath: string): Row[]   { ... }
  function classifyRows(rows: Row[]): Summary  { ... }
  ```

### Surface — what a reader encounters

- **Readability** — would a teammate understand this in 30 seconds? Structure matching the mental model; no clever tricks that need re-reading.

- **Naming** — where the project declares a convention skill, flag what *it* would flag and invent nothing. Where it declares none, ask only the question those skills cannot: does the name still describe what the code now does?

- **Test coverage** — do the tests assert behaviour rather than restate the implementation? A test that would still pass with the function body deleted is worse than no test. On a change, a new branch with no test covering it is a finding. On a standing review, ask a different question: **is there anything that runs these tests, and does it reach them?** Check whether a test command exists at all, whether CI invokes it, and whether its paths match the files on disk — a suite nobody executes is the most expensive kind of dead code. Establish the toolchain is installed before treating a failing run as evidence of anything.

- **UI hygiene** *(only if UI code is present)* — dead selectors, structure mixed with styling, hardcoded layout values.

- **Docs drift** — mismatches between the code and design docs, comments, or docstrings. Flag; don't fix.

---

## The bar for every finding

Applied while writing, not while reading. A finding that cannot meet it is noise
— drop it. If you believed it before the bar rejected it, that belief goes in
`Dropped` with the reason, so the reader can overrule a bar you applied wrongly.

| Group | No finding unless you can name… |
|---|---|
| **Fit** | the package that already does this, the simpler shape, or the decision it contradicts |
| **Inside / At the edges** | what couples to what, or the assumption that breaks |
| **Breakage** | the input or state that triggers the failure |
| **Waste / Shape / Surface** | the concrete change you would make instead |

**A nameable trigger is not the same as a correct model of the runtime.** You can
describe a precise failing input and still be wrong about what the language does
with it — an exit status that propagates differently than it reads, a guard that
is inert, a local that outlives the branch that set it. Where a finding turns on
runtime behaviour rather than on what the source plainly says, run it before you
file it. The `tested` provenance below is for exactly this, and in that case it is
not optional.

### Before you write it down

**Can the caller already do this another way?** A finding that grants an attacker
or a caller nothing they do not already have is not a finding. Fetching a URL
server-side looks like SSRF — but if the same caller can already run arbitrary
containers on that host, the fetch grants nothing. Ask this of every security
finding. It is the most common thing separating a real one from noise.

**Is it reachable only under a configuration nobody runs?** Then report it, name
the configuration, and mark it conditional. Do not inflate it into a live bug and
do not drop it silently.

**Have you checked the premise?** Some rules in this skill turn an observation
into a finding — a document contradicting the code, a failing test suite, a set
that looks incomplete. Each rests on a premise: that the document is current, that
the suite was meant to run here, that the missing member matters. Check the
premise before you file, and say you did. A rule that promotes without a premise
check is how a review ends up arguing against correct code.

**Where does this claim come from?** Say which, on every finding:

- **Verified** — against code you read.
- **Tested** — you ran something to check. A quick experiment is worth writing
  when the answer turns on runtime semantics rather than what the source says.
  This is what separates a confident wrong finding from a real one.
- **Inferred** — you did not read every path. Say what you would need to check.

A confident wrong finding costs more trust than a hedged right one.

### Do not report

The characteristic noise of an LLM review. None of these is a finding on its own:

- Tests for trivial code, or a test that would only restate the implementation.
- Error handling for a failure that cannot happen given the current design.
- "Consider adding a comment", or a suggestion to extract something for
  readability with no named replacement. Naming the split and the reason — these
  four concerns change at different rates, extract *this* — is a finding, not
  noise.
- Defensive wrapping around code with no failure mode.
- Style, formatting, or import order the project's formatter or linter owns.
- A scale or concurrency problem with no evidence the scale or concurrency exists.
- An abstraction proposed for a single use site.

This list is flavoured by the codebases it was written against. Every language
and domain has its own version — the plausible-sounding suggestion that adds
nothing, aimed at an idiom that is already correct. Recognise yours and suppress
it on the same grounds.

---

## Output format

**Reviewed:** <what you actually read, per the target mode> · **Scope:** <what you covered, and what you surveyed rather than read>

### Severity

Three questions set it, not one:

- **Consequence** — what happens when this goes wrong?
- **Reversibility** — can it be undone, and by whom?
- **Blast radius** — whose systems, data, or machines does it touch?

A small consequence that cannot be undone, on a system or an account its author
does not control, outranks a large one that can be reverted locally.

- **Must** — do not ship it in this state. Causes a failure, a security hole, or data loss; or makes an irreversible change on a system its author does not control.
- **Should** — a real cost that will be paid later. Shipping is defensible; fixing now is cheaper than fixing then.
- **Consider** — worth a look. No obligation.

A recorded decision that the *code* contradicts is serious — once you have
established the document is the newer of the two. Documentation trailing the code
belongs in Docs out of sync, not in a finding against the code.

### Disposition

Every finding carries one:

- **Apply** — local, reversible, the author can do it now.
- **Decide** — structural or a trade-off; it needs a human choice, not a patch.
- **Escalate** — it needs access, authority, or a person who is not in this
  conversation: rotating a credential, purging history, changing infrastructure,
  telling another team. Never offer to do these. State the steps and who has to
  act.

### Sections

Omit any with nothing in it.

**Breakage** — ordered worst first. This is why the reader opened the review; an
empty one is the best result available, not a sign you looked too lightly.
`file:line` — **<severity>** · **<disposition>** — What fails, and the input or state that triggers it. What to do. *(verified | tested | inferred)*

**Architecture & Design**
`file or module` — **<severity>** · **<disposition>** — What the problem is. Why it matters structurally. *(provenance)*

**Quality**
`file:line` — **<severity>** · **<disposition>** — What it is. What to do. *(provenance)*

**Docs out of sync** — flag only, no action needed until the code stabilises.

**Dropped** — everything you set aside and why, in one line each. Include what a
rule in this skill told you not to report but you still believed. Required in
every mode; on a widened change review the reader needs it most, because the
widening made your scope invisible to them.

**Verdict** — one line, choosing from the options your target mode allows.

Close with the disposition summary — how many to apply, decide, escalate. Offer
to apply the **Apply** findings unless the caller asked for a report only, in
which case say what you would apply and stop there.

---

## Example — a complete review

These show the shape, not a quota. The number of findings is whatever met the
bar.

> **Reviewed:** PR #412 "Add CSV bulk import", 4 files changed, +230/-45 · **Scope:** changed files whole, widened to `importers/` for the shared staging path
>
> **Breakage**
>
> `src/importers/rows.ts:31` — **Must** · **Apply** — `rows.reduce((a, b) => …)` has no initial value, so an empty CSV throws `TypeError` before the "no rows found" path is reached. A header-only upload hits this. Pass the initial accumulator. *(verified)*
>
> `src/importers/client.ts:18` — **Must** · **Apply** — the new billing call sets no timeout, and a non-2xx propagates as an unhandled rejection. When billing is slow the import request hangs instead of failing. Set a timeout; return a typed error. *(verified)*
>
> `src/importers/staging.ts:77` — **Should** · **Decide** — the staging directory is removed in the success path only, so a failed import leaves the upload on disk until someone notices. Reachable on any parse error. Move the cleanup to the error path too, or accept it and document the retention. *(tested — ran the parse-failure case against a local fixture)*
>
> **Architecture & Design**
>
> `src/importers/csv.ts` — **Should** · **Decide** — parses CSV *and* classifies rows by value threshold in one function, so a format change and a rule change land in the same place. Split `parseCSV` from `classifyRows`; they change at different rates. *(verified)*
>
> **Quality**
>
> `src/importers/rows.ts:52` — **Consider** · **Apply** — `mapRow` takes the whole `ImportConfig` but reads only `delimiter`. Passing the field would make it testable without building a config. *(verified)*
>
> **Verdict**
>
> **Needs changes first** — both Breakage Musts are reachable from a normal upload.
>
> Three to apply, two to decide, none to escalate. Shall I apply the three?

And a standing review, which carries a different header and an obligatory
`Dropped` section:

> **Reviewed:** `atk-job-manager-core` — 4,600 lines of `src/` read in full (`contract/`, `core/`, `runners/`, `server/`); **surveyed, not read whole:** `storage/backends/s3.ts`, the 35 remaining test files, and the CLI (grepped for how it reaches the core) · **Scope:** widened to the CLI and to `deploy/compose.yml`, because the severity of the first finding turns on what the engine process is at runtime. No CI job runs this suite, so no run was leaned on.
>
> **Breakage**
>
> `src/core/kernel.ts:293` — **Should** · **Apply** — `cancel` reaches the runner through `?.`, so when the runner is not registered the stop is a silent no-op and line 295 still writes `cancelled`. Reachable by unsetting `ATK_JM_SLURM_API_URL` while cluster jobs are in flight: the record reads cancelled while the job holds its allocation. `reconcile` and `sweepStale` both handle a missing runner explicitly; this is the one that does not. *Conditional on that configuration.* *(verified)*
>
> **Architecture & Design**
>
> `src/server/engine.ts:154` — **Must** · **Decide** — the `shell` runner is registered unconditionally and no config key removes it, so anyone holding `submit` can run arbitrary processes as the engine's uid. Gate it, or bind it to a separate action — that is a decision about the deployment's trust model. *(verified)*
>
> **Dropped**
>
> - Waste (2): a duplicated `#SBATCH --output`; a helper declared between two imports.
> - Breakage (1): `store.insert` throwing leaves the workspace behind — real, no reader-visible consequence I could name.
> - Believed but blocked by a rule here (1): four repeated `assertInputName` calls looked like needless re-validation; every caller writes to the path rather than forwarding, so the bullet's own qualifier ruled it out. Recording it in case that qualifier is wrong.
>
> **Verdict**
>
> **Stop and decide** — the containment story is written for the docker runner and the shell runner walks around all of it.
>
> One to apply, one to decide, none to escalate.

**When there is nothing real to report,** the whole review is the header and one
sentence:

> **Reviewed:** PR #412, 4 files, +230/-45 · **Scope:** changed files whole
>
> Nothing to flag — the empty-input path is covered and the external call handles failure. Safe to commit.

---

## Tone

Be direct. Say what to do, not just what's wrong. Skip anything minor enough that
a reasonable engineer would leave it as-is — and if you were in two minds about
it, that is a `Dropped` line, not silence.

**One row per issue, but name every problem in it.** When two checks land on the
same lines, report once and say what both found; the fix usually addresses both,
and folding one away without naming it loses a real finding.

**Never cite a principle in place of a finding.** "Violates SRP" is unactionable;
"a format change and a rule change touch the same function" is the same
observation, and the reader can act on it. The named principles above are for
recognising the problem, not for reporting it.

Never post to a PR, approve, or request changes unless explicitly asked.
