"""Materials Project comparisons for the desktop GUI, independent of Qt.

Entries are fetched from the official API once per element and option set, then evaluated
offline at any aqueous activity and grid. Evaluating every filtered entry and taking the
minimum gives the same stable phase at each point as pymatgen's stable-entry list.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, replace
from importlib.metadata import PackageNotFoundError, version
from importlib.util import find_spec
from typing import Any, Callable, Sequence

import numpy as np

from ..exceptions import MaterialsProjectUnavailableError
from ..materials_project import (
    OfficialMaterialsProjectComparison,
    OfficialMaterialsProjectDiagram,
    apply_aqueous_activities,
    evaluate_official_materials_project_entries,
    thermodynamic_species_equivalence_key,
)
from ..models import AqueousActivityModel, PourbaixConditions
from .engine import SweepCancelled

SUPERSCRIPT = str.maketrans("0123456789+-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻")
SUBSCRIPT = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def client_available() -> bool:
    return find_spec("mp_api") is not None and find_spec("pymatgen") is not None


def pretty_label(label: str) -> str:
    """Convert pymatgen names such as ``Fe[+2]``, ``FeO4[-2]`` or ``Fe2O3(s)`` to formulas."""
    match = re.fullmatch(r"(.*?)\[([+-])(\d*)\]", label)
    charge = ""
    if match:
        label, sign, magnitude = match.groups()
        magnitude = "" if magnitude in ("", "1") else magnitude
        charge = (magnitude + sign).translate(SUPERSCRIPT)
    suffix = ""
    if label.endswith("(s)"):
        label, suffix = label[:-3], "(s)"
    return re.sub(r"(?<=[A-Za-z)])(\d+)", lambda m: m.group(1).translate(SUBSCRIPT), label) + charge + suffix


@dataclass(frozen=True)
class PhaseView:
    """An MP phase in the shape the plotting views expect of a species."""

    record_id: str
    species: str
    phase: str
    phase_detail: str


@dataclass(frozen=True)
class AgreementClass:
    record_id: str
    species: str
    phase: str = "comparison"
    phase_detail: str = ""


AGREEMENT = (AgreementClass("same", "Same species"), AgreementClass("different", "Different species"))


@dataclass
class FetchedEntries:
    symbol: str
    entries: Sequence[Any]
    database_version: str
    mp_api_version: str
    pymatgen_version: str
    filter_solids: bool
    use_gibbs_300K: bool


def fetch_entries(symbol: str, api_key: str, filter_solids: bool, use_gibbs_300K: bool) -> FetchedEntries:
    """Download the official Pourbaix entries for one element (network access)."""
    try:
        from mp_api.client import MPRester
        from pymatgen.analysis.pourbaix_diagram import PourbaixDiagram as MPPourbaixDiagram
        mp_api_version = version("mp-api")
        pymatgen_version = version("pymatgen")
    except (ImportError, PackageNotFoundError) as error:
        raise MaterialsProjectUnavailableError(
            'Live Materials Project diagrams need the optional dependencies: '
            'pip install "pourbase[materials-project]"'
        ) from error
    try:
        with MPRester(api_key, mute_progress_bars=True, notify_db_version=False) as rester:
            entries = rester.get_pourbaix_entries([symbol], use_gibbs=300 if use_gibbs_300K else None)
            database_version = str(rester.db_version)
        # Solid filtering does not depend on ion concentrations, so one diagram suffices
        filtered = MPPourbaixDiagram(entries, filter_solids=filter_solids).all_entries
    except Exception as error:
        message = str(error).replace(api_key, "[redacted]")
        raise MaterialsProjectUnavailableError(
            f"Materials Project could not provide the {symbol} entries: {message}"
        ) from error
    return FetchedEntries(symbol, list(filtered), database_version, mp_api_version,
                          pymatgen_version, filter_solids, use_gibbs_300K)


class MaterialsProjectSource:
    """Cached MP entries per element, evaluated on demand for diagrams and sweeps."""

    def __init__(self, fetcher: Callable[..., FetchedEntries] = fetch_entries) -> None:
        self.fetcher = fetcher
        self._fetched: dict[tuple, FetchedEntries] = {}
        self._lock = threading.Lock()

    @staticmethod
    def key(symbol: str, filter_solids: bool, use_gibbs_300K: bool) -> tuple:
        return (symbol, filter_solids, use_gibbs_300K)

    def fetched(self, symbol: str, filter_solids: bool, use_gibbs_300K: bool) -> FetchedEntries | None:
        return self._fetched.get(self.key(symbol, filter_solids, use_gibbs_300K))

    def fetch(self, symbol: str, api_key: str, filter_solids: bool, use_gibbs_300K: bool) -> FetchedEntries:
        key = self.key(symbol, filter_solids, use_gibbs_300K)
        if key not in self._fetched:
            self._fetched[key] = self.fetcher(symbol, api_key, filter_solids, use_gibbs_300K)
        return self._fetched[key]

    def diagram(self, fetched: FetchedEntries, conditions: PourbaixConditions) -> OfficialMaterialsProjectDiagram:
        """Evaluate the fetched entries at the activities and grid of ``conditions``."""
        with self._lock:  # entries carry their ion concentration as mutable state
            apply_aqueous_activities(fetched.entries, conditions)
            return evaluate_official_materials_project_entries(
                fetched.symbol, conditions, fetched.entries,
                database_version=fetched.database_version, mp_api_version=fetched.mp_api_version,
                pymatgen_version=fetched.pymatgen_version, filter_solids=fetched.filter_solids,
                use_gibbs_300K=fetched.use_gibbs_300K,
            )

    @staticmethod
    def compare(experimental: Any, official: OfficialMaterialsProjectDiagram) -> OfficialMaterialsProjectComparison:
        equivalence = equivalence_matrix(experimental.system.species, official)
        same = equivalence[experimental.stable_species_index, official.stable_phase_index]
        same.setflags(write=False)
        return OfficialMaterialsProjectComparison(experimental, official, same)

    def sweep(
        self,
        fetched: FetchedEntries,
        experimental_sweep: Any,
        progress: Callable[[float], bool] | None = None,
    ) -> tuple[np.ndarray, tuple[PhaseView, ...]]:
        """MP stable-phase indices on the grid of every level of an experimental sweep."""
        volume = []
        phases: tuple[PhaseView, ...] = ()
        for number, (level, diagram) in enumerate(zip(experimental_sweep.log10_activities,
                                                      experimental_sweep.diagrams)):
            if progress is not None and progress(number / len(experimental_sweep.diagrams)) is False:
                raise SweepCancelled()
            conditions = replace(
                diagram.conditions, aqueous_activities=AqueousActivityModel(default_log10_activity=float(level))
            )
            official = self.diagram(fetched, conditions)
            volume.append(official.stable_phase_index.astype(np.int16))
            phases = phase_views(official)
        return np.stack(volume), phases


def equivalence_matrix(species: Sequence[Any], official: OfficialMaterialsProjectDiagram) -> np.ndarray:
    """``[experimental species, MP phase]`` is True when both describe the same species."""
    return np.asarray([
        [thermodynamic_species_equivalence_key(item) == phase.equivalence_key for phase in official.phases]
        for item in species
    ], dtype=np.bool_)


def phase_views(official: OfficialMaterialsProjectDiagram) -> tuple[PhaseView, ...]:
    return tuple(
        PhaseView(
            record_id=f"mp:{phase.phase_id}",
            species=pretty_label(phase.label),
            phase=phase.phase_type,
            phase_detail=f"{phase.phase_id}" if phase.phase_type == "solid" else "aq",
        )
        for phase in official.phases
    )


def matched_colors(experimental_species: Sequence[Any], official: OfficialMaterialsProjectDiagram,
                   experimental_colors: dict[str, Any], fallback: Callable[[list[str]], dict[str, Any]]
                   ) -> dict[str, Any]:
    """Give each MP phase the color of the experimental species it matches, if any."""
    equivalence = equivalence_matrix(experimental_species, official)
    colors: dict[str, Any] = {}
    unmatched = []
    for column, view in enumerate(phase_views(official)):
        matches = [experimental_species[row].record_id for row in np.nonzero(equivalence[:, column])[0]
                   if experimental_species[row].record_id in experimental_colors]
        if matches:
            colors[view.record_id] = experimental_colors[matches[0]]
        else:
            unmatched.append(view.record_id)
    if unmatched:
        extra = fallback(sorted(set(experimental_colors) | set(unmatched)))
        for record_id in unmatched:
            colors[record_id] = extra[record_id]
    return colors
