"""Ingest: read a source dataset into the common table.

Only LNPDB is supported today. A new source adds one reader that returns the same
columns as read_lnpdb, leaving curation and everything after it unchanged.
"""

from pathlib import Path

import pandas as pd

from lnp_il.core.exceptions import DataSourceError

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
