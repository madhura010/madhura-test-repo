"""Study registry: which LNPDB studies are sealed or overlap LiON's training data.

Both sets are decisions recorded in docs/design.md (open questions 1 and 3), not
properties computed from the data. Change them there first.
"""

# Whole studies fixed before any modeling. Never read for training, normalization,
# feature engineering, or tuning. See docs/design.md, open question 1.
SEALED_HOLDOUT_STUDIES: frozenset[str] = frozenset({"JL_2024", "XH_2025", "AP_2025", "RG_2023"})

# LNPDB studies that match the training references of LiON (Witten et al., Nat Biotechnol
# 2024). Matched by DOI and first-author initials, not confirmed against LiON's
# Supplementary Table 1. Unpublished LiON datasets cannot be identified.
# See docs/design.md, open question 3.
LION_TRAINING_STUDIES: frozenset[str] = frozenset(
    {
        "LM_2019",
        "BL_2024",
        "BL_2023",
        "JM_2016",
        "KZ_2016",
        "SL_2021",
        "AA_2008",
        "SL_2020",
        "LL_2012",
        "LR_2023",
        "JW_2024",
    }
)
