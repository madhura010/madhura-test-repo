# Mental model — LNP-IL Design

Concepts are defined by what each is and is not. Items marked **OPEN** are unresolved.

## Concepts

**Formulation** — one measured LNP: an IL, helper lipid, cholesterol, PEG lipid, their molar ratios, a mixing method and a cargo. It is not an IL alone. Two formulations that share an IL but differ in ratio are different rows.

**Ionizable lipid (IL)** — the structure being designed: a head group with an ionizable amine, a linker, and tails. Identity is the canonical structure, not a name or catalog ID. It is not the formulation.

**Study** — one publication's experiment, with its own protocol. The unit within which labels are comparable. Every row belongs to exactly one study.

**Context** — what was measured on: cell line or animal, route, cargo, readout. Two studies can share a context and still not be comparable.

**Label** — the measured transfection efficiency after within-study normalization (z-score of log luminescence or equivalent). It has meaning only relative to other rows of the same study and context. It is not an absolute efficiency and not comparable across studies.

**Prediction target** — two outputs per candidate and context: a within-study z-score estimate (the rank is derived from it) and a hit call (top quantile of its study). The z-score is not an absolute efficiency, and the hit call is not independent of it: both are reported together and both are evaluated on the holdout.

**Candidate** — an IL proposed by the generator that is not in the training data. It carries a predicted value, an uncertainty, a distance to the training set, a synthesis route, and a domain flag.

**Applicability domain** — the region of chemical and formulation space where the training data supports a prediction. A candidate outside it is exploratory, whatever its score.

**Shortlist** — the delivered artifact: ranked candidates plus controls, with the evidence on each row. It is a recommendation to test, not a claim of activity.

**Sealed holdout** — whole studies fixed before modeling and used once. Not a random subset, and not tuned against.

**Cycle** — one pass of shortlist → partner measurement → ingest → refit → next shortlist.

## Invariants

- A label is never compared across studies without its study identity.
- No holdout study contributes a row to training, feature engineering, normalization or hyperparameter selection.
- Every candidate has a synthesis route and a domain flag before it leaves the system.
- Partner measurements enter as a new study with its own plate controls, never merged into an old one.

## Boundaries

- The system does not synthesize, formulate or assay.
- Source datasets are read-only inputs. Curation changes are recorded in this system, not pushed back to LNPDB.
