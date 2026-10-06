"""Compare LNP Atlas structures with LNPDB, without letting sealed-holdout structures through.

Atlas has no usable label, so it adds structures and formulation fields only. Each Atlas
IL is compared with the development ILs of LNPDB. An Atlas row whose IL also appears in a
sealed study is dropped, so holdout structures cannot reach the generator through Atlas.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from lnp_il.core.curate import il_keys_by_split
from lnp_il.core.ingest import lnpdb_csv_path, read_atlas, read_lnpdb
from lnp_il.core.structures import add_standard_structures

ATLAS_FILE = "atlas_formulations.csv"
ATLAS_REPORT_FILE = "atlas_report.json"


@dataclass(frozen=True)
class AtlasReport:
    """Row and IL counts for the Atlas comparison."""

    rows: int
    rows_without_structure: int
    rows_with_unparseable_structure: int
    rows_excluded_sealed_overlap: int
    rows_kept: int
    unique_ils: int
    ils_in_lnpdb_dev: int
    ils_not_in_lnpdb_dev: int


@dataclass(frozen=True)
class AtlasResult:
    """Kept Atlas rows (each flagged `in_lnpdb_dev`) and the counts.

    `in_lnpdb_dev` means the IL appears in LNPDB's labeled development rows. LNPDB's
    catalog-only rows (no experiment, no label) do not count.
    """

    formulations: pd.DataFrame
    report: AtlasReport


def compare_atlas(
    atlas: pd.DataFrame, dev_il_keys: frozenset[str], sealed_il_keys: frozenset[str]
) -> AtlasResult:
    """Standardize Atlas structures, drop sealed overlap, and flag ILs in LNPDB's development rows."""
    has_structure = atlas["il_smiles_raw"].notna()
    standardized = add_standard_structures(atlas)
    overlaps_sealed = standardized["il_inchikey"].isin(sealed_il_keys)
    kept = standardized.loc[~overlaps_sealed].reset_index(drop=True)
    kept["in_lnpdb_dev"] = kept["il_inchikey"].isin(dev_il_keys)
    unique = kept.drop_duplicates("il_inchikey")
    report = AtlasReport(
        rows=len(atlas),
        rows_without_structure=int((~has_structure).sum()),
        rows_with_unparseable_structure=int(has_structure.sum()) - len(standardized),
        rows_excluded_sealed_overlap=int(overlaps_sealed.sum()),
        rows_kept=len(kept),
        unique_ils=len(unique),
        ils_in_lnpdb_dev=int(unique["in_lnpdb_dev"].sum()),
        ils_not_in_lnpdb_dev=int((~unique["in_lnpdb_dev"]).sum()),
    )
    return AtlasResult(formulations=kept, report=report)


def atlas_against_lnpdb(atlas_csv: Path, lnpdb_dir: Path) -> AtlasResult:
    """Read Atlas and LNPDB, and compare them using LNPDB's development and sealed ILs."""
    keys = il_keys_by_split(read_lnpdb(lnpdb_csv_path(lnpdb_dir)))
    return compare_atlas(read_atlas(atlas_csv), dev_il_keys=keys.dev, sealed_il_keys=keys.sealed)


def write_atlas(result: AtlasResult, out_dir: Path) -> dict[str, Path]:
    """Write the kept Atlas rows and the report to out_dir. Returns the paths by name."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {"formulations": out_dir / ATLAS_FILE, "report": out_dir / ATLAS_REPORT_FILE}
    result.formulations.to_csv(paths["formulations"], index=False)
    paths["report"].write_text(json.dumps(asdict(result.report), indent=2) + "\n")
    return paths
