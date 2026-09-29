"""Side-by-side comparison of the experimental and official Materials Project diagrams."""

from __future__ import annotations

from dataclasses import replace

import html
from typing import Any

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QHBoxLayout, QHeaderView, QLabel, QPushButton, QSplitter,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from .formula import formula_delegate
from .materials import AGREEMENT, matched_colors, phase_views
from .plots import DiagramView, DisplayOptions, record_colors
from .sweep import AGREEMENT_COLORS


class MaterialsProjectPage(QWidget):
    refreshRequested = Signal()
    optionsChanged = Signal()
    keyRequested = Signal()
    exportRequested = Signal()
    probeMoved = Signal(float, float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.filter_solids = QCheckBox("Filter solids on the MP phase diagram")
        self.filter_solids.setChecked(True)
        self.filter_solids.setToolTip("pymatgen's default: only solids stable on the compositional phase diagram")
        self.gibbs_300K = QCheckBox("300 K Gibbs corrections for solids")
        self.gibbs_300K.setToolTip("MP's machine-learned finite-temperature correction (SISSO)")
        for check in (self.filter_solids, self.gibbs_300K):
            check.toggled.connect(lambda _v: self.optionsChanged.emit())
        refresh = QPushButton("Fetch again")
        refresh.setToolTip("Download the entries again from the Materials Project API")
        refresh.clicked.connect(self.refreshRequested.emit)
        export = QPushButton("Export figure…")
        export.clicked.connect(self.exportRequested.emit)
        key = QPushButton("API key…")
        key.clicked.connect(self.keyRequested.emit)
        toolbar = QHBoxLayout()
        for widget in (self.filter_solids, self.gibbs_300K):
            toolbar.addWidget(widget)
        toolbar.addStretch(1)
        for widget in (refresh, export, key):
            toolbar.addWidget(widget)

        self.views = {name: DiagramView() for name in ("experimental", "materials_project", "agreement")}
        for view in self.views.values():
            view.setMinimumWidth(200)
            view.probeMoved.connect(self.probeMoved.emit)
        panels = QSplitter()
        for view in self.views.values():
            panels.addWidget(view)

        self.summary = QLabel()
        self.summary.setTextFormat(Qt.RichText)
        self.summary.setWordWrap(True)
        self.summary.setOpenExternalLinks(True)
        self.pairs = QTableWidget(0, 3)
        self.pairs.setHorizontalHeaderLabels(["Experimental species", "Materials Project phase", "Share of grid"])
        self.pairs.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.pairs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for column in (0, 1):
            self.pairs.setItemDelegateForColumn(column, formula_delegate(self.pairs))
        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.addWidget(self.summary)
        bottom_layout.addWidget(QLabel("Where the two datasets differ"))
        bottom_layout.addWidget(self.pairs, 1)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(panels)
        splitter.addWidget(bottom)
        splitter.setSizes([560, 240])
        layout = QVBoxLayout(self)
        layout.addLayout(toolbar)
        layout.addWidget(splitter, 1)

    def options(self) -> tuple[bool, bool]:
        return self.filter_solids.isChecked(), self.gibbs_300K.isChecked()

    def set_dark(self, dark: bool) -> None:
        for view in self.views.values():
            view.set_dark(dark)

    def show_comparison(self, comparison: Any, display: DisplayOptions, notes: list[str],
                        reset_range: bool = False) -> None:
        experimental, official = comparison.experimental, comparison.materials_project
        # Domain labels identify the species; only the agreement map needs a legend
        display = replace(display, boltzmann=False, plating=False, legend=False)
        experimental_colors = record_colors([item.record_id for item in experimental.stable_species])
        self.views["experimental"].show_diagram(experimental, display, colors=experimental_colors,
                                                reset_range=reset_range)
        phases = phase_views(official)
        colors = matched_colors(experimental.system.species, official, experimental_colors, record_colors)
        views = self.views
        views["materials_project"].show_grid(
            official.stable_phase_index, official.pH, official.eh_V, phases, display,
            colors=colors, reset_range=reset_range,
        )
        views["materials_project"].set_water(official.pH, official.her_V, official.oer_V, display.water)
        agreement_colors = {item.record_id: AGREEMENT_COLORS[item.record_id] for item in AGREEMENT}
        views["agreement"].show_grid(
            np.where(comparison.same_thermodynamic_species, 0, 1), experimental.pH, experimental.eh_V,
            AGREEMENT, replace(display, labels=False, legend=True),
            colors=agreement_colors, reset_range=reset_range,
        )
        views["agreement"].set_water(experimental.pH, experimental.her_V, experimental.oer_V, display.water)
        views["experimental"].setTitle("Experimental (pourbase)")
        views["materials_project"].setTitle(f"Materials Project {html.escape(official.database_version)}")
        views["agreement"].setTitle("Agreement")

        rows = comparison.changed_phase_pairs()
        total = comparison.same_thermodynamic_species.size
        self.pairs.setRowCount(len(rows))
        for row, (species, phase, count) in enumerate(rows):
            from .materials import pretty_label

            for column, value in enumerate((species, pretty_label(phase), f"{count / total:.1%}")):
                self.pairs.setItem(row, column, QTableWidgetItem(value))
        details = (
            f"<b>{comparison.equivalent_domain_fraction:.1%}</b> of the grid and "
            f"<b>{comparison.water_window_equivalent_domain_fraction:.1%}</b> of the water-stability "
            "window have the same thermodynamic species in both datasets. "
            f"MP database {html.escape(official.database_version)}, mp-api "
            f"{html.escape(official.mp_api_version)}, pymatgen {html.escape(official.pymatgen_version)}; "
            f"solids {'filtered' if official.filter_solids else 'unfiltered'}, "
            f"{'300 K Gibbs corrections' if official.use_gibbs_300K else '0 K formation energies'}. "
            "Solids match on O and H per metal; aqueous species on protons, electrons and metals per "
            "species. MP data are CC BY 4.0; cite Materials Project with the database version."
        )
        if notes:
            details += "<br><i>" + " ".join(html.escape(note) for note in notes) + "</i>"
        self.summary.setText(details)

    def set_probe(self, pH: float, eh_V: float) -> None:
        for view in self.views.values():
            view.probe.setVisible(True)
            view.set_probe(pH, eh_V)
