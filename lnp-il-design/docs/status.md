# Status

Updated 2026-10-02.

Nothing is committed. Design decisions settled so far: result intake, evidence-flag calibration, pooled model with controls, model-selection score (mean rank), generator (full enumeration with reaction templates, scoped by the partner's chemistry).

## Done

- Vision, mental model and first design draft written (`vision.md`, `mental-model.md`, `design.md`).
- Public data inventoried (`data-sources.md`). LNPDB profiled: 19,797 rows, 42 studies, 12,845 unique ILs, 17,140 in vitro and 2,388 in vivo rows.
- LiON's training overlap mapped to LNPDB study IDs (`design.md`, open question 3). Eleven LNPDB studies are contaminated for any LiON comparison.
- Sealed holdout and hit threshold chosen (`design.md`, open questions 1 and 2), open to the author's veto.
- Project scaffold: package skeleton, Makefile, front-door files.
- Ingest and Curate built for LNPDB (`lnp-il data curate`), 20 tests passing, lint and type-check clean. On the real data: 17,444 development rows, 1,474 sealed rows, hit rate 15.6%. Code review done and its three priorities fixed (JSON errors, sealed outputs isolated in `sealed/`, `curate()` split up). Preflight run 2026-10-02 and its documentation items fixed.

## Next

1. **Blocked on the partner:** which two or three synthesis routes their chemist can run. The generator and the first shortlist depend on it. The result-file template also needs agreeing with them.

2. Author reviews the design doc and vetoes or confirms the holdout and hit threshold.
3. Ship Ingest and Curate (`aganitha-ship`; the repo is public, so push only on a fresh yes). Then add Atlas structures (downloaded, no labels). LANCE is skipped and the COMET repository is not used, because of its license.
4. Confirm the new label rules and the uptake readout (`design.md`, decision 'Which rows count as labels', open question 9).
5. Baselines under leave-one-study-out, then the model ladder.

## Not started

Model, Design (candidate generation) and Select modules.

## Known gaps

- LiON overlap is matched by DOI and initials, not confirmed against its Supplementary Table 1.
- The partner's result file format and plate-control convention are undecided (`design.md`, open question 4).
- Per-source licenses are unchecked (`design.md`, open question 5).
