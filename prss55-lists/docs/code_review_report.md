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
  **Follow-up (resolved)**: the four computed values were initially passed
  through to the output TSV but not consumed by triage logic. `contact_density_8a`,
  `exposure_robustness`, `ss_p1`/`ss_p1prime`, and `has_multiple_isoforms` are
  now wired into `triage_prss55_sites.py` as `REVIEW` flags (not hard
  exclusions, per §6 of the design doc — only sequence/processing/membrane
  conflicts are `EXCLUDE`). `domain_annotations` was also added as a `REVIEW`
  flag, covering the design doc's "domain context" criterion (§4) which had no
  implementation. `family_annotations` was deliberately left unused for
  triage: it is protein-family membership, not site-level evidence, and would
  flag nearly every row without adding signal.

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

## 6. Under-committed decision (Isoform provenance dropped) — ✅ RESOLVED

- **Trigger**: An upstream `seq_id` carrying an isoform-specific accession (e.g. `sp|Q6UWB4-2|PRS55_HUMAN`).
- **Issue**: `prepare_prss55_predictions.py` unconditionally hardcoded `source_isoform` to `""`, even when `accession()` had already parsed an isoform suffix out of the `seq_id`. This contradicts §2 of the design doc, which requires recording the "reviewed isoform" per site. Confirmed via live UniProt API that isoform-suffixed accessions (`Q6UWB4-2.json`) resolve correctly, including their own `ALTERNATIVE PRODUCTS` comment, so downstream feature extraction was never at risk — only the audit-trail field was silently dropped.
- **Change**: Derive `source_isoform` from the parsed accession's `-N` suffix instead of hardcoding blank.
- **Resolution**: Added `isoform_suffix()` in `prepare_prss55_predictions.py` and used it to populate `source_isoform`. Verified against a canonical accession (blank, unchanged) and an isoform-suffixed accession (`Q6UWB4-2` → `source_isoform: 2`); the real dataset (`data/prss55_predictions.raw.tsv`, no isoform-suffixed accessions) produces identical output to before the change.

## 7. Breakage (Subcellular-location substring false positive) — ✅ RESOLVED

