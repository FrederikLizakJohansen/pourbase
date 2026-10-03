"""Materials Project comparisons for the desktop GUI, independent of Qt.

Entries are fetched from the official API once per element and option set, then evaluated
offline at any aqueous activity and grid. Evaluating every filtered entry and taking the
minimum gives the same stable phase at each point as pymatgen's stable-entry list.
"""

from __future__ import annotations

import atexit
import json
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from importlib.metadata import PackageNotFoundError, version
from importlib.util import find_spec
from typing import Any, Callable, Sequence

import numpy as np

from ..exceptions import CalculationCancelled, MaterialsProjectUnavailableError
from ..materials_project import (
    OfficialMaterialsProjectComparison,
    OfficialMaterialsProjectDiagram,
    apply_aqueous_activities,
    evaluate_official_materials_project_entries,
    thermodynamic_species_equivalence_key,
)
from ..models import PourbaixConditions

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
    retrieved_at: float | None = None


CACHE_DAYS = 30
_clients: dict[str, Any] = {}
_clients_lock = threading.Lock()
_fetch_lock = threading.Lock()


def _client(api_key: str) -> Any:
    """An open ``MPRester`` for this key, shared by every fetch.

    Opening a client and loading the ion reference table take about ten seconds, and the
    client keeps both for later fetches. Fetches through one client run one at a time.
    """
    from mp_api.client import MPRester

    with _clients_lock:
        if api_key not in _clients:
            _clients[api_key] = MPRester(api_key, mute_progress_bars=True, notify_db_version=False)
        return _clients[api_key]


@atexit.register
def close_clients() -> None:
    with _clients_lock:
        for client in _clients.values():
            try:
                client.__exit__(None, None, None)
            except Exception:
                pass
        _clients.clear()


def warm_up(api_key: str) -> None:
    """Import the client libraries, open the client and load its ion reference table.

    These take most of the time of a first fetch; the client keeps the table for every element.
    """
    from pymatgen.analysis.pourbaix_diagram import PourbaixDiagram  # noqa: F401

    rester = _client(api_key)
    with _fetch_lock:
        rester.get_ion_reference_data()


def fetch_entries(symbol: str, api_key: str, filter_solids: bool, use_gibbs_300K: bool) -> FetchedEntries:
    """Download the official Pourbaix entries for one element (network access)."""
    try:
        import mp_api.client  # noqa: F401
        from pymatgen.analysis.pourbaix_diagram import PourbaixDiagram as MPPourbaixDiagram
        mp_api_version = version("mp-api")
        pymatgen_version = version("pymatgen")
    except (ImportError, PackageNotFoundError) as error:
        raise MaterialsProjectUnavailableError(
            'Live Materials Project diagrams need the optional dependencies: '
            'pip install "pourbase[materials-project]"'
        ) from error
    try:
        rester = _client(api_key)
        with _fetch_lock:
            entries = rester.get_pourbaix_entries([symbol], use_gibbs=300 if use_gibbs_300K else None)
            database_version = str(rester.db_version)
        filtered = MPPourbaixDiagram(entries, filter_solids=filter_solids).all_entries
    except Exception as error:
        with _clients_lock:
            _clients.pop(api_key, None)
        message = str(error).replace(api_key, "[redacted]")
        raise MaterialsProjectUnavailableError(
            f"Materials Project could not provide the {symbol} entries: {message}"
        ) from error
    return FetchedEntries(symbol, list(filtered), database_version, mp_api_version,
                          pymatgen_version, filter_solids, use_gibbs_300K, retrieved_at=time.time())


