"""Panels under the diagram: a path through pH and potential, and measured points placed on the diagram."""

from __future__ import annotations

import csv
import html
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QMessageBox,
    QPushButton, QSlider, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..measurements import MeasuredPoint, PointAssessment
from ..paths import PhasePath
from .formula import formula_delegate, to_html
from .plots import PhaseStripView, record_colors
from .scales import REFERENCE_ELECTRODES_V, from_scale

ELECTRODE_ALIASES = {"she": "SHE", "nhe": "SHE", "rhe": "RHE", "sce": "SCE (sat. KCl)", "hg/hgo": "Hg/HgO (1 M KOH)"}


def reaction_html(reaction: str, database) -> str:
    """A reaction with ligand IDs written as their formulas, e.g. ``chloride-cl`` as Cl⁻."""
    for ligand in database.available_ligands():
        name = ligand.name
        symbol = name[name.find("(") + 1:-1] if name.endswith(")") and "(" in name else ligand.formula_ascii
        reaction = reaction.replace(ligand.ligand_id, symbol)
    return to_html(reaction).replace(" e-", " e⁻")


class PathPanel(QWidget):
    """A path through points in pH and potential, with the species along it and the boundaries it crosses."""

    changed = Signal()
    pickRequested = Signal()
    pickFinished = Signal()
    probeRequested = Signal(float, float)  # pH and Eh against the SHE

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.result: PhasePath | None = None
        self.database = None
        self.vertices: list[tuple[float, float]] = []
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["pH", "Eh (V vs SHE)"])
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemChanged.connect(self._table_edited)
        self.table.setMinimumWidth(200)
        self.shape = QComboBox()
        self.shape.addItem("Straight segments", False)
        self.shape.addItem("Smooth curve", True)
        self.shape.currentIndexChanged.connect(lambda _index: self.changed.emit())
        self.pick = QPushButton("Pick points on the diagram")
        self.pick.setCheckable(True)
        self.pick.setToolTip("Click to add points; double-click or press this button again to finish")
        self.pick.toggled.connect(self._pick_toggled)
        self.add = QPushButton("Add point")
        self.add.clicked.connect(self._add_point)
        self.remove = QPushButton("Remove point")
        self.remove.clicked.connect(self._remove_point)
        self.sweep_eh = QPushButton("Potential sweep at the probe pH")
        self.sweep_pH = QPushButton("pH sweep at the probe Eh")
        self.sweep_eh.clicked.connect(lambda: self._from_probe("eh"))
        self.sweep_pH.clicked.connect(lambda: self._from_probe("pH"))
        self.clear = QPushButton("Clear")
        self.clear.clicked.connect(lambda: self.set_vertices([]))
        edit = QHBoxLayout()
        edit.addWidget(self.add)
        edit.addWidget(self.remove)
        sweeps = QHBoxLayout()
        sweeps.addWidget(self.sweep_eh)
        sweeps.addWidget(self.sweep_pH)
        controls = QVBoxLayout()
        controls.addWidget(self.pick)
        controls.addWidget(self.table, 1)
        controls.addLayout(edit)
        controls.addWidget(self.shape)
        controls.addWidget(self.clear)
        self.strip = PhaseStripView()
        self.strip.setLabel("bottom", "Position along the path (%)")
        self.strip.getAxis("left").setWidth(4)
        self.set_dark(False)
        self.along = QSlider(Qt.Horizontal)
        self.along.setRange(0, 1000)
        self.along.setToolTip("Move the probe along the path")
        self.along.valueChanged.connect(self._along_moved)
        from PySide6.QtWidgets import QFrame, QTextBrowser

        self.crossings = QTextBrowser()
        self.crossings.setFrameShape(QFrame.NoFrame)
        self.crossings.setOpenLinks(False)
        self.crossings.viewport().setAutoFillBackground(False)
        scroll = self.crossings
        self.here = QLabel()
        self.here.setTextFormat(Qt.RichText)
        self.here.hide()
        result = QVBoxLayout()
        result.addLayout(sweeps)
        result.addWidget(self.strip)
        result.addWidget(self.along)
        result.addWidget(self.here)
        result.addWidget(scroll, 1)
        layout = QHBoxLayout(self)
        layout.addLayout(controls)
        layout.addLayout(result, 1)
        self._probe = (7.0, 0.0)
        self.set_vertices([])

    def set_probe(self, pH: float, eh_V: float) -> None:
        self._probe = (pH, eh_V)

    def set_dark(self, dark: bool) -> None:
        from .plots import apply_plot_theme

        apply_plot_theme(self.strip, dark)
        self.dark = dark

    def smooth(self) -> bool:
        return bool(self.shape.currentData())

    def path(self) -> tuple[list[tuple[float, float]], bool] | None:
        """``(points, smooth)``, or None while the path has fewer than two points."""
        return (list(self.vertices), self.smooth()) if len(self.vertices) >= 2 else None

    def set_vertices(self, vertices: list[tuple[float, float]]) -> None:
        self.vertices = [(float(x), float(y)) for x, y in vertices]
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.vertices))
        for row, (pH, eh) in enumerate(self.vertices):
            self.table.setItem(row, 0, QTableWidgetItem(f"{pH:.2f}"))
            self.table.setItem(row, 1, QTableWidgetItem(f"{eh:.3f}"))
        self.table.blockSignals(False)
        self.remove.setEnabled(bool(self.vertices))
        if len(self.vertices) < 2:
            self.result = None
            self.strip.hide()
            self.along.hide()
            self.crossings.setHtml("Pick points on the diagram, add them here, or start from a sweep through the "
                                   "probe. The path runs through every point, straight or smoothly.")
        self.changed.emit()

    def _table_edited(self, _item) -> None:
        vertices = []
        for row in range(self.table.rowCount()):
            try:
                vertices.append((float(self.table.item(row, 0).text()), float(self.table.item(row, 1).text())))
            except (AttributeError, ValueError):
                vertices.append(self.vertices[row] if row < len(self.vertices) else self._probe)
        self.set_vertices(vertices)

    def _add_point(self) -> None:
        self.set_vertices(self.vertices + [self._probe])

    def _remove_point(self) -> None:
        rows = sorted({index.row() for index in self.table.selectedIndexes()}) or [len(self.vertices) - 1]
        self.set_vertices([vertex for row, vertex in enumerate(self.vertices) if row not in rows])

    def _pick_toggled(self, on: bool) -> None:
        self.pick.setText("Finish picking (or double-click)" if on else "Pick points on the diagram")
        if on:
            self.set_vertices([])  # the previous path disappears at once
            self.pickRequested.emit()
        else:
            self.pickFinished.emit()

    def finish_pick(self, vertices: list[tuple[float, float]]) -> None:
        """Called when picking ends with the points clicked."""
        self.pick.blockSignals(True)
        self.pick.setChecked(False)
        self.pick.setText("Pick points on the diagram")
        self.pick.blockSignals(False)
        self.set_vertices(vertices)

    def _from_probe(self, axis: str) -> None:
        pH, eh_V = self._probe
        window = getattr(self, "window_limits", ((0.0, 14.0), (-1.5, 1.5)))
        if axis == "eh":
            self.set_vertices([(pH, window[1][0]), (pH, window[1][1])])
        else:
            self.set_vertices([(window[0][0], eh_V), (window[0][1], eh_V)])

    def _along_moved(self, value: int) -> None:
        if self.result is None:
            return
        index = int(round(value / 1000 * (self.result.fraction.size - 1)))
        self._render_crossings(index)
        self.probeRequested.emit(float(self.result.pH[index]), float(self.result.eh_V[index]))

    def _render_crossings(self, index: int | None = None) -> None:
        """The crossings, with the species at the slider and the crossing nearest to it highlighted."""
        result, database = self.result, self.database
        if result is None:
            return
        lines = []
        self.here.setVisible(index is not None)
        if index is not None:
            here = result.species[int(result.stable_species_index[index])]
            self.here.setText(f"At {result.fraction[index]:.0%} · pH {result.pH[index]:.2f}, "
                              f"Eh {result.eh_V[index]:+.3f} V: {to_html(here.species)} is stable")
        if not result.crossings:
            first = result.species[int(result.stable_species_index[0])]
            lines.append(f"{to_html(first.species)} is stable along the whole path.")
            self.crossings.setHtml("<br>".join(lines))
            return
        nearest = None
        if index is not None:
            position = result.fraction[index]
            nearest = min(range(len(result.crossings)), key=lambda i: abs(result.crossings[i].fraction - position))
        highlight = "#4a3a14" if getattr(self, "dark", False) else "#fdf3dc"
        for number, crossing in enumerate(result.crossings):
            boundary = crossing.boundary
            reaction = reaction_html(boundary.reaction, database) if boundary and database else ""
            equation = html.escape(boundary.equation.replace("-", "−")) if boundary else ""
            text = (f"{crossing.fraction:.0%} · pH {crossing.pH:.2f}, Eh {crossing.eh_V:+.3f} V: "
                    f"{to_html(crossing.before.species)} → {to_html(crossing.after.species)}"
                    + (f"<br><span style='color:gray'>{reaction} · {equation}</span>" if boundary else ""))
            if number == nearest:
                text = f"<table width='100%' cellpadding='2'><tr><td bgcolor='{highlight}'>{text}</td></tr></table>"
            else:
                text = f"<table width='100%' cellpadding='2'><tr><td>{text}</td></tr></table>"
            lines.append(f"<a name='c{number}'></a>{text}")
        self.crossings.setHtml("".join(f"<div>{line}</div>" for line in lines))
        if nearest is not None:
            self.crossings.scrollToAnchor(f"c{nearest}")

    def show_result(self, result: PhasePath | None, stable_ids: list[str], database=None) -> None:
        self.result = result
        self.database = database
        if result is None:
            return
        self.strip.show()
        self.along.show()
        colors = record_colors(stable_ids)
        self.strip.show_rows(result.fraction * 100, [("", result.stable_species_index, result.species, colors)])
        self.strip.getAxis("left").setTicks([[]])
        self._render_crossings()


