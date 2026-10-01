---
name: lnp-il-design
description: Build and use the curated public LNP transfection dataset from LNPDB, and respect the study-level holdout and label rules when modeling or designing ionizable lipids. Use this skill whenever a task involves LNPDB rows, the lnp-il CLI, the sealed holdout, leave-one-study-out evaluation, hit calls, or deciding which public LNP studies may be used for training. Do not use it for synthesis planning, formulation lab protocols, or predictions of in vivo efficacy or safety.
---

# LNP-IL Design

A public-data pipeline for predicting mRNA transfection efficiency of lipid nanoparticle (LNP) formulations and, later, proposing ionizable lipids (ILs) for a wet-lab partner to test. The project's decisions are in `docs/design.md` and its goals and stop conditions are in `docs/vision.md`. Read the design doc before changing behavior.

## What exists today

Only data ingest and curation for LNPDB. There is no model, no candidate generator and no shortlist yet. Do not describe the project as predicting anything.

## Set up

```bash
make install
git clone https://github.com/evancollins1/LNPDB.git ../LNPDB   # MIT code; check data terms
export LNPDB_DIR=$PWD/../LNPDB
```

## Build the dataset

```bash
uv run lnp-il data curate --out-dir data/curated          # uses $LNPDB_DIR
uv run lnp-il --json data curate --lnpdb-dir ../LNPDB -o data/curated
```

Output in `--out-dir`:

| File | Use |
|---|---|
| `dataset_dev.csv` | Development rows. The only table to train, tune or select models on. |
| `studies.csv` | One row per development study: size, context, LiON-overlap flag, fragment coverage. |
| `curation_report.json` | Row counts at each step and the hit definition used. |
| `sealed/` | The sealed holdout. Do not open before the final report. |

Under `--json`, success is `{"ok": true, "data": ...}` and failure is `{"ok": false, "error": {"code", "message"}}` with exit code 1. A usage error exits 2.

## Rules that must hold

1. **Sealed holdout.** Studies JL_2024, XH_2025, AP_2025 and RG_2023 are held out whole. They must not enter training, normalization, feature engineering, model selection or tuning. Open `sealed/` once, for the final report. To change the set, edit `docs/design.md` first, then `src/lnp_il/core/studies.py`.
2. **Labels are within-study.** `label_z` is a z-score within one (study, context) group. Never compare or pool labels across studies without the study ID, and never read a value from one study as an absolute efficiency.
3. **Evaluate on whole studies.** Use leave-one-study-out. Random or scaffold splits inside a study are optimistic, because libraries are built from related analogs.
4. **LiON contamination.** Eleven LNPDB studies were in LiON's training data (`lion_contaminated` in `studies.csv`). Any comparison with LiON on them is contaminated. LiON's unpublished datasets cannot be identified.
5. **Hit calls.** `hit` marks the top 16% within a (study, context) group. It is missing for groups under 20 rows and for groups where ties make a top-16% call impossible (the four-level discretized readouts in KZ_2016 and ZC_2023). Missing is not "not a hit".
6. **Readouts.** Particle diameter, zeta potential and hemolysis are not delivery labels and are dropped. `uptake` rows are kept pending author confirmation (`docs/design.md`, open question 9).

## Data sources and licenses

- LNPDB is the only source of labels. LNP Atlas has structures but its activity values are free text, so it is not used for labels.
- The COMET/LANCE repository and data are not used. Its license excludes commercial research and development and forbids redistribution.
- No copyrighted paper text, PDFs or raw datasets go into the repository.

## Interpreting results

- Everything produced here is retrospective. Do not claim efficacy, safety or in vivo performance for any lipid without experimental support.
- In vivo contexts have 1 to 4 studies each, and mouse intramuscular training data is about 135 rows once the holdout is removed. Treat in vivo output as exploratory.
- Only 2.6% of ILs appear in more than one study, so cross-study results mostly measure generalization to new chemistry.

## Troubleshooting

- `DATA_SOURCE` error, "table not found": `--lnpdb-dir` must point at a clone of the LNPDB repository (it expects `data/LNPDB_for_LiON/LNPDB.csv`).
- Hit rate far from 16% in a new context: check tie structure before changing the definition; see `_hit_calls_for_group` in `src/lnp_il/core/curate.py`.
- Counts differ from `docs/design.md`: the pinned numbers are for LNPDB commit `fc7c389`. A newer LNPDB changes them.