- **Trigger**: A protein annotated `Secreted; Cytoplasmic vesicle, secretory vesicle, acrosome` — found in the real 2336-row dataset (`results/epid_triaged_sites.tsv`), accession `P20155`.
- **Issue**: The original exclusion (`"cytoplasm" in subcell.lower()`) matched the substring "cytoplasm" inside "**Cytoplasmic** vesicle," which is a distinct membrane-bound compartment, not bulk cytosol — and the protein was explicitly also marked `Secreted`. Confirmed against real data: this false positive, plus a second one (`P56377`, `Golgi apparatus; Cytoplasmic vesicle membrane; ...`), wrongly excluded 27 rows total.
- **Change**: Match per semicolon-separated location term rather than the whole string; broaden the check to other unambiguous intracellular compartments while keeping any accessible term (Secreted/Cell membrane/Cell surface/extracellular/acrosome) as an override.
- **Resolution**: `subcellular_verdict()` in `triage_prss55_sites.py` replaces the naive substring check. Hard-excludes `Cytoplasm`, `Nucleus`, `Chromosome`, `Mitochondrion`, `Peroxisome` only when no accessible term is also present; treats `Golgi apparatus`/`Endoplasmic reticulum`/`Lysosome` as a `REVIEW` flag (ambiguous secretory-pathway residency), not an exclusion. Verified against the real dataset: both false positives corrected (7 rows rescued to `REVIEW`, 5 of `P20155`'s 20 rows rescued), and one previously-missed accession (`Q70EK9`, annotated only `Chromosome`, 80 rows) correctly caught for the first time.

## 8. Under-committed decision (Topology-annotation flag conflated two kinds of "missing") — ✅ RESOLVED

- **Trigger**: Any purely secreted/soluble protein with no transmembrane segment — the majority of this dataset (60 of 87 accessions).
- **Issue**: `topology_annotations` empty → `REVIEW` flag, unconditionally. But UniProt only curates `Topological domain` for proteins that actually cross a membrane; a protein with no membrane-spanning region has no cytoplasmic-vs-extracellular sidedness to annotate in the first place. The flag treated "not applicable" identically to "genuinely unresolved," inflating `REVIEW` for the majority of the dataset (2126 of 2336 rows carried this flag).
- **Change**: Suppress the flag when `subcellular_location` indicates purely soluble/secreted with no membrane term; keep it when a membrane term is also present (e.g. a shed ectodomain still has a real sidedness question) or the location is itself ambiguous.
- **Resolution**: Added `has_no_membrane_topology_question()` in `triage_prss55_sites.py`. Verified against the real dataset: rows carrying the flag dropped from 2126 to 867, and `ELIGIBLE` went from 0 to 10 rows for the first time.

## 9. Missing criterion (No electrostatic signal) — ✅ RESOLVED

- **Trigger**: A design discussion on why the shortlist skewed almost entirely to `REVIEW`/`EXCLUDE` with zero `ELIGIBLE`, prompting a review of what additional structural evidence could differentiate candidates.
- **Issue**: The design doc's feature table (§4) has no electrostatics criterion. Full electrostatic-potential or docking-based complementarity was considered and rejected: PRSS55 has no solved structure and its own membrane topology is itself uncertain, and the design doc already cautions that whole-protein docking "is not a primary filter."
- **Change**: Add a substrate-side-only electrostatic proxy that doesn't require modeling PRSS55's own pocket: whether the charged P1/P1′ residue is already intramolecularly salt-bridged within the folded substrate, which would reduce its availability to engage the protease even if window-level RSA reads as exposed.
- **Resolution**: Added `residue_names()` and `salt_bridge_partner()` in `extract_prss55_site_features.py` (CA–CA distance as an explicitly-documented coarse proxy for true side-chain salt-bridge distance), new `p1_salt_bridge_partner`/`p1prime_salt_bridge_partner` output columns, and a corresponding `REVIEW` flag in `triage_prss55_sites.py`. `cached_structural_features()` gracefully upgrades any `cache/structural/` entry written before this field existed rather than erroring. Verified against synthetic PDB coordinates (6 cases: bridged, isolated, non-charged, missing residue) and against live AlphaFold data. **Correction (see finding 10):** an early version of this check also flagged sequence-adjacent residues (including P1/P1′ against each other) as salt-bridged purely from fixed peptide-bond CA–CA geometry, not real proximity — this was a bug, not a validating finding, and is fixed in finding 10.

## 10. Breakage (Salt-bridge check flagged sequence-adjacent residues) — ✅ RESOLVED

- **Trigger**: User inspection of the salt-bridge output noticed P1 and P1′ — always exactly one sequence position apart, by construction of the `p1_offset` convention — being flagged as forming a mutual salt bridge with each other.
- **Issue**: `salt_bridge_partner()`'s 8 Å CA–CA radius check has no lower bound. Sequence-adjacent residues (i, i+1) have a CA–CA distance fixed at ~3.8 Å by peptide-bond geometry, essentially constant regardless of conformation or real spatial proximity — always well inside the 8 Å cutoff. Any two adjacent, oppositely-charged residues therefore always "pass," independent of whether their side chains are anywhere near each other in 3D. Since P1′ = P1 + 1 always, this meant P1/P1′ could never be meaningfully evaluated against each other at all — every prior report of a "P1/P1′ mutual salt bridge" (including the one cited as validating evidence in finding 9) was this artifact, not a real structural finding.
- **Change**: Exclude immediately sequence-adjacent residues from the candidate-partner search; residues two or more positions away have CA–CA distances that genuinely vary with conformation and so carry real information.
- **Resolution**: `salt_bridge_partner()` in `extract_prss55_site_features.py` now skips `abs(other - position) <= 1`. Verified against synthetic coordinates (adjacent pair no longer matches; a non-adjacent pair 2 positions away, same distance, still correctly matches) and against live data: the two real cases that previously showed a P1/P1′ mutual match no longer do, while genuine non-adjacent matches (2+ positions away) are preserved.

## 11. Surface (Misleading column name: `exposure_robustness`) — ✅ RESOLVED

- **Trigger**: User question — "why is it called exposure robustness if all that it does is pLDDT."
- **Issue**: The column name and its design-doc definition (§5: "exposed... consistently... model is low confidence, site may be an interface") implied a conclusion about solvent exposure. The implementation never read `window_rsa`/`rsa` at all — it's computed purely from `window_plddt` (AlphaFold model confidence). A confidently *buried* site (high pLDDT, low RSA) would be labeled `"Medium (confident AlphaFold region)"`, reading like "medium confidence this is exposed" when it measures no such thing.
- **Change**: Rename to something that describes what's actually computed, rather than fix the deeper implementation gap (combining RSA and pLDDT into a true exposure-confidence label) — a decision to revisit only if the richer version is later worth the complexity.
- **Resolution**: Renamed `exposure_robustness` → `plddt_confidence` in `extract_prss55_site_features.py` (including the internal `robustness` variable) and `triage_prss55_sites.py`; the `REVIEW` reason text now also points to `rsa_window_mean`/`rsa_window_min` for actual exposure. Verified end-to-end with no stale references remaining in either script; no cache-compatibility concern since the label is recomputed fresh from cached raw pLDDT each run, never itself cached.
