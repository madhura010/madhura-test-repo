# Handoff

Updated: 2026-09-07

## Objective
Implement code-review and design-doc requirements for the PRSS55 intact-protein substrate prioritization workflow, ensure documentation is synchronized, and stage/commit clean pipeline code to `https://github.com/madhura010/prss55-lists`.

## Current state
- **Feature Extraction (`scripts/extract_prss55_site_features.py`)**:
  - Added `subcellular_location` extraction from UniProt `SUBCELLULAR LOCATION` comments.
  - Added `has_multiple_isoforms` detection from `ALTERNATIVE PRODUCTS` comments for input substrate proteins.
  - Added CA atom 3D coordinate parsing and `contact_density_8a` calculation (CA count within 8 Å of candidate 8-mer).
  - Added `exposure_robustness` label (`Medium` if window pLDDT >= 70, `Low` if < 70).
  - Added mmCIF format guard to prevent silent parse failures.
- **Normalization (`scripts/prepare_prss55_predictions.py`)**:
  - Default `--p1-offset` set to `4` per PRSS55 Arg↓P1′ convention.
  - `source_isoform` is now derived from the accession's `-N` isoform suffix (was previously always blank) via a new `isoform_suffix()` helper.
- **Triage (`scripts/triage_prss55_sites.py`)**:
  - Hard exclusions: `topology_annotations` containing "cytoplasmic"; `subcellular_location` containing "cytoplasm" or "nucleus".
  - New `REVIEW` flags (never hard excludes, per design doc §6): secondary structure at P1/P1′ (`ss_p1`/`ss_p1prime` in helix/strand), elevated `contact_density_8a` (>= 20, documented as an uncalibrated heuristic), `exposure_robustness` starting with "Low", `has_multiple_isoforms == "true"`, and non-empty `domain_annotations`. `family_annotations` intentionally left unused (protein-level, not site-level evidence).
  - Verified: old-schema rows (missing the new columns) degrade to `ELIGIBLE` without crashing; a hard exclusion still wins over a review flag on the same row; nothing is dropped from output, only labeled and sorted (`ELIGIBLE` → `REVIEW` → `EXCLUDE`).
- **Documentation**:
  - `README.md` and `docs/prss55_pipeline_usage.md` updated with new columns and default P1 offset.
  - `docs/code_review_report.md` updated: findings 1–4, 6 resolved; finding 5 (missing `AGENTS.md`) still open.

## Decisions and constraints
- **Git Commit Scope**: The user explicitly instructed **not** to commit or stage deleted unrelated directories (`Reference-formats-trial/`, `dossier-explore/`, `patent-extractor-trial/`) or skill dirs (`.agents/`, `.claude/`).
- Only stage files relevant to `prss55-lists`: `README.md`, `docs/`, and `scripts/` (and root metadata if applicable).
- Remote is set to `git@github.com:madhura010/prss55-lists.git` on branch `main`.
- `contact_density_8a >= 20` in `triage_prss55_sites.py` is a documented-as-provisional heuristic, not experimentally calibrated; expect to revisit once real cleavage outcomes exist.

## Evidence
- `extract_prss55_site_features.py` parses PDBs and returns the new columns without syntax errors; re-ran end-to-end against live UniProt/AlphaFold (`--with-rsa`) with `data/prss55_predicted_sites.csv`.
- `triage_prss55_sites.py` validated against 8 synthetic rows (one per new condition, plus a hard-exclude-wins case and an old-schema case) and against the real `results/prss55_site_features.tsv`.
- `prepare_prss55_predictions.py` validated against a synthetic isoform-suffixed accession (`Q6UWB4-2` → `source_isoform: 2`) and re-run against `data/prss55_predictions.raw.tsv` with identical output to before the change (no isoform-suffixed accessions in the real dataset).
- `docs/code_review_report.md` tracks resolutions against `docs/prss55_intact_protein_substrate_prioritization.md`.
- PyDSSP is not installed in this environment (`ModuleNotFoundError`), so live secondary-structure/contact-density values could not be produced end-to-end here — triage logic for those fields was validated with synthetic data instead. Real PyDSSP-backed values remain unverified against triage until run in an environment with it installed.

## Next action
Stage only the PRSS55-relevant changes and push to `origin main`:
```bash
git add README.md docs/ scripts/
git commit -m "Implement PRSS55 substrate prioritization features and review fixes"
git push -u origin main
```

## Blockers and risks
- Avoid `git add -A` or `git add .` as it stages deleted trial directories and skill directories that the user explicitly wants excluded.
- `skills-lock.json` and `skills-pack.lock.json` are also modified but were not part of the original PRSS55 scope — not included in the staging command above; confirm with user before staging if they should be included.
