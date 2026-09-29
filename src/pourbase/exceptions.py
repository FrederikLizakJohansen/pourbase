"""Public exceptions raised by :mod:`pourbase`."""


class PourbaseError(Exception):
    """Base class for package-specific failures."""


class DatabaseSchemaError(PourbaseError):
    """The SQLite file does not provide the schema required by this package."""


class MetalSystemNotFoundError(PourbaseError):
    """The requested element symbol has no records in the database."""


class IncompleteSystemError(PourbaseError):
    """A calculation would omit a ligand-free species without a Gibbs value."""


class UnsupportedConditionError(PourbaseError):
    """The requested calculation is outside the validated scientific scope."""


class MaterialsProjectUnavailableError(PourbaseError):
    """The optional live Materials Project workflow could not run."""


class CalculationCancelled(PourbaseError):
    """A long calculation was cancelled through its progress callback."""
