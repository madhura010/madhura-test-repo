# Handoff

Updated: 2026-09-07

## Objective
Implement code-review and design-doc requirements for the PRSS55 intact-protein substrate prioritization workflow, keep documentation synchronized, and push the pipeline code to the user's mirror at `madhura010/madhura-test-repo` (`prss55-lists/` subfolder). The original `origin` remote (`git@github.com:madhura010/prss55-lists.git`) no longer resolves — the repo has been deleted — so `madhura-test-repo` is the current push target, by explicit user decision (leave the stale `origin` remote as-is, don't repoint it).

## Current state
- **Feature Extraction (`scripts/extract_prss55_site_features.py`)**:
  - `subcellular_location`, `has_multiple_isoforms`, `contact_density_8a` (CA atoms within 8 Å of window), `exposure_robustness` (Medium ≥70 pLDDT / Low <70 / Unknown), mmCIF format guard — all from earlier rounds.
  - `p1_salt_bridge_partner` / `p1prime_salt_bridge_partner`: new. `residue_names()` parses residue identity from PDB CA lines; `salt_bridge_partner()` finds the nearest oppositely-charged residue within an 8 Å CA–CA proxy radius (documented as a coarse heuristic — true salt bridges are side-chain-atom contacts, not CA–CA).
  - `cached_structural_features()` caches AlphaFold/RSA/secondary-structure/residue-identity per accession under `cache/structural/` (`--structural-cache-dir`), so proteins with many candidate sites are fetched once, not once per site (~29x fewer fetches on the real 87-accession dataset). Gracefully upgrades any cache entry written before residue identity was added, rather than erroring on the missing key.
  - `[i/N] accession source_id` progress printed to stderr per row.
- **Normalization (`scripts/prepare_prss55_predictions.py`)**:
  - `--p1-offset` defaults to `4`; `source_isoform` derived from the accession's `-N` suffix.
- **Triage (`scripts/triage_prss55_sites.py`)**:
  - `subcellular_verdict()`: matches per semicolon-separated location term (not the whole string — a naive substring check on "cytoplasm" false-matched "Cytoplasmic vesicle, secretory vesicle, acrosome"). Hard-excludes `Cytoplasm`/`Nucleus`/`Chromosome`/`Mitochondrion`/`Peroxisome` unless an accessible term (Secreted/Cell membrane/Cell surface/extracellular/acrosome) is also present; `Golgi`/`Endoplasmic reticulum`/`Lysosome` are a `REVIEW` flag instead (ambiguous secretory-pathway residency).
  - `has_no_membrane_topology_question()`: suppresses the "no topology annotation" `REVIEW` flag for proteins that are purely soluble/secreted with no membrane term — such a protein never crosses a membrane, so it has no sidedness for UniProt to annotate in the first place.
  - New `REVIEW` flag for a possible intramolecular salt bridge at P1/P1′.
  - Full flag set now: sequence/processing/membrane/topology/subcellular-location hard exclusions; `REVIEW` for missing topology (with the above suppression), glycosylation/PTM proximity, disulfide overlap, helix/strand at P1/P1′, elevated contact density, salt bridge at P1/P1′, low exposure robustness, multiple isoforms, domain/motif overlap, secretory-pathway-only location, and unresolved P1 position. `family_annotations` deliberately unused (protein-level, not site-level).
- **Documentation**: `README.md`, `docs/prss55_pipeline_usage.md`, `docs/code_review_report.md` all updated to match. `docs/code_review_report.md` findings 1–4 and 6–9 resolved; finding 5 (missing `AGENTS.md`) still open.

## Decisions and constraints
- Push destination is `madhura-test-repo/prss55-lists`, not the original `origin` — done via a separate local clone (in the session scratchpad) rather than a git remote on this working directory, since the target is a subfolder of a different repo with unrelated history. Push scope is `scripts/`, `docs/`, `README.md`, `skills/aganitha-uniprot-parser/`, `requirements.txt` — not the full working tree (`.agents/`, `.claude/`, `cache/`, `data/`, `results/`, the rest of `skills/` stay local-only), confirmed with the user.
- `contact_density_8a >= 20` and the salt-bridge check are both documented-as-provisional heuristics, not experimentally calibrated — expect to revisit once real cleavage outcomes exist. Neither is a hard exclusion for this reason.
- The user has their own real dataset in this same working directory: `data/epid_positives_1*.{csv,xlsx}`, `results/epid_site_features.tsv`, `results/epid_triaged_sites.tsv` (2336 rows, 87 unique accessions) — not created by this session, explicitly confirmed as the user's own files, left untouched.

## Evidence
- All script changes verified against both synthetic cases (unit-level, covering edge cases like the "cytoplasmic vesicle" false positive and salt-bridge geometry) and the user's real 2336-row dataset.
- Real-data before/after on the two triage fixes: subcellular-location broadening rescued 2 wrongly-excluded accessions and caught 1 previously-missed one (net EXCLUDE 1316→1384, for the right reasons in both directions); topology fix dropped rows carrying that flag from 2126→867 and moved `ELIGIBLE` from 0→10.
- Salt-bridge check verified against 6 synthetic PDB cases and live AlphaFold data, including a real case of P1/P1′ forming a mutual salt bridge.
- Cache-upgrade path (old `cache/structural/*.json` without a `residues` key) verified to recompute and rewrite in place rather than raising `KeyError`.
- A published flowchart artifact exists summarizing the full pipeline/decision logic for a slide deck: see the session's Artifact publish (title "PRSS55 Shortlisting Logic") — not part of the repo, referenced here in case it needs regenerating after further triage changes.

## Next action
The user is re-running `extract_prss55_site_features.py --with-rsa` on their real ~2500-row input themselves, to pick up the new salt-bridge columns (first run will re-fetch structural data for all 87 accessions to upgrade the cache — expected, not a bug). No pending action on this side unless asked to help interpret the regenerated output.

## Blockers and risks
- Avoid `git add -A`/`git add .` in this working directory — deleted trial directories (`Reference-formats-trial/`, `dossier-explore/`, `patent-extractor-trial/`) and skill dirs (`.agents/`, `.claude/`) must stay unstaged, per earlier explicit instruction. This constraint is about *this* working directory's own (now-orphaned) git history, not about the `madhura-test-repo` push, which uses a separate clone and explicit file-scoped `git add`.
- `skills-lock.json` and `skills-pack.lock.json` are modified in this working directory but out of scope for the PRSS55 work; not part of any push.