def read_points(path: str) -> list[MeasuredPoint]:
    """Measured points from a CSV with the columns ``label``, ``pH``, ``potential_V`` and optionally ``reference``."""
    points = []
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = {"pH", "potential_V"} - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"The file needs the columns label, pH, potential_V and optionally reference; "
                             f"{', '.join(sorted(missing))} is missing")
        for number, row in enumerate(reader, start=2):
            name = (row.get("reference") or "SHE").strip()
            reference = name if name in REFERENCE_ELECTRODES_V else ELECTRODE_ALIASES.get(name.lower())
            if reference is None:
                raise ValueError(f"Line {number}: unknown reference electrode {name!r}; use one of "
                                 + ", ".join(REFERENCE_ELECTRODES_V))
            try:
                pH, potential = float(row["pH"]), float(row["potential_V"])
            except (TypeError, ValueError):
                raise ValueError(f"Line {number}: pH and potential_V must be numbers") from None
            label = (row.get("label") or f"Point {number - 1}").strip()
            points.append(MeasuredPoint(label, pH, float(from_scale(potential, pH, reference))))
    return points


POINT_COLUMNS = ["Label", "pH", "Eh (V vs SHE)", "Predicted", "Runner-up", "Margin (kJ/mol)", "Note"]


class PointsPanel(QWidget):
    """Measured points: imported from a file, drawn on the diagram, each with its predicted species."""

    changed = Signal()
    probeRequested = Signal(float, float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.points: list[MeasuredPoint] = []
        self.assessments: tuple[PointAssessment, ...] = ()
        load = QPushButton("Import measured points…")
        load.clicked.connect(self.import_points)
        self.clear = QPushButton("Clear")
        self.clear.clicked.connect(lambda: self.set_points([]))
        self.hint = QLabel("CSV columns: label, pH, potential_V and optionally reference (SHE, RHE, SCE, "
                           "Ag/AgCl (sat. KCl), Ag/AgCl (3 M KCl) or Hg/HgO (1 M KOH)). Click a row to put the probe "
                           "there.")
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet("color: gray;")
        buttons = QHBoxLayout()
        buttons.addWidget(load)
        buttons.addWidget(self.clear)
        buttons.addWidget(self.hint, 1)
        self.table = QTableWidget(0, len(POINT_COLUMNS))
        self.table.setHorizontalHeaderLabels(POINT_COLUMNS)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        for column in (3, 4):
            self.table.setItemDelegateForColumn(column, formula_delegate(self.table))
        self.table.cellClicked.connect(self._row_clicked)
        layout = QVBoxLayout(self)
        layout.addLayout(buttons)
        layout.addWidget(self.table, 1)
        self.clear.setEnabled(False)

    def import_points(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Measured points", "", "CSV (*.csv);;All files (*)")
        if not path:
            return
        try:
            points = read_points(path)
        except (OSError, ValueError, KeyError) as error:
            QMessageBox.warning(self, "Measured points", f"{Path(path).name}: {error}")
            return
        self.set_points(points)

    def set_points(self, points: list[MeasuredPoint]) -> None:
        self.points = list(points)
        self.clear.setEnabled(bool(points))
        self.changed.emit()

    def show_assessments(self, assessments: tuple[PointAssessment, ...]) -> None:
        self.assessments = assessments
        self.table.setRowCount(len(assessments))
        for row, item in enumerate(assessments):
            point = item.point
            margin = item.margin_J_mol_metal
            if not item.inside:
                note = "Outside the diagram window"
            elif item.within_uncertainty:
                note = "Runner-up within the uncertainty of the data"
            else:
                note = ""
            values = (point.label, f"{point.pH:.2f}", f"{point.eh_V:+.3f}",
                      item.species.species if item.species else "", item.runner_up.species if item.runner_up else "",
                      f"{margin / 1000:.2f}" + (f" ± {item.margin_uncertainty_J_mol_metal / 1000:.2f}"
                                                if item.margin_uncertainty_J_mol_metal is not None else "")
                      if margin is not None else "", note)
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

    def _row_clicked(self, row: int, _column: int) -> None:
        if 0 <= row < len(self.assessments):
            point = self.assessments[row].point
            self.probeRequested.emit(point.pH, point.eh_V)


def stable_ids(calculation) -> list[str]:
    return [item.record_id for item in calculation.diagram.stable_species]

