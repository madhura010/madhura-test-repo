"""Command-line entry point: `lnp-il`."""

from typing import Annotated

import typer

from lnp_il import __version__
from lnp_il.cli import data

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Public-data pipeline for LNP transfection prediction and ionizable lipid design.",
)
app.add_typer(data.app, name="data")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"lnp-il/{__version__}")
        raise typer.Exit()


@app.callback()
def root(
    ctx: typer.Context,
    json_output: Annotated[
        bool, typer.Option("--json", help="Machine-readable JSON on stdout.")
    ] = False,
    version: Annotated[
        bool,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version."),
    ] = False,
) -> None:
    """Public-data pipeline for LNP transfection prediction and ionizable lipid design.

    \b
    Commands:
      data curate --lnpdb-dir <path> --out-dir <path>   Build the curated dataset.
    """
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output
