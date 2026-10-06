import json
import os
from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from lnp_il.cli.main import app
from lnp_il.core import DataSourceError, atlas_against_lnpdb, read_atlas, write_atlas
from lnp_il.core.ingest import normalize_doi
from lnp_il.core.structures import standardize_smiles
from tests.helpers import atlas_row, make_rows, write_atlas_csv, write_lnpdb

DEV_IL = "CCCCN(CC)CC"
NEW_IL = "CCCCCCCCN(CC)CC"
SEALED_IL = "CCCCCCCN(CC)CC"


@pytest.fixture
def lnpdb_for_atlas(tmp_path: Path) -> Path:
    """LNPDB with development ILs of DEV_IL's family and one sealed study with SEALED_IL."""
    root = tmp_path / "lnpdb"
    write_lnpdb(root, make_rows("DEV_A", 30) + make_rows("JL_2024", 25, smiles=SEALED_IL))
    return root


@pytest.fixture
def atlas_csv(tmp_path: Path) -> Path:
    rows = [
        atlas_row(1, DEV_IL),  # already in LNPDB development data
        atlas_row(2, NEW_IL),  # new
        atlas_row(3, SEALED_IL),  # also in a sealed study: dropped
        atlas_row(4, None),  # no structure
        atlas_row(5, "not a smiles"),  # unparseable
        atlas_row(6, DEV_IL + ".Cl"),  # salt form of the development IL
    ]
    return write_atlas_csv(tmp_path / "atlas.csv", rows)


def test_atlas_is_read_with_the_right_encoding_and_no_label(atlas_csv: Path) -> None:
    table = read_atlas(atlas_csv)
    assert table["particle_size_text"].iloc[0] == "108.0 ± 2.1"
    assert table["row_id"].iloc[0] == "ATLAS_1"
    assert "label_z" not in table.columns
    assert table["bioactivity_text"].iloc[0].startswith("gene_expression_result")


def test_dois_are_normalized() -> None:
    assert normalize_doi("https://doi.org/10.1038/ABC-1") == "10.1038/abc-1"
    assert normalize_doi("https://dx.doi.org/10.1021/x") == "10.1021/x"
    assert normalize_doi("doi: 10.1/Y") == "10.1/y"
    assert normalize_doi("10.1/z") == "10.1/z"


def test_read_atlas_errors_are_domain_errors(tmp_path: Path) -> None:
    with pytest.raises(DataSourceError, match="not found"):
        read_atlas(tmp_path / "missing.csv")
    short = tmp_path / "short.csv"
    short.write_text("lnp_id\n1\n", encoding="euc-kr")
    with pytest.raises(DataSourceError, match="missing columns"):
        read_atlas(short)
    binary = tmp_path / "binary.csv"
    binary.write_bytes(b"lnp_id\n\xff\xfe\n")
    with pytest.raises(DataSourceError, match="euc-kr"):
        read_atlas(binary)


def test_atlas_rows_are_sorted_into_new_known_and_dropped(
    atlas_csv: Path, lnpdb_for_atlas: Path
) -> None:
    result = atlas_against_lnpdb(atlas_csv, lnpdb_for_atlas)
    report = result.report
    assert report.rows == 6
    assert report.rows_without_structure == 1
    assert report.rows_with_unparseable_structure == 1
    assert report.rows_excluded_sealed_overlap == 1
    assert report.rows_kept == 3
    assert report.unique_ils == 2
    assert report.ils_in_lnpdb_dev == 1
    assert report.ils_not_in_lnpdb_dev == 1


def test_a_salt_form_matches_the_development_il(atlas_csv: Path, lnpdb_for_atlas: Path) -> None:
    kept = atlas_against_lnpdb(atlas_csv, lnpdb_for_atlas).formulations
    assert kept.loc[kept["row_id"] == "ATLAS_6", "in_lnpdb_dev"].item()
    assert not kept.loc[kept["row_id"] == "ATLAS_2", "in_lnpdb_dev"].item()


