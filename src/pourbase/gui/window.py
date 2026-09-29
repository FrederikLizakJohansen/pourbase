"""Main window of the desktop GUI."""

from __future__ import annotations

import html
import json
import math
import re
import sqlite3
import threading
import time
from contextlib import closing
from pathlib import Path
from typing import Any

import numpy as np
from PySide6.QtCore import QObject, QSettings, QSortFilterProxyModel, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QActionGroup, QGuiApplication, QKeySequence, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog,
    QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QScrollArea, QSplitter, QStyle, QTableView, QTableWidget, QTableWidgetItem,
    QTabWidget, QTextBrowser, QVBoxLayout, QWidget,
)

from .. import ATOMIC_WEIGHT_G_MOL, __version__
from ..speciation import speciation_profile
from .formula import formula_delegate, phase_label, to_html
from .engine import (
    CONCENTRATION_UNITS, MODES, RESOLUTIONS, Engine, Parameters, SweepCancelled, SweepSettings,
)
from .credentials import clear_key, load_key, save_key, storage_description
from .ligands import LigandPanel
from .materials import MaterialsProjectSource, client_available, equivalence_matrix, matched_colors, phase_views
from .mp_page import MaterialsProjectPage
from .periodic import COLOR_MODES, PeriodicTableCanvas
from .placeholder import StackedView
from .plots import DiagramView, DisplayOptions, PhaseStripView, SpeciationView, record_colors
from .sweep import SweepPage
from .theme import THEME_MODES, apply_theme
from .widgets import FloatSlider

PUBLIC_TABLES = (
    "species", "thermochemistry", "reported_thermochemistry", "sources", "phases", "warnings",
    "computational_fallbacks", "element_coverage", "materials_project_matches",
    "materials_project_energies", "ligands", "metadata",
)
DEBOUNCE_MS = 30


def _kj(value: float | None) -> str:
    return "" if value is None else f"{value / 1000:.2f}"


def _source_html(source: dict[str, Any] | None) -> str:
    if not source:
        return "<i>no source</i>"
    citation = html.escape(source.get("citation") or source.get("source_id") or "")
    if source.get("url"):
        citation = f'<a href="{html.escape(source["url"])}">{citation}</a>'
    locator = source.get("locator")
    return citation + (f"<br><small>Locator: {html.escape(locator)}</small>" if locator else "")


class TaskWorker(QObject):
    """Runs one background task at a time: ``function(progress)`` with a named result."""

    finished = Signal(str, object, str)
    progress = Signal(str, float)

    @Slot(str, object)
    def run(self, task: str, function: Any) -> None:
        def report(fraction: float) -> bool:
            self.progress.emit(task, fraction)
            return True

        try:
            result = function(report)
        except SweepCancelled:
            self.finished.emit(task, None, "")
            return
        except Exception as error:  # reported by the page that asked for the task
            self.finished.emit(task, None, f"{type(error).__name__}: {error}")
            return
        self.finished.emit(task, result, "")


class SweepWorker(QObject):
    finished = Signal(object, object, str)
    progress = Signal(float)

    @Slot(object, object, object, object, object)
    def run(self, engine: Engine, parameters: Parameters, settings: SweepSettings, key: tuple,
            cancel: threading.Event) -> None:
        def report(fraction: float) -> bool:
            self.progress.emit(fraction)
            return not cancel.is_set()

        try:
            sweep = engine.sweep(parameters, settings, progress=report)
        except SweepCancelled:
            self.finished.emit(key, None, "")
            return
        except Exception as error:  # shown on the sweep page
            self.finished.emit(key, None, f"{type(error).__name__}: {error}")
            return
        self.finished.emit(key, sweep, "")


