"""`lnp-il data`: dataset commands."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer

from lnp_il.cli.output import fail, wants_json
from lnp_il.core import (
    LnpIlError,
    atlas_against_lnpdb,
    curate,
    lnpdb_csv_path,
    read_lnpdb,
    write_atlas,
    write_curated,
)
from lnp_il.core.curate import DEFAULT_HIT_QUANTILE

app = typer.Typer(no_args_is_help=True, help="Build and inspect the curated dataset.")


@app.command("curate")
def curate_command(
    ctx: typer.Context,
    lnpdb_dir: Annotated[
        Path,
        typer.Option(
            "--lnpdb-dir",
            envvar="LNPDB_DIR",
            help="Path to a clone of the LNPDB repository [$LNPDB_DIR].",
        ),
    ],
    out_dir: Annotated[
        Path,
        typer.Option("--out-dir", "-o", help="Directory to write the curated files to."),
    ],
    hit_quantile: Annotated[
        float,
        typer.Option("--hit-quantile", min=0.01, max=0.5, help="Top fraction called a hit."),
    ] = DEFAULT_HIT_QUANTILE,
) -> None:
    """Clean LNPDB, split off the sealed holdout, and write the curated files.

    Writes dataset_dev.csv, studies.csv and curation_report.json, and puts the sealed
    holdout in a sealed/ subfolder. The sealed file is read once, for the final report.

    \b
    Examples:
      lnp-il data curate --lnpdb-dir ~/LNPDB --out-dir data/curated
      LNPDB_DIR=~/LNPDB lnp-il data curate -o data/curated
      lnp-il --json data curate --lnpdb-dir ~/LNPDB -o data/curated
    """
    try:
        result = curate(read_lnpdb(lnpdb_csv_path(lnpdb_dir)), hit_quantile=hit_quantile)
        paths = write_curated(result, out_dir)
    except LnpIlError as error:
        fail(ctx, error)
    report = result.report
    if wants_json(ctx):
        data = {
            "report": asdict(report),
            "sealed_rows": len(result.sealed),
            "files": {name: str(path) for name, path in paths.items()},
        }
        typer.echo(json.dumps({"ok": True, "data": data}))
        return
    typer.echo(
        f"✓ Curated {report.dev_rows} development rows "
        f"({report.studies} studies, {report.unique_ils} unique ILs); "
        f"{len(result.sealed)} sealed rows written separately"
    )
    typer.echo(
        f"  dropped: {report.dropped_no_context} no context, {report.dropped_no_label} no label, "
        f"{report.dropped_non_transfection_readout} non-delivery readout, "
        f"{report.dropped_bad_smiles} bad structure"
    )
    typer.echo(f"  Wrote {out_dir} (sealed files in {out_dir / 'sealed'})")


@app.command("atlas")
def atlas_command(
    ctx: typer.Context,
    atlas_csv: Annotated[
        Path,
        typer.Option(
            "--atlas-csv", envvar="ATLAS_CSV", help="Path to the LNP Atlas CSV [$ATLAS_CSV]."
        ),
    ],
    lnpdb_dir: Annotated[
        Path,
        typer.Option(
            "--lnpdb-dir",
            envvar="LNPDB_DIR",
            help="Path to a clone of the LNPDB repository [$LNPDB_DIR].",
        ),
    ],
    out_dir: Annotated[
        Path,
        typer.Option("--out-dir", "-o", help="Directory to write the Atlas files to."),
    ],
) -> None:
    """Compare LNP Atlas structures with LNPDB and write the usable Atlas rows.

    Atlas has no usable label, so it adds structures and formulation fields only. Rows whose IL is also in a sealed-holdout study are dropped. Writes atlas_formulations.csv and atlas_report.json.

    \b
    Examples:
      lnp-il data atlas --atlas-csv atlas.csv --lnpdb-dir ~/LNPDB -o out
      ATLAS_CSV=atlas.csv LNPDB_DIR=~/LNPDB lnp-il --json data atlas -o out
    """
    try:
        result = atlas_against_lnpdb(atlas_csv, lnpdb_dir)
        paths = write_atlas(result, out_dir)
    except LnpIlError as error:
        fail(ctx, error)
    report = result.report
    if wants_json(ctx):
        payload = {"report": asdict(report), "files": {k: str(v) for k, v in paths.items()}}
        typer.echo(json.dumps({"ok": True, "data": payload}))
        return
    typer.echo(
        f"✓ Atlas: {report.rows_kept} of {report.rows} rows kept "
        f"({report.unique_ils} unique ILs: {report.ils_not_in_lnpdb_dev} not in LNPDB's "
        f"development rows, {report.ils_in_lnpdb_dev} already in them)"
    )
    typer.echo(
        f"  dropped: {report.rows_without_structure} no structure, "
        f"{report.rows_with_unparseable_structure} unparseable, "
        f"{report.rows_excluded_sealed_overlap} overlap a sealed study"
    )
    typer.echo(f"  Wrote {out_dir}")
