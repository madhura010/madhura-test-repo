from pathlib import Path

import pandas as pd

from lnp_il.core.ingest import lnpdb_csv_path

LNPDB_COLUMNS = [
    "LNP_ID",
    "Experiment_ID",
    "Formulation_ID",
    "IL_name",
    "IL_SMILES",
    "IL_head_SMILES",
    "IL_linker_SMILES",
    "IL_tail1_SMILES",
    "IL_tail2_SMILES",
    "IL_molratio",
    "IL_to_nucleicacid_massratio",
    "HL_name",
    "HL_molratio",
    "CHL_molratio",
    "PEG_name",
    "PEG_molratio",
    "Mixing_method",
    "Model",
    "Model_type",
    "Route_of_administration",
    "Cargo_type",
    "Experiment_method",
    "Experiment_value",
    "Publication_link",
    "Publication_PMID",
]


def make_rows(
    study: str,
    n: int,
    smiles: str = "CCCCN(CC)CC",
    cargo: str = "FLuc",
    fragments: bool = True,
    model: str | None = "in_vitro",
    readout: str = "luminescence_normalized",
) -> list[dict[str, object]]:
    """n rows of one study with labels that increase evenly from -1 to 1."""
    rows: list[dict[str, object]] = []
    for i in range(n):
        rows.append(
            {
                "LNP_ID": f"{study}_{i}",
                "Experiment_ID": study,
                "Formulation_ID": f"{study}_F{i}",
                "IL_name": f"il{i}",
                "IL_SMILES": smiles + ("C" * (i % 3)) if smiles == "CCCCN(CC)CC" else smiles,
                "IL_head_SMILES": "CCN" if fragments else None,
                "IL_tail1_SMILES": "CCCC" if fragments else None,
                "Mixing_method": "handmixed",
                "Model": model,
                "Model_type": "HeLa" if model else None,
                "Route_of_administration": "in_vitro" if model else None,
                "Cargo_type": cargo,
                "Experiment_method": readout,
                "Experiment_value": -1 + 2 * i / max(n - 1, 1),
                "Publication_link": f"https://example.org/{study}",
                "Publication_PMID": 1.0,
            }
        )
    return rows


def write_lnpdb(root: Path, rows: list[dict[str, object]]) -> Path:
    """Write rows as an LNPDB-format CSV inside a fake LNPDB clone at root."""
    frame = pd.DataFrame(rows).reindex(columns=LNPDB_COLUMNS)
    csv_path = lnpdb_csv_path(root)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(csv_path, index=False)
    return csv_path
