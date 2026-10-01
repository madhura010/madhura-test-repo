"""Curate: clean the common table, tag studies, and separate the sealed holdout.

The holdout is split off before anything else, and the two halves are cleaned
independently. Nothing computed for development (counts, study table, report) includes a
sealed row, and the sealed outputs are written to their own folder. The sealed table is
meant to be read once, for the final report (docs/design.md, mental-model invariants).
"""

import json
from dataclasses import asdict, dataclass
from functools import reduce
from pathlib import Path

import pandas as pd
from rdkit import Chem, rdBase
from rdkit.Chem.MolStandardize import rdMolStandardize

from lnp_il.core.studies import LION_TRAINING_STUDIES, SEALED_HOLDOUT_STUDIES

rdBase.DisableLog("rdApp.*")

DEFAULT_HIT_QUANTILE = 0.16
# Smallest (study, context) group that gets a hit call or is checked for off-standard labels.
MIN_GROUP_SIZE = 20
# A hit call is kept only if the realized hit rate lands within this factor of the target.
HIT_RATE_TOLERANCE = 0.5

# Readouts that describe the particle or its safety, not delivery. They are not labels.
NON_TRANSFECTION_READOUTS = frozenset({"diameter", "zeta_potential", "hemolysis_percent"})

DEV_FILE = "dataset_dev.csv"
STUDIES_FILE = "studies.csv"
REPORT_FILE = "curation_report.json"
SEALED_DIR = "sealed"
SEALED_FILE = "SEALED_holdout.csv"

_CONTEXT_PARTS = ("study_id", "model_type", "route", "cargo_type", "readout")
_FRAGMENT_COLUMNS = ("il_head_smiles", "il_tail1_smiles")


@dataclass(frozen=True)
class CurationReport:
    """Counts for the development rows only, and the hit definition that was applied."""

    input_rows: int
    dropped_no_context: int
    dropped_no_label: int
    dropped_non_transfection_readout: int
    dropped_bad_smiles: int
    dev_rows: int
    studies: int
    unique_ils: int
    hit_quantile: float
    hit_rate: float | None  # None when no group is large enough for a hit call
    context_groups_renormalized: int
    context_groups_without_hit_call: int


@dataclass(frozen=True)
class CurationResult:
    """Development outputs (with their report) and, separately, the sealed-holdout outputs."""

    dev: pd.DataFrame
    dev_studies: pd.DataFrame
    report: CurationReport
    sealed: pd.DataFrame
    sealed_studies: pd.DataFrame


@dataclass(frozen=True)
class _Cleaned:
    """Cleaned rows plus how many rows were dropped for each reason."""

    rows: pd.DataFrame
    input_rows: int
    dropped_no_context: int
    dropped_no_label: int
    dropped_non_transfection_readout: int
    dropped_bad_smiles: int
    renormalized_groups: int


