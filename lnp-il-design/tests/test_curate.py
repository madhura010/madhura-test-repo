import json
import os
from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from lnp_il.cli.main import app
from lnp_il.core import DataSourceError, curate, lnpdb_csv_path, read_lnpdb, write_curated
from lnp_il.core.curate import MIN_GROUP_SIZE, CurationResult, standardize_smiles
from lnp_il.core.studies import SEALED_HOLDOUT_STUDIES
from tests.helpers import make_rows, write_lnpdb


def curated(lnpdb_dir: Path) -> CurationResult:
    return curate(read_lnpdb(lnpdb_csv_path(lnpdb_dir)))


def labeled(tmp_path: Path, values: list[float]) -> pd.DataFrame:
    """Curate one study whose labels are exactly `values`, and return the development table."""
    rows = make_rows("T", len(values))
    for row, value in zip(rows, values, strict=True):
        row["Experiment_value"] = value
    write_lnpdb(tmp_path, rows)
    return curate(read_lnpdb(lnpdb_csv_path(tmp_path))).dev


def test_drops_rows_without_context_label_or_valid_structure(lnpdb_dir: Path) -> None:
    report = curated(lnpdb_dir).report
    assert report.input_rows == 50 + 30 + 5 + 3 + 4 + 2  # development rows, sealed excluded
    assert report.dropped_no_context == 5
    assert report.dropped_no_label == 2
    assert report.dropped_non_transfection_readout == 4
    assert report.dropped_bad_smiles == 3
    assert report.dev_rows == 50 + 30


def test_sealed_studies_are_only_in_the_sealed_table(lnpdb_dir: Path) -> None:
    result = curated(lnpdb_dir)
    assert set(result.sealed["study_id"]) == {"JL_2024"}
    assert len(result.sealed) == 25
    assert not set(result.dev["study_id"]) & SEALED_HOLDOUT_STUDIES


def test_nothing_sealed_appears_in_development_outputs(lnpdb_dir: Path, tmp_path: Path) -> None:
    result = curated(lnpdb_dir)
    assert not set(result.dev_studies["study_id"]) & SEALED_HOLDOUT_STUDIES
    out = tmp_path / "out"
    paths = write_curated(result, out)
    for name in ("dev", "studies", "report"):
        assert "JL_2024" not in paths[name].read_text()
        assert paths[name].parent == out
    assert paths["sealed"].parent == out / "sealed"
    assert "JL_2024" in paths["sealed_studies"].read_text()


def test_standardize_strips_salts_and_matches_equivalent_smiles() -> None:
    salt = standardize_smiles("CCN(CC)CC.Cl")
    plain = standardize_smiles("N(CC)(CC)CC")
    assert salt is not None
    assert salt == plain
    assert standardize_smiles("not a smiles") is None


def test_hits_are_the_top_quantile_within_each_group(lnpdb_dir: Path) -> None:
    dev = curated(lnpdb_dir).dev
    group = dev[dev["study_id"] == "DEV_A"]
    assert len(group) >= MIN_GROUP_SIZE
    assert group["hit"].sum() == pytest.approx(0.16 * len(group), abs=1)
    assert group.loc[group["hit"].astype(bool), "label_z"].min() > group["label_z"].median()


def test_small_groups_get_no_hit_call(tmp_path: Path) -> None:
    write_lnpdb(tmp_path, make_rows("TINY", MIN_GROUP_SIZE - 1))
    result = curate(read_lnpdb(lnpdb_csv_path(tmp_path)))
    assert result.dev["hit"].isna().all()
    assert result.report.hit_rate is None


def test_contexts_within_one_study_are_kept_apart(tmp_path: Path) -> None:
    write_lnpdb(tmp_path, make_rows("S", 25, cargo="FLuc") + make_rows("S", 25, cargo="GFP"))
    dev = curate(read_lnpdb(lnpdb_csv_path(tmp_path))).dev
    assert dev["context_id"].nunique() == 2


def test_flags_mark_lion_overlap_and_missing_fragments(tmp_path: Path) -> None:
    write_lnpdb(tmp_path, make_rows("AA_2008", 25) + make_rows("PLAIN", 25, fragments=False))
    studies = curate(read_lnpdb(lnpdb_csv_path(tmp_path))).dev_studies.set_index("study_id")
    assert studies.loc["AA_2008", "lion_contaminated"]
    assert not studies.loc["PLAIN", "lion_contaminated"]
    assert studies.loc["PLAIN", "fragment_coverage"] == 0
    assert studies.loc["AA_2008", "fragment_coverage"] == 1


