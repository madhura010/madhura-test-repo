# Public data source inventory (Step 1)

Compiled 2026-10-01 from web search and page fetches. Nothing has been downloaded.
Items marked **(verify)** come from search snippets or a partial fetch only.

## Summary table

| Source | Size | Lipids | Context | Readout / normalization | Access / license |
|---|---|---|---|---|---|
| **LNPDB** (Collins et al., *Nat Commun* 2026, doi:10.1038/s41467-026-68818-1) | 19,528 LNPs, 42 publications + BroadPharm | 12,845 unique ILs | 78.4% in vitro; in vivo lung 9.6%, liver 4.6%, other ~7.4%. mRNA 74.7%, siRNA 19.2%, pDNA 6.1%. Hand-mixed 93.8%, microfluidic 6.2% | Luminescence 75.2%, discretized luminescence 15.7%, protein 3.9%, uptake 2.5%. Log-transform where needed, then z-score within each publication and delivery context | Web tool lnpdb.molcube.com. GitHub evancollins1/LNPDB (MIT): `data/LNPDB_for_LiON/LNPDB.csv`, with LiON-format splits and AGILE-format held-out sets. Data license beyond MIT for the code not stated in the paper (verify) |
| **LNP Atlas** (Song, Baek, Seo, *Sci Data* 2026, doi:10.1038/s41597-025-06456-w) | 1,092 formulations, 63 publications | 39 distinct IL species (97.4% have SMILES) | In vitro and in vivo, 28 fields incl. size/PDI/zeta/EE, dose, route | Reported as in the source papers (single value, range, or ± error); not harmonized across studies | CC BY 4.0. Zenodo doi:10.5281/zenodo.17243732; lnp-atlas.kisti.re.kr |
| **AGILE** (Xu et al., *Nat Commun* 2024;15:6305) | ~1,200 experimental ILs (+ ~60k virtual pretraining set, ~12k screening set) | Ugi-3CR library | HeLa and RAW264.7, luciferase mRNA, 24 h | log2 luminescence ratio vs untreated cells | CC BY 4.0 paper. Dataset reported on Zenodo by search (Ma, Xu, Cui); the paper fetch showed only SI SMILES (verify) |
| **LiON** (Witten et al., *Nat Biotechnol* 2024) | >9,000 LNP activity measurements (8,727 per LNPDB paper) | D-MPNN; screened ~1.6M structures | Pulmonary focus; mouse and ferret lung validation (FO-32, FO-35) | Not fetched (paywalled) | Original data now folded into LNPDB (LiON-format files and checkpoints in the LNPDB repo) |
| **COMET / LANCE** (Chan et al., *Nat Nanotechnol* 2025;20:1491) | >3,000 LNPs, >6,000 labelled points | Only 7 ILs (incl. dual-IL formulations) | Mouse DC2.4 and B16-F10, luciferase mRNA | log-transformed, scaled 0–1 | Data in paper SI; code and weights at github.com/alvinchangw/COMET; CC BY 4.0 |

## What this means for the plan

1. **LNPDB is the backbone.** It already provides within-study z-scoring, but z-scores are only comparable inside a (study, context) group. Treat the study ID as a grouping variable for splits.
2. **Composition is skewed.** ~78% in vitro, ~94% hand-mixed, ~75% mRNA. In vivo extrahepatic data is thin (a few hundred to ~2k rows), so in vivo models should be treated as exploratory.
3. **LNP Atlas is small but richer in physicochemical fields** (size, PDI, zeta, EE, pKa where reported) and unnormalized. Useful as a metadata and sanity-check source, not for pooled regression.
4. **COMET/LANCE has very low lipid diversity (7 ILs).** It informs helper/PEG/ratio effects and not IL structure-activity.
5. **Leakage risk is high.** LiON, AGILE and COMET were all trained on data that is now in or overlaps LNPDB. LNPDB's own LiON benchmark splits by amine identity, not by study. Any comparison with those models must use studies they did not train on, or be flagged as contaminated.
6. **LNPDB's own caveats**: variable dose, cell type and instrumentation across studies; single protonation state per IL in the MD work.

## Open items

- Obtain the LNPDB CSV schema and the full per-study table (Table S1/S2 in the paper), which I couldn't read: the PMC page showed a CAPTCHA and I did not try to bypass it.
- Confirm AGILE Zenodo DOI and whether it overlaps LNPDB's "LNPDB_for_AGILE" held-out files.
- Read the LiON paper and the LNPDB repo's `scripts/` to confirm exactly which studies were in LiON's training set (needed to define a clean sealed holdout).
- Confirm data licenses per source study before any redistribution.
- Candidate sealed-holdout studies: choose after the per-study table is in hand. Prefer the most recent studies, and ones with microfluidic mixing or in vivo data.

## Update 2026-10-02: downloaded and checked

Downloaded to a `sources/` folder outside git.

**LNP Atlas** (`atlas/LNP_Atlas_DB_202509_v1.csv`, CC BY 4.0, text encoding cp1252)

- 1,092 rows, 28 columns, 62 papers. Structures parse for 934 rows (259 unique ILs).
- 23 of those 259 ILs are already in LNPDB. **236 are not**, so Atlas adds new IL structures.
- About 277 rows come from 10 papers that LNPDB also covers (matched by DOI suffix, rough).
- **No usable label.** `bioactivity_profile` is free text with mixed units and contexts ("2.58E+07 RLU", "~1.0 fold vs TT3 in liver", "included in study"). It cannot be z-scored within a study. Atlas is usable for structures and physicochemical fields (size, PDI, zeta, encapsulation), not as regression labels.

**COMET / LANCE** (`COMET/`, cloned from github.com/alvinchangw/COMET)

- The repo carries `license.pdf`: an internal research end-user agreement from MIT, NTU and BWH. It limits use to academic or internal non-profit research, **expressly excludes commercial research and development and any use with human subjects**, and forbids redistribution.
- Decision: nothing from this repo (code, data JSONs or weights) is ingested or used. The LANCE data is available separately in the paper's supplementary files (the paper is CC BY 4.0). That supplement has not been downloaded.
- The cloned repo stays outside git. Delete it if the license is a concern.

**LANCE data via the paper (checked 2026-10-02)**

- The paper (Chan et al., *Nat Nanotechnol* 2025) is CC BY 4.0 per Europe PMC. Its data statement says the data are "available within the paper and its Supplementary Information files", and raw data in other formats are available from the corresponding authors on reasonable request.
- The supplement is two PDFs (`41565_2025_1975_MOESM1_ESM.pdf`, `..._MOESM2_ESM.pdf`). MOESM2 downloaded and is a 3-page image-only PDF with no extractable text (probably the reporting summary). MOESM1 returned HTTP 503 twice from Springer and was not retrieved. No workaround was attempted.
- A PDF supplement is unlikely to hold the 3,028-LNP table in machine-readable form. The machine-readable data appears to live only in the license-restricted GitHub repo, which we do not use.
- Open route: ask the corresponding authors for the data file, stating our intended use. Not done. Needs the author's decision.
- What the paper reports: more than 6,000 labelled points, 3,028 LNPs in mouse DC2.4 and B16-F10 cells, bioluminescence log-transformed and scaled 0-1, 7 ionizable lipids, 3 sterols, 2 helper lipids, 2 PEG lipids, 13 molar ratios.

**Decision (2026-10-02, author): LANCE is skipped.** Its value is formulation effects, not IL structure, and the only machine-readable copy is under a license that does not fit. Revisit only if the authors supply the data under terms that do.
