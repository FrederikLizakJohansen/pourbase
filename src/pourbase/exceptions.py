"""Public exceptions raised by :mod:`pourbase`."""


class GibbsPourbaixError(Exception):
    """Base class for package-specific failures."""


class DatabaseSchemaError(GibbsPourbaixError):
    """The SQLite file does not provide the schema required by this package."""


class MetalSystemNotFoundError(GibbsPourbaixError):
    """The requested element symbol has no records in the database."""


class IncompleteSystemError(GibbsPourbaixError):
    """A calculation would omit a ligand-free species without a Gibbs value."""


class UnsupportedConditionError(GibbsPourbaixError):
    """The requested calculation is outside the validated scientific scope."""


class MaterialsProjectUnavailableError(GibbsPourbaixError):
    """The optional live Materials Project workflow could not run."""