class MainWindow(QMainWindow):
    requestTask = Signal(str, object)
    requestSweep = Signal(object, object, object, object, object)

    def __init__(self, symbol: str | None = None, settings: QSettings | None = None) -> None:
        super().__init__()
        self.setWindowTitle(f"pourbase {__version__}")
        screen = QGuiApplication.primaryScreen()
        available = screen.availableGeometry() if screen is not None else None
        if available is not None and available.width() > 0:
            self.resize(min(1500, int(available.width() * 0.92)), min(920, int(available.height() * 0.9)))
        else:
            self.resize(1500, 900)
        self.settings = settings if settings is not None else QSettings("pourbase", "pourbase")
        self.engine = Engine()
        self.systems = dict(self.engine.systems())
        self.params = self._restored_parameters()
        if symbol:
            self.params.symbol = symbol.strip().capitalize()
        self.display = DisplayOptions()
        self.theme_mode = str(self.settings.value("theme", "System"))
        self.dark = False
        self.diagram: Any = None
        self.result: dict[str, Any] | None = None
        self._updating = False
        self._reset_range = True
        self.mp_source = MaterialsProjectSource()
        self.mp_key, self.mp_key_source = load_key(self.settings)
        self.mp_comparison: Any = None
        self._mp_errors: dict[tuple, str] = {}
        self._tasks: set[str] = set()
        self._mp_sweeps: dict[tuple, tuple] = {}
        self._sweep_key: tuple | None = None
        self._sweep_running: tuple | None = None
        self._sweep_cancel = threading.Event()
        self._periodic_conditions: dict[str, Any] | None = None
        self._sweep_pending = False

        self._build_ui()
        self._build_menu()
        # Long lists scroll; the Fusion style would otherwise hide the scroll bar
        for combo in self.findChildren(QComboBox):
            combo.setMaxVisibleItems(15)
            combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._start_task_worker()
        self._start_sweep_worker()
        self._debounce = QTimer(self, singleShot=True, interval=DEBOUNCE_MS)
        self._debounce.timeout.connect(self.recalculate)
        self._periodic_debounce = QTimer(self, singleShot=True, interval=DEBOUNCE_MS)
        self._periodic_debounce.timeout.connect(self.update_periodic_table)
        self._apply_params_to_controls()
        self.set_theme(self.theme_mode)
        hints = QGuiApplication.styleHints()
        if hasattr(hints, "colorSchemeChanged"):
            hints.colorSchemeChanged.connect(
                lambda _scheme: self.theme_mode == "System" and self.set_theme("System")
            )
        geometry = self.settings.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        self.recalculate()
        self.update_periodic_table()
        self.load_table()
        self.pages.setTabText(1, self.systems.get(self.params.symbol, self.params.symbol))
        self.pages.setCurrentIndex(1 if symbol else 0)

    # -- settings ----------------------------------------------------------------------------

    def _restored_parameters(self) -> Parameters:
        try:
            parameters = Parameters.from_dict(json.loads(str(self.settings.value("parameters", "{}"))))
        except (TypeError, ValueError):
            parameters = Parameters()
        if parameters.symbol not in self.systems:
            parameters.symbol = "Fe"
        return parameters

    def closeEvent(self, event) -> None:
        self.settings.setValue("parameters", json.dumps(self.params.to_dict()))
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("theme", self.theme_mode)
        for thread in (self._task_thread, self._sweep_thread):
            thread.quit()
            thread.wait(2000)
        super().closeEvent(event)

    # -- UI construction ---------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.controls = QTabWidget()
        self.controls.addTab(self._scroll(self._system_tab()), "System")
        self.controls.addTab(self._scroll(self._grid_tab()), "Grid")
        self.controls.addTab(self._scroll(self._display_tab()), "Display")
        # Wide enough for the widest settings page and its scroll bar, so nothing is clipped
        self.controls.setMinimumWidth(max(
            self.controls.widget(index).widget().minimumSizeHint().width()
            for index in range(self.controls.count())
        ) + self.style().pixelMetric(QStyle.PM_ScrollBarExtent) + 24)

        self.diagram_view = DiagramView()
        self.diagram_view.cursorMoved.connect(lambda text: self.cursor_label.setText(text or " "))
        self.diagram_view.probeMoved.connect(self.set_probe)
        self.cursor_label = QLabel(" ")
        self.cursor_label.setTextFormat(Qt.RichText)
        # Fixed height: scripts in species names would otherwise change the line height
        self.cursor_label.setFixedHeight(int(self.cursor_label.fontMetrics().height() * 2))
        self.probe_text = QTextBrowser()
        self.probe_text.setOpenExternalLinks(True)
        self.probe_text.setFixedHeight(200)
        diagram_page = QWidget()
        diagram_layout = QVBoxLayout(diagram_page)
        diagram_layout.setContentsMargins(0, 0, 0, 0)
        diagram_layout.addWidget(self.diagram_view, 1)
        diagram_layout.addWidget(self.cursor_label)
        diagram_layout.addWidget(self.probe_text)
        self.diagram_stack = StackedView(diagram_page)

        self.sweep_page = SweepPage()
        self.sweep_page.requested.connect(self.request_sweep)
        self.sweep_page.materialsProjectRequested.connect(self.request_mp_sweep)
        self.sweep_stack = StackedView(self.sweep_page)
        self.species_page = self._species_page()
        self.boundary_stack = StackedView(self._boundaries_page())
        self.speciation_stack = StackedView(self._speciation_page())
        self.database_page = self._database_page()
        self.mp_page = MaterialsProjectPage()
        self.mp_page.refreshRequested.connect(lambda: self.fetch_materials_project(force=True))
        self.mp_page.optionsChanged.connect(self._materials_project_options_changed)
        self.mp_page.keyRequested.connect(self.edit_api_key)
        self.mp_page.exportRequested.connect(self.export_mp_figure)
        self.mp_page.probeMoved.connect(self.set_probe)
        self.mp_stack = StackedView(self.mp_page)

        self.views = QTabWidget()
        self.views.setDocumentMode(True)
        self.views.addTab(self.diagram_stack, "Diagram")
        self.views.addTab(self.species_page, "Species")
        self.views.addTab(self.boundary_stack, "Boundaries")
        self.views.addTab(self.speciation_stack, "Speciation")
        self.views.addTab(self.sweep_stack, "Concentration sweep")
        self.views.addTab(self.mp_stack, "DFT comparison")
        self.views.currentChanged.connect(lambda _index: self._refresh_current_view())

        system_page = QSplitter()
        system_page.addWidget(self.controls)
        system_page.addWidget(self.views)
        system_page.setStretchFactor(1, 1)
        system_page.setCollapsible(0, False)
        system_page.setSizes([self.controls.minimumWidth(), 10_000])
        self.system_splitter = system_page

        self.pages = QTabWidget()
        self.pages.setDocumentMode(True)
        self.pages.addTab(self._overview_page(), "Periodic table")
        self.pages.addTab(system_page, "System")
        self.pages.addTab(self.database_page, "Database")
        self.pages.currentChanged.connect(self._page_changed)
        self.setCentralWidget(self.pages)
        self.status_label = QLabel()
        self.statusBar().addWidget(self.status_label, 1)

    def _overview_page(self) -> QWidget:
        self.periodic_pH = FloatSlider("pH", -2.0, 16.0, 7.0, decimals=2, step=0.25, label_width=24)
        self.periodic_potential = FloatSlider("E", -2.5, 2.5, 0.0, decimals=3, step=0.05, unit="V",
                                              label_width=14)
        self.periodic_reference = QComboBox()
        self.periodic_reference.addItems(["vs SHE", "vs RHE"])
        self.periodic_color = QComboBox()
        for key, label in COLOR_MODES.items():
            self.periodic_color.addItem(label, key)
        for slider in (self.periodic_pH, self.periodic_potential):
            slider.valueChanged.connect(lambda _v: self._periodic_debounce.start())
        self.periodic_reference.currentIndexChanged.connect(lambda _i: self.update_periodic_table())
        self.periodic_color.currentIndexChanged.connect(
            lambda _i: self.periodic_canvas.set_color_mode(self.periodic_color.currentData())
        )
        self.periodic_note = QLabel()
        self.periodic_note.setStyleSheet("color: gray;")
        controls = QHBoxLayout()
        controls.addWidget(self.periodic_pH, 3)
        controls.addSpacing(16)
        controls.addWidget(self.periodic_potential, 3)
        controls.addWidget(self.periodic_reference)
        controls.addSpacing(16)
        controls.addWidget(QLabel("Color by"))
        controls.addWidget(self.periodic_color)
        self.periodic_canvas = PeriodicTableCanvas()
        self.periodic_canvas.elementClicked.connect(self.open_element)
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 12, 16, 8)
        layout.addLayout(controls)
        layout.addWidget(self.periodic_note)
        layout.addWidget(self.periodic_canvas, 1)
        return page

    @staticmethod
    def _scroll(widget: QWidget) -> QScrollArea:
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        area.setWidget(widget)
        return area

    def _system_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        system_box = QGroupBox("Element")
        form = QFormLayout(system_box)
        self.symbol_combo = QComboBox()
        for symbol, name in self.systems.items():
            self.symbol_combo.addItem(f"{name}", symbol)
        self.symbol_combo.currentIndexChanged.connect(
            lambda _i: self._set("symbol", self.symbol_combo.currentData(), reset_range=False)
        )
        form.addRow("System", self.symbol_combo)
        self.mode_combo = QComboBox()
        for key, label in MODES.items():
            self.mode_combo.addItem(label, key)
        self.mode_combo.currentIndexChanged.connect(lambda _i: self._set("mode", self.mode_combo.currentData()))
        form.addRow("Model", self.mode_combo)
        layout.addWidget(system_box)

        concentration_box = QGroupBox("Metal concentration")
        form = QFormLayout(concentration_box)
        self.unit_combo = QComboBox()
        for key, label in CONCENTRATION_UNITS.items():
            self.unit_combo.addItem(label, key)
        self.unit_combo.currentIndexChanged.connect(self._unit_changed)
        form.addRow("Unit", self.unit_combo)
        self.concentration_slider = FloatSlider("Value", -12.0, 0.0, -6.0, decimals=3, step=0.5, label_width=50)
        self.concentration_slider.valueChanged.connect(lambda v: self._set("concentration_value", v))
        form.addRow(self.concentration_slider)
        self.density_spin = QDoubleSpinBox()
        self.density_spin.setRange(0.5, 3.0)
        self.density_spin.setDecimals(3)
        self.density_spin.setSingleStep(0.01)
        self.density_spin.setSuffix(" kg/L")
        self.density_spin.setToolTip("Solution density, used to convert weight percent")
        self.density_spin.valueChanged.connect(lambda v: self._set("solution_density_kg_L", v))
        form.addRow("Solution density", self.density_spin)
        self.concentration_note = QLabel()
        self.concentration_note.setWordWrap(True)
        form.addRow(self.concentration_note)
        layout.addWidget(concentration_box)

        activity_box = QGroupBox("Activities")
        form = QFormLayout(activity_box)
        self.davies_check = QCheckBox("Davies activity coefficients (mass balance)")
        self.davies_check.toggled.connect(lambda v: self._set("davies", v))
        form.addRow(self.davies_check)
        self.ionic_slider = FloatSlider("I", 0.0, 0.1, 0.01, decimals=4, step=0.005, unit="mol/L", label_width=20)
        self.ionic_slider.valueChanged.connect(lambda v: self._set("ionic_strength_mol_L", v))
        form.addRow("Ionic strength", self.ionic_slider)
        self.gas_slider = FloatSlider("", -12.0, 2.0, 0.0, decimals=2, step=0.5, label_width=0)
        self.gas_slider.setToolTip("log₁₀ of every gas fugacity relative to 1 bar")
        self.gas_slider.valueChanged.connect(lambda v: self._set("log10_gas_fugacity", v))
        form.addRow("log₁₀ gas fugacity", self.gas_slider)
        layout.addWidget(activity_box)

        evidence_box = QGroupBox("Evidence policy")
        evidence = QVBoxLayout(evidence_box)
        self.incomplete_check = QCheckBox("Allow incomplete systems (omit species without Gibbs data)")
        self.incomplete_check.toggled.connect(lambda v: self._set("allow_incomplete", v))
        self.fallback_check = QCheckBox("Fill missing solid Gibbs values with labelled MP 300 K estimates")
        self.fallback_check.toggled.connect(lambda v: self._set("use_mp_fallbacks", v))
        for widget in (self.incomplete_check, self.fallback_check):
            evidence.addWidget(widget)
        layout.addWidget(evidence_box)

        ligand_box = QGroupBox("Ligands")
        ligand_layout = QVBoxLayout(ligand_box)
        self.ligand_panel = LigandPanel(self.engine.ligands)
        self.ligand_panel.changed.connect(self._ligands_changed)
        ligand_layout.addWidget(self.ligand_panel)
        layout.addWidget(ligand_box)
        layout.addStretch(1)
        return page

    def _grid_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        box = QGroupBox("Axes")
        form = QFormLayout(box)
        self.range_spins: dict[str, QDoubleSpinBox] = {}
        for name, label, low, high, step in (
            ("pH_min", "pH minimum", -4.0, 18.0, 0.5),
            ("pH_max", "pH maximum", -4.0, 18.0, 0.5),
            ("eh_min_V", "Eh minimum (V)", -4.0, 4.0, 0.1),
            ("eh_max_V", "Eh maximum (V)", -4.0, 4.0, 0.1),
        ):
            spin = QDoubleSpinBox()
            spin.setRange(low, high)
            spin.setSingleStep(step)
            spin.setDecimals(2)
            spin.setKeyboardTracking(False)
            spin.valueChanged.connect(lambda v, name=name: self._set(name, v, reset_range=True))
            self.range_spins[name] = spin
            form.addRow(label, spin)
        self.resolution_combo = QComboBox()
        for name, (pH_points, eh_points) in RESOLUTIONS.items():
            self.resolution_combo.addItem(f"{name} ({pH_points} × {eh_points})", name)
        self.resolution_combo.currentIndexChanged.connect(
            lambda _i: self._set("resolution", self.resolution_combo.currentData())
        )
        form.addRow("Resolution", self.resolution_combo)
        reset = QPushButton("Default axes")
        reset.clicked.connect(self.reset_axes)
        form.addRow(reset)
        layout.addWidget(box)

        probe_box = QGroupBox("Probe point")
        form = QFormLayout(probe_box)
        self.probe_pH = QDoubleSpinBox()
        self.probe_pH.setRange(-4.0, 18.0)
        self.probe_eh = QDoubleSpinBox()
        self.probe_eh.setRange(-4.0, 4.0)
        self.probe_eh.setDecimals(3)
        self.probe_eh.setSingleStep(0.05)
        for spin in (self.probe_pH, self.probe_eh):
            spin.setKeyboardTracking(False)
            spin.valueChanged.connect(lambda _v: self.set_probe(self.probe_pH.value(), self.probe_eh.value()))
        form.addRow("pH", self.probe_pH)
        form.addRow("Eh (V vs SHE)", self.probe_eh)
        hint = QLabel("Click or drag in the diagram to move the probe.")
        hint.setWordWrap(True)
        form.addRow(hint)
        layout.addWidget(probe_box)
        layout.addStretch(1)
        return page

    def _display_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        box = QGroupBox("Diagram")
        column = QVBoxLayout(box)
        self.display_checks: dict[str, QCheckBox] = {}
        for name, label in (
            ("labels", "Domain labels"),
            ("legend", "Legend"),
            ("boundaries", "Phase boundaries"),
            ("water", "Water stability lines"),
            ("plating", "Direct plating potential (fixed activity)"),
        ):
            check = QCheckBox(label)
            check.setChecked(getattr(self.display, name))
            check.toggled.connect(lambda v, name=name: self._set_display(name, v))
            self.display_checks[name] = check
            column.addWidget(check)
        layout.addWidget(box)

        soft = QGroupBox("Boltzmann-like soft minimum (fixed activity)")
        form = QFormLayout(soft)
        self.boltzmann_check = QCheckBox("Blend species colors by their weights")
        self.boltzmann_check.toggled.connect(lambda v: self._set_display("boltzmann", v))
        form.addRow(self.boltzmann_check)
        self.boltzmann_slider = FloatSlider("Scale", 0.05, 20.0, 1.0, decimals=2, log=True, label_width=40)
        self.boltzmann_slider.valueChanged.connect(lambda v: self._set_display("boltzmann_scale", v))
        form.addRow(self.boltzmann_slider)
        note = QLabel(
            "Weights are proportional to exp(−(G − Gmin) / (scale·R·T)). They show energetic "
            "competition and are not conserved phase fractions."
        )
        note.setWordWrap(True)
        form.addRow(note)
        layout.addWidget(soft)
        layout.addStretch(1)
        return page

    def _species_page(self) -> QWidget:
        self.species_table = QTableWidget(0, 8)
        self.species_table.setHorizontalHeaderLabels(
            ["Species", "Phase", "ΔfG° (kJ/mol)", "±", "Status", "Stable", "Warnings", "Record ID"]
        )
        self.species_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.species_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.species_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.species_table.setSortingEnabled(True)
        self.species_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.species_table.itemSelectionChanged.connect(self._show_species_details)
        self.species_table.setItemDelegateForColumn(0, formula_delegate(self.species_table))
        self.species_details = QTextBrowser()
        self.species_details.setOpenExternalLinks(True)
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.species_table)
        splitter.addWidget(self.species_details)
        splitter.setSizes([450, 350])
        return splitter

    def _boundaries_page(self) -> QWidget:
        self.boundary_table = QTableWidget(0, 4)
        self.boundary_table.setHorizontalHeaderLabels(["Reaction", "Equation", "Kind", "Gibbs sources"])
        self.boundary_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.boundary_table.setItemDelegateForColumn(0, formula_delegate(self.boundary_table))
        self.boundary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.boundary_note = QLabel()
        self.boundary_note.setWordWrap(True)
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self.boundary_note)
        layout.addWidget(self.boundary_table, 1)
        return page

    def _speciation_page(self) -> QWidget:
        self.speciation_view = SpeciationView()
        self.speciation_strip = PhaseStripView()
        self.speciation_mp_note = QLabel()
        self.speciation_mp_note.setWordWrap(True)
        self.speciation_mp_button = QPushButton()
        self.speciation_mp_button.clicked.connect(self._speciation_mp_action)
        mp_row = QHBoxLayout()
        mp_row.addWidget(self.speciation_mp_note, 1)
        mp_row.addWidget(self.speciation_mp_button)
        page = QWidget()
        layout = QVBoxLayout(page)
        note = QLabel("Metal fractions along pH at the probe potential, from the closed total-metal solver.")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addWidget(self.speciation_view, 1)
        layout.addWidget(QLabel("Predominant species along pH at the probe potential"))
        layout.addWidget(self.speciation_strip)
        layout.addLayout(mp_row)
        return page

    def _database_page(self) -> QWidget:
        self.table_combo = QComboBox()
        self.table_combo.addItems(PUBLIC_TABLES)
        self.table_combo.currentIndexChanged.connect(lambda _i: self.load_table())
        self.table_filter = QLineEdit()
        self.table_filter.setPlaceholderText("Filter rows…")
        self.table_filter.setClearButtonEnabled(True)
        self.table_model = QStandardItemModel(self)
        self.table_proxy = QSortFilterProxyModel(self)
        self.table_proxy.setSourceModel(self.table_model)
        self.table_proxy.setFilterKeyColumn(-1)
        self.table_proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.table_filter.textChanged.connect(self._filter_table)
        self.table_view = QTableView()
        self.table_view.setModel(self.table_proxy)
        self.table_view.setSortingEnabled(True)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_count = QLabel()
        row = QHBoxLayout()
        row.addWidget(QLabel("Table"))
        row.addWidget(self.table_combo)
        row.addWidget(self.table_filter, 1)
        row.addWidget(self.table_count)
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addLayout(row)
        layout.addWidget(self.table_view, 1)
        return page

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        for text, slot, shortcut in (
            ("Export figure…", self.export_figure, QKeySequence.Save),
            ("Export grid as CSV…", self.export_grid, None),
            ("Copy Python code", self.copy_python, None),
            (None, None, None),
            ("Quit", self.close, QKeySequence.Quit),
        ):
            if text is None:
                file_menu.addSeparator()
                continue
            action = QAction(text, self)
            action.triggered.connect(slot)
            if shortcut is not None:
                action.setShortcut(shortcut)
            file_menu.addAction(action)

        view_menu = self.menuBar().addMenu("&View")
        theme_menu = view_menu.addMenu("Theme")
        group = QActionGroup(self)
        self.theme_actions = {}
        for mode in THEME_MODES:
            action = QAction(mode, self, checkable=True)
            action.triggered.connect(lambda _checked=False, mode=mode: self.set_theme(mode))
            group.addAction(action)
            theme_menu.addAction(action)
            self.theme_actions[mode] = action
        reset = QAction("Reset zoom", self)
        reset.setShortcut("Ctrl+0")
        reset.triggered.connect(lambda: self._draw(reset_range=True))
        view_menu.addAction(reset)

        tools_menu = self.menuBar().addMenu("&Tools")
        compare = QAction("DFT comparison (Materials Project)", self)
        compare.triggered.connect(self.show_materials_project)
        tools_menu.addAction(compare)
        key = QAction("Materials Project API key…", self)
        key.triggered.connect(self.edit_api_key)
        tools_menu.addAction(key)

        help_menu = self.menuBar().addMenu("&Help")
        about = QAction("About pourbase", self)
        about.triggered.connect(self.about)
        help_menu.addAction(about)

    # -- parameters --------------------------------------------------------------------------

    def _apply_params_to_controls(self) -> None:
        self._updating = True
        p = self.params
        self.symbol_combo.setCurrentIndex(max(self.symbol_combo.findData(p.symbol), 0))
        self.mode_combo.setCurrentIndex(max(self.mode_combo.findData(p.mode), 0))
        self.unit_combo.setCurrentIndex(max(self.unit_combo.findData(p.concentration_unit), 0))
        self._configure_concentration_slider()
        self.concentration_slider.setValue(p.concentration_value)
        self.density_spin.setValue(p.solution_density_kg_L)
        self.davies_check.setChecked(p.davies)
        self.ionic_slider.setValue(p.ionic_strength_mol_L)
        self.gas_slider.setValue(p.log10_gas_fugacity)
        self.incomplete_check.setChecked(p.allow_incomplete)
        self.fallback_check.setChecked(p.use_mp_fallbacks)
        for name, spin in self.range_spins.items():
            spin.setValue(getattr(p, name))
        self.resolution_combo.setCurrentIndex(max(self.resolution_combo.findData(p.resolution), 0))
        self.probe_pH.setValue(p.probe_pH)
        self.probe_eh.setValue(p.probe_eh_V)
        self.ligand_panel.set_settings(p.ligands)
        self.ligand_panel.set_system(p.symbol, self.engine.ligand_species.get(p.symbol, {}))
        self._updating = False
        self._update_enabled_controls()

    def _configure_concentration_slider(self) -> None:
        low, high, value = {
            "log10_molar": (-12.0, 1.0, -6.0),
            "molar": (1e-12, 10.0, 1e-6),
            "ppm": (1e-6, 1e5, 0.1),
            "wt_percent": (1e-8, 50.0, 1e-5),
        }[self.params.concentration_unit]
        slider = self.concentration_slider
        slider._minimum, slider._maximum, slider._log = low, high, self.params.concentration_unit != "log10_molar"
        slider._default_maximum = slider._hard_maximum = high
        slider.spin.setDecimals(3 if not slider._log else 12)
        slider.spin.setRange(low, high)
        if not low <= self.params.concentration_value <= high:
            self.params.concentration_value = value

    def _unit_changed(self) -> None:
        if self._updating:
            return
        unit = self.unit_combo.currentData()
        if self.result is not None:
            # Express the current molar concentration in the new unit
            molar = self.result["concentration_input"]["molar_concentration"]
            grams_per_litre = molar * ATOMIC_WEIGHT_G_MOL[self.params.symbol]
            self.params.concentration_value = {
                "log10_molar": math.log10(molar),
                "molar": molar,
                "ppm": grams_per_litre * 1000,
                "wt_percent": grams_per_litre / (10 * self.params.solution_density_kg_L),
            }[unit]
        self.params.concentration_unit = unit
        self._updating = True
        self._configure_concentration_slider()
        self.concentration_slider.setValue(self.params.concentration_value)
        self._updating = False
        self._update_enabled_controls()
        self.schedule()

    def _update_enabled_controls(self) -> None:
        mass_balance = self.params.mode == "mass_balance"
        self.davies_check.setEnabled(mass_balance)
        self.ionic_slider.setEnabled(mass_balance and self.params.davies)
        self.density_spin.setEnabled(self.params.concentration_unit == "wt_percent")
        self.boltzmann_check.setEnabled(not mass_balance)
        self.boltzmann_slider.setEnabled(not mass_balance)
        self.display_checks["plating"].setEnabled(not mass_balance)

    def _ligands_changed(self) -> None:
        if not self._updating:
            self.schedule()

    def _set(self, name: str, value: Any, reset_range: bool = False) -> None:
        if self._updating:
            return
        setattr(self.params, name, value)
        if name == "symbol":
            self.ligand_panel.set_system(value, self.engine.ligand_species.get(value, {}))
            self.pages.setTabText(1, self.systems.get(value, value))
        self._reset_range = self._reset_range or reset_range
        self._update_enabled_controls()
        self.schedule()

    def _set_display(self, name: str, value: Any) -> None:
        setattr(self.display, name, value)
        self._draw()

    def reset_axes(self) -> None:
        defaults = Parameters()
        for name in ("pH_min", "pH_max", "eh_min_V", "eh_max_V"):
            setattr(self.params, name, getattr(defaults, name))
        self._apply_params_to_controls()
        self._reset_range = True
        self.schedule()

    def set_probe(self, pH: float, eh_V: float) -> None:
        if self._updating:
            return
        self.params.probe_pH, self.params.probe_eh_V = pH, eh_V
        self._updating = True
        self.probe_pH.setValue(pH)
        self.probe_eh.setValue(eh_V)
        self._updating = False
        self.diagram_view.set_probe(pH, eh_V)
        self._refresh_probe()
        if self.views.currentWidget() is self.speciation_stack:
            self._refresh_speciation()

    def open_element(self, symbol: str) -> None:
        conditions = self._periodic_conditions
        self.params.symbol = symbol
        if conditions is not None:
            self.params.probe_pH = conditions["pH"]
            self.params.probe_eh_V = conditions["potential_V_vs_SHE"]
        self._apply_params_to_controls()
        self.pages.setTabText(1, self.systems.get(symbol, symbol))
        self.pages.setCurrentIndex(1)
        self.views.setCurrentWidget(self.diagram_stack)
        self.recalculate()

    def _page_changed(self, index: int) -> None:
        if index == 0:
            self.update_periodic_table()

    # -- calculation -------------------------------------------------------------------------

    def schedule(self) -> None:
        self._debounce.start()

    def recalculate(self) -> None:
        if self.params.pH_max <= self.params.pH_min or self.params.eh_max_V <= self.params.eh_min_V:
            self._set_status("Each axis maximum must exceed its minimum", error=True)
            return
        start = time.perf_counter()
        try:
            self.diagram, self.result = self.engine.compute(self.params)
        except Exception as error:  # shown in place of the diagram
            self._show_calculation_error(error)
            return
        elapsed = time.perf_counter() - start
        self.diagram_stack.show_view()
        self._draw(reset_range=self._reset_range)
        self._reset_range = False
        self._refresh_probe()
        self._refresh_current_view(all_tables=True)
        conversion = self.result["concentration_input"]
        self.concentration_note.setText(
            f"{conversion['molar_concentration']:.3g} mol/L, "
            f"log₁₀ a = {conversion['log10_standard_activity']:.3f}"
        )
        fallbacks = self.result["fallback_record_ids"]
        excluded = self.result["excluded_species"]
        message = (
            f"{self.result['system']}: {len(self.result['stable_species'])} stable of "
            f"{len(self.diagram.system.species)} species"
        )
        if elapsed > 1e-3:
            message += f", calculated in {elapsed * 1e3:.0f} ms"
        missing = [item for item in excluded if item["reason"] == "recommended_gibbs_energy_unavailable"]
        ligand = [item for item in excluded if item["reason"] == "ligand_species_not_selected"]
        other = len(excluded) - len(missing) - len(ligand)
        if missing:
            message += f"; {len(missing)} species omitted for missing Gibbs data"
        if ligand:
            message += f"; {len(ligand)} ligand species available (System → Ligands)"
        if other:
            message += f"; {other} species outside this model (see Species)"
        if fallbacks:
            message += f"; {len(fallbacks)} MP 300 K estimate(s) in use"
        self._set_status(message, error=bool(missing or fallbacks))

    def _show_calculation_error(self, error: Exception) -> None:
        from ..exceptions import IncompleteSystemError

        self.diagram, self.result = None, None
        name = self.systems.get(self.params.symbol, self.params.symbol)
        if isinstance(error, IncompleteSystemError):
            self.diagram_stack.show_message(
                f"{name} has documented evidence gaps",
                html.escape(str(error)).replace(". Pass allow_incomplete=True for exploratory use.", ".")
                + "<br><br>Species without a recommended Gibbs energy can be omitted for an "
                "exploratory diagram, or filled with labelled Materials Project 300 K estimates "
                "where those exist.",
                ("Allow an incomplete system", lambda: self.incomplete_check.setChecked(True)),
                glyph="!",
            )
        else:
            self.diagram_stack.show_message(
                "The diagram cannot be calculated", html.escape(f"{type(error).__name__}: {error}"),
                glyph="!",
            )
        self._set_status(f"{name}: no diagram for the current settings", error=True)
        self._refresh_current_view(all_tables=True)

    def _draw(self, reset_range: bool = False) -> None:
        if self.diagram is None or self.result is None:
            return
        plating = self.result.get("plating_limit_V_vs_SHE")
        self.diagram_view.show_diagram(self.diagram, self.display, plating, reset_range=reset_range)
        self.diagram_view.set_probe(self.params.probe_pH, self.params.probe_eh_V)

    def _refresh_current_view(self, all_tables: bool = False) -> None:
        current = self.views.currentWidget()
        if all_tables or current is self.species_page:
            self._refresh_species()
        if all_tables or current is self.boundary_stack:
            self._refresh_boundaries()
        if current is self.speciation_stack:
            self._refresh_speciation()
        if current is self.sweep_stack:
            self.request_sweep()
        if current is self.mp_stack:
            self._refresh_materials_project()

    def _refresh_probe(self) -> None:
        if self.diagram is None:
            return
        try:
            probe = self.engine.probe(self.diagram, self.params.probe_pH, self.params.probe_eh_V)
        except ValueError as error:
            self.probe_text.setHtml(html.escape(str(error)))
            return
        species = probe["species"]
        details = self.engine.database.species_details([species.record_id])[0]
        thermo = details["thermochemistry"] or {}
        muted = "#8c8f94" if self.dark else "#6a6f76"

        def row(label: str, value: str) -> str:
            return (f'<tr><td style="color:{muted}; padding-right:10px" valign="top">{label}</td>'
                    f"<td>{value}</td></tr>")

        uncertainty = thermo.get("gibbs_uncertainty_J_mol")
        energy = f"{_kj(species.gibbs_energy_J_mol)} kJ/mol"
        if uncertainty is not None:
            energy += f" ± {_kj(uncertainty)}"
        source = thermo.get("gibbs_source") or {}
        thermo_rows = [
            row("ΔfG°", energy),
            row("Status", html.escape(species.gibbs_status.replace("_", " "))),
            row("Source", _source_html(source) if source else "<i>none</i>"),
            row("Record", f"<code>{species.record_id}</code>"),
        ]
        comparison = self.mp_comparison
        if comparison is not None and comparison.experimental.system.symbol == self.params.symbol:
            try:
                phase = comparison.materials_project.phase_at(probe["pH"], probe["eh_V"])
                from .materials import pretty_label

                thermo_rows.append(row("DFT (MP)", to_html(pretty_label(phase.label))))
            except ValueError:
                pass
        columns = [
            f'<td valign="top" width="58%"><b>Thermochemistry</b><table cellspacing="0" cellpadding="1">'
            f'{"".join(thermo_rows)}</table></td>'
        ]
        if "dissolved_metal_mol_L" in probe:
            fractions = sorted(probe["speciation"], key=lambda item: -item["metal_fraction"])
            inventory = [
                row("Dissolved", f"{probe['dissolved_metal_mol_L']:.3g} mol/L"),
                row("Precipitated", f"{probe['precipitated_fraction']:.1%} of the metal"),
            ] + [
                row(to_html(item["species"]), f"{item['metal_fraction']:.1%}")
                for item in fractions[:6] if item["metal_fraction"] >= 1e-3
            ]
            columns.append(
                f'<td valign="top" style="padding-left:18px"><b>Metal inventory</b>'
                f'<table cellspacing="0" cellpadding="1">{"".join(inventory)}</table></td>'
            )
        header = (
            f'<span style="font-size:12pt"><b>{to_html(species.species, 12)}</b></span>'
            f"&nbsp; {html.escape(phase_label(species))}"
            f'&nbsp;&nbsp;<span style="color:{muted}">at pH {probe["pH"]:.2f}, '
            f'Eh {probe["eh_V"]:+.3f} V vs SHE</span>'
        )
        warnings = "".join(
            f'<div style="color:#c77700">⚠ {html.escape(item.get("message", str(item)) if isinstance(item, dict) else str(item))}</div>'
            for item in details.get("warnings", [])
        )
        self.probe_text.setHtml(
            f'{header}<table width="100%" cellspacing="0" cellpadding="0" style="margin-top:4px">'
            f"<tr>{''.join(columns)}</tr></table>{warnings}"
        )

    def _refresh_species(self) -> None:
        if self.result is None:
            self.species_table.setRowCount(0)
            self.species_details.clear()
            return
        rows = [(item, None) for item in self.result["substances"]["included"]] + [
            (item, item["exclusion"]) for item in self.result["substances"]["excluded"]
        ]
        self._species_rows = {item["record_id"]: item for item, _ in rows}
        table = self.species_table
        table.blockSignals(True)
        table.clearSelection()
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))
        for row, (item, exclusion) in enumerate(rows):
            thermo = item.get("thermochemistry") or {}
            status = exclusion["reason"] if exclusion else item.get("calculation_gibbs_status", "")
            energy = item.get("calculation_gibbs_energy_J_mol", thermo.get("gibbs_energy_J_mol"))
            values = [
                item["species"], item.get("phase_detail") or item["phase"], _kj(energy),
                _kj(thermo.get("gibbs_uncertainty_J_mol")), status,
                "yes" if item.get("stable_on_grid") else "", str(len(item.get("warnings") or [])) or "",
                item["record_id"],
            ]
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column == 2 and value:
                    cell.setData(Qt.EditRole, float(value))
                if exclusion:
                    cell.setForeground(Qt.gray)
                table.setItem(row, column, cell)
        table.setSortingEnabled(True)
        table.blockSignals(False)
        self.species_details.clear()

    def _show_species_details(self) -> None:
        selected = self.species_table.selectedItems()
        if not selected:
            return
        record_id = self.species_table.item(selected[0].row(), 7).text()
        item = self._species_rows.get(record_id)
        if item is None:
            return
        thermo = item.get("thermochemistry") or {}
        parts = [f"<h3>{to_html(item['species'], 13)} <small>({html.escape((item.get('phase_detail') or item['phase']).strip('()'))})</small></h3>",
                 f"<code>{record_id}</code>"]
        for label, key, unit, divisor in (
            ("Gibbs energy of formation", "gibbs", "kJ/mol", 1000),
            ("Formation enthalpy", "formation_enthalpy", "kJ/mol", 1000),
            ("Absolute entropy", "entropy", "J/(mol K)", 1),
        ):
            value = thermo.get(f"{key}_energy_J_mol" if key == "gibbs" else (
                f"{key}_J_mol" if key == "formation_enthalpy" else f"{key}_J_mol_K"))
            status = thermo.get(f"{key}_status", "not_available")
            text = "—" if value is None else f"{value / divisor:.3f} {unit}"
            parts.append(f"<p><b>{label}:</b> {text} <i>({status})</i><br>{_source_html(thermo.get(f'{key}_source'))}</p>")
        if item.get("computational_fallback"):
            fallback = item["computational_fallback"]
            parts.append("<p><b>Materials Project fallback:</b> " + html.escape(
                ", ".join(f"{k}: {v}" for k, v in fallback.items() if v not in (None, ""))) + "</p>")
        identity = item.get("phase_identity")
        if identity:
            parts.append("<p><b>Phase identity:</b> " + html.escape(
                ", ".join(f"{k}: {v}" for k, v in identity.items() if v not in (None, "") and k != "source_url")) + "</p>")
        warnings = item.get("warnings") or []
        if warnings:
            parts.append("<p><b>Warnings</b><ul>" + "".join(
                f"<li>{html.escape(w.get('message', str(w)) if isinstance(w, dict) else str(w))}</li>"
                for w in warnings) + "</ul></p>")
        reported = item.get("reported_thermochemistry") or []
        if reported:
            rows = "".join(
                f"<tr><td>{html.escape(r['property'])}</td><td>{r['value']}</td><td>{html.escape(r['unit'])}</td>"
                f"<td>{html.escape(r['status'])}</td><td>{'✓' if r['selected_as_recommended'] else ''}</td>"
                f"<td>{html.escape(r.get('source_citation') or '')}</td></tr>"
                for r in reported
            )
            parts.append(
                "<p><b>Reported values</b></p><table border='1' cellspacing='0' cellpadding='3'>"
                "<tr><th>Property</th><th>Value</th><th>Unit</th><th>Status</th><th>Recommended</th>"
                f"<th>Source</th></tr>{rows}</table>"
            )
        self.species_details.setHtml("".join(parts))

    def _refresh_boundaries(self) -> None:
        if self.result is None:
            self.boundary_stack.show_message("No diagram", "Boundaries appear once the diagram is calculated.")
            return
        if self.params.mode == "mass_balance":
            self.boundary_stack.show_message(
                "Boundary equations describe fixed-activity diagrams",
                "In the mass-balance model, boundaries are numerical equilibria that include metal "
                "inventory and precipitation, so pairwise Nernst equations do not apply.",
                ("Switch to fixed activity", lambda: self._set_mode("fixed_activity")),
            )
            return
        self.boundary_stack.show_view()
        rows = self.result.get("boundaries", [])
        self.boundary_note.setText(self.result.get("boundary_note", (
            "Balanced reactions and activity-conditioned Nernst equations for adjacent domains."
        )))
        self.boundary_table.setRowCount(len(rows))
        for row, item in enumerate(rows):
            for column, value in enumerate(
                (item["reaction"], item["equation"], item["kind"], ", ".join(item["source_ids"]))
            ):
                self.boundary_table.setItem(row, column, QTableWidgetItem(value))

    def _set_mode(self, mode: str) -> None:
        self.mode_combo.setCurrentIndex(self.mode_combo.findData(mode))
        self.recalculate()
        self._refresh_current_view()

    def _refresh_speciation(self) -> None:
        if self.params.mode != "mass_balance":
            self.speciation_stack.show_message(
                "Species fractions need a closed metal inventory",
                "In fixed-activity mode every aqueous species has an externally set activity, so "
                "there is no conserved amount to divide between species. The mass-balance model "
                "conserves the total metal and reports the fraction held by each species.",
                ("Switch to mass balance", lambda: self._set_mode("mass_balance")),
            )
            return
        if self.diagram is None:
            self.speciation_stack.show_message("No diagram", "Speciation appears once the diagram is calculated.")
            return
        self.speciation_stack.show_view()
        self._refresh_speciation_strip()
        self.speciation_view.show_profile(speciation_profile(self.diagram, self.params.probe_eh_V))

    def _start_sweep_worker(self) -> None:
        self._sweep_thread = QThread(self)
        self._sweep_worker = SweepWorker()
        self._sweep_worker.moveToThread(self._sweep_thread)
        self.requestSweep.connect(self._sweep_worker.run)
        self._sweep_worker.finished.connect(self._sweep_finished)
        self._sweep_worker.progress.connect(self._sweep_progress)
        self._sweep_thread.start()

    def request_sweep(self) -> None:
        """Show the cached sweep for the current settings, or calculate it in the background."""
        if self.views.currentWidget() is not self.sweep_stack:
            return
        settings = self.sweep_page.settings()
        if settings.log10_max <= settings.log10_min:
            self.sweep_stack.show_message("Invalid activity range", "The upper activity must exceed the lower.")
            return
        key = self.engine.sweep_key(self.params, settings)
        if key == self._sweep_key and self.sweep_stack.currentWidget() is self.sweep_page:
            return
        cached = self.engine.cached_sweep(self.params, settings)
        if cached is not None:
            self._show_sweep(key, cached)
            return
        if self._sweep_pending:
            if key != self._sweep_running:
                self._sweep_cancel.set()  # the finished handler starts the newer request
            return
        self._sweep_pending = True
        self._sweep_running = key
        self._sweep_cancel = threading.Event()
        self._sweep_message = (
            f"{settings.points} fixed-activity diagrams on a {settings.pH_points} × {settings.eh_points} grid, "
            f"from log₁₀ a = {settings.log10_min:g} to {settings.log10_max:g}."
        )
        self._sweep_progress(0.0)
        self.requestSweep.emit(
            self.engine, Parameters.from_dict(self.params.to_dict()), settings, key,
            self._sweep_cancel,
        )

    @Slot(float)
    def _sweep_progress(self, fraction: float) -> None:
        if self._sweep_pending:
            self.sweep_stack.show_message(
                f"Calculating the concentration sweep… {fraction:.0%}", self._sweep_message, glyph="…",
            )

    @Slot(object, object, str)
    def _sweep_finished(self, key: tuple, sweep: Any, error: str) -> None:
        self._sweep_pending = False
        self._sweep_running = None
        current = self.engine.sweep_key(self.params, self.sweep_page.settings())
        if key != current or (sweep is None and not error):
            self._sweep_key = None
            self.request_sweep()
            return
        if error:
            self.sweep_stack.show_message("The sweep cannot be calculated", html.escape(error), glyph="!")
            return
        self._show_sweep(key, sweep)

    def _show_sweep(self, key: tuple, sweep: Any) -> None:
        level = self.result["concentration_input"]["log10_standard_activity"] if self.result else -6.0
        self.sweep_page.clear_materials_project()
        self._sweep_key = key
        self.sweep_page.set_sweep(
            sweep, self.display, level, (self.params.probe_pH, self.params.probe_eh_V)
        )
        self.sweep_stack.show_view()
        note = " Mass-balance settings are ignored; each slice is a fixed-activity diagram." if (
            self.params.mode == "mass_balance") else ""
        self._set_status(f"{sweep.system.system}: {len(sweep.diagrams)} slices.{note}")

    def update_periodic_table(self) -> None:
        reference = "RHE" if self.periodic_reference.currentIndex() == 1 else "SHE"
        try:
            screen = self.engine.periodic_table(
                self.params, self.periodic_pH.value(), self.periodic_potential.value(), reference
            )
        except Exception as error:  # reported in the status bar
            self._set_status(f"{type(error).__name__}: {error}", error=True)
            return
        self._periodic_conditions = screen["conditions"]
        self.periodic_canvas.show_screen(screen)
        self.periodic_canvas.set_selected(self.params.symbol)
        unit = CONCENTRATION_UNITS[self.params.concentration_unit]
        self.periodic_note.setText(
            f"Metal concentration {self.params.concentration_value:g} {unit}"
            + (", incomplete systems allowed" if self.params.allow_incomplete else "")
            + (", MP fallbacks in use" if self.params.use_mp_fallbacks else "")
            + ". These follow the System settings."
        )

    def load_table(self) -> None:
        name = self.table_combo.currentText()
        uri = f"file:{self.engine.database.path}?mode=ro"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            cursor = connection.execute(f'SELECT * FROM "{name}"')
            columns = [item[0] for item in cursor.description]
            rows = cursor.fetchall()
        self.table_model.clear()
        self.table_model.setHorizontalHeaderLabels(columns)
        for values in rows:
            items = []
            for value in values:
                item = QStandardItem("" if value is None else str(value))
                if isinstance(value, (int, float)):
                    item.setData(value, Qt.EditRole)
                items.append(item)
            self.table_model.appendRow(items)
        self.table_view.resizeColumnsToContents()
        for column in range(len(columns)):
            self.table_view.setColumnWidth(column, min(self.table_view.columnWidth(column), 360))
        self._filter_table(self.table_filter.text())

    def _filter_table(self, text: str) -> None:
        self.table_proxy.setFilterFixedString(text)
        self.table_count.setText(f"{self.table_proxy.rowCount()} of {self.table_model.rowCount()} rows")

    # -- actions -----------------------------------------------------------------------------

    def export_figure(self) -> None:
        if self.diagram is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export figure", f"pourbaix-{self.params.symbol.lower()}.png",
            "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)",
        )
        if not path:
            return
        import matplotlib.pyplot as plt

        from ..boltzmann import boltzmann_smooth
        from ..plotting import plot_boltzmann_diagram, plot_diagram, plot_mass_balance_summary

        options = dict(
            label_domains=self.display.labels, show_legend=self.display.legend,
            show_boundaries=self.display.boundaries, show_water=self.display.water,
        )
        title = f"{self.diagram.system.system} - experimental data"
        if self.params.mode == "mass_balance":
            figure, _ = plot_mass_balance_summary(self.diagram, title=title, **options)
        elif self.display.boltzmann:
            figure = plot_boltzmann_diagram(
                boltzmann_smooth(self.diagram, self.display.boltzmann_scale), title=title, **options
            ).figure
        else:
            figure = plot_diagram(self.diagram, title=title, **options).figure
        figure.savefig(path, dpi=300)
        plt.close(figure)
        self._set_status(f"Wrote {path}")

    def export_grid(self) -> None:
        if self.diagram is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export grid", f"pourbaix-grid-{self.params.symbol.lower()}.csv", "CSV (*.csv)"
        )
        if path:
            from ..service import render_grid_csv

            Path(path).write_bytes(render_grid_csv(self.diagram))
            self._set_status(f"Wrote {path}")

    def copy_python(self) -> None:
        QGuiApplication.clipboard().setText(self.params.python_code())
        self._set_status("Copied the equivalent Python code to the clipboard")

    # -- Materials Project -------------------------------------------------------------------

    def _start_task_worker(self) -> None:
        self._task_thread = QThread(self)
        self._task_worker = TaskWorker()
        self._task_worker.moveToThread(self._task_thread)
        self.requestTask.connect(self._task_worker.run)
        self._task_worker.finished.connect(self._task_finished)
        self._task_worker.progress.connect(self._task_progress)
        self._task_thread.start()

    def _start_task(self, task: str, function: Any) -> None:
        if task not in self._tasks:
            self._tasks.add(task)
            self.requestTask.emit(task, function)

    def _mp_key(self) -> tuple:
        filter_solids, gibbs_300K = self.mp_page.options()
        return (self.params.symbol, filter_solids, gibbs_300K)

    def _mp_fetched(self):
        return self.mp_source.fetched(*self._mp_key())

    def _mp_blocker(self) -> tuple[str, str, tuple | None] | None:
        """Why no comparison can be shown now, as (title, message, action), or None."""
        if not client_available():
            return (
                "The Materials Project client is not installed",
                "Comparisons use the official mp-api client and pymatgen. Install them with "
                "<code>pip install \"pourbase[materials-project]\"</code> and restart pourbase.",
                None,
            )
        if not self.mp_key:
            return (
                "A Materials Project API key is needed",
                "The key is free with a Materials Project account and is available on the "
                '<a href="https://materialsproject.org/api">API page</a>. pourbase can remember it '
                f"in {html.escape(storage_description())}.",
                ("Enter API key…", self.edit_api_key),
            )
        error = self._mp_errors.get(self._mp_key())
        if error:
            return ("Materials Project could not provide this element", html.escape(error),
                    ("Try again", lambda: self.fetch_materials_project(force=True)))
        return None

    def show_materials_project(self) -> None:
        self.pages.setCurrentIndex(1)
        self.views.setCurrentWidget(self.mp_stack)

    def fetch_materials_project(self, force: bool = False) -> bool:
        """Start downloading the entries for the current element; True when they are ready."""
        key = self._mp_key()
        if force:
            self.mp_source._fetched.pop(key, None)
            self._mp_errors.pop(key, None)
            self._mp_sweeps.clear()
        if self.mp_source.fetched(*key) is not None:
            return True
        if self._mp_blocker() is not None:
            return False
        symbol, filter_solids, gibbs_300K = key
        api_key = self.mp_key
        self._start_task(
            f"fetch:{symbol}:{filter_solids}:{gibbs_300K}",
            lambda _progress: self.mp_source.fetch(symbol, api_key, filter_solids, gibbs_300K),
        )
        self._set_status(f"Fetching the Materials Project entries for {symbol}…")
        return False

    def _materials_project_options_changed(self) -> None:
        self._mp_sweeps.clear()
        self.sweep_page.clear_materials_project()
        self._refresh_current_view()

    def _mp_experimental(self) -> tuple[Any, list[str]]:
        """The experimental fixed-activity diagram to compare, and notes on the comparison."""
        notes = []
        diagram = self.diagram
        if self.params.mode != "fixed_activity":
            from ..service import calculate

            fixed = Parameters.from_dict({**self.params.to_dict(), "mode": "fixed_activity"})
            diagram, _ = calculate(fixed.to_payload(), self.engine.database)
            notes.append("MP diagrams use fixed activities, so the experimental panel shows the "
                         "fixed-activity diagram at the same concentration.")
        if self.params.ligand_payload():
            notes.append("MP diagrams are ligand-free; the experimental panel includes the enabled ligands.")
        return diagram, notes

    def _refresh_materials_project(self, reset_range: bool = False) -> None:
        blocker = self._mp_blocker()
        if blocker is not None:
            self.mp_stack.show_message(blocker[0], blocker[1], blocker[2])
            return
        if self.diagram is None:
            self.mp_stack.show_message("No experimental diagram", "The comparison needs the experimental diagram.")
            return
        fetched = self._mp_fetched()
        if fetched is None:
            self.fetch_materials_project()
            self.mp_stack.show_message(
                f"Fetching the Materials Project entries for {self.params.symbol}…",
                "The entries are downloaded once per element and then evaluated locally for every "
                "setting, sweep and speciation view.", glyph="…",
            )
            return
        try:
            experimental, notes = self._mp_experimental()
            official = self.mp_source.diagram(fetched, experimental.conditions)
            self.mp_comparison = self.mp_source.compare(experimental, official)
        except Exception as error:  # shown in place of the comparison
            self.mp_stack.show_message("The comparison cannot be calculated",
                                       html.escape(f"{type(error).__name__}: {error}"), glyph="!")
            return
        first = self.mp_stack.currentWidget() is not self.mp_page
        self.mp_stack.show_view()
        self.mp_page.show_comparison(self.mp_comparison, self.display, notes, reset_range=first or reset_range)
        self.mp_page.set_probe(self.params.probe_pH, self.params.probe_eh_V)
        self._set_status(
            f"{self.result['system'] if self.result else self.params.symbol}: "
            f"{self.mp_comparison.equivalent_domain_fraction:.1%} of the grid agrees with Materials Project "
            f"{fetched.database_version}"
        )

    @Slot(str, float)
    def _task_progress(self, task: str, fraction: float) -> None:
        if task.startswith("mpsweep:"):
            self.sweep_page.hint.setText(f"Evaluating the Materials Project sweep… {fraction:.0%}")

    @Slot(str, object, str)
    def _task_finished(self, task: str, result: Any, error: str) -> None:
        self._tasks.discard(task)
        if task.startswith("fetch:"):
            _, symbol, filter_solids, gibbs_300K = task.split(":")
            key = (symbol, filter_solids == "True", gibbs_300K == "True")
            if error:
                self._mp_errors[key] = error
                self._set_status(error, error=True)
            else:
                self._set_status(f"Materials Project entries for {symbol}: database {result.database_version}")
            self._refresh_current_view()
            if self.views.currentWidget() is self.sweep_stack and self.sweep_page.source != "experimental":
                self.request_mp_sweep()
            self._refresh_probe()
        elif task.startswith("mpsweep:"):
            if error:
                self._set_status(error, error=True)
                self.sweep_page.hint.setText(error)
                return
            if result is None:
                return
            key, payload = result
            self._mp_sweeps[key] = payload
            self.request_mp_sweep()

    def request_mp_sweep(self) -> None:
        """Evaluate the MP entries on every level of the shown sweep, then add them to the page."""
        sweep = self.sweep_page.sweep
        if sweep is None:
            return
        blocker = self._mp_blocker()
        if blocker is not None:
            self.sweep_page.hint.setText(re.sub("<[^>]+>", "", blocker[1]))
            if not self.mp_key and client_available():
                self.edit_api_key()
            return
        if not self.fetch_materials_project():
            self.sweep_page.hint.setText(f"Fetching the Materials Project entries for {self.params.symbol}…")
            return
        fetched = self._mp_fetched()
        key = (self._sweep_key, self._mp_key())
        if key in self._mp_sweeps:
            index, phases, colors, same = self._mp_sweeps[key]
            self.sweep_page.set_materials_project(
                index, phases, colors, same,
                "Materials Project slices use the same activity for every aqueous species.",
            )
            return
        experimental = self.sweep_page.volumes["experimental"]
        species = experimental.species

        def work(progress):
            index, phases = self.mp_source.sweep(fetched, sweep, progress)
            official = self.mp_source.diagram(fetched, sweep.diagrams[0].conditions)
            colors = matched_colors(species, official, experimental.colors, record_colors)
            same = equivalence_matrix(species, official)[experimental.index, index]
            return key, (index, phases, colors, same)

        self._start_task(f"mpsweep:{hash(key)}", work)

    def _refresh_speciation_strip(self) -> None:
        diagram = self.diagram
        rows = []
        eh_index = int(np.abs(diagram.eh_V - self.params.probe_eh_V).argmin())
        experimental_colors = record_colors([item.record_id for item in diagram.stable_species])
        rows.append(("Experimental", diagram.stable_species_index[eh_index], diagram.system.species,
                     experimental_colors))
        fetched = self._mp_fetched() if client_available() and self.mp_key else None
        if fetched is not None:
            official = self.mp_source.diagram(fetched, diagram.conditions)
            colors = matched_colors(diagram.system.species, official, experimental_colors, record_colors)
            rows.append(("DFT (MP)", official.stable_phase_index[eh_index], phase_views(official), colors))
            self.speciation_mp_note.setText(
                f"Materials Project {fetched.database_version} at the same total activity. MP has no "
                "closed metal balance, so its row shows the lowest-energy phase."
            )
            self.speciation_mp_button.hide()
        else:
            blocker = self._mp_blocker()
            if blocker is not None:
                self.speciation_mp_note.setText(re.sub("<[^>]+>", "", blocker[0]) + ".")
                self.speciation_mp_button.setText(blocker[2][0] if blocker[2] else "")
                self.speciation_mp_button.setVisible(blocker[2] is not None)
            else:
                self.speciation_mp_note.setText("Compare with the official Materials Project DFT diagram.")
                self.speciation_mp_button.setText("Show DFT comparison")
                self.speciation_mp_button.show()
        self.speciation_strip.show_rows(diagram.pH, rows)

    def _speciation_mp_action(self) -> None:
        blocker = self._mp_blocker()
        if blocker is not None and blocker[2] is not None:
            blocker[2][1]()
        else:
            self.fetch_materials_project()
            self.speciation_mp_note.setText(f"Fetching the Materials Project entries for {self.params.symbol}…")
            self.speciation_mp_button.hide()

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
        key = QLineEdit(self.mp_key)
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
        remember.setChecked(self.mp_key_source in ("keyring", "settings") or not self.mp_key)
        layout.addWidget(remember)
        layout.addWidget(wrapped(f"The key is stored in {html.escape(storage_description())}."))
        if self.mp_key_source == "environment":
            layout.addWidget(wrapped("The current key comes from the MP_API_KEY environment variable."))
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        forget = buttons.addButton("Forget key", QDialogButtonBox.DestructiveRole)
        forget.clicked.connect(lambda: (key.clear(), remember.setChecked(False)))
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.adjustSize()
        dialog.setMinimumSize(dialog.sizeHint())
        if dialog.exec() != QDialog.Accepted:
            return
        value = key.text().strip()
        if remember.isChecked() and value:
            self.mp_key_source = save_key(self.settings, value)
        else:
            clear_key(self.settings)
            self.mp_key_source = "session" if value else ""
        if value != self.mp_key:
            self.mp_key = value
            self._mp_errors.clear()
        self._refresh_current_view()
        if self.views.currentWidget() is self.sweep_stack and self.sweep_page.source != "experimental":
            self.request_mp_sweep()

    def export_mp_figure(self) -> None:
        if self.mp_comparison is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export comparison", f"pourbaix-mp-{self.params.symbol.lower()}.png",
            "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)",
        )
        if not path:
            return
        import matplotlib.pyplot as plt

        from ..plotting import plot_official_materials_project_comparison

        figure, _ = plot_official_materials_project_comparison(self.mp_comparison)
        figure.savefig(path, dpi=300)
        plt.close(figure)
        self._set_status(f"Wrote {path}")

    def about(self) -> None:
        QMessageBox.about(
            self, "About pourbase",
            f"<b>pourbase {__version__}</b><p>Source-linked experimental thermochemistry and "
            "Pourbaix diagrams at 298.15 K and 1 bar.</p><p>Cite this release and the scientific "
            "sources attached to each value. See CITATION.cff and THIRD_PARTY_NOTICES.md.</p>",
        )

    # -- theme and status --------------------------------------------------------------------

    def set_theme(self, mode: str) -> None:
        self.theme_mode = mode if mode in THEME_MODES else "System"
        self.dark = apply_theme(self.theme_mode)
        self.theme_actions[self.theme_mode].setChecked(True)
        self.diagram_view.set_dark(self.dark)
        self.speciation_view.set_dark(self.dark)
        self.sweep_page.set_dark(self.dark)
        self.mp_page.set_dark(self.dark)
        self.speciation_strip.set_dark(self.dark)
        self.periodic_canvas.set_dark(self.dark)
        self._draw()
        if hasattr(self, "_status"):
            self._set_status(*self._status)

    def _set_status(self, text: str, error: bool = False) -> None:
        self._status = (text, error)
        color = "#e06c75" if (error and self.dark) else ("#b00020" if error else "")
        self.status_label.setStyleSheet(f"color: {color};" if color else "")
        self.status_label.setText(text)
