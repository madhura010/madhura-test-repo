"""Output helpers shared by commands: JSON mode and error reporting."""

import json
from typing import NoReturn

import typer

from lnp_il.core import LnpIlError


def wants_json(ctx: typer.Context) -> bool:
    """True when the root `--json` flag was given."""
    return bool((ctx.obj or {}).get("json"))


def fail(ctx: typer.Context, error: LnpIlError) -> NoReturn:
    """Report an expected error and exit 1.

    The message goes to stderr in both modes. Under `--json`, the error is also written to
    stdout as {"ok": false, "error": {"code", "message"}} so scripts can parse the failure.
    """
    typer.echo(f"Error: {error}", err=True)
    if wants_json(ctx):
        payload = {"ok": False, "error": {"code": error.code, "message": str(error)}}
        typer.echo(json.dumps(payload))
    raise typer.Exit(code=1)
