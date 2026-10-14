"""The main window: connects settings, pages, background work and persistence."""

from __future__ import annotations

import html
import math
import json
import re
import time
import copy
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
from PySide6.QtCore import QPoint, QSettings, QStandardPaths, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QFont, QGuiApplication, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QSplitter, QTabWidget, QVBoxLayout, QWidget,
)

from .. import __version__
from ..conversions import express_concentration
from ..exceptions import IncompleteSystemError
from ..export import diagram_figure, grid_csv, save_figure
from ..models import ExclusionReason
from ..records import SpeciesRecord
from ..scenario import Calculation, Mode, calculate
from ..uncertainty import stability_margin
from ..selection import SelectionPolicy, select, with_policy
from ..exceptions import DatabaseSchemaError
from ..user_data import open_dataset, with_user_species
from . import logo_pixmap
from .compare import ComparePage
from .context_bar import ACCENT, NEUTRAL, WARNING, ContextBar, power_of_ten
from .credentials import storage_description
from .history import History
from .pinned import PinnedDiagram
from .dft import DftController
from .materials import matched_colors, phase_views, pretty_label
from .mp_page import MaterialsProjectPage
from .pages import BoundariesPage, DatabasePage, DiagramPage, SensitivityPage, SpeciationPage, SpeciesPage
from .periodic import OverviewPage
from .placeholder import StackedView
from .plots import record_colors
from .session import SUFFIX as SESSION_SUFFIX
from .session import (
    SessionError, read_session, session_selection_policy, session_user_species, sidecar_path, write_session,
)
from .settings_panel import SettingsPanel
from .state import CONCENTRATION_UNITS, LigandSetting, Session, Settings, database_code, python_code
from .sweep import SweepPage
from .tasks import TaskRunner
from .widgets import LoadingOverlay, WheelGuard, cross_fade
from .theme import THEME_MODES, apply_theme

DEBOUNCE_MS = 30


