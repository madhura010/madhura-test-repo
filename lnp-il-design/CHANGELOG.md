# Changelog

Past-tense history, newest first. Present-tense state is in `docs/status.md`.

## 2026-10-02 (later)

**What:** Added the Atlas step: `lnp-il data atlas` reads the LNP Atlas CSV and compares its structures with LNPDB's development rows. Moved structure standardization into its own module so both sources share it.

**Why:** Atlas adds 240 ILs that are not in LNPDB's labeled development rows, which widens the structure pool for the later generator. Its activity values are free text, so it contributes structures only.

**Rejected:**
- Reading the file as cp1252: it garbled every "±". The file is EUC-KR.
- Using Atlas activity text as a label: mixed units and contexts cannot be z-scored within a study.
- Comparing Atlas with all LNPDB rows: that would reveal which ILs are in the sealed holdout, and counted catalog-only rows that have no label. It compares with development rows only and drops Atlas rows that overlap a sealed study.
- Running the full `curate()` from the Atlas step just to get IL key sets: it repeats hit calls and label normalization. A small `il_keys_by_split` shares curation's row rule instead.
- Parsing the Atlas size, PDI and zeta fields now: they hold single values, ranges and "value ± error" in one column, and nothing uses them yet.

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
