# Handoff

Updated: 2026-11-20

## Objective
Landscape of patents covering targeted lipid nanoparticles (LNPs), including Bristol Myers Squibb (BMS) and allied companies, classified by target cell, ligand, cargo, disease, ionizable lipid and formulation. Success: a verified, reasonably complete table for a patent review. Not a freedom-to-operate opinion.

## Current state
- **Deliverable:** interactive table, 16 families (A to P), published privately at https://claude.ai/artifact/J3cyoXS7HCEx26LkUxXNUz (version 3). Saved copies: `outputs/targeted-lnp-patents-v1.html`, `-v2.html`, `-v3.html` (v3 is current).
- **Families A to J** (Ramot, Capstan, Penn x3, NanoVation x2, Tessera x2, ReCode): lead patent full text read; claim 1 and examples verified. Family members from the SureChEMBL snapshot (2026-08-18) and Google Patents.
- **Families K to P** (BMS WO2024059714 retinoid HSP47 siRNA LNP; Nitto Denko retinoid carriers and lipids; Juno co-LNP; Orna; BMS lipid chemistry): claims and formulation text read; not every example. Orna covers 13 of about 175 documents; its LNP patents claim lipids, and ligand targeting is only an optional embodiment.
- **Candidate list:** `outputs/google-patents-candidates-2026-11-19.json` holds 2,132 Google Patents results (title, assignee, dates, snippet) from a first-batch search by assignee. Titles and snippets only; none read.
- **Not done (coverage):** flagged patents from the first batch are unread: Generation Bio (US 12,453,706 B2, WO2024119074A1, WO2026174149A1, WO2025090663A1), Tessera (WO2025189161A1, WO2026122998A1), Capstan (US20260102510A1, WO2025129201A1), Penn (WO2024077232A2, WO2022081702A1, US20240131181A1, US20240216523A1), CRISPR Therapeutics WO2023248125A1, Beam WO2023230601A1, Acuitas EP4713016A2, Genzyme EP4658313A1, Orbital WO2025259931A1. Companies not searched at all: Alnylam, MIT, Harvard, UBC, Ionis, Sangamo, Roche/Genentech, Lilly, Merck, Gilead/Kite, Amgen, Sanofi, GSK, AstraZeneca, Janssen, Stanford, Emory and other universities, MagicRNA, Immorna, Starna, Everest. UT Southwestern SORT family search is incomplete. Moderna, Arcturus and Intellia appeared only in broad web searches.
- **Orbital:** the OTX-201 targeted-LNP filing was not found; only unrelated Orbital filings (RNA ligation, VZV, viral particles) and WO2025259931A1 / WO2026006203.
- **Corporate:** AbbVie completed its Capstan acquisition on 2025-08-19, so Capstan's patents are now AbbVie's.

## Decisions and constraints
- **Google Patents is blocking me:** requests return 503 or a CAPTCHA page, and the fetch tool gets 503 too. Justia returns 403. The system denied a background script that ran many requests against Google's undocumented query endpoint. I did not retry or work around it. Do not run high-volume automated queries against it without the user's explicit go-ahead.
- **Source limits:** the SureChEMBL snapshot stores titles only (no claim text or sequences) and lacks some JP, KR, AU and CA entries. Legal status in the table is Google's own label, not a legal determination.
- **Host setup:** I installed `duckdb` in `~/ie-venv` on `hpc3` for snapshot queries. The `aganitha-ie-tools` 0.148.0 install failed with a 401, so `aganitha-ie-epo-ops` is not available. It needs `! atk login`, plus a free EPO OPS key.
- **Classification:** NanoVation's high-sterol patents (US 12,343,405 and US 11,951,177) and ReCode's SORT patent are organ-selective without a ligand. They are labelled "No ligand".

## Evidence
- Full texts were downloaded before the block and searched locally; those scratchpad downloads may be cleared. Scripts: `fam.py` and `bms.py` (snapshot queries) in the session scratchpad.
- Details marked `[summary]` in the table came from model summaries, not page text. Lipid structures are drawings in every patent, so lipids appear by name only.
- Several example tables in the NanoVation, BMS and Tessera WO publications are images, so sizes, N/P ratios and mol% are missing for those rows.

## Next action
Get past the block through a legitimate route, then read the unread flagged patents above and add the confirmed targeted ones to the table. Options, in order: (1) retry Google Patents later, one page at a time; (2) use EPO Open Patent Services after `! atk login` and an OPS key; (3) the user exports a list or PDFs from Google Patents, Lens.org or Espacenet in a browser and hands them over. Then run company-by-company searches for the missing list, in batches.

## Blockers and risks
- Google Patents 503 or CAPTCHA, and Justia 403, until access is restored.
- The coverage claim "exhaustive" is false: do not describe this as a complete landscape. Peptide, aptamer, GalNAc and folate ligands were not searched systematically.
- "Ceased" on PCT applications reflects the lapsed 30-month window, not the national-phase family.
- The directory is not under git, so these files are unversioned.
