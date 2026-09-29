"""Offline Materials Project entries built with pymatgen (no network access)."""

from __future__ import annotations

from importlib.util import find_spec

PYMATGEN = find_spec("pymatgen") is not None
MP_API = find_spec("mp_api") is not None


def iron_entries() -> list:
    """A small Fe system: metal, Fe²⁺, FeO₄²⁻ and two oxides (energies in eV per formula)."""
    from pymatgen.analysis.pourbaix_diagram import IonEntry, PourbaixEntry
    from pymatgen.core.ion import Ion
    from pymatgen.entries.computed_entries import ComputedEntry

    return [
        PourbaixEntry(ComputedEntry("Fe", 0.0), entry_id="mp-13"),
        PourbaixEntry(ComputedEntry("Fe2O3", -7.6), entry_id="mp-19770"),
        PourbaixEntry(ComputedEntry("Fe3O4", -10.4), entry_id="mp-19306"),
        PourbaixEntry(IonEntry(Ion.from_formula("Fe[+2]"), -0.95), entry_id="ion-fe2"),
        PourbaixEntry(IonEntry(Ion.from_formula("FeO4[-2]"), -5.0), entry_id="ion-feo4"),
    ]


class FakeRester:
    """Stands in for ``mp_api.client.MPRester``."""

    db_version = "test-db"

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def __enter__(self) -> "FakeRester":
        return self

    def __exit__(self, *_exc) -> None:
        return None

    def get_pourbaix_entries(self, *_args, **_kwargs) -> list:
        return iron_entries()


def fake_fetcher(symbol: str, api_key: str, filter_solids: bool, use_gibbs_300K: bool):
    from pymatgen.analysis.pourbaix_diagram import PourbaixDiagram

    from pourbase.gui.materials import FetchedEntries

    entries = PourbaixDiagram(iron_entries(), filter_solids=filter_solids).all_entries
    return FetchedEntries(symbol, list(entries), "test-db", "test-api", "test-pymatgen",
                          filter_solids, use_gibbs_300K)