def standardize_smiles(smiles: str) -> tuple[str, str] | None:
    """Return (canonical isomeric SMILES, InChIKey) for the largest fragment, or None if invalid."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    mol = rdMolStandardize.LargestFragmentChooser().choose(mol)
    return Chem.MolToSmiles(mol), Chem.MolToInchiKey(mol)


def _add_standard_structures(table: pd.DataFrame) -> pd.DataFrame:
    """Add il_smiles and il_inchikey; drop rows whose structure cannot be parsed."""
    cache = {s: standardize_smiles(s) for s in table["il_smiles_raw"].dropna().unique()}
    parsed = table["il_smiles_raw"].map(cache)
    ok = parsed.notna()
    out = table.loc[ok].copy()
    out["il_smiles"] = parsed[ok].map(lambda pair: pair[0])
    out["il_inchikey"] = parsed[ok].map(lambda pair: pair[1])
    return out.drop(columns="il_smiles_raw")


def _context_ids(rows: pd.DataFrame) -> pd.Series:
    """Join the context columns into one key per row (works when `rows` is empty)."""
    parts = [rows[column].astype(str) for column in _CONTEXT_PARTS]
    return reduce(lambda joined, part: joined + "|" + part, parts)


def _hit_calls_for_group(label: pd.Series, quantile: float) -> pd.Series:
    """Top-`quantile` hit call for one (study, context) group, aware of tied values.

    Many readouts have few distinct values (discretized scores, or a floor of untransfected
    wells), so a cutoff can fall inside a tie. Both `>=` and `>` the cutoff are tried and the
    one whose hit rate is closer to `quantile` is used. If even that rate is further than
    HIT_RATE_TOLERANCE from the target, the group gets no hit call.
    """
    unknown = pd.Series(pd.NA, index=label.index, dtype="boolean")
    if len(label) < MIN_GROUP_SIZE:
        return unknown
    cutoff = label.quantile(1 - quantile)
    at_least, above = label >= cutoff, label > cutoff
    chosen = at_least if abs(at_least.mean() - quantile) <= abs(above.mean() - quantile) else above
    if abs(chosen.mean() - quantile) > HIT_RATE_TOLERANCE * quantile:
        return unknown
    return chosen.astype("boolean")


def _hit_calls_by_group(table: pd.DataFrame, quantile: float) -> pd.Series:
    """Hit calls for every (study, context) group, aligned to the table's index."""
    calls = [
        _hit_calls_for_group(rows["label_z"], quantile) for _, rows in table.groupby("context_id")
    ]
    if not calls:
        return pd.Series(pd.NA, index=table.index, dtype="boolean")
    return pd.concat(calls).reindex(table.index)


def _groups_without_hit_call(table: pd.DataFrame) -> int:
    """Count groups large enough for a hit call that still got none, because of ties."""
    groups = table.groupby("context_id").agg(
        size=("label_z", "size"), called=("hit", lambda h: bool(h.notna().any()))
    )
    return int(((groups["size"] >= MIN_GROUP_SIZE) & ~groups["called"]).sum())


