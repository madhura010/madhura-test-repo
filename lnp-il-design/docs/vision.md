# Vision — LNP-IL Design

## In one line

For wet-lab partners that need to decide which ionizable lipids (ILs) to synthesize and test for mRNA delivery, LNP-IL Design is a public-data modeling pipeline that ranks known and newly proposed ILs by predicted transfection efficiency, with an uncertainty and a synthesis route on each. Unlike published predictors that report performance on random or library-internal splits, it reports performance on studies the model never saw, and it says which candidates lie outside that evidence.

A docking-and-triage funnel, applied to ionizable lipids: it narrows what to make, and it does not claim what works.

## Problem

Public LNP data (about 19.5k formulations in LNPDB, plus smaller sets) is spread over 42 publications with different cells, doses, cargo, mixing methods and readouts. Labels are comparable only within one study. Published models (LiON, AGILE, COMET) were trained on overlapping subsets of it, so benchmarking one against another on public data tests them on their own training data. In vivo luminescence or protein data for IL structure-activity is about 1,000 rows. A partner choosing what to synthesize gets a score with no evidence of how far it can be trusted outside the chemistry it was trained on, and no route from a known IL to a nearby analog they can make.

## Where it fits

- **Consumes:** LNPDB (backbone, the only source of labels) and LNP Atlas (structures and physicochemical fields). AGILE and LiON data are already inside LNPDB. Purchasable-lipid listings (BroadPharm, in LNPDB) feed the availability check.
- **Hands off to:** the partner's synthesis and screening. This system stops at a ranked shortlist, a synthesis route per candidate, and a protocol for testing it. It does not synthesize, formulate or assay.
- **Receives back:** the partner's measurements, which become the first prospective data.
- **Neighbours that own what it stops short of:** LNPDB owns data curation at source; the partner's wet lab owns experimental truth; published models (LiON, AGILE, COMET) own their own architectures, and this system benchmarks them but does not extend them.

## Who it serves

**Partner wet-lab team** (chemists and formulation scientists) — They receive a shortlist as a table plus structure sheets: predicted efficiency within a stated context, uncertainty, similarity to the nearest training lipids, predicted pKa, building blocks and route, and a flag for candidates outside the evidence. They synthesize and screen it under their own protocol and return the measurements.

**Aganitha computational scientist** — Builds and runs the pipeline, owns the sealed holdout, and writes the benchmark and the shortlist. Uses it to compare models on clean splits, to rerun a cycle when partner data arrives, and to explain a given candidate's score and distance from the training set.

**One path through it** — Dr. Rao's lab can run about 48 syntheses per round. On Monday the Aganitha scientist sends a shortlist of 48: 34 near well-measured analogs, 10 further out with high uncertainty, and 4 benchmark controls. Each row names its building blocks, and the five in-stock ones are marked. Rao's chemist strikes two that look unstable, and two replacements come up the ranked list. The lab formulates all 48 with MC3 and SM-102 on every plate and returns luminescence values six weeks later. The scientist normalizes them to the plate controls, scores the original predictions against them, and reports the rank correlation and the hit rate against a random sample of the same library. The model is refit with the new data, and the next shortlist states how the first one performed.

## Must satisfy

- Public data only. Every row carries its source, DOI and license, and no source with unclear terms is redistributed.
- No label pooling across studies without within-study normalization. Study ID is a grouping variable in every split.
- A holdout of whole studies is fixed before any modeling and is used once for the final report.
- Every candidate carries an uncertainty and an applicability-domain flag. Output outside the domain is labeled exploratory.
- Every candidate has a stated synthesis route, and building-block availability is checked, before it reaches a partner.
- No efficacy, safety or in vivo claim without experimental support. Retrospective results are labeled as such.

## Success looks like

Success is staged and each stage is a gate.

1. **Retrospective gate.** On leave-one-study-out and the sealed holdout, the model beats a nearest-neighbor Tanimoto baseline and an IL-free ablation on Spearman and top-k hit rate, with confidence intervals and calibrated uncertainty.
2. **Benchmark gate.** The pipeline reproduces one published model's reported result, then compares it on studies it did not train on, and documents the gap.
3. **Prospective gate.** A partner tests the shortlist. Success is a Spearman of at least 0.4 between predicted and measured rank, a hit rate (at or above the best in-plate control) at least twice that of random library members, and at least one novel IL within 2x of the best control.

**Exit and stop conditions.**

- **Done** when all three gates pass in one cycle, and the shortlist, benchmark and handoff protocol are delivered.
- **Stop design work and switch to data generation** if gate 1 fails after the baselines and one pretrained model. The deliverable then becomes a specification for a diverse screening library, since the data cannot support design.
- **Stop** if two partner rounds both miss the prospective gate, after checking for plate or batch artifacts.

## Not for

- Predicting in vivo efficacy, biodistribution, toxicity or clinical safety.
- Replacing a wet-lab screen. The output reduces what is made and does not remove the need to measure it.
- Competing with LiON, AGILE or COMET on a leaderboard.
- Designing lipids outside the ionizable-lipid chemotype, or optimizing helper, PEG or ratio formulations on their own.
- Anyone who needs a result without the uncertainty and the domain flag.
