# Handoff

Updated: 2026-09-08

## Objective
Implement code-review and design-doc requirements for the PRSS55 intact-protein substrate prioritization workflow, keep documentation synchronized, and push the pipeline code to the user's mirror at `madhura010/madhura-test-repo` (`prss55-lists/` subfolder). The original `origin` remote (`git@github.com:madhura010/prss55-lists.git`) no longer resolves — the repo has been deleted — so `madhura-test-repo` is the current push target, by explicit user decision (leave the stale `origin` remote as-is, don't repoint it).

## Current state
- **Feature Extraction (`scripts/extract_prss55_site_features.py`)**:
  - `subcellular_location`, `has_multiple_isoforms`, `contact_density_8a` (CA atoms within 8 Å of window), mmCIF format guard — from earlier rounds.
  - `plddt_confidence` (Medium ≥70 pLDDT / Low <70 / Unknown) — **renamed from `exposure_robustness`**. It's computed purely from `window_plddt` and never reads RSA, so the old name overclaimed (implied it measured solvent exposure, which it doesn't — a confidently *buried* site would have read as "Medium").
  - `p1_salt_bridge_partner` / `p1prime_salt_bridge_partner`: `residue_names()` parses residue identity from PDB CA lines; `salt_bridge_partner()` finds the nearest oppositely-charged residue within an 8 Å CA–CA proxy radius. **Fixed**: sequence-adjacent residues (i, i+1) are now excluded from the candidate search — their CA–CA distance is fixed at ~3.8 Å by peptide-bond geometry regardless of real proximity, so P1/P1′ (always exactly 1 apart) could never have been meaningfully evaluated against each other before this fix; every earlier "P1/P1′ mutual salt bridge" report was this artifact.
  - `proline_in_window` / `p1prime_is_proline`: sequence-only (no structural dependency), whether the 8-mer contains Proline anywhere / specifically at P1′.
  - `p1_is_basic` / `p1_is_coil_favoring`: sequence-only, two **independent** columns (deliberately not merged) — whether P1 is basic (Arg/Lys, matching PRSS55's trypsin-like S1 specificity) and whether P1 is a Chou-Fasman coil/turn-former (Gly/Ser/Asn/Asp) as a fallback that at least won't lock the local backbone into rigid secondary structure. Nothing upstream previously verified the dataset's "central residue" convention held per-row.
  - `cached_structural_features()` caches AlphaFold/RSA/secondary-structure/residue-identity per accession under `cache/structural/` (`--structural-cache-dir`), so proteins with many candidate sites are fetched once, not once per site. Gracefully upgrades any cache entry written before residue identity was added.
  - `[i/N] accession source_id` progress printed to stderr per row.
- **Normalization (`scripts/prepare_prss55_predictions.py`)**:
  - `--p1-offset` defaults to `4`; `source_isoform` derived from the accession's `-N` suffix.
- **Triage (`scripts/triage_prss55_sites.py`)**:
  - `subcellular_verdict()`: matches per semicolon-separated location term (not the whole string — a naive substring check on "cytoplasm" false-matched "Cytoplasmic vesicle, secretory vesicle, acrosome"). Hard-excludes `Cytoplasm`/`Nucleus`/`Chromosome`/`Mitochondrion`/`Peroxisome` unless an accessible term (Secreted/Cell membrane/Cell surface/extracellular/acrosome) is also present; `Golgi`/`Endoplasmic reticulum`/`Lysosome` are a `REVIEW` flag instead.
  - `has_no_membrane_topology_question()`: suppresses the "no topology annotation" `REVIEW` flag for proteins that are purely soluble/secreted with no membrane term.
  - `REVIEW` flag for a possible intramolecular salt bridge at P1/P1′ (now adjacency-safe, see above).
  - `review-pro` — dedicated column (not folded into `review_reason`), so proline concerns are independently filterable: fires for Proline at P1′ (mechanistic concern) or anywhere in the window (context-dependent, informational).
  - `review-p1` — dedicated column, fires only when P1 is **both** non-basic and non-coil-favoring (reads `p1_is_basic` and `p1_is_coil_favoring` independently).
  - Full flag set: sequence/processing/membrane/topology/subcellular-location hard exclusions; `REVIEW` for missing topology (with suppression), glycosylation/PTM proximity, disulfide overlap, helix/strand at P1/P1′, elevated contact density, salt bridge at P1/P1′, low `plddt_confidence`, multiple isoforms, domain/motif overlap, secretory-pathway-only location, unresolved P1 position, plus `review-pro`/`review-p1`. `family_annotations` deliberately unused (protein-level, not site-level).
- **Documentation**: `README.md` and `docs/prss55_pipeline_usage.md` updated for the `exposure_robustness`→`plddt_confidence` rename and the salt-bridge adjacency fix. **Not yet updated** for `review-pro`/`review-p1`/proline/P1-basic-or-coil-favoring — those were implemented and verified but doc sync for them hasn't been requested yet. `docs/code_review_report.md` findings 1–4 and 6–11 resolved; finding 5 (missing `AGENTS.md`) still open. `docs/prss55_intact_protein_substrate_prioritization.md` (the design doc) updated earlier for the compartment broadening and electrostatics addition, but not yet for proline/P1-criteria either.

## Decisions and constraints
- Push destination is `madhura-test-repo/prss55-lists`, not the original `origin` — via a separate local clone (session scratchpad), explicit file-scoped `git add`, not a git remote on this working directory.
- `contact_density_8a >= 20` and the salt-bridge check are both documented-as-provisional heuristics, not experimentally calibrated.
- Column-naming precision matters to this user — two things got relabeled/restructured after direct questions exposed a mismatch between name and behavior: `exposure_robustness`→`plddt_confidence`, and a merged P1 pass/fail boolean was split into independent `p1_is_basic`/`p1_is_coil_favoring` columns on request. Prefer separate, honestly-named columns over merged/overclaiming ones going forward.
- The user has their own real dataset in this working directory: `data/epid_positives_1*.{csv,xlsx}`, `results/epid_site_features_2.tsv`, `results/epid_triaged_sites_2.tsv` (2336 rows, 87 unique accessions, `_2` suffix intentional — not the pipeline's default output names, user's own choice) — not created by this session, left untouched.

## Evidence
- Every change this session verified both with synthetic unit-style cases and against the user's real 2336-row dataset before being reported as done.
- Salt-bridge adjacency fix: synthetic case confirmed (adjacent pair no longer matches, non-adjacent 2-apart pair still does) and confirmed on live data that the two previously-reported P1/P1′ mutual matches are gone.
- `p1_is_basic`/`p1_is_coil_favoring`: 4 synthetic cases (Arg, Gly, Leu, unresolved offset) all correct; real dataset shows `p1_is_basic: true` throughout (matches the dataset's actual central-Arg convention).
- `plddt_confidence` rename: verified no stale `exposure_robustness`/`robustness` references remain in either script; no cache-compatibility concern (the label is recomputed fresh from cached raw pLDDT each run).
- A published flowchart artifact exists summarizing the pipeline/decision logic for a slide deck (title "PRSS55 Shortlisting Logic") — predates the proline/P1-criteria/rename work, would need regenerating if the user wants it current.

## Next action
None pending on this side. Recent script changes (salt-bridge adjacency fix, `review-pro`/`review-p1`, `plddt_confidence` rename) are implemented and verified but **not yet pushed** — the user said "let me test first" and hasn't yet asked to push. Wait for that go-ahead, or for a request to finish syncing `README.md`/`docs/prss55_pipeline_usage.md`/the design doc for the proline and P1-criteria columns (only the rename and salt-bridge fix are doc-synced so far).

## Blockers and risks
- Avoid `git add -A`/`git add .` in this working directory — deleted trial directories and skill dirs (`.agents/`, `.claude/`) must stay unstaged.
- `skills-lock.json` and `skills-pack.lock.json` are modified in this working directory but out of scope for the PRSS55 work.
