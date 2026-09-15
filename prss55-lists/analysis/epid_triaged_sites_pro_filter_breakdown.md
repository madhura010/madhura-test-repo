# `epid_triaged_sites_pro.tsv` — filter/criteria breakdown

Generated 2026-09-15, against the latest results file:
`results/epid_triaged_sites_pro.tsv` (2,336 rows; companion features file
`results/epid_site_features_pro.tsv`). Criteria correspond to the decision
logic drawn in `docs/prss55_shortlisting_flowchart.html` and implemented in
`scripts/triage_prss55_sites.py`.

## Which results file this covers

`results/` contains several generations of output; this file documents the
most recent one as of 2026-09-15:

| File | Modified | Notes |
|---|---|---|
| **`epid_triaged_sites_pro.tsv`** | Sep 9 00:04 | **latest** — has proline + P1-residue-class columns |
| `epid_site_features_pro.tsv` | Sep 9 00:04 | its features-only companion |
| `epid_triaged_sites_2.tsv` | Sep 7 22:12 | predates proline/P1-class additions |
| `epid_site_features_2.tsv` | Sep 7 22:10 | predates proline/P1-class additions |
| `prss55_triaged_sites.tsv` | Sep 7 17:51 | small 8-row example dataset, not real data |
| `prss55_site_features.tsv` | Sep 3 19:11 | small 8-row example dataset |

## 1. Final status (Figure 2 terminal outcomes)

| Status | Count | % |
|---|---|---|
| ELIGIBLE | 2 | 0.1% |
| REVIEW | 950 | 40.7% |
| EXCLUDE | 1,384 | 59.2% |
| **Total** | **2,336** | **100%** |

## 2. Criteria breakdown (how many rows *trigger* each condition)

### Hard exclusion gate (any TRUE → EXCLUDE; 5 rules)

| Rule | Count | % of all rows |
|---|---|---|
| Overlaps Signal/Propeptide/Initiator-Met | 819 | 35.1% |
| Cytoplasm/Nucleus/Chromosome/Mitochondrion/Peroxisome | 536 | 22.9% |
| Overlaps Transmembrane/Intramembrane | 18 | 0.8% |
| Cytoplasmic topological-domain annotation | 11 | 0.5% |
| 8-mer ≠ UniProt sequence | 0 | 0.0% |

### Review gate — Cluster A: Annotation-based (UniProt)

| Condition | Count | % |
|---|---|---|
| Multiple isoforms | 906 | 38.8% |
| No topology annotation | 867 | 37.1% |
| Domain/motif/region overlap | 549 | 23.5% |
| Nearby glycosylation | 178 | 7.6% |
| Disulfide overlap | 166 | 7.1% |
| Secretory-pathway-only location | 88 | 3.8% |
| Nearby PTM (non-glycan) | 39 | 1.7% |

### Review gate — Cluster B: Structural heuristics (AlphaFold-derived)

| Condition | Count | % |
|---|---|---|
| Low pLDDT confidence | 1,722 | 73.7% |
| Helix/strand at P1/P1′ | 838 | 35.9% |
| Intramolecular salt bridge P1/P1′ | 259 | 11.1% |
| Contact density ≥ 20 | 63 | 2.7% |

### Review gate — Cluster C: Bond definition

| Condition | Count | % |
|---|---|---|
| P1–P1′ unresolved | 0 | 0.0% |

### Review gate — Cluster D: Sequence-only (`review-pro` / `review-p1` dedicated columns)

| Condition | Count | % |
|---|---|---|
| `review-p1` fires (P1 neither basic nor coil-favoring) | 1,649 | 70.6% |
| `review-pro` fires (Proline at P1′ or in window) | 1,016 | 43.5% |
| — of which, Proline specifically at P1′ (`p1prime_is_proline = true`) | 120 | 5.1% |
| — of which, Proline elsewhere in window only | 896 | 38.4% |

Underlying P1-identity split behind `review-p1`: `p1_is_basic` (Arg/Lys) =
217 rows (9.3%); `p1_is_coil_favoring` (Gly/Ser/Asn/Asp) = 470 rows (20.1%) —
together the 29.4% that do *not* trigger `review-p1`.

`p1prime_is_proline` full breakdown: `true` = 120 (5.1%), `false` = 2,216
(94.9%), blank/unresolved = 0 (0.0%) — every row had a resolved P1/P1′ bond.

Rows accumulate multiple flags simultaneously, so cluster percentages don't
sum to the REVIEW total. The two largest single contributors are low pLDDT
confidence (73.7%) and the P1 residue-class check (70.6%).

## 3. Each filter applied independently (in isolation)

Answers "how many rows would remain if *only* this one filter were
applied," not cumulatively. Condition text is the exact logic from
`scripts/triage_prss55_sites.py`.

### Hard Exclusion Gate

