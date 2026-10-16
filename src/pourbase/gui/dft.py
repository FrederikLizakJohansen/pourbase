"""Materials Project comparisons: API key, downloads and evaluated layers."""

from __future__ import annotations

import html
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QSettings, Signal

from ..materials_project import OfficialMaterialsProjectComparison, OfficialMaterialsProjectDiagram
from ..models import PourbaixConditions
from .credentials import clear_key, load_key, save_key, storage_description
from .materials import (
    FetchedEntries, MaterialsProjectSource, client_available, equivalence_matrix, fetch_entries, matched_colors,
    warm_up,
)
from .plots import record_colors
from .tasks import TaskRunner


@dataclass(frozen=True)
class Blocker:
    """Why no comparison can be shown; ``action`` is "key", "retry" or None."""

    title: str
    message: str
    action: str | None = None

    @property
    def action_label(self) -> str | None:
        return {"key": "Enter API key…", "retry": "Try again"}.get(self.action or "")


class DftController(QObject):
    """Downloads MP entries once per element and evaluates them for every view.

    ``changed`` fires when entries arrive or fail; ``sweepReady(key)`` when a sweep layer
    is evaluated.
    """

    changed = Signal()
    sweepReady = Signal(object)

    def __init__(self, tasks: TaskRunner, settings: QSettings, parent: QObject | None = None,
                 cache_dir: Path | None = None) -> None:
        super().__init__(parent)
        self.tasks = tasks
        self.settings = settings
        self.source = MaterialsProjectSource(cache_dir=cache_dir)
        self._key: tuple[str, str] | None = None
        self.filter_solids = True
        self.gibbs_300K = False
        self.errors: dict[tuple, str] = {}
        self._sweeps: OrderedDict[Any, tuple] = OrderedDict()
        tasks.finished.connect(self._finished)

    @property
    def api_key(self) -> str:
        return self._stored_key()[0]

    @api_key.setter
    def api_key(self, value: str) -> None:
        self._key = (value, "session" if value else "")

    @property
    def key_source(self) -> str:
        """Where the key came from: "keyring", "settings", "environment", "session" or ""."""
        return self._stored_key()[1]

    def _stored_key(self) -> tuple[str, str]:
        # The keyring backend takes a noticeable time to load, so the key is read on first use.
        if self._key is None:
            self._key = load_key(self.settings)
        return self._key

    def entry_key(self, symbol: str) -> tuple:
        return (symbol, self.filter_solids, self.gibbs_300K)

    def blocker(self, symbol: str) -> Blocker | None:
        if not client_available():
            return Blocker(
                "The Materials Project client is not installed",
                'Comparisons use the official mp-api client and pymatgen. Install them with '
                '<code>pip install "pourbase[materials-project]"</code> and restart pourbase.',
            )
        if not self.api_key:
            return Blocker(
                "A Materials Project API key is needed",
                "The key is free with a Materials Project account and is available on the "
                '<a href="https://materialsproject.org/api">API page</a>. pourbase can remember it '
                f"in {html.escape(storage_description())}.",
                "key",
            )
        if error := self.errors.get(self.entry_key(symbol)):
            return Blocker("Materials Project could not provide this element", html.escape(error), "retry")
        return None

    def entries(self, symbol: str, fetch: bool = True) -> FetchedEntries | None:
        """Downloaded entries, or None while they are fetched or unavailable."""
        key = self.entry_key(symbol)
        if (entries := self.source.fetched(*key)) is not None:
            return entries
        if fetch and self.blocker(symbol) is None:
            api_key = self.api_key
            self.tasks.submit("dft-fetch", key, lambda _progress: self.source.fetch(symbol, api_key, *key[1:]))
        return None

    def warm_up(self) -> None:
        """Open the Materials Project client in the background before the first fetch."""
        if self.source.fetcher is fetch_entries and self.api_key and client_available():
            api_key = self.api_key
            self.tasks.submit("dft-warm", api_key, lambda _progress: warm_up(api_key))

    def fetching(self, symbol: str) -> bool:
        return self.tasks.running("dft-fetch") == self.entry_key(symbol)

    def retry(self, symbol: str) -> None:
        self.source.invalidate(symbol)
        self.errors.pop(self.entry_key(symbol), None)
        self._sweeps.clear()
        self.entries(symbol)

    def set_options(self, filter_solids: bool, gibbs_300K: bool) -> None:
        self.filter_solids, self.gibbs_300K = filter_solids, gibbs_300K
        self._sweeps.clear()

    def set_api_key(self, value: str, remember: bool) -> None:
        previous = self.api_key
        if remember and value:
            source = save_key(self.settings, value)
        else:
            clear_key(self.settings)
            source = "session" if value else ""
        self._key = (value, source)
        if value != previous:
            self.errors.clear()
        self.changed.emit()

    def official(self, entries: FetchedEntries, conditions: PourbaixConditions) -> OfficialMaterialsProjectDiagram:
        return self.source.diagram(entries, conditions)

    def compare(self, experimental: Any, entries: FetchedEntries) -> OfficialMaterialsProjectComparison:
        return self.source.compare(experimental, self.official(entries, experimental.conditions))

    def sweep_layer(self, sweep: Any, experimental: Any, sweep_key: Any) -> tuple | None:
        """MP phase indices, phases, colors and agreement for a sweep, once evaluated."""
        entries = self.entries(sweep.system.symbol)
        if entries is None:
            return None
        key = (sweep_key, self.entry_key(sweep.system.symbol))
        if key in self._sweeps:
            return self._sweeps[key]

        def work(progress):
            index, phases = self.source.sweep(entries, sweep, progress)
            official = self.official(entries, sweep.diagrams[0].conditions)
            colors = matched_colors(experimental.species, official, experimental.colors, record_colors)
            same = equivalence_matrix(experimental.species, official)[experimental.index, index]
            return index, phases, colors, same

        self.tasks.submit("dft-sweep", key, work)
        return None

    def _finished(self, kind: str, key: Any, result: Any, error: str) -> None:
        if kind == "dft-fetch":
            if error:
                self.errors[key] = error
            self.changed.emit()
        elif kind == "dft-sweep" and result is not None:
            self._sweeps[key] = result
            while len(self._sweeps) > 4:
                self._sweeps.popitem(last=False)
            self.sweepReady.emit(key)
        elif kind == "dft-sweep" and error:
            self.errors[key[1]] = error
            self.changed.emit()
