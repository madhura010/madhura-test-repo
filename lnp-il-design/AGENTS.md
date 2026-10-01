# lnp-il-design

Public-data pipeline that predicts LNP transfection efficiency and proposes ionizable lipids (ILs) for a wet-lab partner to test. Status: design phase, no pipeline code yet.

## Map

| Path | What it is |
|---|---|
| docs/vision.md | Why this exists, who it serves, gates and stop conditions |
| docs/mental-model.md | Definitions: formulation, study, context, label, holdout, candidate |
| docs/design.md | Modules, decisions, open questions. Read before writing code |
| docs/data-sources.md | Inventory of public datasets, sizes, licenses, overlaps |
| docs/lnpdb_per_experiment_summary.csv | One row per LNPDB study: rows, ILs, context, readout |
| docs/status.md | Current state and next steps |
| CHANGELOG.md | Past-tense history with the rejected alternative for each change |
| docs/handoff.md | Transfer summary for the next operator. Read first when resuming |
| src/lnp_il/core/ | ingest.py (read LNPDB), curate.py (clean, tag, split off the holdout), studies.py (sealed and LiON study sets) |
| src/lnp_il/cli/ | `lnp-il` command, thin over core. Model, design and select modules are planned in design.md |
| tests/ | pytest |
| skills/lnp-il-design/ | Project skill (SKILL.md): how to run the pipeline and the rules that must hold |
| skills-pack.lock.json | Recorded skill installs (dev-pack). Restore with `make skills-install` |

## Rules

- Commands go through `make` (`make help` lists them). Toolchain is uv, ruff, ty, pytest.
- `lnp-il data curate` builds the dataset. Development code reads `dataset_dev.csv`, `studies.csv` and `curation_report.json` only. The `sealed/` folder is opened once, for the final report.
- Labels are z-scored within a study. Never compare or pool labels across studies without the study ID.
- The sealed holdout (JL_2024, XH_2025, AP_2025, RG_2023) must not enter training, normalization, feature engineering or tuning. Do not read it before the final report.
- Raw datasets are read-only inputs and are not committed. LNPDB is cloned separately (see README); set `LNPDB_DIR` to its path.
- No copyrighted paper text, PDFs or extracted text in the repo.
- No efficacy, safety or in vivo claim without experimental support. Mark retrospective results as retrospective.
- Prose in docs and READMEs follows `aganitha-doc-writing`.

## Deeper

- Decisions and module contracts: docs/design.md
- Current state and TODO: docs/status.md
