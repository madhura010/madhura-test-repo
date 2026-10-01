# Handoff

Updated: 2026-10-02

## Objective

Predict mRNA transfection efficiency of LNP formulations from public data only, and propose ionizable lipids (ILs) for a wet-lab partner to test. Success is three sequential gates in [vision.md](vision.md): beat nearest-neighbor under leave-one-study-out and on the sealed holdout; reproduce and compare a published model on clean studies; a partner test of the shortlist. The project is in the design and first-build phase. No model, generator or shortlist exists.

## Current state

- **Done and checked:** Ingest and Curate for LNPDB (`lnp-il data curate`), written to the design in [design.md](design.md). Review findings were fixed. Docs are synced to the code.
- **Not done:** Model, Design (candidate generation) and Select modules; Atlas ingest; preflight; any commit.
- **Uncommitted:** all of `lnp-il-design/` is untracked in the local clone of `madhura010/madhura-test-repo` (branch `main`). Nothing has been pushed. That repo is public.
- **Generated data** is outside git: `/Users/madhura/LNP-ML-tests/curated/` (dev table, study table, report, and `sealed/`). LNPDB clone: `/Users/madhura/LNP-ML-tests/LNPDB`. Atlas CSV: `/Users/madhura/LNP-ML-tests/sources/atlas/`.

## Decisions and constraints

- **Holdout:** JL_2024, XH_2025, AP_2025, RG_2023 are sealed whole. Chosen by Claude, open to the author's veto. Never use them before the final report.
- **Labels:** within-study z-scores only. Hit = top 16% per (study, context), tie-aware, so some groups have no call (KZ_2016, ZC_2023). Diameter, zeta and hemolysis rows are dropped.
- **Model:** one pooled model with context features (author's choice, against Claude's advice). It needs three controls first; see "One model or one per context" in the design doc. Selection is by mean rank over Spearman, hit rate and calibration.
- **Generator:** enumerate head and tail fragments through reaction templates (author's choice). Templates cover only the partner chemist's routes. Max two tails.
- **Licenses:** COMET/LANCE is not used. Its license excludes commercial R&D, and the data is only machine-readable inside that repo. LNPDB's underlying papers' terms are unchecked. Whether this work is commercial is Aganitha's call with counsel.
- **LiON overlap:** eleven LNPDB studies are contaminated for any LiON comparison; matched by DOI and initials.

## Evidence

Run 2026-10-02 in `lnp-il-design/` with `LNPDB_DIR` set: `make lint` and `make build` pass; `pytest` 20 passed, including the real-data test (counts pinned to LNPDB commit `fc7c389`). A live run gave 17,444 development rows, 1,474 sealed rows, hit rate 15.6%, and no sealed study ID in any dev-side file.

Unverified: `make install && make test` from a fresh clone; the LiON study matching against LiON's Supplementary Table 1; the Atlas–LNPDB paper overlap (rough, by DOI suffix).

## Next action

Run `aganitha-preflight` in `lnp-il-design/`. If it passes, decide how to ship with `aganitha-ship`. The author prefers to finish working before any push, so do not push without a fresh yes.

## Blockers and risks

- **Partner input** (which synthesis routes their chemist can run; the result-file template) gates the generator and the first shortlist. The forward model does not depend on it.
- **Author confirmations pending:** the new label rules, and whether `uptake` rows (479, LX_2024) belong in a transfection label ([design.md](design.md), open question 9).
- **Stray files outside the repo** in `/Users/madhura/LNP-ML-tests/`: `lion_paper.txt` is extracted text of a copyrighted paper (the repo ignores it; consider deleting); `docs/`, `data_source_inventory.md` and `per_experiment_summary.csv` are stale duplicates of files now in the project.
- The repo root's `CLAUDE.md` points to an `AGENTS.md` that does not exist; left unchanged. An older clone at `/Users/madhura/madhura-test-repo` is 14 commits behind and untouched.