def test_sealed_structures_do_not_appear_in_the_atlas_output(
    atlas_csv: Path, lnpdb_for_atlas: Path, tmp_path: Path
) -> None:
    result = atlas_against_lnpdb(atlas_csv, lnpdb_for_atlas)
    sealed = standardize_smiles(SEALED_IL)
    assert sealed is not None
    assert sealed[1] not in set(result.formulations["il_inchikey"])
    paths = write_atlas(result, tmp_path / "out")
    written = pd.read_csv(paths["formulations"])
    assert sealed[0] not in set(written["il_smiles"])


def test_catalog_only_lnpdb_rows_do_not_count_as_development_ils(tmp_path: Path) -> None:
    """An IL that LNPDB lists only in a no-context catalog row is not in its development rows."""
    catalog_il = "CCCCCCCCCN(CC)CC"
    root = tmp_path / "lnpdb"
    write_lnpdb(
        root, make_rows("DEV_A", 30) + make_rows("CATALOG", 4, smiles=catalog_il, model=None)
    )
    atlas = write_atlas_csv(
        tmp_path / "atlas.csv", [atlas_row(1, catalog_il), atlas_row(2, DEV_IL)]
    )
    kept = atlas_against_lnpdb(atlas, root).formulations.set_index("row_id")
    assert not kept.loc["ATLAS_1", "in_lnpdb_dev"]
    assert kept.loc["ATLAS_2", "in_lnpdb_dev"]


def test_cli_atlas_json(atlas_csv: Path, lnpdb_for_atlas: Path, tmp_path: Path) -> None:
    args = [
        "--json",
        "data",
        "atlas",
        "--atlas-csv",
        str(atlas_csv),
        "--lnpdb-dir",
        str(lnpdb_for_atlas),
        "-o",
        str(tmp_path / "out"),
    ]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["report"]["ils_not_in_lnpdb_dev"] == 1


def test_cli_atlas_plain_output_summarizes_the_counts(
    atlas_csv: Path, lnpdb_for_atlas: Path, tmp_path: Path
) -> None:
    args = [
        "data",
        "atlas",
        "--atlas-csv",
        str(atlas_csv),
        "--lnpdb-dir",
        str(lnpdb_for_atlas),
        "-o",
        str(tmp_path / "out"),
    ]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert (
        "✓ Atlas: 3 of 6 rows kept (2 unique ILs: 1 not in LNPDB's development rows"
        in result.stdout
    )
    assert "1 no structure, 1 unparseable, 1 overlap a sealed study" in result.stdout


def test_cli_atlas_without_required_options_is_a_usage_error(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app, ["data", "atlas", "-o", str(tmp_path)], env={"ATLAS_CSV": "", "LNPDB_DIR": ""}
    )
    assert result.exit_code == 2


def test_cli_atlas_missing_file_is_a_json_error(lnpdb_for_atlas: Path, tmp_path: Path) -> None:
    args = [
        "--json",
        "data",
        "atlas",
        "--atlas-csv",
        str(tmp_path / "nope.csv"),
        "--lnpdb-dir",
        str(lnpdb_for_atlas),
        "-o",
        str(tmp_path / "out"),
    ]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 1
    assert json.loads(result.stdout)["error"]["code"] == "DATA_SOURCE"


@pytest.mark.skipif(
    not (os.environ.get("LNPDB_DIR") and os.environ.get("ATLAS_CSV")),
    reason="LNPDB_DIR and ATLAS_CSV not set",
)
def test_real_atlas_counts() -> None:
    """Counts measured on LNP Atlas v1 (Zenodo 17243732) against LNPDB commit fc7c389."""
    result = atlas_against_lnpdb(Path(os.environ["ATLAS_CSV"]), Path(os.environ["LNPDB_DIR"]))
    report = result.report
    assert report.rows == 1092
    assert report.rows_without_structure == 152
    assert report.rows_with_unparseable_structure == 6
    assert report.rows_excluded_sealed_overlap == 0
    assert report.rows_kept == 934
    assert report.unique_ils == 259
    assert report.ils_in_lnpdb_dev == 19
    assert report.ils_not_in_lnpdb_dev == 240
