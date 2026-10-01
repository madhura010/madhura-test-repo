# Changelog

Past-tense history, newest first. Present-tense state is in `docs/status.md`.

## 2026-10-02

**What:** Started the project: vision, mental model and design draft; data inventory of the public LNP sources; Ingest and Curate for LNPDB (`lnp-il data curate`) with 20 tests; project scaffold (Makefile, AGENTS.md, project skill, dev-pack lock).

**Why:** To predict LNP transfection efficiency and propose ionizable lipids from public data only, for a wet-lab partner. Everything downstream (baselines, model, generator, shortlist) needs a curated dataset whose holdout is sealed and whose labels mean one thing.

**Rejected:**
- Random or scaffold splits as the headline evaluation: libraries are built from related analogs, so they overstate performance. Whole-study splits (leave-one-study-out plus a sealed holdout) instead.
- Cleaning everything together and splitting afterwards: development counts and the study table would carry sealed-study information. The holdout is split off first.
- Keeping every LNPDB readout as a label: diameter, zeta potential and hemolysis rows are not delivery measures.
- A plain `>=` top-16% cutoff for hit calls: floor-heavy and discretized groups were called up to 100% hits. Tie-aware calls instead, with no call where ties make 16% impossible.
- Using the COMET/LANCE data: its license excludes commercial R&D and its only machine-readable copy is inside that repo.
- A separate repository: the project is a subfolder of an existing repo, at the author's direction.
