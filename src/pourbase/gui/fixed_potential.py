"""Diagrams at the potential of the probe: solubility against pH, and ligand predominance against pH."""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QRadioButton, QVBoxLayout, QWidget,
)

from .figure_export import install_export_menu
from .formula import to_html
from .placeholder import StackedView
from .plots import LABEL_PT, DiagramView, DisplayOptions, apply_plot_theme, record_colors

SOLUBILITY, PREDOMINANCE = "solubility", "predominance"


class FixedPotentialPage(StackedView):
    """Two classic diagrams at one potential, set by the probe."""

    changed = Signal()
    potentialChanged = Signal(float)

    def __init__(self, parent=None) -> None:
        body = QWidget()
        layout = QVBoxLayout(body)
        controls = QHBoxLayout()
        self.solubility_button = QRadioButton("Solubility")
        self.predominance_button = QRadioButton("Ligand predominance")
        self.solubility_button.setChecked(True)
        group = QButtonGroup(body)
        for button in (self.solubility_button, self.predominance_button):
            group.addButton(button)
            controls.addWidget(button)
        controls.addSpacing(16)
        controls.addWidget(QLabel("Eh (V vs SHE)"))
        self.eh = QDoubleSpinBox()
        self.eh.setRange(-4.0, 4.0)
        self.eh.setDecimals(3)
        self.eh.setSingleStep(0.05)
        self.eh.setKeyboardTracking(False)
        self.eh.setToolTip("The potential of the probe; moving the probe in the diagram changes it too")
        controls.addWidget(self.eh)
        self.ligand_label = QLabel("Ligand")
        self.ligand = QComboBox()
        controls.addSpacing(16)
        controls.addWidget(self.ligand_label)
        controls.addWidget(self.ligand)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setTextFormat(Qt.RichText)
        layout.addWidget(self.summary)
        self.plot = pg.PlotWidget()
        self.plot.setMenuEnabled(False)
        self.plot.getPlotItem().setContentsMargins(4, 12, 14, 4)
        self.plot.setLabel("bottom", "pH")
        self.plot.setLabel("left", "log₁₀ (dissolved metal / mol L⁻¹)")
        self.legend = self.plot.addLegend(offset=(-10, 36), labelTextSize=f"{LABEL_PT:g}pt")
        install_export_menu(self.plot, self.export_table, "pourbase-solubility")
        self.grid = DiagramView()
        layout.addWidget(self.plot, 1)
        layout.addWidget(self.grid, 1)
        super().__init__(body, parent)
        self.eh.valueChanged.connect(self.potentialChanged)
        self.ligand.currentIndexChanged.connect(lambda _index: self.changed.emit())
        for button in (self.solubility_button, self.predominance_button):
            button.toggled.connect(lambda checked: checked and self._mode_changed())
        self.result = None
        self.dark = False
        apply_plot_theme(self.plot, False)
        self._mode_changed(emit=False)

    def mode(self) -> str:
        return SOLUBILITY if self.solubility_button.isChecked() else PREDOMINANCE

    def _mode_changed(self, emit: bool = True) -> None:
        predominance = self.mode() == PREDOMINANCE
        self.ligand_label.setVisible(predominance)
        self.ligand.setVisible(predominance)
        self.plot.setVisible(not predominance)
        self.grid.setVisible(predominance)
        if emit:
            self.changed.emit()

    def set_dark(self, dark: bool) -> None:
        self.dark = dark
        apply_plot_theme(self.plot, dark)
        self.grid.set_dark(dark)

    def set_potential(self, eh_V: float) -> None:
        self.eh.blockSignals(True)
        self.eh.setValue(eh_V)
        self.eh.blockSignals(False)

    def set_ligands(self, ligands: list[tuple[str, str]]) -> None:
        """``(ligand ID, name)`` of the ligands that form species with this element."""
        current = self.ligand.currentData()
        self.ligand.blockSignals(True)
        self.ligand.clear()
        for ligand_id, name in ligands:
            self.ligand.addItem(name, ligand_id)
        self.ligand.setCurrentIndex(max(self.ligand.findData(current), 0))
        self.ligand.blockSignals(False)

    def show_solubility(self, result, log10_metal: float, mass_balance: bool) -> None:
        self.result = result
        plot = self.plot
        plot.clear()
        self.legend.clear()
        colors = record_colors([item.record_id for item in result.species])
        pH = result.pH
        low = max(float(np.nanmin(result.log10_total_mol_L)) - 4, -16)
        high = min(max(float(np.nanmax(result.log10_total_mol_L)) + 1, log10_metal + 1, 0.5), 4)
        clipped = np.clip(result.log10_metal_mol_L, low - 1, high + 1)
        for item, row in zip(result.species, clipped):
            if np.nanmax(row) < low:
                continue  # never contributes within the plotted range
            line = plot.plot(pH, row, pen=pg.mkPen(colors[item.record_id], width=1.4))
            self.legend.addItem(line, to_html(item.species))
        text = "#dfe1e5" if self.dark else "#000000"
        total = plot.plot(pH, np.clip(result.log10_total_mol_L, low - 1, high + 1), pen=pg.mkPen(text, width=2.6))
        self.legend.addItem(total, "Total dissolved")
        top = pg.PlotDataItem(pH, np.full_like(pH, high + 1))
        fill = pg.FillBetweenItem(total, top, brush=pg.mkBrush(128, 128, 128, 40))
        plot.addItem(fill)
        level = pg.InfiniteLine(log10_metal, angle=0, pen=pg.mkPen("#c0392b", width=1.4, style=Qt.DashLine))
        plot.addItem(level)
        start = 0
        for column in range(1, pH.size + 1):  # name the controlling solid along the top
            if column == pH.size or result.solid_index[column] != result.solid_index[start]:
                solid = result.solids[int(result.solid_index[start])]
                label = pg.TextItem(html=f'<span style="color:{text}; font-size:{LABEL_PT}pt">'
                                         f"{to_html(solid.species, LABEL_PT)}</span>", anchor=(0.5, 0))
                label.setPos(float((pH[start] + pH[column - 1]) / 2), high)
                plot.addItem(label)
                if column < pH.size:
                    plot.addItem(pg.InfiniteLine(float(pH[column]), angle=90,
                                                 pen=pg.mkPen((128, 128, 128), width=1, style=Qt.DotLine)))
                start = column
        plot.setXRange(float(pH[0]), float(pH[-1]), padding=0)
        plot.setYRange(low, high, padding=0)
        model = ("In the mass-balance model this is where the solid precipitates." if mass_balance
                 else "In a fixed-activity diagram the solid is stable wherever the line lies below the total.")
        self.summary.setText(
            f"Dissolved metal in equilibrium with the most stable solid at {result.eh_V:+.3f} V vs SHE, with ideal "
            f"activities (Eqs. 6 and 7). The shaded region lies above saturation. The dashed red line is the metal "
            f"concentration of the system, 10<sup>{log10_metal:.2f}</sup> mol/L. {model}")
        self.show_view()

    def show_predominance(self, result, ligand_name: str, log10_metal: float) -> None:
        self.result = result
        self.grid.show_grid(result.stable_species_index, result.pH, result.log10_activity, result.species,
                            DisplayOptions(legend=False), reset_range=True,
                            axes=("pH", f"log₁₀ a({ligand_name})"))
        self.summary.setText(
            f"Stable species over pH and the free activity of {ligand_name} at {result.eh_V:+.3f} V vs SHE, for "
            f"a fixed metal activity of 10<sup>{log10_metal:.2f}</sup> and the other ligands as set in the System "
            "tab.")
        self.show_view()

    def export_table(self):
        result = self.result
        if result is None or self.mode() != SOLUBILITY or not hasattr(result, "log10_total_mol_L"):
            return None
        header = ["pH", "log10 total (mol/L)", "controlling solid",
                  *(f"log10 {item.species} (mol/L metal)" for item in result.species)]
        rows = [[f"{result.pH[i]:.4g}", f"{result.log10_total_mol_L[i]:.6g}",
                 result.solids[int(result.solid_index[i])].species,
                 *(f"{value:.6g}" for value in result.log10_metal_mol_L[:, i])] for i in range(result.pH.size)]
        return header, rows
