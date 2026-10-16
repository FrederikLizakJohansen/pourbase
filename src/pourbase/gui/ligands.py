"""Editor for buffered ligand reservoirs."""

from __future__ import annotations

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QGridLayout, QLabel, QVBoxLayout, QWidget

from ..models import LigandReference
from .formula import pretty_formula, to_html
from .state import LIGAND_MODES, LigandSetting

SHOWN = 6  # complexes listed before "+ N more"
SUPERSCRIPTS = "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻"


def complex_order(name: str) -> tuple:
    """Simpler complexes first: by formula length without charge, then by charge."""
    base = re.sub(r"\s+\([^()]*\)$", "", name)
    core = "".join(character for character in base if character not in SUPERSCRIPTS)
    return (len(core), core, base)


class LigandRow(QWidget):
    """Controls for one ligand on two rows."""

    def __init__(self, reference: LigandReference, changed) -> None:
        super().__init__()
        self.reference = reference
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 4, 0, 4)
        grid.setColumnStretch(1, 1)
        row = 0
        self.enabled = QCheckBox(reference.name)
        self.mode = QComboBox()
        for key, label in LIGAND_MODES.items():
            self.mode.addItem(label, key)
        self.value = QDoubleSpinBox()
        self.value.setKeyboardTracking(False)
        self.use_pKa = QCheckBox("pKa")
        self.use_pKa.setToolTip("Protonation of the pool: HL ⇌ H⁺ + L; the free fraction follows pH")
        self.pKa = QDoubleSpinBox()
        self.pKa.setRange(-5.0, 20.0)
        self.pKa.setDecimals(2)
        self.pKa.setKeyboardTracking(False)
        self.count = QLabel()
        self.count.setStyleSheet("color: gray;")
        self.count.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.species = QLabel()
        self.species.setTextFormat(Qt.RichText)
        self.species.setWordWrap(True)
        self.species.setStyleSheet("color: gray;")
        grid.addWidget(self.enabled, row, 0, 1, 2)
        grid.addWidget(self.count, row, 2, 1, 2)
        grid.addWidget(self.species, row + 1, 0, 1, 4)
        grid.addWidget(self.mode, row + 2, 0)
        grid.addWidget(self.value, row + 2, 1)
        grid.addWidget(self.use_pKa, row + 2, 2)
        grid.addWidget(self.pKa, row + 2, 3)
        self._setting = LigandSetting()
        self._changed = changed
        self._updating = False
        self.enabled.toggled.connect(self._read)
        self.mode.currentIndexChanged.connect(self._mode_changed)
        self.value.valueChanged.connect(self._read)
        self.use_pKa.toggled.connect(self._read)
        self.pKa.valueChanged.connect(self._read)

    def set_setting(self, setting: LigandSetting) -> None:
        self._updating = True
        self._setting = setting
        self.enabled.setChecked(setting.enabled)
        self.mode.setCurrentIndex(max(self.mode.findData(setting.mode), 0))
        self._configure_value()
        self.use_pKa.setChecked(setting.use_pKa)
        self.pKa.setValue(setting.acid_pKa)
        self._updating = False
        self._update_enabled()

    def set_relevant(self, species: list[str] | None) -> None:
        ordered = sorted(dict.fromkeys(species or []), key=complex_order)
        self.setVisible(bool(ordered))
        if not ordered:
            return
        shown = " · ".join(to_html(pretty_formula(name), 8.0) for name in ordered[:SHOWN])
        more = len(ordered) - SHOWN
        self.species.setText(f"<span style='font-size:8pt'>{shown}"
                             + (f" · + {more} more" if more > 0 else "") + "</span>")
        self.count.setText(f"{len(ordered)} complex{'es' if len(ordered) != 1 else ''}")
        tooltip = "Complexes with this ligand:\n" + "\n".join(ordered)
        for widget in (self.species, self.count, self.enabled):
            widget.setToolTip(tooltip)

    def _configure_value(self) -> None:
        if self._setting.mode == "free":
            self.value.setRange(-12.0, 1.0)
            self.value.setDecimals(2)
            self.value.setSingleStep(0.5)
            self.value.setSuffix("")
            self.value.setValue(self._setting.log10_free_activity)
        else:
            self.value.setRange(1e-9, 10.0)
            self.value.setDecimals(6)
            self.value.setSingleStep(0.001)
            self.value.setSuffix(" mol/L")
            self.value.setValue(self._setting.total_unbound_mol_L)

    def _mode_changed(self) -> None:
        if self._updating:
            return
        self._setting.mode = self.mode.currentData()
        self._updating = True
        self._configure_value()
        self._updating = False
        self._update_enabled()
        self._changed()

    def _update_enabled(self) -> None:
        enabled = self._setting.enabled
        total = self._setting.mode == "total"
        self.mode.setEnabled(enabled)
        self.value.setEnabled(enabled)
        self.use_pKa.setEnabled(enabled and total)
        self.pKa.setEnabled(enabled and total and self._setting.use_pKa)

    def _read(self) -> None:
        if self._updating:
            return
        setting = self._setting
        setting.enabled = self.enabled.isChecked()
        if setting.mode == "free":
            setting.log10_free_activity = self.value.value()
        else:
            setting.total_unbound_mol_L = self.value.value()
        setting.use_pKa = self.use_pKa.isChecked()
        setting.acid_pKa = self.pKa.value()
        self._update_enabled()
        self._changed()

    @property
    def setting(self) -> LigandSetting:
        return self._setting


class LigandPanel(QWidget):
    """Every database ligand; only those forming complexes with the current element are shown."""

    changed = Signal()

    def __init__(self, ligands: tuple[LigandReference, ...], parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.note = QLabel()
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        self.rows = {
            reference.ligand_id: LigandRow(reference, self.changed.emit) for reference in ligands
        }
        for row in self.rows.values():
            layout.addWidget(row)

    def set_settings(self, settings: dict[str, LigandSetting]) -> None:
        for ligand_id, row in self.rows.items():
            row.set_setting(settings.setdefault(ligand_id, LigandSetting()))

    def set_system(self, symbol: str, species_by_ligand: dict[str, list[str]]) -> None:
        for ligand_id, row in self.rows.items():
            row.set_relevant(species_by_ligand.get(ligand_id))
        self.note.setText(
            "Buffered free-ligand reservoirs; the model does not solve a closed ligand balance."
            if species_by_ligand else
            f"The database holds no ligand complexes for {symbol}."
        )
