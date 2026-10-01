# Design — LNP-IL Design

**Status: draft.** The prediction target is the author's decision. The holdout, the hit threshold and the LiON-overlap handling were settled by Claude on the author's instruction to proceed with the best option, and are open to veto. The remaining decisions are proposed.

## Purpose

This proposes the structure of a pipeline that turns public LNP data into a ranked, evidence-labeled shortlist of ionizable lipids for a partner wet lab. It is for the Aganitha scientist who will build it and the partner who will consume its output, and it supports the decision to approve this shape before code is written. It is judged against `docs/vision.md`: public data only, whole-study holdout, uncertainty and domain flag on every candidate, a synthesis route on every candidate, and three sequential gates.

## Shape

Five modules, in a line, with the data store beneath them.

- **Ingest** — turns each source dataset into rows in one common table, with provenance and the original label kept.
  - exposes: add a source; produce the unified table. A merge report comes with the second source.
  - hands off: to Curate, a table with one row per formulation, plus source, DOI and license columns.
- **Curate** — splits off the sealed holdout first, then standardizes structures and normalizes labels within study and context for each half independently. Deduplication across sources comes with the second source. Development outputs carry no information about sealed studies.
  - exposes: build a dataset version; list studies and their split assignment.
  - hands off: to Model, a versioned dataset with study ID, context, z-score and task flags per row; to Design, the annotated head, linker and tail fragments of the known ILs.
- **Model** — predicts the z-score and the hit call, with an uncertainty, and evaluates both under study-level splits.
  - exposes: train, evaluate (with the benchmark protocol), predict.
  - hands off: to Design and Select, predictions as a structured record (z-score, hit probability, uncertainty, distance to training set).
- **Design** — enumerates candidate ILs from the known head, linker and tail fragments through reaction templates, and removes those that violate chemical, synthesis or novelty rules.
  - exposes: enumerate candidates from fragments and templates; apply the filter set.
  - hands off: to Select, candidates with origin, synthesis route and filter outcomes.
- **Select** — scores candidates with Model, balances exploitation and exploration, adds controls, and writes the shortlist and the evaluation report for a cycle.
  - exposes: build shortlist; ingest a returned measurement set as a new study and score the previous shortlist against it.
  - hands off: to the partner, the shortlist table and structure sheets; back to Ingest, partner results as a new study.

## State

The system remembers between runs, and the scientist owns all of it:

- Dataset versions (the unified table and its merge report).
- Split definitions, including the sealed holdout. A record of when the holdout was last read is planned and not yet built.
- Trained model artifacts and their evaluation results.
- Cycle records: each shortlist, the evidence on it, and the measurements that came back.

Losing the split definitions or the cycle records makes earlier results unreproducible and the holdout's integrity unprovable. Losing model artifacts is recoverable from data and configuration. Nothing is held for the partner. They receive files and return files.

## Scenarios

**First benchmark run.** The scientist adds LNPDB for labels and Atlas for structures. Ingest reports how many rows each contributed and how many were duplicates. Curate fixes the holdout studies and records the split. Model trains the baselines and the pretrained model and reports study-level results against a nearest-neighbor baseline and an IL-free ablation. Nothing is generated until the retrospective gate passes.

**A cycle with a partner.** After gate 1 passes, Design generates candidates from the best-measured ILs. Select ranks 48 of them plus controls and writes the shortlist. The partner synthesizes and screens them and sends back a file of values and plate controls. Select ingests it as a new study and reports predicted-versus-measured rank, hit rate against random library members, and calibration. Model is refit.

**Adding a data source.** A developer writes one adapter that maps the new source's fields to the common table and declares its label type and license. Curate and everything after it are unchanged. The merge report shows the new source's contribution and its duplicates. A model or generator is added the same way: implement the module's contract, register it by name, run the benchmark protocol unchanged.

## Decisions

### What the model predicts

- **Options:** rank within context only (simplest); z-score regression; hit classification; all three.
- **Chose:** one model with two outputs, a z-score estimate (rank derived from it) and a hit call. This is the author's choice and matches the vision's two uses: ordering what to make and flagging likely hits.
- **Consequences:** two sets of metrics to report, and the hit threshold becomes a fixed, documented parameter. Disagreement between the two outputs is itself a flag. Costs a second evaluation but no second dataset.

