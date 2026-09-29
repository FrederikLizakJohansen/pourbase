"""The main window: connects settings, pages, background work and persistence."""

from __future__ import annotations

import html
import json
import re
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QGuiApplication, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QSplitter, QTabWidget, QVBoxLayout,
)

from .. import __version__
from ..exceptions import IncompleteSystemError
from ..export import diagram_figure, grid_csv, save_figure
from ..models import ExclusionReason
from ..records import SpeciesRecord
from ..scenario import Calculation, Mode
from .credentials import storage_description
from .dft import DftController
from .materials import matched_colors, phase_views, pretty_label
from .mp_page import MaterialsProjectPage
from .pages import BoundariesPage, DatabasePage, DiagramPage, SpeciationPage, SpeciesPage
from .periodic import OverviewPage
from .placeholder import StackedView
from .plots import record_colors
from .settings_panel import SettingsPanel
from .state import CONCENTRATION_UNITS, Session, Settings
from .sweep import SweepPage
from .tasks import TaskRunner
from .theme import THEME_MODES, apply_theme

DEBOUNCE_MS = 30


class MainWindow(QMainWindow):
    def __init__(self, symbol: str | None = None, settings: QSettings | None = None) -> None:
        super().__init__()
        self.setWindowTitle(f"pourbase {__version__}")
        self.stored = settings if settings is not None else QSettings("pourbase", "pourbase")
        self.session = Session()
        self.database = self.session.database
        self.systems = dict(self.database.available_systems())
        self.tasks = TaskRunner(self)
        self.dft = DftController(self.tasks, self.stored, self)
        self.calculation: Calculation | None = None
        self.comparison: Any = None
        self._records: dict[str, SpeciesRecord] = {}
        self._reset_range = True
        self._shown_sweep: Any = None
        self._status = ("", False)
        self.theme_mode = str(self.stored.value("theme", "System"))
        self.dark = False

        self._calculate_timer = QTimer(self, singleShot=True, interval=DEBOUNCE_MS, timeout=self.recalculate)
        self._overview_timer = QTimer(self, singleShot=True, interval=DEBOUNCE_MS, timeout=self.update_overview)
        self._build()
        self._build_menu()
        restored = self._restored_settings()
        if symbol and symbol.strip().capitalize() in self.systems:
            restored.symbol = symbol.strip().capitalize()
        self.panel.set_settings(restored)
        self._size_window()
        self.set_theme(self.theme_mode)
        hints = QGuiApplication.styleHints()
        if hasattr(hints, "colorSchemeChanged"):
            hints.colorSchemeChanged.connect(lambda _scheme: self.theme_mode == "System" and self.set_theme("System"))
        self.recalculate()
        self.update_overview()
        self.pages.setCurrentIndex(1 if symbol else 0)

    @property
    def settings(self) -> Settings:
        return self.panel.settings

    @property
    def display(self):
        return self.panel.display

    def _build(self) -> None:
        self.overview = OverviewPage()
        self.overview.changed.connect(self._overview_timer.start)
        self.overview.canvas.elementClicked.connect(self.open_element)
        self.overview.allow_incomplete.toggled.connect(self._overview_incomplete_toggled)
        self.panel = SettingsPanel(self.database)
        self.panel.changed.connect(self._settings_changed)
        self.panel.displayChanged.connect(self.refresh_view)
        self.panel.probeChanged.connect(self.set_probe)
        self.diagram_page = DiagramPage()
        self.diagram_page.probeMoved.connect(self.set_probe)
        self.species_page = SpeciesPage()
        self.boundaries_page = BoundariesPage()
        self.speciation_page = SpeciationPage()
        self.sweep_page = SweepPage()
        self.sweep_page.requested.connect(self.request_sweep)
        self.sweep_page.materialsProjectRequested.connect(self.request_dft_sweep)
        self.sweep_stack = StackedView(self.sweep_page)
        self.dft_page = MaterialsProjectPage()
        self.dft_page.optionsChanged.connect(self._dft_options_changed)
        self.dft_page.refreshRequested.connect(lambda: self.dft.retry(self.settings.symbol))
        self.dft_page.keyRequested.connect(self.edit_api_key)
        self.dft_page.exportRequested.connect(self.export_dft_figure)
        self.dft_page.probeMoved.connect(self.set_probe)
        self.dft_stack = StackedView(self.dft_page)
        self.dft.changed.connect(self._dft_changed)
        self.dft.sweepReady.connect(lambda _key: self.request_dft_sweep())
        self.database_page = DatabasePage(self.database)
        self.tasks.finished.connect(self._task_finished)
        self.tasks.progress.connect(self._task_progress)

        self.views = QTabWidget()
        self.views.setDocumentMode(True)
        for page, title in (
            (self.diagram_page, "Diagram"), (self.species_page, "Species"), (self.boundaries_page, "Boundaries"),
            (self.speciation_page, "Speciation"), (self.sweep_stack, "Concentration sweep"),
            (self.dft_stack, "DFT comparison"),
        ):
            self.views.addTab(page, title)
        self.views.currentChanged.connect(lambda _index: self.refresh_view())
        system = QSplitter()
        system.addWidget(self.panel)
        system.addWidget(self.views)
        system.setStretchFactor(1, 1)
        system.setCollapsible(0, False)
        system.setSizes([self.panel.minimumWidth(), 10_000])
        self.pages = QTabWidget()
        self.pages.setDocumentMode(True)
        self.pages.addTab(self.overview, "Periodic table")
        self.pages.addTab(system, "System")
        self.pages.addTab(self.database_page, "Database")
        self.pages.currentChanged.connect(self._page_changed)
        self.setCentralWidget(self.pages)
        self.status_label = QLabel()
        self.statusBar().addWidget(self.status_label, 1)
        for combo in self.findChildren(QComboBox):
            combo.setMaxVisibleItems(15)
            combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu("&File")
        for text, slot, shortcut in (
            ("Export figure…", self.export_figure, QKeySequence.Save),
            ("Export grid as CSV…", self.export_grid, None),
            ("Copy Python code", self.copy_python, None),
            (None, None, None),
            ("Quit", self.close, QKeySequence.Quit),
        ):
            if text is None:
                menu.addSeparator()
                continue
            action = menu.addAction(text, slot)
            if shortcut is not None:
                action.setShortcut(shortcut)
        view = self.menuBar().addMenu("&View")
        themes = view.addMenu("Theme")
        group = QActionGroup(self)
        self.theme_actions = {}
        for mode in THEME_MODES:
            action = QAction(mode, self, checkable=True)
            action.triggered.connect(lambda _checked=False, mode=mode: self.set_theme(mode))
            group.addAction(action)
            themes.addAction(action)
            self.theme_actions[mode] = action
        view.addAction("Reset zoom", lambda: self.refresh_view(reset_range=True)).setShortcut("Ctrl+0")
        tools = self.menuBar().addMenu("&Tools")
        tools.addAction("DFT comparison (Materials Project)", self.show_dft)
        tools.addAction("Materials Project API key…", self.edit_api_key)
        self.menuBar().addMenu("&Help").addAction("About pourbase", self.about)

    def _size_window(self) -> None:
        geometry = self.stored.value("geometry")
        if geometry is not None and self.restoreGeometry(geometry):
            return
        screen = QGuiApplication.primaryScreen()
        area = screen.availableGeometry() if screen is not None else None
        if area is not None and area.width() > 0:
            self.resize(min(1500, int(area.width() * 0.92)), min(920, int(area.height() * 0.9)))
        else:
            self.resize(1500, 900)

    def _restored_settings(self) -> Settings:
        try:
            settings = Settings.from_dict(json.loads(str(self.stored.value("settings", "{}"))))
        except (TypeError, ValueError):
            settings = Settings()
        return settings if settings.symbol in self.systems else Settings()

    def closeEvent(self, event) -> None:
        self.stored.setValue("settings", json.dumps(self.settings.to_dict()))
        self.stored.setValue("geometry", self.saveGeometry())
        self.stored.setValue("theme", self.theme_mode)
        self.tasks.shutdown()
        super().closeEvent(event)


    def _overview_incomplete_toggled(self, checked: bool) -> None:
        if checked != self.settings.allow_incomplete:
            self.panel.allow_incomplete.setChecked(checked)

    def _settings_changed(self, reset_range: bool) -> None:
        self._overview_timer.start()
        self._reset_range |= reset_range
        self.pages.setTabText(1, self.systems.get(self.settings.symbol, self.settings.symbol))
        self._calculate_timer.start()

    def recalculate(self) -> None:
        settings = self.settings
        self.pages.setTabText(1, self.systems.get(settings.symbol, settings.symbol))
        start = time.perf_counter()
        try:
            calculation = self.session.calculate(settings.scenario())
        except Exception as error:
            self._show_calculation_error(error)
            return
        elapsed = time.perf_counter() - start
        self.calculation = calculation
        self.panel.set_concentration_note(calculation.concentration.molar_concentration,
                                          calculation.concentration.log10_standard_activity)
        self.diagram_page.show_calculation(calculation, self.display, self._reset_range)
        self._reset_range = False
        self._update_probe()
        self.refresh_view()
        self._set_status(self._summary(calculation, elapsed))

    def _summary(self, calculation: Calculation, elapsed: float) -> str:
        reasons = [item.reason for item in calculation.excluded]
        missing = reasons.count(ExclusionReason.GIBBS_ENERGY_UNAVAILABLE)
        ligand = reasons.count(ExclusionReason.LIGAND_NOT_SELECTED)
        other = len(reasons) - missing - ligand
        system = calculation.diagram.system
        parts = [f"{system.system}: {len(calculation.stable_species)} stable of {len(system.species)} species"
                 + (f", calculated in {elapsed * 1e3:.0f} ms" if elapsed > 1e-3 else "")]
        if missing:
            parts.append(f"{missing} species omitted for missing Gibbs data")
        if ligand:
            parts.append(f"{ligand} ligand species available (System → Ligands)")
        if other:
            parts.append(f"{other} species outside this model (see Species)")
        if calculation.fallback_species:
            parts.append(f"{len(calculation.fallback_species)} MP 300 K estimate(s) in use")
        text = "; ".join(parts)
        return text if not (missing or calculation.fallback_species) else f"!{text}"

    def _show_calculation_error(self, error: Exception) -> None:
        self.calculation = None
        name = self.systems.get(self.settings.symbol, self.settings.symbol)
        if isinstance(error, IncompleteSystemError):
            self.diagram_page.show_message(
                f"{name} has documented evidence gaps",
                f"{html.escape(str(error))}.<br><br>Species without a recommended Gibbs energy can be "
                "left out for an exploratory diagram, or replaced by labelled Materials Project 300 K "
                "estimates where those exist.",
                ("Allow an incomplete system", lambda: self.panel.allow_incomplete.setChecked(True)),
                glyph="!",
            )
        else:
            self.diagram_page.show_message("The diagram cannot be calculated",
                                           html.escape(f"{type(error).__name__}: {error}"), glyph="!")
        self._set_status(f"!{name}: no diagram for the current settings")
        self.refresh_view()

    def set_probe(self, pH: float, eh_V: float) -> None:
        self.panel.set_probe(pH, eh_V)
        self._update_probe()
        current = self.views.currentWidget()
        if current is self.speciation_page:
            self._show_speciation()
        elif current is self.dft_stack and self.comparison is not None:
            self.dft_page.set_probe(pH, eh_V)

    def _update_probe(self) -> None:
        if self.calculation is None:
            return
        settings = self.settings
        try:
            probe = self.calculation.probe(settings.probe_pH, settings.probe_eh_V)
        except ValueError as error:
            self.diagram_page.probe.setHtml(html.escape(str(error)))
            return
        dft_phase = None
        if self.comparison is not None and self.comparison.experimental.system.symbol == settings.symbol:
            try:
                dft_phase = pretty_label(self.comparison.materials_project.phase_at(probe.pH, probe.eh_V).label)
            except ValueError:
                pass
        self.diagram_page.show_probe(probe, self._record(probe.species.record_id), dft_phase)

    def _record(self, record_id: str) -> SpeciesRecord | None:
        return self._records_for([record_id]).get(record_id)

    def _records_for(self, record_ids) -> dict[str, SpeciesRecord]:
        missing = [item for item in record_ids if item not in self._records]
        if missing:
            self._records.update({item.record_id: item for item in self.database.species_records(missing)})
        return {item: self._records[item] for item in record_ids if item in self._records}

    def open_element(self, symbol: str) -> None:
        screen = self.overview.canvas.screen
        settings = self.settings
        settings.symbol = symbol
        if screen is not None:
            settings.probe_pH, settings.probe_eh_V = screen.pH, screen.potential_V_vs_SHE
        self.panel.set_settings(settings)
        self.pages.setCurrentIndex(1)
        self.views.setCurrentWidget(self.diagram_page)
        self.recalculate()

    def _page_changed(self, index: int) -> None:
        if index == 0:
            self.update_overview()
        elif index == 2:
            self.database_page.load()

    def update_overview(self) -> None:
        settings = self.settings
        try:
            screen = self.session.screen(
                **self.overview.conditions(), concentration=settings.concentration,
                concentration_unit=settings.concentration_unit,
                solution_density_kg_L=settings.solution_density_kg_L,
                allow_incomplete=settings.allow_incomplete, energy_policy=settings.energy_policy.value,
            )
        except Exception as error:
            self._set_status(f"!{type(error).__name__}: {error}")
            return
        checkbox = self.overview.allow_incomplete
        checkbox.blockSignals(True)
        checkbox.setChecked(settings.allow_incomplete)
        checkbox.blockSignals(False)
        canvas = self.overview.canvas
        canvas.selected = settings.symbol
        canvas.show_screen(screen)
        self.overview.note.setText(
            f"Metal concentration {settings.concentration:g} {CONCENTRATION_UNITS[settings.concentration_unit]}"
            + (", incomplete systems allowed" if settings.allow_incomplete else "")
            + (", MP estimates in use" if settings.use_mp_fallbacks else "")
            + ". These follow the System settings."
        )


    def refresh_view(self, reset_range: bool = False) -> None:
        current = self.views.currentWidget()
        calculation = self.calculation
        if current is self.diagram_page and calculation is not None:
            self.diagram_page.show_calculation(calculation, self.display, reset_range)
            self._update_probe()
        elif current is self.species_page:
            if calculation is None:
                self.species_page.clear()
            else:
                system = calculation.diagram.system
                ids = [item.record_id for item in system.species] + [item.record_id for item in system.excluded]
                self.species_page.show_calculation(calculation, self._records_for(ids))
        elif current is self.boundaries_page:
            self._show_boundaries()
        elif current is self.speciation_page:
            self._show_speciation()
        elif current is self.sweep_stack:
            self.request_sweep()
        elif current is self.dft_stack:
            self._show_dft(reset_range)

    def _set_mode(self, mode: Mode) -> None:
        self.panel.mode.setCurrentIndex(self.panel.mode.findData(mode.value))
        self.recalculate()

    def _show_boundaries(self) -> None:
        page = self.boundaries_page
        if self.settings.mode == Mode.MASS_BALANCE.value:
            page.show_message(
                "Boundary equations describe fixed-activity diagrams",
                "In the mass-balance model, boundaries are numerical equilibria that include metal "
                "inventory and precipitation, so pairwise Nernst equations do not apply.",
                ("Switch to fixed activity", lambda: self._set_mode(Mode.FIXED_ACTIVITY)),
            )
        elif self.calculation is None:
            page.show_message("No diagram", "Boundaries appear once the diagram is calculated.")
        else:
            page.show_calculation(self.calculation)

    def _show_speciation(self) -> None:
        page, calculation = self.speciation_page, self.calculation
        if self.settings.mode != Mode.MASS_BALANCE.value:
            page.show_message(
                "Species fractions need a closed metal inventory",
                "In fixed-activity mode every aqueous species has an externally set activity, so "
                "there is no conserved amount to divide between species. The mass-balance model "
                "conserves the total metal and reports the fraction held by each species.",
                ("Switch to mass balance", lambda: self._set_mode(Mode.MASS_BALANCE)),
            )
            return
        if calculation is None:
            page.show_message("No diagram", "Speciation appears once the diagram is calculated.")
            return
        diagram = calculation.diagram
        row = int(np.abs(diagram.eh_V - self.settings.probe_eh_V).argmin())
        colors = record_colors([item.record_id for item in diagram.stable_species])
        rows = [("Experimental", diagram.stable_species_index[row], diagram.system.species, colors)]
        symbol = self.settings.symbol
        entries = self.dft.entries(symbol, fetch=False)
        blocker = self.dft.blocker(symbol)
        action = None
        if entries is not None:
            official = self.dft.official(entries, diagram.conditions)
            rows.append(("DFT (MP)", official.stable_phase_index[row], phase_views(official),
                         matched_colors(diagram.system.species, official, colors, record_colors)))
            note = (f"Materials Project {entries.database_version} at the same total activity. MP has no "
                    "closed metal balance, so its row shows the lowest-energy phase.")
        elif blocker is not None:
            note = blocker.title + "."
            if blocker.action:
                action = (blocker.action_label, lambda: self._resolve(blocker.action))
        elif self.dft.fetching(symbol):
            note = f"Fetching the Materials Project entries for {symbol}…"
        else:
            note = "Compare with the official Materials Project DFT diagram."
            action = ("Show DFT comparison", lambda: (self.dft.entries(symbol), self._show_speciation()))
        page.show_calculation(calculation, self.settings.probe_eh_V, rows, note, action)


    def request_sweep(self) -> None:
        """Show the cached sweep for the current settings, or calculate it in the background."""
        sweep_settings = self.sweep_page.settings()
        if sweep_settings.log10_max <= sweep_settings.log10_min:
            self.sweep_stack.show_message("Invalid activity range", "The upper activity must exceed the lower.")
            return
        scenario = sweep_settings.scenario(self.settings)
        key = (scenario, sweep_settings)
        cached = self.session.cached("sweep", key)
        if cached is not None:
            if key != self._shown_sweep:
                self._show_sweep(key, cached)
            return
        self._sweep_message = (
            f"{sweep_settings.levels} fixed-activity diagrams on a {sweep_settings.pH_points} × "
            f"{sweep_settings.eh_points} grid, from log₁₀ a = {sweep_settings.log10_min:g} to "
            f"{sweep_settings.log10_max:g}."
        )
        self.sweep_stack.show_message("Calculating the concentration sweep…", self._sweep_message, glyph="…")
        self.tasks.submit("sweep", key, lambda progress: self.session.sweep(scenario, sweep_settings, progress))

    def _show_sweep(self, key: Any, sweep: Any) -> None:
        calculation = self.calculation
        level = calculation.concentration.log10_standard_activity if calculation else -6.0
        self._shown_sweep = key
        self.sweep_page.clear_materials_project()
        self.sweep_page.set_sweep(sweep, self.display, level, (self.settings.probe_pH, self.settings.probe_eh_V))
        self.sweep_stack.show_view()
        note = " Mass-balance settings do not apply; each slice is a fixed-activity diagram." if (
            self.settings.mode == Mode.MASS_BALANCE.value) else ""
        self._set_status(f"{sweep.system.system}: {len(sweep.diagrams)} slices.{note}")

    def request_dft_sweep(self) -> None:
        sweep = self.sweep_page.sweep
        if sweep is None or self._shown_sweep is None:
            return
        blocker = self.dft.blocker(sweep.system.symbol)
        if blocker is not None:
            self.sweep_page.hint.setText(re.sub("<[^>]+>", "", blocker.message))
            if blocker.action == "key":
                self.edit_api_key()
            return
        layer = self.dft.sweep_layer(sweep, self.sweep_page.volumes["experimental"], self._shown_sweep)
        if layer is None:
            self.sweep_page.hint.setText(f"Evaluating the Materials Project sweep for {sweep.system.symbol}…")
        else:
            self.sweep_page.set_materials_project(
                *layer, "Materials Project slices use the same activity for every aqueous species."
            )

    def _task_progress(self, kind: str, key: Any, fraction: float) -> None:
        if kind == "sweep" and self.sweep_stack.currentWidget() is not self.sweep_page:
            self.sweep_stack.show_message(f"Calculating the concentration sweep… {fraction:.0%}",
                                          self._sweep_message, glyph="…")
        elif kind == "dft-sweep":
            self.sweep_page.hint.setText(f"Evaluating the Materials Project sweep… {fraction:.0%}")

    def _task_finished(self, kind: str, key: Any, result: Any, error: str) -> None:
        if kind != "sweep" or self.views.currentWidget() is not self.sweep_stack:
            return
        if error:
            self.sweep_stack.show_message("The sweep cannot be calculated", html.escape(error), glyph="!")
        elif result is not None and key == (self.sweep_page.settings().scenario(self.settings),
                                            self.sweep_page.settings()):
            self._show_sweep(key, result)


    def show_dft(self) -> None:
        self.pages.setCurrentIndex(1)
        self.views.setCurrentWidget(self.dft_stack)

    def _resolve(self, action: str | None) -> None:
        if action == "key":
            self.edit_api_key()
        elif action == "retry":
            self.dft.retry(self.settings.symbol)
            self.refresh_view()

    def _dft_options_changed(self) -> None:
        self.dft.set_options(*self.dft_page.options())
        self.sweep_page.clear_materials_project()
        self.refresh_view()

    def _dft_changed(self) -> None:
        self.refresh_view()
        self._update_probe()
        if self.views.currentWidget() is self.sweep_stack and self.sweep_page.source != "experimental":
            self.request_dft_sweep()

    def _show_dft(self, reset_range: bool = False) -> None:
        symbol = self.settings.symbol
        blocker = self.dft.blocker(symbol)
        if blocker is not None:
            action = (blocker.action_label, lambda: self._resolve(blocker.action)) if blocker.action else None
            self.dft_stack.show_message(blocker.title, blocker.message, action)
            return
        if self.calculation is None:
            self.dft_stack.show_message("No experimental diagram", "The comparison needs the experimental diagram.")
            return
        entries = self.dft.entries(symbol)
        if entries is None:
            self.dft_stack.show_message(
                f"Fetching the Materials Project entries for {symbol}…",
                "The entries are downloaded once per element and then evaluated locally for every "
                "setting, sweep and speciation view.", glyph="…",
            )
            return
        notes = []
        scenario = self.settings.scenario()
        if scenario.mode is Mode.MASS_BALANCE:
            scenario = replace(scenario, mode=Mode.FIXED_ACTIVITY, davies_ionic_strength_mol_L=None)
            notes.append("MP diagrams use fixed activities, so the experimental panel shows the "
                         "fixed-activity diagram at the same concentration.")
        if scenario.ligands:
            notes.append("MP diagrams are ligand-free; the experimental panel includes the enabled ligands.")
        try:
            self.comparison = self.dft.compare(self.session.calculate(scenario).diagram, entries)
        except Exception as error:
            self.dft_stack.show_message("The comparison cannot be calculated",
                                        html.escape(f"{type(error).__name__}: {error}"), glyph="!")
            return
        first = self.dft_stack.currentWidget() is not self.dft_page
        self.dft_stack.show_view()
        self.dft_page.show_comparison(self.comparison, self.display, notes, reset_range=first or reset_range)
        self.dft_page.set_probe(self.settings.probe_pH, self.settings.probe_eh_V)
        self._set_status(f"{self.systems[symbol]}: {self.comparison.equivalent_domain_fraction:.1%} of the grid "
                         f"agrees with Materials Project {entries.database_version}")

    def edit_api_key(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Materials Project API key")
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        width = max(dialog.fontMetrics().horizontalAdvance("M" * 40), 480)

        def wrapped(text: str) -> QLabel:
            label = QLabel(text)
            label.setWordWrap(True)
            label.setOpenExternalLinks(True)
            label.setFixedWidth(width)
            label.setFixedHeight(label.heightForWidth(width))
            return label

        layout.addWidget(wrapped(
            "The DFT comparison uses the official Materials Project diagrams and needs a free API "
            'key from the <a href="https://materialsproject.org/api">Materials Project API page</a>.'
        ))
        key = QLineEdit(self.dft.api_key)
        key.setEchoMode(QLineEdit.Password)
        key.setPlaceholderText("Paste your API key")
        key.setMinimumWidth(key.fontMetrics().horizontalAdvance("W" * 34))
        show = QCheckBox("Show")
        show.toggled.connect(lambda on: key.setEchoMode(QLineEdit.Normal if on else QLineEdit.Password))
        row = QHBoxLayout()
        row.addWidget(QLabel("API key"))
        row.addWidget(key, 1)
        row.addWidget(show)
        layout.addLayout(row)
        remember = QCheckBox("Remember on this computer")
        remember.setChecked(self.dft.key_source in ("keyring", "settings") or not self.dft.api_key)
        layout.addWidget(remember)
        layout.addWidget(wrapped(f"The key is stored in {html.escape(storage_description())}."))
        if self.dft.key_source == "environment":
            layout.addWidget(wrapped("The current key comes from the MP_API_KEY environment variable."))
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.addButton("Forget key", QDialogButtonBox.DestructiveRole).clicked.connect(
            lambda: (key.clear(), remember.setChecked(False))
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.adjustSize()
        dialog.setMinimumSize(dialog.sizeHint())
        if dialog.exec() == QDialog.Accepted:
            self.dft.set_api_key(key.text().strip(), remember.isChecked())


    def _save_path(self, title: str, name: str, filters: str) -> str:
        path, _ = QFileDialog.getSaveFileName(self, title, name, filters)
        return path

    def export_figure(self) -> None:
        if self.calculation is None:
            return
        path = self._save_path("Export figure", f"pourbaix-{self.settings.symbol.lower()}.png",
                               "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)")
        if not path:
            return
        display, calculation = self.display, self.calculation
        fixed = not calculation.is_mass_balance
        figure = diagram_figure(
            calculation.diagram, labels=display.labels, legend=display.legend,
            boundaries=display.boundaries, water=display.water,
            plating_potential_V=(calculation.plating[0].potential_V_vs_SHE
                                 if fixed and display.plating and calculation.plating else None),
            boltzmann_scale=display.boltzmann_scale if fixed and display.boltzmann else None,
        )
        self._set_status(f"Wrote {save_figure(figure, path)}")

    def export_grid(self) -> None:
        if self.calculation is None:
            return
        path = self._save_path("Export grid", f"pourbaix-grid-{self.settings.symbol.lower()}.csv", "CSV (*.csv)")
        if path:
            Path(path).write_text(grid_csv(self.calculation.diagram))
            self._set_status(f"Wrote {path}")

    def export_dft_figure(self) -> None:
        if self.comparison is None:
            return
        path = self._save_path("Export comparison", f"pourbaix-mp-{self.settings.symbol.lower()}.png",
                               "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)")
        if path:
            from ..plotting import plot_official_materials_project_comparison

            figure, _ = plot_official_materials_project_comparison(self.comparison)
            self._set_status(f"Wrote {save_figure(figure, path)}")

    def copy_python(self) -> None:
        QGuiApplication.clipboard().setText(self.settings.python_code())
        self._set_status("Copied the equivalent Python code to the clipboard")

    def about(self) -> None:
        QMessageBox.about(
            self, "About pourbase",
            f"<b>pourbase {__version__}</b>, dataset {html.escape(self.database.data_version)}"
            "<p>Source-linked experimental thermochemistry and Pourbaix diagrams at 298.15 K and "
            "1 bar.</p><p>Cite this release and the scientific sources attached to each value. "
            "See CITATION.cff and THIRD_PARTY_NOTICES.md.</p>",
        )


    def set_theme(self, mode: str) -> None:
        self.theme_mode = mode if mode in THEME_MODES else "System"
        self.dark = apply_theme(self.theme_mode)
        self.theme_actions[self.theme_mode].setChecked(True)
        self.diagram_page.dark = self.dark
        for widget in (self.diagram_page.diagram, self.speciation_page, self.sweep_page, self.dft_page,
                       self.overview.canvas):
            widget.set_dark(self.dark)
        self.refresh_view()
        self._set_status(*self._status)

    def _set_status(self, text: str, error: bool = False) -> None:
        if text.startswith("!"):
            text, error = text[1:], True
        self._status = (text, error)
        color = ("#e06c75" if self.dark else "#b00020") if error else ""
        self.status_label.setStyleSheet(f"color: {color};" if color else "")
        self.status_label.setText(text)
