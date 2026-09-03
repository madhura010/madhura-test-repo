# Doc Writing — worked examples

Referenced from `SKILL.md`. Read this when a rule there is clear but its
application is not. The rules stand without this file; it teaches, it does not
add requirements.

## Avoid / prefer

Sentence-level substitutions.

| Avoid | Prefer |
|---|---|
| a load-bearing assumption | an assumption the design depends on |
| The architecture enables flexibility. | Developers can replace the renderer without changing the skill. |
| The service supports artifact management. | The service stores artifacts, assigns identifiers, and lets users retrieve them later. |
| This creates a leaky abstraction. | The job manager must now know how the runner stores files. A change in the runner may then force a change in the job manager. |
| The registry provides discoverability and governance. | The registry helps developers find available skills. It also lets the platform team mark which ones are approved. |
| The job manager should never know about tools. | The job manager should not know how tools are staged or executed. It may still store the tool name in the job record. |
| The framework supports registration, discovery, and subscription. | A skill asks for a service by name. The registry resolves the name to a definition, and the runtime creates the client. The registry does not make service calls or manage retries. |
| The system is scalable and extensible. | The system must scale and stay extensible. The scheduler adds workers without a restart, and a new job type needs one file under `jobs/`. |

The right-hand column is not the shorter one — it is the one that can be checked.
Several entries above are longer than what they replace.

## A paragraph, before and after

The table works one sentence at a time. Most failures happen at paragraph scale,
where the rules are each satisfied and the result still does not read like
engineering. Below is real output from this skill, with the rewrite an engineer
asked for.

**Before**

> A viewer displays something nobody taught it about. It meets kinds written
> after it shipped, by people it will never meet. It must show them without a
> branch per kind, and must not fail when it meets one it cannot show.

**After**

> The viewer should be extensible. It must be able to display artifact types
> that were added after the viewer was released, without requiring code changes
> for each new type. If it encounters an artifact type it does not support, it
> should degrade gracefully instead of failing.

Every sentence in the "before" is short, active, and literal by the letter of
the style rules. It fails for three reasons:

- It never names the property under discussion, so the reader has to assemble
  *extensible* on their own.
- It states observations — "a viewer displays something nobody taught it about"
  — where the document owes requirements.
- It reaches for figurative framing, "by people it will never meet", where a
  plain condition belongs.

The "after" is longer. Shortness was never the goal.

## Absence, dramatized

The most persistent failure this skill produces. The fact is always the same —
a component has no information about something — and an absence is awkward to
state plainly, so it gets written as a human experience instead.

| Avoid | Prefer |
|---|---|
| kinds written after it shipped, by people it will never meet | kinds defined after release, authored out of band |
| a kind of thing the viewer has never heard of | a kind not present at the viewer's build time |
| teams its authors never talk to | teams with no coordination with the viewer's authors |
| the resolver meets names it did not choose | the resolver receives names from sources it does not own |

The verbs to search for: *meet*, *know*, *hear of*, *remember*, *learn*, *see*,
*talk to*, and their negations. A component reads, stores, receives, resolves,
and rejects. It does not experience anything.

## Filler words

Adapted from the slop table in `simple-english` (MIT,
`github:aminblg/simpleenglish`). These are not in the style rules because they
need no judgment: if the word carries no fact, delete it rather than replacing
it. The four search lists in the checklist cover the vague *verbs*; this covers
the padding around them.

| Avoid | Write instead |
|---|---|
| leverage, utilize | use |
| in order to | to |
| prior to | before |
| due to the fact that | because |
| in the event that | if |
| when it comes to | for |
| it is worth noting that, it's important to, crucially | (delete — state the fact) |
| simply, just, easily, seamlessly, effortlessly | (delete) |
| robust, powerful, comprehensive, performant | (delete, or give the measurable property) |
| enables you to, allows you to | you can |
| is designed to, aims to | (delete — say what it does) |
| functionality | function, feature |
| facilitate | help, make possible |
| streamline | make simpler, make faster |
| dive into, delve into | read, examine |
| gracefully handles | (say what it does: "retries three times, then stops") |
| out of the box | by default |
| under the hood | internally |
| plethora, myriad | many |
| e.g. / i.e. / etc. | for example / that is / (name the items) |
| and/or | pick one, or write "X, or Y, or both" |

## Adding to this file

When feedback finds a document this skill produced badly, add the failing case
here with the rewrite a reader asked for. That is how the skill improves from
use rather than by accreting rules.