def _renormalize_off_standard(table: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Re-standardize groups whose labels are not close to mean 0, SD 1.

    LNPDB reports z-scores within each study and delivery context. A group that is far from
    that (for example a value reported relative to a reference product) is z-scored here.
    The value as received stays in `label_source_value`, and `label_renormalized` marks the
    rows that were changed.
    """
    out = table.copy()
    grouped = out.groupby("context_id")["label_z"]
    mean, std, size = grouped.transform("mean"), grouped.transform("std"), grouped.transform("size")
    off = ((mean.abs() > 0.1) | ((std - 1).abs() > 0.1)) & (size >= MIN_GROUP_SIZE) & (std > 0)
    out["label_source_value"] = out["label_z"]
    out["label_renormalized"] = off
    out.loc[off, "label_z"] = (out["label_z"] - mean) / std
    return out, int(out.loc[off, "context_id"].nunique())


def _study_table(table: pd.DataFrame) -> pd.DataFrame:
    """One row per study: size, context, and the flags that govern how it may be used."""

    def first(series: pd.Series) -> object:
        values = series.dropna()
        return values.iloc[0] if len(values) else None

    studies = table.groupby("study_id").agg(
        rows=("row_id", "size"),
        unique_ils=("il_inchikey", "nunique"),
        model=("model", first),
        model_type=("model_type", first),
        route=("route", first),
        cargo_type=("cargo_type", first),
        readout=("readout", first),
        mixing_method=("mixing_method", first),
        fragment_coverage=("has_fragments", "mean"),
        publication_link=("publication_link", first),
    )
    studies["lion_contaminated"] = studies.index.isin(LION_TRAINING_STUDIES)
    studies["sealed_holdout"] = studies.index.isin(SEALED_HOLDOUT_STUDIES)
    return studies.reset_index().sort_values("rows", ascending=False)


def _clean(table: pd.DataFrame, hit_quantile: float) -> _Cleaned:
    """Drop unusable rows, standardize structures and labels, tag studies, and call hits."""
    has_context = table["model"].notna()
    has_label = table["label_z"].notna()
    is_delivery = ~table["readout"].isin(NON_TRANSFECTION_READOUTS)
    kept = table.loc[has_context & has_label & is_delivery]

    rows = _add_standard_structures(kept)
    rows["context_id"] = _context_ids(rows)
    rows["has_fragments"] = rows[list(_FRAGMENT_COLUMNS)].notna().all(axis=1)
    rows["lion_contaminated"] = rows["study_id"].isin(LION_TRAINING_STUDIES)
    rows, renormalized_groups = _renormalize_off_standard(rows)
    rows["hit"] = _hit_calls_by_group(rows, hit_quantile)
    return _Cleaned(
        rows=rows.reset_index(drop=True),
        input_rows=len(table),
        dropped_no_context=int((~has_context).sum()),
        dropped_no_label=int((has_context & ~has_label).sum()),
        dropped_non_transfection_readout=int((has_context & has_label & ~is_delivery).sum()),
        dropped_bad_smiles=len(kept) - len(rows),
        renormalized_groups=renormalized_groups,
    )


def _report(cleaned: _Cleaned, hit_quantile: float) -> CurationReport:
    rows = cleaned.rows
    called_hits = rows["hit"].dropna()
    return CurationReport(
        input_rows=cleaned.input_rows,
        dropped_no_context=cleaned.dropped_no_context,
        dropped_no_label=cleaned.dropped_no_label,
        dropped_non_transfection_readout=cleaned.dropped_non_transfection_readout,
        dropped_bad_smiles=cleaned.dropped_bad_smiles,
        dev_rows=len(rows),
        studies=int(rows["study_id"].nunique()),
        unique_ils=int(rows["il_inchikey"].nunique()),
        hit_quantile=hit_quantile,
        hit_rate=float(called_hits.mean()) if len(called_hits) else None,
        context_groups_renormalized=cleaned.renormalized_groups,
        context_groups_without_hit_call=_groups_without_hit_call(rows),
    )


def curate(table: pd.DataFrame, hit_quantile: float = DEFAULT_HIT_QUANTILE) -> CurationResult:
    """Split off the sealed holdout, then clean each half independently.

    Rows with no context (for example catalog entries with no experiment), no label, or a
    readout that is not a delivery measure are dropped. Structures are standardized,
    off-standard label groups are re-standardized, each study is tagged, and hits are called
    within each (study, context) group. The report and study table describe development
    rows only.
    """
    is_sealed = table["study_id"].isin(SEALED_HOLDOUT_STUDIES)
    dev = _clean(table.loc[~is_sealed], hit_quantile)
    sealed = _clean(table.loc[is_sealed], hit_quantile)
    return CurationResult(
        dev=dev.rows,
        dev_studies=_study_table(dev.rows),
        report=_report(dev, hit_quantile),
        sealed=sealed.rows,
        sealed_studies=_study_table(sealed.rows),
    )


def write_curated(result: CurationResult, out_dir: Path) -> dict[str, Path]:
    """Write development files to out_dir and sealed files to out_dir/sealed.

    Returns the paths by name.
    """
    sealed_dir = out_dir / SEALED_DIR
    sealed_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "dev": out_dir / DEV_FILE,
        "studies": out_dir / STUDIES_FILE,
        "report": out_dir / REPORT_FILE,
        "sealed": sealed_dir / SEALED_FILE,
        "sealed_studies": sealed_dir / STUDIES_FILE,
    }
    result.dev.to_csv(paths["dev"], index=False)
    result.dev_studies.to_csv(paths["studies"], index=False)
    paths["report"].write_text(json.dumps(asdict(result.report), indent=2) + "\n")
    result.sealed.to_csv(paths["sealed"], index=False)
    result.sealed_studies.to_csv(paths["sealed_studies"], index=False)
    return paths