class MainWindow(QMainWindow):
    def __init__(self, symbol: str | None = None, settings: QSettings | None = None,
                 database: Any = None, dataset_name: str | None = None, dataset_path: str | None = None) -> None:
        """``database`` replaces the bundled data, for example a user dataset from :func:`open_dataset`."""
        super().__init__()
        self.dataset_name = dataset_name
        self.dataset_path = dataset_path
        self.setWindowTitle(f"pourbase {__version__}" + (f" — {dataset_name}" if dataset_name else ""))
        self.stored = settings if settings is not None else QSettings("pourbase", "pourbase")
        application = QApplication.instance()
        if application is not None and not hasattr(application, "_pourbase_wheel_guard"):
            application._pourbase_wheel_guard = WheelGuard(application)
            application.installEventFilter(application._pourbase_wheel_guard)
        self.session = Session(database)
        self.database = self.session.database
        self.user_species_path: str | None = None
        self.policy_path: str | None = None
        self.policy = SelectionPolicy.default()
        self._selections: dict | None = None
        self.systems = dict(self.database.available_systems())
        self.tasks = TaskRunner(self)
        cache_root = (Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation)) if settings is None
                      else Path(self.stored.fileName()).parent)
        self.dft = DftController(self.tasks, self.stored, self, cache_dir=cache_root / "materials-project")
        self.calculation: Calculation | None = None
        self.comparison: Any = None
        self._compared_scenario: Any = None
        self._records: dict[str, SpeciesRecord] = {}
        self._reset_range = True
        self._shown_sweep: Any = None
        self._status = ("", False)
        self.theme_mode = str(self.stored.value("theme", "System"))
        self.dark = False

        self._calculate_timer = QTimer(self, singleShot=True, interval=DEBOUNCE_MS, timeout=self.calculate_in_background)
        self._overview_timer = QTimer(self, singleShot=True, interval=DEBOUNCE_MS, timeout=self.screen_in_background)
        self.history = History()
        self.pinned: list[PinnedDiagram] = []
        self._history_timer = QTimer(self, singleShot=True, interval=600, timeout=self._record_history)
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
        self._record_history()

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
        self.overview.ligandToggled.connect(self._overview_ligand_toggled)
        self.panel = SettingsPanel(self.database)
        self.panel.changed.connect(self._settings_changed)
        self.panel.displayChanged.connect(self.refresh_view)
        self.panel.displayChanged.connect(self._history_timer.start)
        self.panel.probeChanged.connect(self.set_probe)
        self.diagram_page = DiagramPage()
        self.diagram_page.diagram.export_menu.extra_actions.append(
            ("Pop out as a window (Ctrl+Shift+D)", self.pop_out_diagram))
        self.diagram_page.probeMoved.connect(self.set_probe)
        self.diagram_page.speciesRequested.connect(lambda: self.views.setCurrentWidget(self.species_page))
        self.species_page = SpeciesPage()
        self.boundaries_page = BoundariesPage()
        self.speciation_page = SpeciationPage()
        self.sensitivity_page = SensitivityPage()
        self.sensitivity_page.sourcesChanged.connect(lambda: self.refresh_view())
        self.compare_page = ComparePage(self.systems)
        self.compare_page.changed.connect(lambda: self.refresh_view())
        self.compare_page.preview.connect(self._compare_preview)
        self.diagram_page.diagram.python_code = self.python_code
        self.compare_page.views[0].python_code = self.python_code
        self.compare_page.views[1].python_code = lambda: self._code_for(
            self.compare_page.right_settings(self.settings))
        self.speciation_page.profile.python_code = self._speciation_code
        self.overview.canvas.python_code = self._overview_code
        self._compare_shown = False
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
            (self.speciation_page, "Speciation"), (self.sensitivity_page, "Sensitivity"),
            (self.compare_page, "Compare"),
            (self.sweep_stack, "Concentration sweep"),
            (self.dft_stack, "DFT comparison"),
        ):
            self.views.addTab(page, title)
        self.views.currentChanged.connect(lambda _index: self.refresh_view())
        self.views_loading = LoadingOverlay(self.views)
        self.compare_loading = LoadingOverlay(self.compare_page)
        self.overview_loading = LoadingOverlay(self.overview.canvas)
        for flag in (self.views_loading, self.compare_loading, self.overview_loading):
            flag.changed.connect(self._show_busy)
        self._wanted: dict[str, Any] = {}
        self._shown: dict[Any, Any] = {}
        system = QSplitter()
        system.addWidget(self.panel)
        self.context_bar = ContextBar()
        right = QWidget()
        column = QVBoxLayout(right)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        column.addWidget(self.context_bar)
        column.addWidget(self.views, 1)
        system.addWidget(right)
        system.setStretchFactor(1, 1)
        system.setCollapsible(0, False)
        system.setSizes([self.panel.minimumWidth(), 10_000])
        self.pages = QTabWidget()
        self.pages.setDocumentMode(True)
        self.pages.addTab(self.overview, "Periodic table")
        self.pages.addTab(system, "System")
        self.pages.addTab(self.database_page, "Database")
        self.pages.setCornerWidget(self._masthead(), Qt.TopLeftCorner)
        self.pages.setCornerWidget(self._search_button(), Qt.TopRightCorner)
        self.pages.currentChanged.connect(self._page_changed)
        self.setCentralWidget(self.pages)
        self.status_label = QLabel()
        self.statusBar().addWidget(self.status_label, 1)
        for combo in self.findChildren(QComboBox):
            combo.setMaxVisibleItems(15)
            combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def _masthead(self) -> QWidget:
        logo = QLabel()
        logo.setPixmap(logo_pixmap(22, self.devicePixelRatioF()))
        name = QLabel("pourbase")
        font = name.font()
        font.setPointSizeF(font.pointSizeF() * 1.25)
        font.setWeight(QFont.Normal)
        name.setFont(font)
        masthead = QWidget()
        layout = QHBoxLayout(masthead)
        layout.setContentsMargins(10, 4, 18, 4)
        layout.setSpacing(7)
        layout.addWidget(logo)
        layout.addWidget(name)
        return masthead

    def _state(self):
        return (self.settings, self.display)

    def _record_history(self) -> None:
        if self._dragging():
            self._history_timer.start()  # record once the slider is released
            return
        self.history.record(self._state())
        self._update_history_actions()

    def _update_history_actions(self) -> None:
        if hasattr(self, "undo_action"):
            self.undo_action.setEnabled(self.history.can_undo())
            self.redo_action.setEnabled(self.history.can_redo())

    def undo(self) -> None:
        self._record_history()  # a change still waiting to be recorded becomes the step undone
        if self.history.can_undo():
            self._restore(self.history.undo(), "Undo")

    def redo(self) -> None:
        if self.history.can_redo():
            self._restore(self.history.redo(), "Redo")

    def _restore(self, state, verb: str) -> None:
        settings, display = state
        self._history_timer.stop()
        self.panel.set_settings(settings)
        self.panel.set_display(display)
        self._settings_changed(False)
        self._history_timer.stop()
        self.refresh_view()
        self._update_history_actions()
        self._set_status(verb)

    def _show_overlay(self, calculation: Calculation) -> None:
        """Draw the second element's boundaries over the diagram, calculating them off the UI thread."""
        view = self.diagram_page.diagram
        symbol = self.display.overlay_symbol
        if not symbol or symbol == self.settings.symbol:
            self._wanted.pop("overlay", None)
            view.show_overlay(None, self.display)
            return
        if view.preview_mode:
            return  # the overlay follows when the slider is released
        scenario = calculation.scenario
        molar = scenario.concentration_conversion.molar_concentration
        settings = copy.deepcopy(self.settings)
        settings.symbol = symbol
        settings.concentration = express_concentration(symbol, molar, settings.concentration_unit,
                                                       solution_density_kg_L=settings.solution_density_kg_L)
        second = replace(settings.scenario(), pH_points=scenario.pH_points, eh_points=scenario.eh_points,
                         pH_min=scenario.pH_min, pH_max=scenario.pH_max, eh_min_V=scenario.eh_min_V,
                         eh_max_V=scenario.eh_max_V)
        cached = self.session.cached("calculation", second)
        if cached is not None:
            self._wanted.pop("overlay", None)
            view.show_overlay(cached.diagram, self.display)
            return
        key = (second, id(self.session))
        if self._wanted.get("overlay") == key:
            return
        self._wanted["overlay"] = key
        session = self.session
        self.tasks.submit("overlay", key, lambda _progress: session.calculate(second))

    def pop_out_diagram(self) -> None:
        """Keep the current diagram in its own window; its probe follows the probes of all other diagrams."""
        calculation = self.calculation
        if calculation is None:
            return
        if calculation.diagram.stable_species_index.shape != (self.settings.eh_points, self.settings.pH_points):
            self._set_status("The diagram is still being calculated; pop it out when it is complete")
            return
        context = self.context_bar.text()
        chips = self.context_bar.chips
        title = " · ".join(text for text in (chips["element"].text(), chips["model"].text()) if text) \
            or self.settings.symbol
        window = PinnedDiagram(calculation, self.display, title, context, self.dark, self)
        window.probeMoved.connect(self._pinned_probe_moved)
        window.destroyed.connect(lambda _object=None, window=window: self._forget_pinned(window))
        offset = 30 * (len(self.pinned) % 10)
        window.move(self.geometry().topLeft() + QPoint(80 + offset, 80 + offset))
        self.pinned.append(window)
        window.set_probe(self.settings.probe_pH, self.settings.probe_eh_V)
        window.show()
        self._set_status(f"Popped out {title}; probes in all diagrams move together")

    def _pinned_probe_moved(self, pH: float, eh_V: float) -> None:
        self.set_probe(pH, eh_V)
        self.diagram_page.diagram.set_probe(pH, eh_V)

    def _forget_pinned(self, window) -> None:
        if window in self.pinned:
            self.pinned.remove(window)

    def close_pinned(self) -> None:
        for window in list(self.pinned):
            window.close()

    def arrange_pinned(self) -> None:
        """Tile the popped-out diagrams over the screen of the main window."""
        if not self.pinned:
            return
        area = self.screen().availableGeometry()
        count = len(self.pinned)
        columns = math.ceil(math.sqrt(count))
        rows = math.ceil(count / columns)
        width, height = area.width() // columns, area.height() // rows
        for index, window in enumerate(self.pinned):
            row, column = divmod(index, columns)
            window.setGeometry(area.x() + column * width, area.y() + row * height, width, height - 30)
            window.raise_()

    def _search_button(self) -> QWidget:
        from PySide6.QtWidgets import QPushButton

        button = QPushButton("Search elements, species, sources and commands (Ctrl+K)")
        button.setToolTip("Find an element, species, source or command")
        button.setFocusPolicy(Qt.NoFocus)
        button.clicked.connect(self.show_search)
        corner = QWidget()
        layout = QHBoxLayout(corner)
        layout.setContentsMargins(6, 3, 8, 3)
        layout.addWidget(button)
        self.search_button = button
        return corner

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu("&File")
        for text, slot, shortcut in (
            ("Open session…", self.open_session, QKeySequence.Open),
            ("Save session…", self.save_session, QKeySequence.SaveAs),
            (None, None, None),
            ("Export figure…", self.export_figure, QKeySequence.Save),
            ("Export grid as CSV…", self.export_grid, None),
            ("Copy Python code", self.copy_python, None),
            (None, None, None),
            ("Open dataset (CSV or SQLite)…", self.open_dataset, None),
            ("Load own species (CSV)…", self.open_user_species, None),
            ("Remove own species", lambda: self.load_user_species(None), None),
            ("Load selection policy (TOML)…", self.open_policy, None),
            ("Use the default selection policy", lambda: self.load_policy(None), None),
            (None, None, None),
            ("Quit", self.close, QKeySequence.Quit),
        ):
            if text is None:
                menu.addSeparator()
                continue
            action = menu.addAction(text, slot)
            if shortcut is not None:
                action.setShortcut(shortcut)
        edit = self.menuBar().addMenu("&Edit")
        self.undo_action = edit.addAction("Undo", self.undo)
        self.undo_action.setShortcut(QKeySequence.Undo)
        self.redo_action = edit.addAction("Redo", self.redo)
        self.redo_action.setShortcuts([QKeySequence.Redo, QKeySequence("Ctrl+Shift+Z")])
        self._update_history_actions()
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
        view.addSeparator()
        view.addAction("Pop out diagram", self.pop_out_diagram).setShortcut("Ctrl+Shift+D")
        view.addAction("Arrange popped-out diagrams", self.arrange_pinned)
        view.addAction("Close popped-out diagrams", self.close_pinned)
        tools = self.menuBar().addMenu("&Tools")
        search = tools.addAction("Search…", self.show_search)
        search.setShortcuts([QKeySequence("Ctrl+K"), QKeySequence.Find])
        tools.addSeparator()
        tools.addAction("Sources behind this diagram…", self.show_sources)
        tools.addAction("Compare selection policies…", self.compare_policies)
        tools.addSeparator()
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
        if settings.symbol not in self.systems:
            settings = Settings()
            if settings.symbol not in self.systems:
                settings.symbol = next(iter(self.systems))
        return settings

    def closeEvent(self, event) -> None:
        self.stored.setValue("settings", json.dumps(self.settings.to_dict()))
        self.stored.setValue("geometry", self.saveGeometry())
        self.stored.setValue("theme", self.theme_mode)
        self.tasks.shutdown()
        super().closeEvent(event)


    def _overview_ligand_toggled(self, ligand_id: str, checked: bool) -> None:
        """A ligand reservoir switched on the periodic table: the same setting as in the element view."""
        settings = self.settings
        if ligand_id:
            settings.ligands.setdefault(ligand_id, LigandSetting()).enabled = checked
            if checked:
                settings.use_ligands = True
        else:
            settings.use_ligands = checked
        self.panel.set_settings(settings)
        self._settings_changed(False)

    def _settings_changed(self, reset_range: bool) -> None:
        if self.pages.currentIndex() == 0:  # the periodic table is screened again when it is shown
            self._overview_timer.start()
        else:
            self._overview_stale = True
        self._reset_range |= reset_range
        self._history_timer.start()
        self.pages.setTabText(1, self.systems.get(self.settings.symbol, self.settings.symbol))
        if self._dragging():
            self._preview()
        self._calculate_timer.start()

    @staticmethod
    def _dragging() -> bool:
        """True while a mouse button is held, for example on a slider being dragged."""
        return QApplication.mouseButtons() != Qt.NoButton

    def _preview(self) -> None:
        """Draw a coarse diagram at once while a slider moves; the full grid follows on release."""
        scenario = self.settings.scenario()
        coarse = replace(scenario, pH_points=max(scenario.pH_points // 4, 41),
                         eh_points=max(scenario.eh_points // 4, 41))
        try:
            calculation = calculate(coarse, self.session.database)  # previews bypass the result cache
        except Exception:
            return
        self.calculation = calculation
        self._previewing = True
        views = (self.diagram_page.diagram, *self.compare_page.views)
        for view in views:
            view.preview_mode = True
        try:
            self.refresh_view()
        finally:
            self._previewing = False
            for view in views:
                view.preview_mode = False

    def _compare_preview(self) -> None:
        """While the comparison slider moves, draw the right diagram on a coarse grid at once."""
        page = self.compare_page
        if not self._dragging() or self.calculation is None or page.calculations is None:
            return
        scenario = page.right_settings(self.settings).scenario()
        coarse = replace(scenario, pH_points=max(scenario.pH_points // 4, 41),
                         eh_points=max(scenario.eh_points // 4, 41))
        try:
            right = calculate(coarse, self.session.database)
        except Exception:
            return
        for view in page.views:
            view.preview_mode = True
        try:
            page.show_calculations(self.calculation, right, self.display, False,
                                   (self.settings.probe_pH, self.settings.probe_eh_V))
        finally:
            for view in page.views:
                view.preview_mode = False

    def recalculate(self) -> None:
        settings = self.settings
        self.pages.setTabText(1, self.systems.get(settings.symbol, settings.symbol))
        start = time.perf_counter()
        try:
            calculation = self.session.calculate(settings.scenario())
        except Exception as error:
            self._show_calculation_error(error)
            return
        self._apply_calculation(calculation, time.perf_counter() - start)

    def calculate_in_background(self) -> None:
        """Calculate the current settings off the UI thread; the views grey out while it runs."""
        if self._dragging():
            self._calculate_timer.start(120)  # the full grid waits until the slider is released
            return
        scenario = self.settings.scenario()
        key = (scenario, id(self.session))
        if self.session.cached("calculation", scenario) is not None:
            self._wanted.pop("calculate", None)
            self.views_loading.stop()
            self.recalculate()
            return
        self._wanted["calculate"] = key
        self.pages.setTabText(1, self.systems.get(self.settings.symbol, self.settings.symbol))
        self.views_loading.start()
        session = self.session

        def work(_progress):
            start = time.perf_counter()
            try:
                return session.calculate(scenario), time.perf_counter() - start
            except Exception as error:  # reported on the UI thread
                return error, 0.0

        self.tasks.submit("calculate", key, work)

    def screen_in_background(self) -> None:
        """Screen the periodic table off the UI thread; the table greys out while it runs."""
        arguments = self._screen_arguments()
        key = (tuple(sorted(arguments.items())), id(self.session))
        if self.session.cached("screen", key[0]) is not None:
            self.update_overview()
            return
        self._wanted["screen"] = key
        self.overview_loading.start()
        session = self.session
        self.tasks.submit("screen", key, lambda _progress: session.screen(**arguments))

    def _apply_calculation(self, calculation: Calculation, elapsed: float) -> None:
        self.calculation = calculation
        self.panel.set_concentration_note(calculation.concentration.molar_concentration,
                                          calculation.concentration.log10_standard_activity)
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
        own = sum(item.gibbs_status.value == "user_supplied" for item in system.species)
        if own:
            parts.append(f"{own} own species in use")
        if self.policy_path:
            parts.append(f"selection policy: {self.policy.name}")
        text = "; ".join(parts)
        return text if not (missing or calculation.fallback_species) else f"~{text}"

    def _show_calculation_error(self, error: Exception) -> None:
        self.calculation = None
        name = self.systems.get(self.settings.symbol, self.settings.symbol)
        if isinstance(error, IncompleteSystemError):
            self.diagram_page.show_message(
                f"{name} has documented evidence gaps",
                f"{html.escape(str(error))}.<br><br>Species without a recommended Gibbs energy can be "
                "left out for an exploratory diagram, or replaced by labelled Materials Project 300 K "
                "estimates where those exist.",
                ("Leave these species out", lambda: self.panel.require_complete.setChecked(False)),
                glyph="!",
            )
        else:
            self.diagram_page.show_message("The diagram cannot be calculated",
                                           html.escape(f"{type(error).__name__}: {error}"), glyph="!")
        self._set_status(f"!{name}: no diagram for the current settings")
        self.refresh_view()

    def set_probe(self, pH: float, eh_V: float) -> None:
        self.panel.set_probe(pH, eh_V)
        for window in self.pinned:  # every popped-out diagram aims at the same point
            window.set_probe(pH, eh_V)
        self._update_probe()
        current = self.views.currentWidget()
        if current is self.speciation_page:
            self._show_speciation()
        elif current is self.dft_stack and self.comparison is not None:
            self.dft_page.set_probe(pH, eh_V)

    def _update_probe(self) -> None:
        if getattr(self, "_previewing", False):
            self.diagram_page.diagram.set_probe(self.settings.probe_pH, self.settings.probe_eh_V)
            return
        if self.calculation is None:
            return
        settings = self.settings
        try:
            probe = self.calculation.probe(settings.probe_pH, settings.probe_eh_V)
        except ValueError as error:
            self.diagram_page.probe.setHtml(html.escape(str(error)))
            return
        dft_phase = None
        if self.comparison is not None and self._compared_scenario == self._comparison_scenario():
            try:
                dft_phase = pretty_label(self.comparison.materials_project.phase_at(probe.pH, probe.eh_V).label)
            except ValueError:
                pass
        margin = None
        if not self.calculation.is_mass_balance:
            try:
                margin = stability_margin(self.calculation.diagram, probe.pH, probe.eh_V,
                                          self.display.assumed_uncertainty_kJ_mol * 1000)
            except ValueError:
                margin = None
        self.diagram_page.show_probe(probe, self._record(probe.species.record_id), dft_phase, margin)

    def _record(self, record_id: str) -> SpeciesRecord | None:
        return self._records_for([record_id]).get(record_id)

    def _records_for(self, record_ids) -> dict[str, SpeciesRecord]:
        missing = [item for item in record_ids if item not in self._records]
        if missing:
            self._records.update({item.record_id: item for item in self.session.database.species_records(missing)})
        return {item: self._records[item] for item in record_ids if item in self._records}

    def open_element(self, symbol: str) -> None:
        screen = self.overview.canvas.screen
        settings = self.settings
        settings.symbol = symbol
        if screen is not None:
            settings.probe_pH, settings.probe_eh_V = screen.pH, screen.potential_V_vs_SHE
        self.panel.set_settings(settings)
        self._history_timer.start()
        self.pages.setCurrentIndex(1)
        self.views.setCurrentWidget(self.diagram_page)
        self.pages.setTabText(1, self.systems.get(symbol, symbol))
        if self.session.cached("calculation", settings.scenario()) is None:
            # never show the previous element's diagram under the new element's name
            self.diagram_page.show_message(self.systems.get(symbol, symbol), "Calculating the diagram…", glyph="…")
        # the page appears at once; the diagram follows in stages: a coarse preview on the next event-loop
        # pass, then the full grid from the background, which fades in
        QTimer.singleShot(0, self._open_element_content)

    def _open_element_content(self) -> None:
        scenario = self.settings.scenario()
        if self.session.cached("calculation", scenario) is not None:
            self.recalculate()
            return
        coarse = replace(scenario, pH_points=max(scenario.pH_points // 4, 41),
                         eh_points=max(scenario.eh_points // 4, 41))
        try:
            self.calculation = calculate(coarse, self.session.database)
        except Exception as error:
            self._show_calculation_error(error)
            return
        self._reset_range = True
        view = self.diagram_page.diagram
        view.prepare_labels = False
        try:
            self.refresh_view()
        finally:
            view.prepare_labels = True
        self.calculate_in_background()

    def _page_changed(self, index: int) -> None:
        if index == 0:
            self._overview_stale = False
            self.screen_in_background()
        elif index == 1:
            self.dft.warm_up()
        elif index == 2:
            self.database_page.load()

    def _screen_arguments(self) -> dict:
        settings = self.settings
        return dict(**self.overview.conditions(), concentration=settings.concentration,
                    concentration_unit=settings.concentration_unit,
                    solution_density_kg_L=settings.solution_density_kg_L,
                    allow_incomplete=settings.allow_incomplete, energy_policy=settings.energy_policy.value,
                    ligands=settings.ligand_activities())

    def update_overview(self) -> None:
        settings = self.settings
        try:
            screen = self.session.screen(**self._screen_arguments())
        except Exception as error:
            self._set_status(f"!{type(error).__name__}: {error}")
            return
        self.overview.set_ligands(self.database.available_ligands(), settings)
        canvas = self.overview.canvas
        canvas.selected = settings.symbol
        canvas.show_screen(screen)
        self.overview.note.setText(
            f"Metal concentration {settings.concentration:g} {CONCENTRATION_UNITS[settings.concentration_unit]}"
            + ("" if settings.allow_incomplete else ", a Gibbs energy required for every species")
            + (f", {len(settings.ligand_activities())} ligand reservoir(s)" if settings.ligand_activities() else "")
            + (", MP estimates in use" if settings.use_mp_fallbacks else "")
            + ". These follow the System settings."
        )


    def _unchanged(self, page: Any, *signature: Any) -> bool:
        """True when ``page`` already shows exactly this content, so it need not be redrawn."""
        key = (id(self.calculation), repr(self.display), self.dark, id(self.session), *signature)
        if self._shown.get(page) == key:
            return True
        self._shown[page] = key
        return False

    def update_context(self) -> None:
        """State in the context bar what the shown result is calculated from."""
        bar, settings, display, calculation = self.context_bar, self.settings, self.display, self.calculation
        panel = self.panel
        chips = bar.chips
        name = self.systems.get(settings.symbol, settings.symbol)
        overlay = display.overlay_symbol if display.overlay_symbol != self.settings.symbol else ""
        if overlay:
            name = f"{name} + {overlay} dashed"
        chips["element"].configure(name, "The element of the diagram, and a second element drawn over it. "
                                   "Click to choose another.",
                                   action=lambda: panel.reveal(panel.symbol), dark=self.dark)
        if calculation is not None:
            conversion = calculation.concentration
            if calculation.scenario.mode is Mode.MASS_BALANCE:
                text = f"Mass balance · c_T = {power_of_ten(math.log10(conversion.molar_concentration))} M"
                tip = ("Closed system: this total metal concentration is shared between dissolved species and "
                       "at most one precipitating solid.")
            else:
                text = f"Fixed activity · a = {power_of_ten(conversion.log10_standard_activity)}"
                tip = "Every dissolved species of the element has this activity, as in Pourbaix's atlas."
            preview = calculation.diagram.stable_species_index.shape != (settings.eh_points, settings.pH_points)
            chips["model"].configure(text + (" · preview" if preview else ""),
                                     tip + (" A coarse preview is shown while a slider moves." if preview else "")
                                     + " Click to change the model or concentration.",
                                     action=lambda: panel.reveal(panel.concentration), dark=self.dark)
        own = len(getattr(self.session.database, "user_species", ()) or ())
        if self.dataset_name:
            data, tip, tone = f"Dataset: {self.dataset_name}", "This window calculates with your dataset only.", ACCENT
        else:
            data, tip, tone = "Bundled data", f"The bundled database, release {self.database.data_version}.", NEUTRAL
        if own:
            data += f" + {own} own species"
            tip += f" {own} species from {Path(self.user_species_path).name} are added or replace bundled ones."
            tone = ACCENT
        chips["data"].configure(data, tip, tone, dark=self.dark, menu=[
            ("Sources behind this diagram…", self.show_sources),
            ("Load own species (CSV)…", self.open_user_species), ("Remove own species", lambda: self.load_user_species(None)),
            ("Open a dataset in a new window…", self.open_dataset)])
        policy_text = (f"Policy: {Path(self.policy_path).name}" if self.policy_path else "Default selection policy")
        chips["policy"].configure(
            policy_text,
            ("The selection policy chooses one recommended value per species from the reported values. "
             + (f"{self.policy.name} ({self.policy.fingerprint})." if self.policy_path else "The bundled default.")),
            ACCENT if self.policy_path else NEUTRAL, dark=self.dark, menu=[
                ("Load selection policy (TOML)…", self.open_policy), ("Use the default selection policy",
                                                                     lambda: self.load_policy(None)),
                ("Compare selection policies…", self.compare_policies)])
        ligands = settings.ligand_activities()
        names = {item.ligand_id: item.name for item in self.database.available_ligands()}
        ligand_names = [names.get(item.ligand_id, item.ligand_id).split(" (")[0] for item in ligands]
        chips["ligands"].configure(
            (("Ligands: " + ", ".join(ligand_names)) if len(ligand_names) <= 2 else f"Ligands: {len(ligand_names)} on")
            if ligands else "No ligands",
            (("Buffered ligand reservoirs whose complexes take part in the calculation: " + ", ".join(ligand_names) + ".")
             if ligands else "No ligand reservoirs are switched on.") + " Click to edit them.",
            ACCENT if ligands else NEUTRAL, action=lambda: panel.reveal(panel.ligands_section), dark=self.dark)
        missing = len(calculation.diagram.system.missing_gibbs) if calculation is not None else 0
        chips["omitted"].configure(
            f"{missing} species left out" if missing else "",
            f"{missing} species of this system have no recommended Gibbs energy and are left out of the "
            "calculation. Click to see them in the Species tab.", WARNING,
            action=lambda: self.views.setCurrentWidget(self.species_page), dark=self.dark)
        extras = []  # (text, control that edits it)
        if display.boltzmann:
            extras.append((f"blend ε = {display.blend_width_kJ_mol:g} kJ/mol", panel.boltzmann))
        if display.uncertainty:
            extras.append((f"hatching within {display.uncertainty_sigma:g}σ", panel.uncertainty))
        if display.potential_scale != "SHE":
            extras.append((f"E vs {display.potential_scale.split(' (')[0]}", panel.potential_scale))
        view_text = ", ".join(text for text, _control in extras)
        control = extras[0][1] if extras else None
        chips["view"].configure(view_text[:1].upper() + view_text[1:],
                                "Display options that change how the result is drawn, not what is calculated. "
                                "Click to edit them.", action=lambda: control and panel.reveal(control),
                                dark=self.dark)

    def refresh_view(self, reset_range: bool = False) -> None:
        self.update_context()
        current = self.views.currentWidget()
        calculation = self.calculation
        if reset_range or self._reset_range:
            self._shown.pop(current, None)
        if current in (self.diagram_page, self.species_page, self.boundaries_page) and calculation is not None \
                and self._unchanged(current, self.policy.fingerprint):
            if current is self.diagram_page:
                self._update_probe()
            return
        if current is self.diagram_page and calculation is not None:
            self.diagram_page.show_calculation(calculation, self.display, reset_range or self._reset_range)
            self._show_overlay(calculation)
            self._reset_range = False
            self._update_probe()
        elif current is self.species_page:
            if calculation is None:
                self.species_page.clear()
            else:
                system = calculation.diagram.system
                ids = [item.record_id for item in system.species] + [item.record_id for item in system.excluded]
                self.species_page.show_calculation(calculation, self._records_for(ids), self._policy_selections(),
                                                   self.policy.name)
        elif current is self.boundaries_page:
            self._show_boundaries()
        elif current is self.speciation_page:
            self._show_speciation()
        elif current is self.sensitivity_page:
            self._show_sensitivity()
        elif current is self.compare_page:
            self._show_compare(reset_range)
        elif current is self.sweep_stack:
            self.request_sweep()
        elif current is self.dft_stack:
            self._show_dft(reset_range)

    def _set_mode(self, mode: Mode) -> None:
        self.panel.mode.setCurrentIndex(self.panel.mode.findData(mode.value))
        self.recalculate()

    def _show_sensitivity(self) -> None:
        """Map where the stable species depends on the choice between published values."""
        page = self.sensitivity_page
        calculation = self.calculation
        if self.settings.mode == Mode.MASS_BALANCE.value:
            page.show_message("Sensitivity is calculated for fixed-activity diagrams",
                              "Switch to fixed activity to see where the choice between published values changes "
                              "the stable species.", ("Switch to fixed activity", lambda: self._set_mode(Mode.FIXED_ACTIVITY)))
            return
        if calculation is None or calculation.diagram.stable_species_index.shape != (self.settings.eh_points,
                                                                                    self.settings.pH_points):
            return  # wait for the full grid
        database = self.session.database
        key = (id(calculation), id(database))
        cached = getattr(self, "_sensitivity_results", None)
        if cached is not None and cached[0] == key:
            shown = (key, page.critical_only())
            if getattr(self, "_sensitivity_key", None) != shown:
                self._sensitivity_key = shown
                page.show_result(cached[1][page.critical_only()], cached[2], cached[3])
            return
        if self._wanted.get("sensitivity") == key:
            return
        diagram = calculation.diagram
        self._wanted["sensitivity"] = key
        page.show_message(self.systems.get(self.settings.symbol, self.settings.symbol),
                          "Comparing the diagram over the eligible published values…", glyph="…")

        def work(progress):
            from ..sensitivity import selection_sensitivity

            def part(offset):
                return lambda fraction: progress(0.5 * (offset + fraction))

            results = {critical: selection_sensitivity(diagram, database.selections, samples=300,
                                                       classes={"A", "B", "C"} if critical else None,
                                                       progress=part(index))
                       for index, critical in enumerate((False, True))}
            return results, diagram, database.selections

        self.tasks.submit("sensitivity", key, work)

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
        if kind == "overlay":
            if self._wanted.get(kind) != key:
                return
            del self._wanted[kind]
            if error or result is None:
                self._set_status(f"The second element cannot be calculated: {error}")
                return
            if self.calculation is not None and self.views.currentWidget() is self.diagram_page:
                self.diagram_page.diagram.show_overlay(result.diagram, self.display)
            return
        if kind == "sensitivity":
            if self._wanted.get(kind) != key:
                return
            del self._wanted[kind]
            if error or result is None:
                self.sensitivity_page.show_message("The sensitivity cannot be calculated", html.escape(error or ""),
                                                   glyph="!")
                return
            self._sensitivity_results = (key, *result)
            self._sensitivity_key = None
            self._show_sensitivity()
            return
        if kind in ("calculate", "screen", "compare"):
            if self._wanted.get(kind) != key:
                return  # superseded by a newer request
            del self._wanted[kind]
            if kind == "calculate":
                coarse = (self.calculation is not None and self.calculation.diagram.stable_species_index.shape
                          != (self.settings.eh_points, self.settings.pH_points))
                if self.views_loading.isVisible() or coarse:  # fade after a wait or over a coarse picture
                    cross_fade(self.views.currentWidget())
                self.views_loading.stop()
                calculation, elapsed = result if result is not None else (RuntimeError(error), 0.0)
                if isinstance(calculation, Exception):
                    self._show_calculation_error(calculation)
                else:
                    self._apply_calculation(calculation, elapsed)
            elif kind == "screen":
                if self.overview_loading.isVisible():
                    cross_fade(self.overview.canvas)
                self.overview_loading.stop()
                self.update_overview()
            else:
                if self.compare_loading.isVisible():
                    cross_fade(self.compare_page)
                self.compare_loading.stop()
                self._show_compare()
            return
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
        scenario = self._comparison_scenario()
        if self.settings.mode == Mode.MASS_BALANCE.value:
            notes.append("MP diagrams use fixed activities, so the experimental panel shows the "
                         "fixed-activity diagram at the same concentration.")
        if scenario.ligands:
            notes.append("MP diagrams are ligand-free; the experimental panel includes the enabled ligands.")
        try:
            self.comparison = self.dft.compare(self.session.calculate(scenario).diagram, entries)
            self._compared_scenario = scenario
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

    def _show_compare(self, reset_range: bool = False) -> None:
        page = self.compare_page
        if self.calculation is None:
            page.show_message("No diagram", "The comparison appears once the diagram is calculated.")
            return
        if not self._compare_shown:
            page.symbol.blockSignals(True)
            page.symbol.setCurrentIndex(max(page.symbol.findData(self.settings.symbol), 0))
            page.symbol.blockSignals(False)
        scenario = page.right_settings(self.settings).scenario()
        if self.session.cached("calculation", scenario) is None and page.calculations is not None:
            key = (scenario, id(self.session))
            self._wanted["compare"] = key
            self.compare_loading.start()
            session = self.session

            def work(_progress):
                try:
                    return session.calculate(scenario)
                except Exception as error:
                    return error

            self.tasks.submit("compare", key, work)
            return
        try:
            right = self.session.calculate(scenario)
        except Exception as error:
            page.show_message("The second diagram cannot be calculated",
                              html.escape(f"{type(error).__name__}: {error}"), glyph="!")
            return
        same = (page.calculations is not None and page.calculations[0] is self.calculation
                and page.calculations[1] is right and repr(page.display) == repr(self.display))
        if same and not reset_range and self._compare_shown:
            return
        page.show_calculations(self.calculation, right, self.display, reset_range or not self._compare_shown,
                               (self.settings.probe_pH, self.settings.probe_eh_V))
        self._compare_shown = True

    def save_session(self) -> None:
        path = self._save_path("Save session", f"pourbase-{self.settings.symbol.lower()}{SESSION_SUFFIX}",
                               f"pourbase session (*{SESSION_SUFFIX} *.json)")
        if path:
            write_session(path, self.settings, self.display, self.sweep_page.settings(), self.user_species_path,
                          self.policy_path)
            self._set_status(f"Saved the session to {path}")

    def open_user_species(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load own species", "", "CSV (*.csv);;All files (*)")
        if path:
            self.load_user_species(path)

    def _rebuild_database(self, policy_path: str | None, user_species_path: str | None, title: str) -> bool:
        """Calculate with a selection policy file and a user-species file over the bundled data."""
        try:
            policy = SelectionPolicy.load(policy_path) if policy_path else SelectionPolicy.default()
            database = with_policy(self.database, policy) if policy_path else self.database
            if user_species_path:
                database = with_user_species(database, user_species_path)
        except (OSError, ValueError, KeyError) as error:
            QMessageBox.warning(self, title, str(error))
            return False
        self.session = Session(database)
        self.policy, self.policy_path, self.user_species_path = policy, policy_path, user_species_path
        self._selections = None
        self._records = {}
        self.database_page.set_database(database)
        self.recalculate()
        self.update_overview()
        return True

    def load_user_species(self, path: str | None) -> bool:
        """Calculate with the species of a user CSV file, or with the bundled data alone for None."""
        if not self._rebuild_database(self.policy_path, path, "Load own species"):
            return False
        count = len(self.session.database.user_species) if path else 0
        self._set_status(f"Calculating with {count} own species from {Path(path).name}" if path
                         else "Calculating without own species")
        return True

    def open_dataset(self, path: str | None = None) -> Any:
        """Open a dataset on its own in a new window; returns the window, or None."""
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self, "Open dataset", "",
                                                  "Datasets (*.csv *.sqlite *.db);;All files (*)")
        if not path:
            return None
        try:
            database = open_dataset(path)
        except (OSError, ValueError, DatabaseSchemaError) as error:
            QMessageBox.warning(self, "Open dataset", str(error))
            return None
        window = MainWindow(settings=self.stored, database=database, dataset_name=Path(path).name,
                            dataset_path=str(Path(path).resolve()))
        window.show()
        self._dataset_windows = [*getattr(self, "_dataset_windows", []), window]
        return window

    def open_policy(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load selection policy", "", "TOML (*.toml);;All files (*)")
        if path:
            self.load_policy(path)

    def load_policy(self, path: str | None) -> bool:
        """Calculate with the recommendations of a selection-policy file, or the default for None."""
        if not self._rebuild_database(path, self.user_species_path, "Load selection policy"):
            return False
        self._set_status(f"Calculating with the selection policy {self.policy.name} ({self.policy.fingerprint})"
                         if path else "Calculating with the default selection policy")
        return True

    def _policy_selections(self) -> dict:
        if self._selections is None:
            # the database derives its recommendations with the active policy and caches them
            database = self.session.database
            self._selections = (database.selections if getattr(database, "policy", None) is self.policy
                                else select(self.database, self.policy))
        return self._selections

    def open_session(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open session", "",
                                              f"pourbase session (*{SESSION_SUFFIX} *.json);;All files (*)")
        if path:
            self.load_session(path)

    def load_session(self, path: str) -> bool:
        """Apply a saved session; returns False and reports the problem when it cannot be read."""
        try:
            settings, display, sweep = read_session(path)
        except SessionError as error:
            QMessageBox.warning(self, "Open session", str(error))
            return False
        if settings.symbol not in self.systems:
            settings.symbol = self.settings.symbol
        user_species = session_user_species(path)
        user_species = user_species if user_species and Path(user_species).is_file() else None
        policy_path = session_selection_policy(path)
        policy_path = policy_path if policy_path and Path(policy_path).is_file() else None
        if (user_species, policy_path) != (self.user_species_path, self.policy_path):
            self._rebuild_database(policy_path, user_species, "Open session")
        self.panel.set_settings(settings)
        self.panel.set_display(display)
        self.sweep_page.set_settings(sweep)
        self._reset_range = True
        self.pages.setCurrentIndex(1)
        self.recalculate()
        self.update_overview()
        self._record_history()
        self._set_status(f"Opened the session {Path(path).name}")
        return True

    def _comparison_scenario(self):
        """The experimental scenario compared with MP: the current one at fixed activity."""
        scenario = self.settings.scenario()
        if scenario.mode is Mode.MASS_BALANCE:
            scenario = replace(scenario, mode=Mode.FIXED_ACTIVITY, davies_ionic_strength_mol_L=None)
        return scenario

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
            blend_width_kJ_mol=display.blend_width_kJ_mol if fixed and display.boltzmann else None,
        )
        written = save_figure(figure, path)
        session = write_session(sidecar_path(written), self.settings, self.display, self.sweep_page.settings(),
                                self.user_species_path, self.policy_path)
        self._set_status(f"Wrote {written} and its settings to {session.name}")

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
        QGuiApplication.clipboard().setText(self.python_code())
        self._set_status("Copied the equivalent Python code to the clipboard")

    def show_search(self) -> None:
        from .search import SearchDialog

        dialog = SearchDialog(self._search_entries(), self)
        dialog.field.setFocus()
        dialog.exec()

    def _search_entries(self) -> list:
        """Every element, species, source and menu command, built once per database."""
        from ..citations import group_sources
        from .search import Entry, normalize

        cached = getattr(self, "_search_cache", None)
        if cached is not None and cached[0] is self.session.database:
            return cached[1]
        database = self.session.database
        entries = []
        for symbol, name in self.systems.items():
            entries.append(Entry("Element", name, "Element: open its diagram", normalize(f"{name} {symbol} element"),
                                 lambda symbol=symbol: self.open_element(symbol)))
        rows = database._rows("SELECT record_id, symbol, species, formula_ascii, phase, phase_detail FROM species")
        names = {}
        for row in rows:
            system = self.systems.get(row["symbol"], row["symbol"])
            detail = f"Species in {system}: {(row['phase_detail'] or row['phase']).strip('()')}"
            names[row["record_id"]] = (row["species"], row["symbol"])
            entries.append(Entry("Species", row["species"], detail,
                                 normalize(f"{row['species']} {row['formula_ascii']} {row['phase_detail']} {system} "
                                           f"{row['record_id']}"),
                                 lambda record=row["record_id"], symbol=row["symbol"]: self.show_species(symbol, record)))
        pairs = []
        for row in database._rows("SELECT record_id, source_id FROM reported_thermochemistry WHERE source_id IS NOT NULL"):
            if row["record_id"] in names:
                pairs.append((database.source(row["source_id"]), row["record_id"]))
        for publication in group_sources(pairs):
            first = publication.species[0]
            species = [names[record][0] for record in publication.species if record in names]
            entries.append(Entry("Source", publication.citation[:110],
                                 f"Source for {len(species)} species, e.g. {', '.join(species[:3])}",
                                 normalize(" ".join(publication.citations)),
                                 lambda record=first: self.show_species(names[record][1], record)))

        def actions(menu, prefix=""):
            for action in menu.actions():
                if action.menu():
                    yield from actions(action.menu(), prefix + action.menu().title().replace("&", "") + " → ")
                elif action.text() and not action.isSeparator() and action.text() != "Search…":
                    yield prefix, action
        for prefix, action in actions(self.menuBar()):
            label = action.text().replace("&", "")
            entries.append(Entry("Command", label, f"Command: {prefix}{label}", normalize(f"{prefix} {label}"),
                                 action.trigger))
        self._search_cache = (database, entries)
        return entries

    def show_species(self, symbol: str, record_id: str) -> None:
        """Open an element with one species selected in the Species tab."""
        self.species_page.pending_record = record_id
        if symbol != self.settings.symbol or self.pages.currentIndex() != 1:
            self.open_element(symbol)
        self.views.setCurrentWidget(self.species_page)
        self.refresh_view()

    def show_sources(self) -> None:
        """The publications behind the shown diagram, with BibTeX export."""
        from .sources_dialog import SourcesDialog

        if self.calculation is None:
            QMessageBox.information(self, "Sources", "Sources appear once a diagram is calculated.")
            return
        SourcesDialog(self.calculation, self.systems.get(self.settings.symbol, self.settings.symbol), self).exec()

    def compare_policies(self) -> None:
        from .policy_compare import PolicyComparisonDialog

        PolicyComparisonDialog(self.database, self.policy if self.policy_path else None, self.policy_path, self).exec()

    def python_code(self) -> str:
        """Python code that reproduces the current diagram, including the data, policy and view."""
        return self._code_for(self.settings)

    def _code_for(self, settings: Settings, plot: bool = True) -> str:
        return python_code(settings, self.display, dataset_path=self.dataset_path, policy_path=self.policy_path,
                           user_species_path=self.user_species_path, plot=plot)

    def _speciation_code(self) -> str:
        """Code for the speciation profile at the probe potential (mass-balance mode)."""
        return "\n".join((
            self._code_for(self.settings, plot=False),
            f"profile = pb.speciation_profile(calculation.diagram, {self.settings.probe_eh_V!r})",
            "pb.plot_speciation_profile(profile)",
        ))

    def _overview_code(self) -> str:
        """Code for the periodic-table screen at the current conditions and ligands."""
        arguments = self._screen_arguments()
        ligands = arguments.pop("ligands")
        text = ", ".join(f"{key}={value!r}" for key, value in sorted(arguments.items()))
        if ligands:
            text += ", ligands=(" + ", ".join(
                "pb.LigandActivity(" + ", ".join([repr(item.ligand_id)] + [
                    f"{name}={getattr(item, name)!r}" for name in
                    ("log10_free_activity", "total_unbound_mol_L", "acid_pKa") if getattr(item, name) is not None])
                + ")" for item in ligands) + ",)"
        lines = database_code(self.dataset_path, self.policy_path, self.user_species_path)
        lines += [f"screen = pb.screen_periodic_table(database, {text})",
                  "for element in screen.elements:",
                  "    if element.stable is not None:",
                  "        print(element.symbol, element.stable.species, element.energy_margin_J_mol_metal)"]
        return "\n".join(lines)

    def about(self) -> None:
        QMessageBox.about(
            self, "About pourbase",
            f"pourbase {__version__}, dataset {html.escape(self.database.data_version)}"
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
                       self.compare_page, self.overview.canvas, self.sensitivity_page):
            widget.set_dark(self.dark)
        for window in self.pinned:
            window.set_dark(self.dark)
        self.refresh_view()
        self._set_status(*self._status)

    def _show_busy(self, busy: bool) -> None:
        """A longer background calculation is reported in the status bar; the views stay as they are."""
        if busy:
            self.status_label.setText("Calculating…")
            self.status_label.setStyleSheet("color: gray;")
        else:
            self._set_status(*self._status)

    def _set_status(self, text: str, error: bool = False) -> None:
        self._status = (text, error)
        warning = text.startswith("~")
        if text.startswith(("!", "~")):
            text, error = text[1:], text.startswith("!") or error
        color = (("#e06c75" if self.dark else "#b00020") if error
                 else ("#e5c07b" if self.dark else "#8a5a00") if warning else "")
        self.status_label.setStyleSheet(f"color: {color};" if color else "")
        self.status_label.setText(text)
