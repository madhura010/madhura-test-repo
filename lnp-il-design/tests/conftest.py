from pathlib import Path

import pytest

from tests.helpers import make_rows, write_lnpdb


@pytest.fixture
def lnpdb_dir(tmp_path: Path) -> Path:
    """A fake LNPDB clone with one dev study, one sealed study, and rows that must be dropped."""
    rows = (
        make_rows("DEV_A", 50)
        + make_rows("AA_2008", 30)  # LiON-contaminated study
        + make_rows("JL_2024", 25)  # sealed holdout
        + make_rows("NOCTX", 5, model=None)  # no context: dropped
        + make_rows("BADSMI", 3, smiles="not a smiles")  # unparseable: dropped
        + make_rows("PHYS", 4, readout="diameter")  # not a delivery readout: dropped
    )
    unlabeled = make_rows("DEV_A", 2)
    for row in unlabeled:
        row["LNP_ID"] = "unlabeled_" + str(row["LNP_ID"])
        row["Experiment_value"] = None
    write_lnpdb(tmp_path, rows + unlabeled)
    return tmp_path
