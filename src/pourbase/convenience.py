"""Small entry points for common package use."""

from __future__ import annotations

from pathlib import Path

from .database import ThermodynamicDatabase
from .engine import PourbaixDiagram, PourbaixEngine
from .models import GibbsEnergyPolicy, PourbaixConditions


def open_database(path: str | Path | None = None) -> ThermodynamicDatabase:
    """Open the bundled publication database or a caller-supplied SQLite file."""
    return (
        ThermodynamicDatabase.bundled() if path is None else ThermodynamicDatabase(path)
    )


def calculate_pourbaix(
    symbol: str,
    conditions: PourbaixConditions | None = None,
    *,
    database: ThermodynamicDatabase | str | Path | None = None,
    allow_incomplete: bool = False,
    energy_policy: GibbsEnergyPolicy | str = GibbsEnergyPolicy.EXPERIMENTAL_ONLY,
) -> PourbaixDiagram:
    """Calculate a fixed-activity diagram with the bundled data by default."""
    selected_database = (
        database
        if isinstance(database, ThermodynamicDatabase)
        else open_database(database)
    )
    selected_conditions = conditions or PourbaixConditions()
    return PourbaixEngine(selected_database).calculate(
        symbol,
        selected_conditions,
        allow_incomplete=allow_incomplete,
        energy_policy=energy_policy,
    )
