# PRSS55 site-prioritization tools

## What the tools do

`scripts/extract_prss55_site_features.py` validates each predicted 8-mer against
the current UniProt sequence, retrieves maturity/topology/PTM annotations, and
optionally calculates per-residue RSA from an AlphaFold model. It does **not**
infer secondary structure, protein-complex interfaces, or a cleavage probability
without separately supplied evidence.

The output distinguishes a UniProt `Chain` (the retained mature protein) from a
`Signal` or `Propeptide` (a region removed during processing), and separately
records an annotated mature `Peptide`. This distinction is essential for small
secreted proteins such as defensins.

`domain_annotations` contains residue-bounded UniProt Domain, Region, Repeat,
Motif, Zinc finger, and Coiled coil features. Each entry retains its feature
type plus description. `family_annotations` contains InterPro/Pfam memberships,
which are useful context but are not reported as site coordinates unless the
source actually supplies boundaries.

With the project-local PyDSSP dependency installed, the output also includes
`ss_window_pattern` and `ss_p1`/`ss_p1prime`: `H` = alpha helix, `E` = beta
strand, and `C` = loop/other. The `ss_*_fraction` columns are the fraction of
the eight residues assigned to each state. They are assignments for the chosen
AlphaFold model, not an experimental ensemble measurement.

The output also includes:

- `has_multiple_isoforms`: whether the protein has multiple known isoforms,
  extracted from UniProt `ALTERNATIVE PRODUCTS` comments;
- `subcellular_location`: UniProt-annotated subcellular compartment(s) for the
  protein (used by the triage step to judge accessibility to a surface-anchored
  ectoenzyme — see below);
- `contact_density_8a`: count of CA atoms within 8 Å of the 8-mer window,
  penalizing sites that are nominally solvent-exposed but sterically buried;
- `exposure_robustness`: confidence label (`Low`, `Medium`, or `Unknown`) for
  the structural-exposure evidence, based on AlphaFold pLDDT;
- `p1_salt_bridge_partner` / `p1prime_salt_bridge_partner`: residue number of
  the nearest oppositely-charged residue within 8 Å (CA–CA proxy) of P1/P1′,
  if the P1/P1′ residue itself is charged (Arg/Lys/Asp/Glu) and has one.
  Empty otherwise. This is a substrate-side electrostatic signal only — it
  does not model PRSS55's own S1 pocket, since PRSS55 has no solved structure
  and its own membrane topology is itself uncertain (see the design doc); it
  only asks whether the charged P1 residue is already ion-paired within the
  folded substrate rather than free to engage a protease.

`scripts/triage_prss55_sites.py` is a deterministic rule-based analysis step.

Subcellular-location handling (`subcellular_verdict()`) matches per
semicolon-separated location term rather than the whole string, because a
naive substring check on `"cytoplasm"` also matches `"Cytoplasmic vesicle,
secretory vesicle, acrosome"` — a distinct membrane-bound compartment, not
bulk cytosol. It hard-excludes unambiguous intracellular compartments with no
route to the extracellular space (`Cytoplasm`, `Nucleus`, `Chromosome`,
`Mitochondrion`, `Peroxisome`), unless an accessible term (`Secreted`, `Cell
membrane`, `Cell surface`, `extracellular`, `acrosome`) also appears anywhere
in the same annotation. Secretory-pathway compartments a protein may only be
transiting through (`Golgi apparatus`, `Endoplasmic reticulum`, `Lysosome`)
are a `REVIEW` flag, not an exclusion, since residency there isn't always
permanent. Separately, `has_no_membrane_topology_question()` suppresses the
"no topology annotation" review flag specifically for proteins whose location
is purely soluble/secreted with no membrane term at all — such a protein never
crosses a membrane, so it has no cytoplasmic-vs-extracellular sidedness for
UniProt to annotate in the first place, and a missing `Topological domain`
feature there is expected, not a genuine gap.