class MaterialsProjectSource:
    """Cached MP entries per element, evaluated on demand for diagrams and sweeps.

    With ``cache_dir``, downloaded entries are also stored on disk and reused for
    ``CACHE_DAYS`` days, or until the installed pymatgen version changes.
    """

    def __init__(self, fetcher: Callable[..., FetchedEntries] = fetch_entries,
                 cache_dir: Path | None = None) -> None:
        self.fetcher = fetcher
        self.cache_dir = cache_dir
        self._fetched: dict[tuple, FetchedEntries] = {}
        self._lock = threading.Lock()
        self._evaluation_lock = threading.Lock()

    @staticmethod
    def key(symbol: str, filter_solids: bool, use_gibbs_300K: bool) -> tuple:
        return (symbol, filter_solids, use_gibbs_300K)

    def fetched(self, symbol: str, filter_solids: bool, use_gibbs_300K: bool) -> FetchedEntries | None:
        with self._lock:
            return self._fetched.get(self.key(symbol, filter_solids, use_gibbs_300K))

    def fetch(self, symbol: str, api_key: str, filter_solids: bool, use_gibbs_300K: bool) -> FetchedEntries:
        """Download once per element and option set; later calls return the cached entries."""
        if (cached := self.fetched(symbol, filter_solids, use_gibbs_300K)) is not None:
            return cached
        key = self.key(symbol, filter_solids, use_gibbs_300K)
        entries = self._read_cache(key)
        if entries is None:
            entries = self.fetcher(symbol, api_key, filter_solids, use_gibbs_300K)
            self._write_cache(key, entries)
        with self._lock:
            return self._fetched.setdefault(key, entries)

    def invalidate(self, symbol: str | None = None) -> None:
        """Forget downloaded entries, for one element or all, in memory and on disk."""
        with self._lock:
            for key in [key for key in self._fetched if symbol is None or key[0] == symbol]:
                del self._fetched[key]
        if self.cache_dir is not None and self.cache_dir.is_dir():
            for path in self.cache_dir.glob(f"{symbol or '*'}-*.json"):
                path.unlink(missing_ok=True)

    def _cache_path(self, key: tuple) -> Path | None:
        if self.cache_dir is None:
            return None
        symbol, filter_solids, use_gibbs_300K = key
        return self.cache_dir / (f"{symbol}-{'filtered' if filter_solids else 'all'}-"
                                 f"{'gibbs300K' if use_gibbs_300K else 'dft'}.json")

    def _read_cache(self, key: tuple) -> FetchedEntries | None:
        path = self._cache_path(key)
        if path is None or not path.is_file():
            return None
        try:
            from pymatgen.analysis.pourbaix_diagram import PourbaixEntry

            stored = json.loads(path.read_text(encoding="utf-8"))
            if (stored["pymatgen_version"] != version("pymatgen")
                    or time.time() - stored["retrieved_at"] > CACHE_DAYS * 86400):
                return None
            entries = [PourbaixEntry.from_dict(item) for item in stored["entries"]]
        except Exception:
            return None
        return FetchedEntries(key[0], entries, stored["database_version"], stored["mp_api_version"],
                              stored["pymatgen_version"], key[1], key[2], stored["retrieved_at"])

    def _write_cache(self, key: tuple, fetched: FetchedEntries) -> None:
        path = self._cache_path(key)
        if path is None:
            return
        try:
            from monty.json import MontyEncoder

            stored = {
                "database_version": fetched.database_version, "mp_api_version": fetched.mp_api_version,
                "pymatgen_version": fetched.pymatgen_version,
                "retrieved_at": fetched.retrieved_at or time.time(),
                "entries": [entry.as_dict() for entry in fetched.entries],
            }
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(stored, cls=MontyEncoder), encoding="utf-8")
            temporary.replace(path)
        except Exception:
            pass

    def diagram(self, fetched: FetchedEntries, conditions: PourbaixConditions) -> OfficialMaterialsProjectDiagram:
        """Evaluate the fetched entries at the activities and grid of ``conditions``."""
        with self._evaluation_lock:
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
        count = len(experimental_sweep.diagrams)
        for number, diagram in enumerate(experimental_sweep.diagrams):
            if progress is not None and progress(number / count) is False:
                raise CalculationCancelled()
            official = self.diagram(fetched, diagram.conditions)
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
