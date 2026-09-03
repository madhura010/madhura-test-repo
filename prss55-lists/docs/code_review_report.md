# Code Review: PRSS55 Site Prioritization Scripts

**Mode**: Standing review
**Target**: `scripts/*.py`
**Context**: `docs/prss55_intact_protein_substrate_prioritization.md`
**Read in full**: `scripts/extract_prss55_site_features.py`, `scripts/prepare_prss55_predictions.py`, `scripts/triage_prss55_sites.py`, `docs/prss55_intact_protein_substrate_prioritization.md`, `README.md`.

---

## 1. Fit / Claim mismatch (Design vs Implementation) — ✅ RESOLVED

The implemented scripts omit several explicit requirements mandated by the design document.

- **Trigger**: Any protein with multiple isoforms, cytosolic proteins, or proteins needing robustness scoring.
- **Issue**: The implementation does not track whether a site occurs in multiple isoforms, does not calculate "Structural depth/contact density", and does not assign an "exposure robustness label" (High/Medium/Low). Furthermore, it fails to evaluate `Subcellular location` to exclude cytosolic proteins, which the design doc strictly forbids for PRSS55 (PRSS55 is extracellular/surface-exposed).
- **Change**: Either implement these missing features (especially extracting `Subcellular location` annotations in `extract_prss55_site_features.py`) or update the design document to match the scoped-down implementation.
- **Resolution**: All four features implemented in `extract_prss55_site_features.py`:
  `has_multiple_isoforms` (from UniProt `ALTERNATIVE PRODUCTS`),
  `subcellular_location` (from UniProt comments),
  `contact_density_8a` (CA atom contacts within 8 Å),
  `exposure_robustness` (Low/Medium/Unknown based on pLDDT).
  Subcellular-location exclusions added to `triage_prss55_sites.py`.

## 2. At the edges (Topology validation gap) — ✅ RESOLVED

- **Trigger**: A predicted site on an integral membrane protein with `Topological domain: Cytoplasmic`.
- **Issue**: The design doc states candidates must be excluded if the scissile bond "is on the membrane side inaccessible to PRSS55". However, `triage_prss55_sites.py` (line 38) only flags if `topology_annotations` is completely missing. If a protein has a "Cytoplasmic" topology annotation, the script silently accepts it as `ELIGIBLE` rather than excluding it.
- **Change**: Update `triage_prss55_sites.py` to parse the value of `topology_annotations` and add an explicit `EXCLUDE` if it matches a known incompatible side (e.g., Cytoplasmic) instead of just checking for presence.
- **Resolution**: `triage_prss55_sites.py` now parses the `topology_annotations`
  value. Sites with "cytoplasmic" topology are excluded. Sites with
  "cytoplasm" or "nucleus" in `subcellular_location` are also excluded.

## 3. Breakage (Brittle PDB text parsing) — ✅ RESOLVED

- **Trigger**: The upstream AlphaFold database API returns an `mmCIF` file instead of `PDB`, or returns a large structure.
- **Issue**: `plddt_by_residue` and `secondary_structure_by_residue` in `extract_prss55_site_features.py` manually slice fixed character indices (e.g., `line[22:26]`) assuming a strict traditional `.pdb` format. AlphaFold DB is migrating away from PDB to mmCIF format. If the parser returns mmCIF, this string slicing will silently fail, returning `{}` for pLDDT.
- **Change**: Use a robust structural parsing library (like `Biopython`'s `PDBParser`/`MMCIFParser`) or at minimum assert the file format and fail loudly if it is not a valid fixed-width `.pdb`.
- **Resolution**: A format guard was added to `structural_features()` that
  detects mmCIF markers (`_atom_site.` or `loop_`) and raises a clear
  `RuntimeError` instead of silently returning empty data.

## 4. Under-committed decisions / Shape (P1 Offset) — ✅ RESOLVED

- **Trigger**: Running `prepare_prss55_predictions.py` without manually passing `--p1-offset 4`.
- **Issue**: The design doc states: "Use the stated central-arginine convention (P1 offset 4) and document it in every result." However, the script defaults the offset to blank (None), shifting the burden to the user and risking silent failure (the triage script will just add a review flag if it's missing, rather than applying the known rule).
- **Change**: Change the default of `--p1-offset` to `4` (or make it a required argument) in `prepare_prss55_predictions.py` to bake in the known PRSS55 biological convention.
- **Resolution**: `--p1-offset` now defaults to `4` in
  `prepare_prss55_predictions.py`. Documentation updated in `README.md` and
  `docs/prss55_pipeline_usage.md`.

## 5. Surface (Broken documentation pointer) — OPEN

- **Trigger**: Opening `CLAUDE.md`.
- **Issue**: `CLAUDE.md` simply points to `@AGENTS.md`, but `AGENTS.md` does not exist in the root directory.
- **Change**: Create `AGENTS.md` or remove the broken pointer.
- **Status**: Not yet addressed. Low priority; does not affect pipeline correctness.
