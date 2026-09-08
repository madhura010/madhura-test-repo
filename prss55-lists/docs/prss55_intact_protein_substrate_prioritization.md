# Computational prioritization of intact-protein substrates for human PRSS55

## Purpose

Rank predicted PRSS55 8-mer sites in human proteins for follow-up testing. This
is a **cleavability-prioritization** workflow, not a claim that a protein has
been cleaved. Computational analysis cannot demonstrate a proteolytic
neo-terminus or an exact cleavage event.

## Scope and assumptions

- An upstream prediction tool supplies predicted 8-mers, their protein
  coordinates, and a `prob_cleavage` score. For the present PRSS55 dataset, the
  central arginine (position 4) is P1 and the proposed bond is Arg↓P1′. Nothing
  upstream verifies this holds per row, so the pipeline checks it: P1 should be
  basic (Arg/Lys, matching PRSS55's trypsin-like S1 pocket) or, short of that,
  a Chou-Fasman coil/turn-former (Gly/Ser/Asn/Asp) that at least won't itself
  lock the local backbone into rigid helix/strand geometry. These are recorded
  as two independent facts, not one merged pass/fail — a site can be basic
  without being coil-favoring and vice versa, and collapsing them loses that
  distinction. Neither holding flags the row for review (data error, or a site
  the central-residue convention doesn't fit), never a hard exclusion.
- The objective is cleavage of intact proteins, not merely hydrolysis of short
  peptides.
- Co-expression in the relevant reproductive setting has already been applied
  as an eligibility filter and is not re-scored here.
- Each candidate is analysed as a *site* (P4–P4′), not as a protein-level
  property.

## Biological constraints specific to PRSS55

Human PRSS55 is testis-enriched and annotated as a probable S1 serine protease.
Its membrane topology is uncertain; the human entry notes possible GPI anchoring
or a type-I membrane topology. Mouse data support a GPI-anchored protein on the
sperm/acrosomal surface. Consequently, a candidate must be present on the side
of a membrane or in the compartment that PRSS55 can physically access. Do not
assume that every co-expressed intracellular protein is eligible.

Sources: [UniProt PRSS55 (Q6UWB4)](https://www.uniprot.org/uniprotkb/Q6UWB4-2);
[Shang et al., 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6208766/).

## Workflow

### 1. Preserve and interpret the prediction input correctly

Before applying structural ranking, verify that each window maps to the correct
protein sequence and preserve the score direction and range.

- Store each hit as an 8-residue window with its start/end coordinates.
- Use `prob_cleavage` only to sort candidates after structural exclusions; it
  is not a probability that the intact protein is cleaved.
- Do not invent a P1-P1′ bond for future datasets. An 8-mer has seven possible
  peptide bonds. Here, use the stated central-arginine convention (P1 offset 4)
  and document it in every result.

### 2. Map every hit to the correct protein form

For each hit, record:

- UniProt accession, reviewed isoform, and sequence version;
- 8-mer sequence and residue coordinates;
- P1–P1′ coordinate and flanking sequence;
- whether the site is removed by a signal peptide, pro-peptide, or other known
  processing event;
- whether the same site occurs in multiple isoforms.

Exclude hits that cannot be mapped unambiguously or do not occur in the mature
protein form being evaluated.

### 3. Apply hard accessibility and topology exclusions

Discard or flag candidates when the scissile bond:

- lies in a transmembrane segment or signal peptide;
- is on the membrane side inaccessible to PRSS55;
- is in an intracellular compartment with no route to the extracellular space
  short of cell lysis (cytoplasm, nucleus, chromosome, mitochondrion,
  peroxisome) — unless the same subcellular-location annotation also
  indicates a secreted or surface-accessible pool (e.g. `Secreted; Membrane`
  for a shed ectodomain), in which case the conflict does not apply;
- is buried in the core of a folded domain;
- has no usable structure or disorder evidence and cannot be assessed.

Treat residency in a secretory-pathway compartment the protein may only be
transiting through (Golgi apparatus, endoplasmic reticulum, lysosome) as a
manual-review flag, not a hard exclusion — residency there is not always
permanent, unlike the compartments above.

Use UniProt topology/processing annotations first. Use a high-quality
experimental structure when available; otherwise use an AlphaFold model, marked
as predicted structural evidence.

### 4. Compute site-level structural features

Calculate all structural features over the 8-mer window and at the defined
P1–P1′ bond (Arg position 4 followed by position 5).

| Feature | Calculation | Interpretation |
| --- | --- | --- |
| Window accessibility | Mean and minimum SASA/RSA across the 8-mer | Site-level evidence of exposure; do not use protein-wide or domain-average SASA alone. |
| Bond-specific accessibility | Per-residue SASA/RSA at P1 and P1′, once the bond is defined | Do not compute or infer this from the centre of the 8-mer. |
| Electrostatic complementarity | Intramolecular salt-bridge check: is the charged P1/P1′ side chain within a proxy radius of an oppositely-charged residue in the folded substrate, excluding the residue's own sequence neighbors | Penalize a charged P1/P1′ residue that may already be ion-paired within the fold rather than free to engage the protease. Substrate-side only — does not model PRSS55's own active site, which has no solved structure. Sequence-adjacent residues must be excluded from the search: their backbone distance is fixed by peptide-bond geometry regardless of real spatial proximity, so P1 and P1′ (always one position apart) would otherwise always trivially "pass" against each other with no genuine signal. |
| Structural depth/contact density | Local atom/residue contacts or depth below protein surface | Penalize grooves and cores that are nominally solvent exposed but sterically constrained. |
| Secondary structure | Secondary structure at least across P2–P2′ | Favor coil, turn, or accessible loop; penalize stable alpha-helix and beta-strand. |
| Proline near the bond | Presence of Proline anywhere in the 8-mer window, and specifically at P1′ | Proline at P1′ is a distinct, localized concern independent of window-level flexibility: no backbone N-H for the oxyanion hole, an elevated cis-peptide-bond population, and steric bulk in the S1′ subsite — a general serine-protease-family observation, not confirmed for PRSS55. Proline elsewhere in the window is reported separately and not treated as unfavorable on its own — it can promote local disorder, which this pipeline otherwise favors. |
| Flexibility | Disorder prediction plus AlphaFold pLDDT where applicable | Supports, but does not prove, transient access. Low pLDDT is not direct evidence of cleavage. |
| Domain context | Domain/core, disulfide-rich region, catalytic site, or binding region | Penalize sites where cleavage is structurally implausible or disruptive without evidence. |
| Interface occlusion | Experimental complex structures or credible complex/interface annotations | Penalize monomer-exposed sites that may be buried in the native assembly. |
| PTM/glycan shielding | Known glycosylation/PTM annotations and nearby N-X-S/T sequons | Flag sites likely shielded in the native protein. |
| Structural confidence | Structure source, model confidence, coverage | Record uncertainty explicitly rather than forcing a precise score. |

### 5. Assess exposure robustness

Avoid treating one static AlphaFold structure as ground truth. Assign an exposure
robustness label for each site:

- **High:** exposed in an experimental structure or consistently exposed across
  multiple relevant structural observations.
- **Medium:** exposed in one confident predicted structural region.
- **Low:** model is low confidence, site may be an interface, or accessibility
  differs across plausible structures.

The current implementation only delivers the model-confidence half of this —
it reports `plddt_confidence` (Medium/Low/Unknown), computed purely from mean
window pLDDT, with no `High` tier since only one AlphaFold model is used and
there is no experimental structure to cross-check against. It does not itself
read the RSA columns, so it does not actually assess *exposure* robustness in
the sense defined above — a site can be confidently buried just as easily as
confidently exposed. The column was named `exposure_robustness` originally,
which overclaimed what it measures; it is now named `plddt_confidence` to
match. Combining it with `rsa_window_mean`/`rsa_window_min` into a label that
matches this section's actual definition remains a gap, not yet implemented.

Whole-protein PRSS55–substrate docking is not a primary filter: unconstrained
docking across many targets tends to create precise-looking but unvalidated
poses. It may be used only for qualitative inspection of the final few sites.

### 6. Rank candidates transparently

Use hard exclusions before any score. For surviving sites, rank with a
documented composite:

```text
priority =
    hard exclusions (sequence mismatch, processing overlap, membrane conflict,
                      intracellular-compartment conflict)
  → manual-review flags (topology, glycan/PTM, disulfide, isoform ambiguity,
                          domain overlap, secretory-pathway residency,
                          secondary structure, contact density,
                          electrostatic/salt-bridge, proline at P1'/in window,
                          P1 residue class, missing structure)
  → sort remaining sites by supplied prob_cleavage
```

Until positive and negative experimental labels exist, this is a prioritization
workflow, not a calibrated probability. Use statuses:

- **ELIGIBLE:** no automatic sequence, processing, membrane, or compartment
  conflict, and none of the manual-review flags above apply.
- **REVIEW:** no hard conflict, but topology/structure/electrostatic/PTM
  evidence needs human interpretation.
- **EXCLUDE:** incompatible sequence mapping, processing annotation,
  transmembrane/intramembrane overlap, or an intracellular compartment with
  no route to the extracellular space.

### 7. Produce a reproducible candidate table

One row per predicted site:

```text
accession | isoform | protein name | 8-mer | P1-P1′ coordinate |
prob_cleavage | P1/P1′ SASA | min/mean window SASA |
secondary structure | disorder/pLDDT | topology status |
PTM/interface flags | electrostatic/salt-bridge flag |
proline flag (P1'/window) | P1 residue class (basic/coil-favoring) |
structure source/confidence | pLDDT confidence |
composite score | tier | rationale
```

Keep the raw feature values, tool/database versions, structure identifiers, and
exclusion rationale. This permits later calibration using experimental outcomes.

## What experimental testing will establish later

Testing the top-ranked sites should determine whether cleavage occurs in the
intact substrate and, if so, which bond is cut. Until then, the pipeline reports
ranked hypotheses, not confirmed PRSS55 substrates.
