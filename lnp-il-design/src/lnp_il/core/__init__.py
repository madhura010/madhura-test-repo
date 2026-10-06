"""Core pipeline logic. Interface layers (cli) import from here, never the reverse."""

__all__ = [
    "AtlasReport",
    "AtlasResult",
    "CurationReport",
    "CurationResult",
    "DataSourceError",
    "LnpIlError",
    "atlas_against_lnpdb",
    "curate",
    "lnpdb_csv_path",
    "read_atlas",
    "read_lnpdb",
    "write_atlas",
    "write_curated",
]

from lnp_il.core.atlas import AtlasReport, AtlasResult, atlas_against_lnpdb, write_atlas
from lnp_il.core.curate import CurationReport, CurationResult, curate, write_curated
from lnp_il.core.exceptions import DataSourceError, LnpIlError
from lnp_il.core.ingest import lnpdb_csv_path, read_atlas, read_lnpdb
