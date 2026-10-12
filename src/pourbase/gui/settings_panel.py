"""The System, Grid and Display settings of one element."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QLabel, QPushButton,
    QScrollArea, QSpinBox, QStyle, QTabWidget, QVBoxLayout, QWidget,
)

from ..conversions import express_concentration
from ..database import ThermodynamicDatabase
from .ligands import LigandPanel
from .plots import DisplayOptions
from .scales import REFERENCE_ELECTRODES_V
from .state import CONCENTRATION_UNITS, MAX_GRID_POINTS, MODES, Settings
from .widgets import FloatSlider

UNIT_RANGES = {
    "log10_molar": (-12.0, 1.0, False, 3),
    "molar": (1e-12, 10.0, True, 12),
    "ppm": (1e-6, 1e5, True, 6),
    "wt_percent": (1e-8, 50.0, True, 8),
}
DISPLAY_CHECKS = (
    ("labels", "Domain labels"),
    ("legend", "Legend"),
    ("boundaries", "Phase boundaries"),
    ("water", "Water stability lines"),
    ("plating", "Direct plating potential (fixed activity)"),
)


def _scroll(widget: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    area.setWidget(widget)
    return area


class SettingsPanel(QTabWidget):
    """Edits :class:`Settings` and :class:`DisplayOptions`.

    ``changed(reset_range)`` reports a new calculation request; ``displayChanged`` only
    affects drawing; ``probeChanged`` moves the probe.
    """

    changed = Signal(bool)
    displayChanged = Signal()
    probeChanged = Signal(float, float)

    def __init__(self, database: ThermodynamicDatabase, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.settings = Settings()
        self.display = DisplayOptions()
        self._updating = False
        self.systems = dict(database.available_systems())
        pages = (self._system_tab(), self._grid_tab(), self._display_tab())
        for page, title in zip(pages, ("System", "Grid", "Display")):
            self.addTab(_scroll(page), title)
        widest = max(page.minimumSizeHint().width() for page in pages)
        self.setMinimumWidth(widest + self.style().pixelMetric(QStyle.PM_ScrollBarExtent) + 24)

    def _system_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        box = QGroupBox("Element")
        form = QFormLayout(box)
        self.symbol = QComboBox()
        for symbol, name in self.systems.items():
            self.symbol.addItem(name, symbol)
        self.symbol.currentIndexChanged.connect(lambda _index: self._set("symbol", self.symbol.currentData()))
        form.addRow("System", self.symbol)
        self.mode = QComboBox()
        for key, label in MODES.items():
            self.mode.addItem(label, key)
        self.mode.currentIndexChanged.connect(lambda _index: self._set("mode", self.mode.currentData()))
        form.addRow("Model", self.mode)
        layout.addWidget(box)

        box = QGroupBox("Metal concentration")
        form = QFormLayout(box)
        self.unit = QComboBox()
        for key, label in CONCENTRATION_UNITS.items():
            self.unit.addItem(label, key)
        self.unit.currentIndexChanged.connect(self._unit_changed)
        form.addRow("Unit", self.unit)
        self.concentration = FloatSlider("Value", -12.0, 1.0, -6.0, decimals=3, step=0.5, label_width=50)
        self.concentration.valueChanged.connect(lambda value: self._set("concentration", value))
        form.addRow(self.concentration)
        self.density = QDoubleSpinBox()
        self.density.setRange(0.5, 3.0)
        self.density.setDecimals(3)
        self.density.setSingleStep(0.01)
        self.density.setSuffix(" kg/L")
        self.density.setToolTip("Solution density, used to convert weight percent")
        self.density.valueChanged.connect(lambda value: self._set("solution_density_kg_L", value))
        form.addRow("Solution density", self.density)
        self.concentration_note = QLabel()
        form.addRow(self.concentration_note)
        layout.addWidget(box)

        box = QGroupBox("Activities")
        form = QFormLayout(box)
        self.davies = QCheckBox("Davies activity coefficients (mass balance)")
        self.davies.toggled.connect(lambda value: self._set("davies", value))
        form.addRow(self.davies)
        self.ionic_strength = FloatSlider("I", 0.0, 0.1, 0.01, decimals=4, step=0.005, unit="mol/L", label_width=20)
        self.ionic_strength.valueChanged.connect(lambda value: self._set("ionic_strength_mol_L", value))
        form.addRow("Ionic strength", self.ionic_strength)
        self.gas = FloatSlider("", -12.0, 2.0, 0.0, decimals=2, step=0.5, label_width=0)
        self.gas.setToolTip("log₁₀ of every gas fugacity relative to 1 bar")
        self.gas.valueChanged.connect(lambda value: self._set("log10_gas_fugacity", value))
        form.addRow("log₁₀ gas fugacity", self.gas)
        layout.addWidget(box)

        box = QGroupBox("Evidence policy")
        column = QVBoxLayout(box)
        self.allow_incomplete = QCheckBox("Allow incomplete systems (omit species without Gibbs data)")
        self.allow_incomplete.toggled.connect(lambda value: self._set("allow_incomplete", value))
        self.use_mp_fallbacks = QCheckBox("Fill missing solid Gibbs values with labelled MP 300 K estimates")
        self.use_mp_fallbacks.toggled.connect(lambda value: self._set("use_mp_fallbacks", value))
        column.addWidget(self.allow_incomplete)
        column.addWidget(self.use_mp_fallbacks)
        layout.addWidget(box)

        box = QGroupBox("Ligands")
        self.ligands = LigandPanel(self.database.available_ligands())
        self.ligands.changed.connect(self._ligands_changed)
        QVBoxLayout(box).addWidget(self.ligands)
        layout.addWidget(box)
        layout.addStretch(1)
        return page

    def _grid_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        box = QGroupBox("Axes")
        form = QFormLayout(box)
        self.axes: dict[str, QDoubleSpinBox] = {}
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
            spin.valueChanged.connect(lambda value, name=name: self._set(name, value, reset_range=True))
            self.axes[name] = spin
            form.addRow(label, spin)
        self.points: dict[str, QSpinBox] = {}
        for name, label in (("pH_points", "pH points"), ("eh_points", "Eh points")):
            spin = QSpinBox()
            spin.setRange(11, MAX_GRID_POINTS)
            spin.setSingleStep(20)
            spin.setKeyboardTracking(False)
            spin.setToolTip("Grid resolution along this axis")
            spin.valueChanged.connect(lambda value, name=name: self._set(name, value))
            self.points[name] = spin
            form.addRow(label, spin)
        reset = QPushButton("Default axes")
        reset.clicked.connect(self.reset_axes)
        form.addRow(reset)
        layout.addWidget(box)

        box = QGroupBox("Probe point")
        form = QFormLayout(box)
        self.probe_pH = QDoubleSpinBox()
        self.probe_pH.setRange(-4.0, 18.0)
        self.probe_eh = QDoubleSpinBox()
        self.probe_eh.setRange(-4.0, 4.0)
        self.probe_eh.setDecimals(3)
        self.probe_eh.setSingleStep(0.05)
        for spin in (self.probe_pH, self.probe_eh):
            spin.setKeyboardTracking(False)
            spin.valueChanged.connect(lambda _value: self._probe_edited())
        form.addRow("pH", self.probe_pH)
        form.addRow("Eh (V vs SHE)", self.probe_eh)
        hint = QLabel("Click or drag in the diagram to move the probe.")
        hint.setWordWrap(True)
        form.addRow(hint)
        layout.addWidget(box)
        layout.addStretch(1)
        return page

    def _display_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        box = QGroupBox("Diagram")
        column = QVBoxLayout(box)
        self.display_checks: dict[str, QCheckBox] = {}
        for name, label in DISPLAY_CHECKS:
            check = QCheckBox(label)
            check.setChecked(getattr(self.display, name))
            check.toggled.connect(lambda value, name=name: self._set_display(name, value))
            self.display_checks[name] = check
            column.addWidget(check)
        layout.addWidget(box)
        box = QGroupBox("Potential scale")
        form = QFormLayout(box)
        self.potential_scale = QComboBox()
        for name, offset in REFERENCE_ELECTRODES_V.items():
            detail = "pH-dependent" if offset is None else f"{offset:+.3f} V vs SHE"
            self.potential_scale.addItem(f"{name}  ({detail})" if name != "SHE" else name, name)
        self.potential_scale.currentIndexChanged.connect(
            lambda _index: self._set_display("potential_scale", self.potential_scale.currentData()))
        form.addRow("Diagram axis", self.potential_scale)
        note = QLabel("Calculations and the probe position use the SHE. On the RHE scale, regions outside "
                      "the calculated potential window stay empty.")
        note.setWordWrap(True)
        form.addRow(note)
        layout.addWidget(box)
        box = QGroupBox("Uncertainty (fixed activity)")
        form = QFormLayout(box)
        self.uncertainty = QCheckBox("Hatch where another species lies within")
        self.uncertainty.toggled.connect(lambda value: self._set_display("uncertainty", value))
        form.addRow(self.uncertainty)
        self.uncertainty_sigma = QComboBox()
        for sigma in (1.0, 2.0, 3.0):
            self.uncertainty_sigma.addItem(f"{sigma:g} σ", sigma)
        self.uncertainty_sigma.currentIndexChanged.connect(
            lambda _index: self._set_display("uncertainty_sigma", self.uncertainty_sigma.currentData()))
        form.addRow("Confidence", self.uncertainty_sigma)
        self.assumed_uncertainty = FloatSlider("Assumed σ", 0.1, 20.0, self.display.assumed_uncertainty_kJ_mol,
                                               decimals=1, unit="kJ/mol", label_width=70)
        self.assumed_uncertainty.valueChanged.connect(
            lambda value: self._set_display("assumed_uncertainty_kJ_mol", value))
        form.addRow(self.assumed_uncertainty)
        note = QLabel("Reported ΔfG° uncertainties are used where available and reference states are exact; "
                      "other species take the assumed σ. The probe panel shows the margin to the runner-up.")
        note.setWordWrap(True)
        form.addRow(note)
        layout.addWidget(box)
        box = QGroupBox("Blend dissolved species")
        form = QFormLayout(box)
        self.boltzmann = QCheckBox("Blend the colors of dissolved species")
        self.boltzmann.toggled.connect(lambda value: self._set_display("boltzmann", value))
        form.addRow(self.boltzmann)
        self.blend_width = FloatSlider("Width", 0.1, 50.0, self.display.blend_width_kJ_mol, decimals=2,
                                           log=True, unit="kJ/mol", label_width=40)
        self.blend_width.valueChanged.connect(lambda value: self._set_display("blend_width_kJ_mol", value))
        form.addRow(self.blend_width)
        note = QLabel("Mass balance: colors mix by the fractions of the dissolved species. Fixed activity: "
                      "weights ∝ exp(−(G − Gmin) / width) among dissolved species; at a width of RT "
                      "(2.48 kJ/mol) these are their fractions. Solids keep sharp edges in both.")
        note.setWordWrap(True)
        form.addRow(note)
        layout.addWidget(box)
        layout.addStretch(1)
        return page

    def set_settings(self, settings: Settings) -> None:
        """Show ``settings`` in the controls without emitting changes."""
        self.settings = settings
        self._updating = True
        self.symbol.setCurrentIndex(max(self.symbol.findData(settings.symbol), 0))
        self.mode.setCurrentIndex(max(self.mode.findData(settings.mode), 0))
        self.unit.setCurrentIndex(max(self.unit.findData(settings.concentration_unit), 0))
        self._configure_concentration()
        self.density.setValue(settings.solution_density_kg_L)
        self.davies.setChecked(settings.davies)
        self.ionic_strength.setValue(settings.ionic_strength_mol_L)
        self.gas.setValue(settings.log10_gas_fugacity)
        self.allow_incomplete.setChecked(settings.allow_incomplete)
        self.use_mp_fallbacks.setChecked(settings.use_mp_fallbacks)
        for name, spin in {**self.axes, **self.points}.items():
            spin.setValue(getattr(settings, name))
        self.probe_pH.setValue(settings.probe_pH)
        self.probe_eh.setValue(settings.probe_eh_V)
        self.ligands.set_settings(settings.ligands)
        self.ligands.set_system(settings.symbol, self.database.ligand_species.get(settings.symbol, {}))
        self._updating = False
        self._update_enabled()

    def set_probe(self, pH: float, eh_V: float) -> None:
        self.settings.probe_pH, self.settings.probe_eh_V = pH, eh_V
        self._updating = True
        self.probe_pH.setValue(pH)
        self.probe_eh.setValue(eh_V)
        self._updating = False

    def set_concentration_note(self, molar: float, log10_activity: float) -> None:
        self.concentration_note.setText(f"{molar:.3g} mol/L, log₁₀ a = {log10_activity:.3f}")

    def reset_axes(self) -> None:
        defaults = Settings()
        for name in (*self.axes, *self.points):
            setattr(self.settings, name, getattr(defaults, name))
        self.set_settings(self.settings)
        self.changed.emit(True)

    def _configure_concentration(self) -> None:
        low, high, log, decimals = UNIT_RANGES[self.settings.concentration_unit]
        if not low <= self.settings.concentration <= high:
            self.settings.concentration = express_concentration(
                self.settings.symbol, 1e-6, self.settings.concentration_unit,
                solution_density_kg_L=self.settings.solution_density_kg_L,
            )
        self.concentration.set_range(low, high, log, decimals)
        self.concentration.setValue(self.settings.concentration)

    def _unit_changed(self) -> None:
        if self._updating:
            return
        settings = self.settings
        molar = settings.scenario().concentration_conversion.molar_concentration
        settings.concentration_unit = self.unit.currentData()
        settings.concentration = express_concentration(
            settings.symbol, molar, settings.concentration_unit, solution_density_kg_L=settings.solution_density_kg_L,
        )
        self._updating = True
        self._configure_concentration()
        self._updating = False
        self._update_enabled()
        self.changed.emit(False)

    def _update_enabled(self) -> None:
        mass_balance = self.settings.mode == "mass_balance"
        self.davies.setEnabled(mass_balance)
        self.ionic_strength.setEnabled(mass_balance and self.settings.davies)
        self.density.setEnabled(self.settings.concentration_unit == "wt_percent")
        self.blend_width.setEnabled(not mass_balance)
        for widget in (self.uncertainty, self.uncertainty_sigma, self.assumed_uncertainty):
            widget.setEnabled(not mass_balance)
        self.display_checks["plating"].setEnabled(not mass_balance)

    def _set(self, name: str, value: object, reset_range: bool = False) -> None:
        if self._updating:
            return
        setattr(self.settings, name, value)
        if name == "symbol":
            self.ligands.set_system(value, self.database.ligand_species.get(value, {}))
        self._update_enabled()
        self.changed.emit(reset_range)

    def _ligands_changed(self) -> None:
        if not self._updating:
            self.changed.emit(False)

    def _set_display(self, name: str, value: object) -> None:
        if self._updating:
            return
        setattr(self.display, name, value)
        self.displayChanged.emit()

    def set_display(self, display: DisplayOptions) -> None:
        """Show ``display`` in the controls without emitting changes."""
        self._updating = True
        for name, check in self.display_checks.items():
            check.setChecked(getattr(display, name))
        self.potential_scale.setCurrentIndex(max(self.potential_scale.findData(display.potential_scale), 0))
        self.uncertainty.setChecked(display.uncertainty)
        self.uncertainty_sigma.setCurrentIndex(max(self.uncertainty_sigma.findData(display.uncertainty_sigma), 0))
        self.assumed_uncertainty.setValue(display.assumed_uncertainty_kJ_mol)
        self.boltzmann.setChecked(display.boltzmann)
        self.blend_width.setValue(display.blend_width_kJ_mol)
        for name, value in vars(display).items():
            setattr(self.display, name, value)
        self._updating = False

    def _probe_edited(self) -> None:
        if not self._updating:
            self.settings.probe_pH, self.settings.probe_eh_V = self.probe_pH.value(), self.probe_eh.value()
            self.probeChanged.emit(self.settings.probe_pH, self.settings.probe_eh_V)