| # | Filter | Condition applied | Flagged | Remains | % remains |
|---|---|---|---|---|---|
| 1 | Sequence identity | `sequence_verified != "true"` | 0 | 2,336 | 100.0% |
| 2 | Transmembrane/Intramembrane overlap | `transmembrane_overlap not in ("", "-")` | 18 | 2,318 | 99.2% |
| 3 | Processing overlap | `processing_overlap not in ("", "-")` | 819 | 1,517 | 64.9% |
| 4 | Cytoplasmic topology | `"cytoplasmic" in topology_annotations.lower()` | 11 | 2,325 | 99.5% |
| 5 | Inaccessible compartment | `subcellular_location` ∈ {cytoplasm, nucleus, chromosome, mitochondrion, peroxisome} **and** no accessible marker (Secreted/Cell membrane/Cell surface/extracellular/acrosome) present anywhere in the annotation | 536 | 1,800 | 77.1% |

### Review Gate — Cluster A: Annotation-based (UniProt)

| # | Filter | Condition applied | Flagged | Remains | % remains |
|---|---|---|---|---|---|
| 6 | No topology annotation | `topology_annotations in ("","-")` **and** not purely-soluble-secreted-no-membrane **and** not cytoplasmic | 867 | 1,469 | 62.9% |
| 7 | Nearby glycosylation | `glycosylation_count_near_site not in ("","0")` | 178 | 2,158 | 92.4% |
| 8 | Nearby PTM (non-glycan) | `modified_residue_count_near_site not in ("","0")` | 39 | 2,297 | 98.3% |
| 9 | Disulfide overlap | `disulfide_overlap == "true"` | 166 | 2,170 | 92.9% |
| 18 | Multiple isoforms | `has_multiple_isoforms == "true"` | 906 | 1,430 | 61.2% |
| 19 | Domain/motif/region overlap | `domain_annotations not in ("","-")` | 549 | 1,787 | 76.5% |
| 20 | Secretory-pathway-only location | `subcellular_location` ∈ {Golgi, ER, Lysosome} **and** no accessible marker present | 88 | 2,248 | 96.2% |

### Review Gate — Cluster B: Structural heuristics (AlphaFold-derived)

| # | Filter | Condition applied | Flagged | Remains | % remains |
|---|---|---|---|---|---|
| 10 | Helix/strand at P1 or P1′ | `ss_p1 in ("H","E") or ss_p1prime in ("H","E")` | 838 | 1,498 | 64.1% |
| 14 | Salt bridge at P1 | `p1_salt_bridge_partner not in ("","-")` | 134 | 2,202 | 94.3% |
| 15 | Salt bridge at P1′ | `p1prime_salt_bridge_partner not in ("","-")` | 125 | 2,211 | 94.6% |
| 16 | Elevated contact density | `contact_density_8a` is numeric **and** `≥ 20` | 63 | 2,273 | 97.3% |
| 17 | Low pLDDT confidence | `plddt_confidence` starts with `"Low"` | 1,722 | 614 | **26.3%** |

### Review Gate — Cluster C: Bond definition

| # | Filter | Condition applied | Flagged | Remains | % remains |
|---|---|---|---|---|---|
| 21 | P1–P1′ unresolved | `p1_position` empty/falsy | 0 | 2,336 | 100.0% |
| 22 | Evidence gaps | `evidence_gaps not in ("","-")` | 8 | 2,328 | 99.7% |

### Review Gate — Cluster D: Sequence-only (`review-pro` / `review-p1`)

| # | Filter | Condition applied | Flagged | Remains | % remains |
|---|---|---|---|---|---|
| 11 | Proline at P1′ | `p1prime_is_proline == "true"` | 120 | 2,216 | 94.9% |
| 12 | Proline in window | `proline_in_window == "true"` | 1,016 | 1,320 | 56.5% |
| 13 | P1 residue class | `p1_is_basic == "false"` **and** `p1_is_coil_favoring == "false"` | 1,649 | 687 | **29.4%** |

## 4. Summary

- **Applied individually (each filter alone, isolated):** the tightest
  single filters are **P1 residue class** (29.4% remain) and **Low pLDDT
  confidence** (26.3% remain) — these two are the dominant bottlenecks on
  their own.
- **Applied all together, as the actual pipeline does** (hard exclusions
  win, then any review flag → REVIEW, else ELIGIBLE): **ELIGIBLE = 2
  (0.1%)**, REVIEW = 950 (40.7%), EXCLUDE = 1,384 (59.2%) — only 2 of 2,336
  candidate sites currently pass every single check cleanly.

Related context: the P1 residue-class check's high flag rate (70.6%) traces
back to the real upstream `prob_cleavage` data not actually being Arg/Lys-
centered — see the project memory / conversation history around
`data/epid_positives_1.csv` being a sliding-window scan, not a curated
Arg-centered candidate list, for why this number is so high.
