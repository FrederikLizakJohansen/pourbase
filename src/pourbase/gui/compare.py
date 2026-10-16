"""Two diagrams side by side with linked axes: the current system and a second scenario."""

from __future__ import annotations

import html
from dataclasses import replace
from typing import Any

import numpy as np
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QTextBrowser, QWidget

from ..uncertainty import stability_margin
from .formula import phase_label, to_html
from .pages import status_label
from .placeholder import StackedView
from .plots import DiagramView, DisplayOptions, record_colors
from .scales import to_scale
from .widgets import FloatSlider


class ComparePage(StackedView):
    """The current diagram on the left and the same settings for another element or
    concentration on the right. Species shared by both diagrams keep one color."""

    changed = Signal()
    preview = Signal()  # the slider moved: a coarse diagram can be drawn at once

    def __init__(self, systems: dict[str, str], parent=None) -> None:
        body = QWidget()
        grid = QGridLayout(body)
        grid.setContentsMargins(0, 0, 0, 0)
        controls = QWidget()
        form = QHBoxLayout(controls)
        form.setContentsMargins(0, 0, 0, 0)
        right = QFormLayout()
        self.symbol = QComboBox()
        for symbol, name in sorted(systems.items(), key=lambda item: item[1]):
            self.symbol.addItem(name, symbol)
        self.concentration = FloatSlider("log₁₀ c", -12.0, 1.0, -4.0, decimals=2, unit="mol/L", label_width=50)
        right.addRow("Right element", self.symbol)
        form.addLayout(right)
        form.addWidget(self.concentration, 1)
        self.temperature = FloatSlider("T", 0.0, 100.0, 25.0, decimals=1, step=5.0, unit="°C", label_width=20)
        self.temperature.setToolTip("Temperature of the right diagram; the left one follows System → Temperature")
        form.addWidget(self.temperature, 1)
        self.left_title, self.right_title = QLabel(), QLabel()
        self.views = (DiagramView(), DiagramView())
        self.cursors = (QLabel(" "), QLabel(" "))
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.details = QTextBrowser()
        self.details.setFixedHeight(130)
        for column, (title, view, cursor) in enumerate(zip(
                (self.left_title, self.right_title), self.views, self.cursors, strict=True)):
            title.setTextFormat(Qt.RichText)
            cursor.setTextFormat(Qt.RichText)
            grid.addWidget(title, 1, column)
            grid.addWidget(view, 2, column)
            grid.addWidget(cursor, 3, column)
            view.cursorMoved.connect(lambda text, cursor=cursor: cursor.setText(text or " "))
            view.probeMoved.connect(self.set_point)
        grid.addWidget(controls, 0, 0, 1, 2)
        grid.addWidget(self.summary, 4, 0, 1, 2)
        grid.addWidget(self.details, 5, 0, 1, 2)
        grid.setRowStretch(2, 1)
        super().__init__(body, parent)
        self.views[1].setXLink(self.views[0])
        self.views[1].setYLink(self.views[0])
        self.calculations: tuple[Any, Any] | None = None
        self.display = DisplayOptions()
        self.point: tuple[float, float] | None = None
        self.symbol.currentIndexChanged.connect(lambda _index: self.changed.emit())
        # wait until the slider settles before recalculating the right diagram
        self._settle = QTimer(self, singleShot=True, interval=120)
        self._settle.timeout.connect(self.changed.emit)
        self.concentration.valueChanged.connect(lambda _value: (self.preview.emit(), self._settle.start()))
        self.temperature.valueChanged.connect(lambda _value: (self.preview.emit(), self._settle.start()))

    def set_dark(self, dark: bool) -> None:
        for view in self.views:
            view.set_dark(dark)

    def right_settings(self, settings: Any) -> Any:
        """The current settings with the right panel's element and concentration."""
        symbol = self.symbol.currentData() or settings.symbol
        ligands = settings.ligands if symbol == settings.symbol else {}
        return replace(settings, symbol=symbol, concentration=self.concentration.value(),
                       concentration_unit="log10_molar", ligands=ligands, temperature_C=self.temperature.value())

    def show_calculations(self, left: Any, right: Any, display: DisplayOptions, reset_range: bool,
                          point: tuple[float, float] = (7.0, 0.0)) -> None:
        """Draw both diagrams; ``point`` (pH, Eh vs SHE) places the shared probe the first time."""
        self.calculations, self.display = (left, right), display
        stable = [item.record_id for item in (*left.stable_species, *right.stable_species)]
        colors = record_colors(stable)
        for view, calculation in zip(self.views, (left, right), strict=True):
            view.show_diagram(calculation.diagram, display, reset_range=reset_range, colors=colors)
        for title, calculation in zip((self.left_title, self.right_title), (left, right), strict=True):
            conversion = calculation.concentration
            title.setText(f"{calculation.diagram.system.system}, log₁₀ c = "
                          f"{np.log10(conversion.molar_concentration):.2f} mol/L ({calculation.scenario.mode.value.replace('_', ' ')})")
        self.summary.setText(self._summary(left, right))
        self.set_point(*(self.point or point))
        self.show_view()

    def set_point(self, pH: float, eh_V: float) -> None:
        """Place the probe of both diagrams at one point and compare the species there."""
        if self.calculations is None:
            return
        self.point = (pH, eh_V)
        for view in self.views:
            view.set_probe(pH, eh_V)
        columns, stable = [], []
        for calculation in self.calculations:
            try:
                probe = calculation.probe(pH, eh_V)
            except ValueError as error:
                columns.append(f"<td>{html.escape(str(error))}</td>")
                stable.append(None)
                continue
            stable.append(probe.species.record_id)
            columns.append(f'<td valign="top" width="50%">{self._column(calculation, probe)}</td>')
        scale = self.display.potential_scale
        scaled = f" ({float(to_scale(eh_V, pH, scale)):+.3f} V vs {html.escape(scale)})" if scale != "SHE" else ""
        if None in stable:
            verdict = ""
        elif stable[0] == stable[1]:
            verdict = " — same species"
        else:
            verdict = " — different species"
        self.details.setHtml(
            f"At pH {pH:.2f}, Eh {eh_V:+.3f} V vs SHE{scaled}{verdict}"
            f'<table width="100%" cellspacing="0" cellpadding="2"><tr>{"".join(columns)}</tr></table>'
        )

    def _column(self, calculation: Any, probe: Any) -> str:
        species = probe.species
        lines = [f"<span style=\"font-size:11pt\">{to_html(species.species)}</span> {html.escape(phase_label(species))}, "
                 f"ΔfG° {species.gibbs_energy_J_mol / 1000:.2f} kJ/mol "
                 f"<i>({html.escape(status_label(species.gibbs_status.value))})</i>"]
        if probe.dissolved_metal_mol_L is not None:
            lines.append(f"Dissolved {probe.dissolved_metal_mol_L:.3g} mol/L, "
                         f"precipitated {probe.precipitated_fraction:.1%}")
        else:
            try:
                margin = stability_margin(calculation.diagram, probe.pH, probe.eh_V,
                                          self.display.assumed_uncertainty_kJ_mol * 1000)
            except ValueError:
                margin = None
            if margin is not None and margin.runner_up is not None:
                lines.append(f"Runner-up {to_html(margin.runner_up.species)} "
                             f"{margin.margin_J_mol_metal / 1000:.2f} ± "
                             f"{(margin.margin_uncertainty_J_mol_metal or 0) / 1000:.2f} kJ/mol metal higher")
        return "<br>".join(lines)

    @staticmethod
    def _summary(left: Any, right: Any) -> str:
        a, b = left.diagram, right.diagram
        if a.system.symbol != b.system.symbol or a.stable_species_index.shape != b.stable_species_index.shape:
            return "The axes are linked: zooming or panning one diagram moves the other."
        codes = {record_id: code for code, record_id in enumerate(
            dict.fromkeys(item.record_id for item in (*a.system.species, *b.system.species)))}
        code_a = np.array([codes[item.record_id] for item in a.system.species])[a.stable_species_index]
        code_b = np.array([codes[item.record_id] for item in b.system.species])[b.stable_species_index]
        differ = float((code_a != code_b).mean())
        return (f"The stable species differs on {differ:.1%} of the grid. The axes are linked: zooming or "
                "panning one diagram moves the other.")