Everything structural is a `REVIEW` flag rather than a hard exclusion, per the
design doc's ranking rules (§6): a predicted helix/strand at P1 or P1′
(`ss_p1`/`ss_p1prime`), elevated local contact density (`contact_density_8a >=
20` — a provisional heuristic, not experimentally calibrated), a possible
intramolecular salt bridge at P1/P1′ (`p1_salt_bridge_partner` /
`p1prime_salt_bridge_partner` — likewise provisional), `Low` exposure
robustness, multiple annotated protein isoforms (`has_multiple_isoforms`), and
overlap with an annotated domain/motif/region (`domain_annotations`) all land
as review flags, alongside the existing glycosylation/PTM/disulfide/topology
flags. `family_annotations` (Pfam/InterPro family membership) is deliberately
not used for triage — it is protein-level, not site-level, evidence. It sorts
eligible candidates by the supplied `prob_cleavage`. It does not fit, retrain,
calibrate, or create an additional ML model.

## Input schema

The supplied table can be normalized directly:

```bash
python3 scripts/prepare_prss55_predictions.py \
  --input data/prss55_predictions.raw.tsv \
  --output data/prss55_predicted_sites.csv
```

For the current PRSS55 predictions, the pivotal central arginine is position 4,
so the proposed cleavage is `P4-P3-P2-Arg↓P1′-P2′-P3′-P4′`. The `--p1-offset`
argument defaults to `4` for this convention; pass a different value only when
working with a dataset that uses a different bond definition.

For other input sources, start from `data/prss55_predicted_sites.template.csv`.
Required fields are:

| Field | Meaning |
| --- | --- |
| `accession` | UniProt accession for the candidate protein |
| `site_start` | 1-based start position of the 8-mer in that accession's sequence |
| `eight_mer` | Eight amino-acid one-letter codes |
| `p1_offset` | Optional 1-based P1 position within the 8-mer; leave blank when the exact bond is unknown |
| `model_score` | Supplied `prob_cleavage`; used only to sort structurally eligible candidates |

`source_isoform` and `source_id` are optional but strongly recommended.

## Run feature extraction

Install the documented optional structural dependency once when secondary-
structure assignment is required:

```bash
pip3 install --target .vendor -r requirements.txt
```

```bash
python3 scripts/extract_prss55_site_features.py \
  --input data/prss55_predicted_sites.csv \
  --output results/prss55_site_features.tsv \
  --with-rsa
```

The first run retrieves UniProt records into `cache/uniprot/`. With `--with-rsa`,
AlphaFold/RSA/secondary-structure results are cached per accession into
`cache/structural/` (override with `--structural-cache-dir`) — structural
evidence is a property of the protein, not the individual site, so a protein
with many candidate sites is only fetched and DSSP-assigned once, not once per
site. Progress (`[i/N] accession source_id`) is printed to stderr as each row
is processed, since a large input can take a while on the first, cold-cache
run. Residue identity (needed for the salt-bridge check) is cached alongside
RSA/pLDDT/secondary structure; a `cache/structural/` entry written before
that field existed is detected and transparently recomputed once, not treated
as an error. Inspect every row with a sequence mismatch, processing overlap,
unknown topology, missing structure, or incomplete structural coverage before
proceeding.

## Run deterministic triage

```bash
python3 scripts/triage_prss55_sites.py \
  --features results/prss55_site_features.tsv \
  --output results/prss55_triaged_sites.tsv
```

`ELIGIBLE` means no automatic structural conflict was found; `REVIEW` means
manual structural/topology interpretation is required (see the flag list
above); `EXCLUDE` means a sequence-processing, membrane, cytoplasmic
topology, or unambiguous intracellular subcellular-location conflict was
found (cytoplasm, nucleus, chromosome, mitochondrion, or peroxisome, with no
accompanying Secreted/surface/acrosome term). None means confirmed substrate.

## Required human review before ordering proteins

- Confirm P1–P1′ alignment and model-score direction/scale.
- Resolve mature-protein processing and membrane orientation for every retained
  candidate.
- Add experimental structure/complex/interface evidence where available.
- Review glycosylation, other PTMs, and disulfide annotations in the actual
  biological form. An annotated mature `Peptide` is supporting context, not an
  automatic exclusion.
- Record database release dates, model version, input checksum, and all manual
  inclusion/exclusion decisions.
