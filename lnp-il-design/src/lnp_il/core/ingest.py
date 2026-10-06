"""Ingest: read a source dataset into a table.

LNPDB is the only source of labels. LNP Atlas is read for structures and formulation fields
only: its activity values are free text. A new source adds one reader here. A source with
labels maps to the common table and feeds curate.py unchanged; a source without a usable
label needs its own comparison, as atlas.py does for Atlas.
"""

import re
from pathlib import Path

import pandas as pd

from lnp_il.core.exceptions import DataSourceError

ATLAS_ENCODING = "euc-kr"  # the Atlas CSV is not UTF-8; EUC-KR decodes its mu, +/-, degree signs
LNPDB_CSV = Path("data") / "LNPDB_for_LiON" / "LNPDB.csv"

# LNPDB column -> common-table column.
_LNPDB_COLUMNS: dict[str, str] = {
    "LNP_ID": "row_id",
    "Experiment_ID": "study_id",
    "Formulation_ID": "formulation_id",
    "IL_name": "il_name",
    "IL_SMILES": "il_smiles_raw",
    "IL_head_SMILES": "il_head_smiles",
    "IL_linker_SMILES": "il_linker_smiles",
    "IL_tail1_SMILES": "il_tail1_smiles",
    "IL_tail2_SMILES": "il_tail2_smiles",
    "IL_molratio": "il_molratio",
    "IL_to_nucleicacid_massratio": "il_to_na_massratio",
    "HL_name": "hl_name",
    "HL_molratio": "hl_molratio",
    "CHL_molratio": "chl_molratio",
    "PEG_name": "peg_name",
    "PEG_molratio": "peg_molratio",
    "Mixing_method": "mixing_method",
    "Model": "model",
    "Model_type": "model_type",
    "Route_of_administration": "route",
    "Cargo_type": "cargo_type",
    "Experiment_method": "readout",
    "Experiment_value": "label_z",
    "Publication_link": "publication_link",
    "Publication_PMID": "pmid",
}


def lnpdb_csv_path(lnpdb_dir: Path) -> Path:
    """Return the path of the LNPDB table inside a clone of the LNPDB repository."""
    return lnpdb_dir / LNPDB_CSV


def read_lnpdb(csv_path: Path) -> pd.DataFrame:
    """Read the LNPDB table into the common columns, one row per formulation.

    Labels are LNPDB's own within-study z-scores and are not changed here.
    """
    if not csv_path.is_file():
        raise DataSourceError(f"LNPDB table not found: {csv_path}")
    raw = pd.read_csv(csv_path, low_memory=False)
    missing = sorted(set(_LNPDB_COLUMNS) - set(raw.columns))
    if missing:
        raise DataSourceError(f"LNPDB table is missing columns: {', '.join(missing)}")
    table = raw[list(_LNPDB_COLUMNS)].rename(columns=_LNPDB_COLUMNS)
    table.insert(0, "source", "LNPDB")
    return table


# LNP Atlas column -> table column. Text fields are kept as received, not parsed.
_ATLAS_COLUMNS: dict[str, str] = {
    "lnp_id": "row_id",
    "ionizable_lipid": "il_name",
    "ionizable_lipid_smiles": "il_smiles_raw",
    "helper_lipid": "hl_name",
    "sterol_lipid": "chl_name",
    "peg_lipid": "peg_name",
    "lipid_molar_ratio": "lipid_molar_ratio_text",
    "particle_size_nm_std": "particle_size_text",
    "pdi_std": "pdi_text",
    "zeta_potential_mv_std": "zeta_text",
    "encapsulation_efficiency_percent_std": "encapsulation_text",
    "loading_capacity_std": "loading_text",
    "target_type": "target_type",
    "paper_doi": "doi",
    "paper_year": "paper_year",
    "bioactivity_profile": "bioactivity_text",
}

_DOI_PREFIX = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.IGNORECASE)


def normalize_doi(doi: str) -> str:
    """Lower-case a DOI and strip any resolver prefix."""
    return _DOI_PREFIX.sub("", doi.strip()).lower()


def read_atlas(csv_path: Path) -> pd.DataFrame:
    """Read the LNP Atlas table into a clean set of columns, one row per formulation.

    `bioactivity_text` is the paper's reported activity as free text. It is not a label and
    is kept only for provenance.
    """
    if not csv_path.is_file():
        raise DataSourceError(f"LNP Atlas table not found: {csv_path}")
    try:
        raw = pd.read_csv(csv_path, encoding=ATLAS_ENCODING, dtype=str)
    except UnicodeDecodeError as error:
        raise DataSourceError(
            f"LNP Atlas table is not {ATLAS_ENCODING} text: {csv_path}"
        ) from error
    missing = sorted(set(_ATLAS_COLUMNS) - set(raw.columns))
    if missing:
        raise DataSourceError(f"LNP Atlas table is missing columns: {', '.join(missing)}")
    table = raw[list(_ATLAS_COLUMNS)].rename(columns=_ATLAS_COLUMNS)
    table["row_id"] = "ATLAS_" + table["row_id"].astype(str)
    table["doi"] = table["doi"].map(lambda d: normalize_doi(d) if isinstance(d, str) else None)
    table.insert(0, "source", "LNP Atlas")
    return table
