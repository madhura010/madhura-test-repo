"""Domain errors raised by the pipeline."""


class LnpIlError(Exception):
    """Base class for all domain errors in this package."""

    code = "ERROR"


class DataSourceError(LnpIlError):
    """A dataset file is missing, unreadable, or does not have the expected columns."""

    code = "DATA_SOURCE"