### How sources are combined

- **Options:** pool all labels into one column; one table with source and original label plus a recomputed within-study z-score (proposed); keep sources as separate datasets.
- **Chose:** one table with both labels and provenance. Sources in scope: LNPDB for labels, and LNP Atlas for structures and physicochemical fields only (its activity values are free text). LANCE/COMET is out of scope (author's decision): its machine-readable data is under a license that excludes commercial use. Pooling raw labels across labs is the error the vision exists to avoid. Separate datasets would lose the extra rows that LANCE and Atlas add.
- **Consequences:** every source needs a normalization rule or is marked rank-only. Sources that cannot be normalized (Atlas reports raw values in mixed forms) contribute metadata and physicochemical fields, not regression labels.

### Which rows count as labels

Found while building the first curation step; not yet reviewed by the author.

- **Options:** use every row LNPDB provides as a label (simplest); drop readouts that are not delivery measures and re-standardize groups that are not z-scored; train a separate model per readout type.
- **Chose:** drop particle diameter, zeta potential and hemolysis percent (282 rows, none of them a delivery label), and z-score within the group any context whose labels are not already close to mean 0, SD 1 (two groups, 60 rows, reported relative to Spikevax). The value as received is kept in a separate column.
- **Consequences:** the label column means one thing across the table. Hit calls are tie-aware: for each (study, context) group the cutoff is tried both inclusive and exclusive, and a group whose realized hit rate stays further than half the target from 16% gets no hit call. That affects the four-level discretized readouts in KZ_2016 (HeLa and intravenous FVII) and ZC_2023, 1,672 development rows (9.6%), which remain usable for ranking but not for the hit output. Without this rule, floor-heavy groups were called 100% hits.

### Splits and the holdout

- **Options:** random; scaffold or cluster; leave-one-study-out plus a sealed holdout of whole studies (proposed).
- **Chose:** leave-one-study-out for development and a sealed holdout for the final report. Random and scaffold splits are reported only as secondary results, because analog series make them optimistic.
- **Consequences:** a small effective sample for any given context, and noisier estimates. The sealed holdout is JL_2024, XH_2025, AP_2025 and RG_2023 (open question 1).

### Model family

- **Options:** gradient-boosted trees and a kernel model on fingerprints and descriptors (simplest); a message-passing network ensemble; a pretrained model fine-tuned on the data (LiON- or AGILE-style).
- **Chose:** run all three as a ladder and select by a combined score, defined before any model is run. Each model is ranked separately on three metrics across the development studies: Spearman, top-16% hit rate and calibration error. The author's choice is the mean of the three ranks, with no weights to tune. If two models tie within one study-level bootstrap standard error on all three metrics, the simpler one wins. The score uses development studies only and never the sealed holdout. A pretrained model counts only on studies outside its own training data.
- **Consequences:** the comparison cannot be tuned after the fact, and a complex model has to win on all three outputs the design promises, not only on ranking. Mean rank discards the size of a gap, so a model that is much better on one metric and slightly worse on the others can lose. Ties within one SE are likely given the small number of effectively independent studies, which favors the simpler model.

### One model or one per context

- **Options:** in vitro primary with in vivo reported only as exploratory transfer (simplest, and the option Claude recommended); one pooled model with the context as an input feature, evaluated on all contexts including the in vivo holdout (chosen by the author); drop in vivo from this phase.
- **Chose:** a pooled model with context features. The author's reasoning is to use all the data and to evaluate in vivo on the sealed in vivo studies.
- **Consequences:** only 2.6% of ILs appear in more than one study, so the context features have little shared signal to learn from, and in vivo contexts have 1 to 4 studies each. To keep the pooling honest, three controls are required before any pooled result is reported: (1) the pooled model must beat per-context models and a context-mean baseline on the same leave-one-study-out splits; (2) a context-shuffle control, where context labels are permuted, must score clearly worse than the real run; (3) in vivo results are reported per context with the number of training studies beside them. Whatever they show, in vivo outputs stay labeled exploratory, because the vision bars an in vivo claim without experimental support. If control 1 fails, the design falls back to per-context models.

### How candidates are generated

- **Options:** one-fragment swaps from a measured lipid, restricted to its chemistry class (simplest, and the option Claude recommended); full head-by-tail enumeration, filtered by reaction rules (chosen by the author); swaps plus automatic decomposition of unannotated lipids; matched-pair transformations; string mutation; a learned generative model.
- **Chose:** enumerate head and tail fragments from the annotated lipids and keep a combination only if a written reaction template says it can be made. 434 heads, 35 linkers and 267 tails are annotated, for 75% of unique ILs, and only 19% of ILs have a second tail and none has more, so candidates are limited to one or two tails. Other generators stay secondary and tagged by origin.
- **Consequences:** the space is far larger than the neighborhood of any measured lipid, so many candidates will sit outside the evidence and carry the flag, and the exploit end of the shortlist will be thinner than with swaps. The reaction templates become the main correctness risk: a wrong template yields lipids that cannot be made, and the data does not record which pairs are makeable, so a chemist has to write and check them. Each template gives the synthesis route for its candidates. Three-tail and four-tail lipids cannot be generated from the annotations.

### How partner results enter the system

- **Options:** the partner sends pre-normalized values (simplest for them); a free-form file with a custom parser per cycle; a raw-value CSV template that we supply (proposed and confirmed by the author).
- **Chose:** the raw-value template. Normalization stays with us, so it can be inspected and reproduced, and it matches the within-study z-scoring the model was trained on.
- **Consequences:** the partner must record raw readouts and include control wells on every plate, which is some extra work for them. A result file without control rows is rejected rather than guessed at. Each cycle's results enter as a new study, per the mental model's invariant.

### What counts as inside the evidence

- **Options:** no flag, report only the score; a fixed rule of thumb such as a Tanimoto cut-off borrowed from other chemistry; thresholds calibrated on leave-one-study-out errors (chosen by the author).
- **Chose:** a candidate is "outside the evidence" when its distance to the training set or its model uncertainty exceeds a cut-off. Each cut-off is set where prediction error on held-out studies rises past a tolerance stated before the analysis, and is re-derived every cycle. Until the baselines exist the cut-offs are unset, and the first shortlist cannot be produced.
- **Consequences:** the flag is a measured property of the model and not a convention. It depends on the leave-one-study-out harness, so that harness is on the critical path. The tolerance is itself a decision, to be written down before looking at the curves.

## Not doing

- **Synthesis, formulation and assay.** The partner's lab owns experimental truth.
- **Free-form de novo generation as the main route.** Not makeable at the rate fragment recombination is.
- **Predicting toxicity, biodistribution or in vivo efficacy.** The data does not support it. Stated in the vision's Not for.
- **Optimizing helper lipid, PEG or ratio on their own.** The IL is the object. Ratio effects enter as features only.
- **A web service or database.** Files and a command-line workflow cover one scientist and one partner. Revisit if a second team needs live access.
- **Writing curation fixes back to LNPDB.** Sources are read-only inputs.

## Open questions

1. **Holdout studies — resolved, open to veto.** Sealed: JL_2024, XH_2025, AP_2025 and RG_2023. None is among the datasets LiON trained on (see the LiON overlap table below), none is AGILE's data, and together they cover two in vitro cell lines (DC2.4, HepG2) and two intramuscular in vivo studies with different cargo.
2. **Hit threshold — resolved, open to veto.** Primary definition: top 16% within a study, the tier AGILE reports. Sensitivity results at top 10% and top 25% are reported alongside, so the choice cannot quietly flatter the model.
3. **LiON overlap — resolved from the paper (Witten et al., *Nat Biotechnol* 2024).** LiON was trained on 20 datasets, 4 in vivo (575 points) and 16 in vitro (8,727 points), including unpublished ones, and the paper does not hold out any whole study. Its reported evaluation is a random 70/15/15 split and an amine-headgroup split, later fivefold cross-validation. So a LiON comparison on any study in the table below is contaminated, and unpublished datasets cannot be identified at all. Label values for some of these datasets were digitized from heat-map colors in the source papers, so they carry extraction error that LNPDB inherits.

   | LiON training reference | LNPDB study | Status for benchmarking |
   |---|---|---|
   | Miao 2019 (ref 15) | LM_2019 | contaminated |
   | Li 2024 *Nat Mater* (ref 28) | BL_2024 | contaminated |
   | Li 2023 *Nat Biotechnol* (ref 46) | BL_2023 | contaminated |
   | Miller 2017 (ref 43) | JM_2016 | contaminated |
   | Zhou 2016 (ref 44) | KZ_2016 | contaminated |
   | Liu 2021 (ref 45) | SL_2021 | contaminated |
   | Akinc 2008 (ref 47) | AA_2008 | contaminated |
   | Lee 2021 (ref 48) | SL_2020 | contaminated |
   | Li 2012 (ref 49) | LL_2012 | contaminated |
   | Rhym 2023 (ref 35, 384-lipid barcoded screen) | LR_2023 | contaminated |
   | The LiON paper's own screens | JW_2024 | contaminated |
   | Li 2023 *Nat Biomed Eng* (ref 41), Jiang 2024 (ref 42) | not found in LNPDB | n/a |

   Matching is by DOI and first-author initials against the links in LNPDB's CSV. I have not confirmed it against LiON's Supplementary Table 1, which is not in the PDF I was given. The LNPDB repository's own LiON held-out sets (BL_2023, LM_2019, SL_2020, ZC_2023) belong to a model LNPDB retrained, not to the original LiON, so they are clean only for that retrained checkpoint.

4. **How partner results arrive — resolved.** Raw values in a CSV template that we supply (one row per well: candidate ID, formulation ID, plate ID, replicate, cell line, dose, raw readout, plus in-plate control rows). We normalize, so the treatment matches the training data. The template itself still has to be written and agreed with the partner.
5. **Licenses — partly checked.** LNPDB code is MIT; the Atlas data is CC BY 4.0; the COMET repository is under an agreement that excludes commercial research and development and forbids redistribution, so none of its files are used. LNPDB's data terms beyond the MIT repository license, and the terms of each underlying paper, are unchecked. Whether this work counts as commercial use is Aganitha's call to make with counsel, and it decides whether any non-commercial source can be used at all.
6. **Evidence thresholds — method resolved, values unset.** Calibrated on leave-one-study-out errors (see the decision above). The error tolerance has to be fixed before the curves are inspected.
7. **Effective sample size per context — measured, and it constrains the design.** After removing BroadPharm, unlabeled rows and the sealed holdout, training has 17,726 rows and 10,788 unique ILs (holdout: 1,474 rows).
   - Only 279 ILs (2.6%) appear in more than one study, so labels from different studies are linked by almost no shared lipids. Leave-one-study-out therefore measures generalization to new chemistry, and a model across contexts has little to anchor on.
   - Only in vitro contexts have enough studies for leave-one-study-out: HeLa 14 studies (7,455 rows), IGROV1 6, HepG2 5, A549 3. Every in vivo context has 1 to 4 studies.
   - With AP_2025 and RG_2023 sealed, mouse intramuscular training data is about 135 rows, and the hEPO context has one IL. In vivo intramuscular prediction has almost nothing to learn from, so it can only be tested as transfer from other contexts.
   - 26 training studies have at least 100 distinct ILs, 17 of them outside LiON's training set (JC_2023, KS_2024, KW_2014, LX_2024, LX_2024_2, LX_2024_3, NC_2024, SW_2024, SX_2025, XH_2024_2, YR_2024, YX_2023, YX_2024, YY_2023, ZC_2023, ZH_2023, ZL_2022). Six training studies have 1 to 3 ILs and are ratio studies.

8. **Reaction templates — scoped, input pending.** Templates are written only for the routes the partner's chemist can run, so every candidate is makeable by whoever will make it. This needs the partner's answer (which two or three routes) before the generator can be built, and the first shortlist waits on it. Who writes each template and who checks it is still to be agreed.

9. **Uptake readouts.** 479 development rows (LX_2024, intravenous DNA-barcode uptake) are kept as a delivery measure. Uptake is not expression, so the author should confirm they belong in a transfection label.

## Next

Review the Decisions section and the three resolved questions, and veto any you disagree with. Then the next step in the cycle is project setup, then code review and preflight on the first change.