def test_off_standard_groups_are_renormalized_and_keep_the_source_value(tmp_path: Path) -> None:
    dev = labeled(tmp_path, [5 + i / 10 for i in range(30)])
    assert dev["label_renormalized"].all()
    assert dev["label_z"].mean() == pytest.approx(0, abs=1e-9)
    assert dev["label_z"].std() == pytest.approx(1, abs=1e-9)
    assert dev["label_source_value"].min() == pytest.approx(5.0)


def test_standard_groups_are_left_alone(tmp_path: Path) -> None:
    values = pd.Series(range(40), dtype=float)
    dev = labeled(tmp_path, list(((values - values.mean()) / values.std()).round(12)))
    assert not dev["label_renormalized"].any()


def test_floor_ties_do_not_make_every_row_a_hit(tmp_path: Path) -> None:
    dev = labeled(tmp_path, [0.0] * 90 + [float(i) for i in range(1, 11)])
    assert dev["hit"].sum() == 10  # only the rows above the floor


def test_a_tie_that_spans_the_cutoff_gives_no_hit_call(tmp_path: Path) -> None:
    rows = make_rows("T", 100)
    for i, row in enumerate(rows):
        row["Experiment_value"] = 1.0 if i < 50 else -float(i)
    write_lnpdb(tmp_path, rows)
    result = curate(read_lnpdb(lnpdb_csv_path(tmp_path)))
    assert result.dev["hit"].isna().all()
    assert result.report.context_groups_without_hit_call == 1


def test_read_lnpdb_errors_are_domain_errors(tmp_path: Path) -> None:
    with pytest.raises(DataSourceError, match="not found"):
        read_lnpdb(tmp_path / "missing.csv")
    bad = tmp_path / "bad.csv"
    pd.DataFrame({"LNP_ID": [1]}).to_csv(bad, index=False)
    with pytest.raises(DataSourceError, match="missing columns"):
        read_lnpdb(bad)


def test_write_curated_puts_sealed_files_in_their_own_folder(
    lnpdb_dir: Path, tmp_path: Path
) -> None:
    out = tmp_path / "out"
    paths = write_curated(curated(lnpdb_dir), out)
    assert {p.name for p in out.iterdir()} == {
        "dataset_dev.csv",
        "studies.csv",
        "curation_report.json",
        "sealed",
    }
    assert {p.name for p in (out / "sealed").iterdir()} == {"SEALED_holdout.csv", "studies.csv"}
    assert json.loads(paths["report"].read_text())["dev_rows"] == 80


def test_cli_curate_json(lnpdb_dir: Path, tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app, ["--json", "data", "curate", "--lnpdb-dir", str(lnpdb_dir), "-o", str(tmp_path / "o")]
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["report"]["dev_rows"] == 80
    assert payload["data"]["sealed_rows"] == 25


def test_cli_missing_argument_is_a_usage_error(lnpdb_dir: Path) -> None:
    result = CliRunner().invoke(app, ["data", "curate", "--lnpdb-dir", str(lnpdb_dir)])
    assert result.exit_code == 2


def test_cli_error_under_json_returns_json_and_exit_1(tmp_path: Path) -> None:
    runner = CliRunner()
    args = ["data", "curate", "--lnpdb-dir", str(tmp_path / "nowhere"), "-o", str(tmp_path / "o")]
    result = runner.invoke(app, ["--json", *args])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "DATA_SOURCE"
    assert "not found" in payload["error"]["message"]
    assert "not found" in result.stderr  # message also goes to stderr


def test_cli_error_without_json_is_plain_text_and_exit_1(tmp_path: Path) -> None:
    args = ["data", "curate", "--lnpdb-dir", str(tmp_path / "nowhere"), "-o", str(tmp_path / "o")]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("Error: ")


@pytest.mark.skipif(not os.environ.get("LNPDB_DIR"), reason="LNPDB_DIR not set")
def test_real_lnpdb_matches_the_measured_counts() -> None:
    """Counts measured on LNPDB commit fc7c389 (docs/design.md, open question 7).

    A later LNPDB release will change them; update the numbers and the commit together.
    """
    result = curate(read_lnpdb(lnpdb_csv_path(Path(os.environ["LNPDB_DIR"]))))
    report = result.report
    assert report.input_rows == 19797 - 1474  # development side only
    assert report.dropped_no_context == 269
    assert report.dropped_no_label == 328
    assert report.dropped_non_transfection_readout == 282
    assert report.dev_rows == 17444
    assert len(result.sealed) == 1474
