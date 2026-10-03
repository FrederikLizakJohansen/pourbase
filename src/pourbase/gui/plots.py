"""pyqtgraph views of Pourbaix diagrams and speciation profiles."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pyqtgraph as pg
from matplotlib import colormaps
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor

from ..boltzmann import boltzmann_smooth
from ..grid import phase_boundary_segments
from ..uncertainty import stability_uncertainty
from .formula import phase_label, to_html
from .scales import axis_label, from_scale, nernst_slope_V, resample, to_scale

LABEL_PT = 9.0
LEGEND_PT = 9.0


def record_colors(record_ids: list[str]) -> dict[str, QColor]:
    """Species colors matching :func:`pourbase.plot_diagram` (tab20 over sorted record IDs)."""
    palette = colormaps["tab20"]
    return {
        record_id: QColor.fromRgbF(*palette(index % palette.N))
        for index, record_id in enumerate(sorted(set(record_ids)))
    }


def _edges(values: np.ndarray) -> tuple[float, float]:
    step = (values[-1] - values[0]) / max(values.size - 1, 1)
    return float(values[0] - step / 2), float(values[-1] + step / 2)


def apply_plot_theme(widget: pg.PlotWidget, dark: bool) -> None:
    """Set background, axis and legend text colors for the light or dark theme."""
    color = "#dfe1e5" if dark else "#1f1f1f"
    widget.setBackground("#1e1f22" if dark else "w")
    item = widget.getPlotItem()
    for name in ("left", "bottom"):
        axis = item.getAxis(name)
        axis.setPen(color)
        axis.setTextPen(color)
        axis.label.setDefaultTextColor(QColor(color))
    if item.legend is not None:
        item.legend.setLabelTextColor(color)
        item.legend.setBrush(pg.mkBrush("#2b2d30d0" if dark else "#ffffffd0"))
        item.legend.setPen(pg.mkPen(color))
        for _sample, label in item.legend.items:
            label.setText(label.text, color=color)


@dataclass
class DisplayOptions:
    labels: bool = True
    legend: bool = True
    boundaries: bool = True
    water: bool = True
    plating: bool = False
    boltzmann: bool = False
    boltzmann_scale: float = 1.0
    potential_scale: str = "SHE"
    uncertainty: bool = False
    uncertainty_sigma: float = 1.0
    assumed_uncertainty_kJ_mol: float = 2.0


class DiagramView(pg.PlotWidget):
    """Phase map with boundaries, water lines, labels, a legend and a draggable probe."""

    cursorMoved = Signal(str)
    probeMoved = Signal(float, float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setLabel("bottom", "pH")
        self.setLabel("left", "Eh (V vs SHE)")
        self.getPlotItem().setContentsMargins(4, 12, 14, 4)
        self.setMenuEnabled(False)
        self.showGrid(x=False, y=False)
        self.image = pg.ImageItem(axisOrder="row-major")
        self.addItem(self.image)
        self.hatch = pg.ImageItem(axisOrder="row-major")
        self.hatch.setZValue(2)
        self.addItem(self.hatch)
        self.scale = "SHE"
        self.uncertainty = None
        self.boundaries = pg.PlotDataItem(connect="pairs")
        self.boundaries.setZValue(3)
        self.addItem(self.boundaries)
        self.her = pg.PlotDataItem()
        self.oer = pg.PlotDataItem()
        self.plating = pg.InfiniteLine(angle=0, movable=False)
        for item in (self.her, self.oer, self.plating):
            item.setZValue(4)
            self.addItem(item)
        self.probe = pg.TargetItem(
            size=14, movable=True, pen=pg.mkPen("#000000", width=2),
            brush=pg.mkBrush(255, 255, 255, 160),
        )
        self.probe.setZValue(6)
        self.probe.sigPositionChangeFinished.connect(self._probe_moved)
        self.addItem(self.probe)
        self.legend = self.addLegend(offset=(-10, 10), labelTextSize=f"{LEGEND_PT:g}pt")
        self.labels: list[pg.TextItem] = []
        self.diagram: Any = None
        self.dark = False
        self.scene().sigMouseMoved.connect(self._mouse_moved)
        self.scene().sigMouseClicked.connect(self._mouse_clicked)


    def set_dark(self, dark: bool) -> None:
        self.dark = dark
        apply_plot_theme(self, dark)

    def show_diagram(
        self,
        diagram: Any,
        options: DisplayOptions,
        plating_V: float | None = None,
        reset_range: bool = False,
        colors: dict[str, QColor] | None = None,
    ) -> None:
        """Draw a pH-Eh diagram; ``colors`` keeps species colors fixed across several diagrams.

        The diagram is drawn on ``options.potential_scale``; fixed-activity diagrams can hatch
        the points where another species lies within the chosen number of uncertainties.
        """
        self.diagram = diagram
        scale = options.potential_scale
        temperature = diagram.conditions.temperature_K
        axis, rows, valid = resample(diagram.pH, diagram.eh_V, scale, temperature)
        columns = np.arange(diagram.pH.size)[np.newaxis, :]
        fixed_activity = getattr(diagram, "transformed_gibbs_J_mol_metal", None) is not None
        rgb = None
        if options.boltzmann and fixed_activity:
            rgb = self._boltzmann_rgb(diagram, options.boltzmann_scale, colors)[rows, columns]
        hatch = None
        self.uncertainty = None
        if options.uncertainty and fixed_activity:
            self.uncertainty = stability_uncertainty(
                diagram, options.uncertainty_sigma, options.assumed_uncertainty_kJ_mol * 1000)
            hatch = self.uncertainty.uncertain[rows, columns] & valid
        self.show_grid(
            diagram.stable_species_index[rows, columns], diagram.pH, axis, diagram.system.species,
            options, colors=colors, reset_range=reset_range, rgb=rgb,
            axes=("pH", axis_label(scale) if scale != "SHE" else "Eh (V vs SHE)"),
            valid=valid, hatch=hatch, scale=scale,
        )
        line = "#dfe1e5" if self.dark else "#000000"
        water_pen = pg.mkPen(line, width=1.2, style=Qt.DashLine)
        self.her.setData(diagram.pH, to_scale(diagram.her_V, diagram.pH, scale, temperature), pen=water_pen)
        self.oer.setData(diagram.pH, to_scale(diagram.oer_V, diagram.pH, scale, temperature), pen=water_pen)
        self.her.setVisible(options.water)
        self.oer.setVisible(options.water)
        self.plating.setVisible(options.plating and plating_V is not None)
        if plating_V is not None:
            slope = nernst_slope_V(temperature) if scale == "RHE" else 0.0
            self.plating.setAngle(math.degrees(math.atan(slope)))
            self.plating.setPos(QPointF(0.0, float(to_scale(plating_V, 0.0, scale, temperature))))
            self.plating.setPen(pg.mkPen("#2e9d4a", width=1.5, style=Qt.DashDotLine))
        self.probe.setVisible(True)

    def show_grid(
        self,
        index: np.ndarray,
        x: np.ndarray,
        y: np.ndarray,
        species: tuple,
        options: DisplayOptions,
        colors: dict[str, QColor] | None = None,
        reset_range: bool = False,
        rgb: np.ndarray | None = None,
        axes: tuple[str, str] = ("pH", "Eh (V vs SHE)"),
        valid: np.ndarray | None = None,
        hatch: np.ndarray | None = None,
        scale: str = "SHE",
    ) -> None:
        """Draw any 2D grid of species indices (rows follow ``y``, columns follow ``x``).

        Points where ``valid`` is False stay empty; points where ``hatch`` is True are hatched.
        """
        valid = np.ones(index.shape, dtype=bool) if valid is None else valid
        self._grid, self._x, self._y, self._species, self._valid = index, x, y, species, valid
        self._axes = axes
        self.scale = scale
        self.setLabel("bottom", axes[0])
        self.setLabel("left", axes[1])
        stable_indices = sorted(int(value) for value in np.unique(index[valid]))
        stable = [species[item] for item in stable_indices]
        colors = colors or record_colors([item.record_id for item in stable])
        compact = np.zeros_like(index)
        for display_index, species_index in enumerate(stable_indices):
            compact[index == species_index] = display_index
        if rgb is None:
            table = np.array([colors[item.record_id].getRgbF()[:3] for item in stable])
            rgb = table[compact]
        rgba = np.empty((*index.shape, 4), dtype=np.ubyte)
        rgba[..., :3] = (np.clip(rgb, 0, 1) * 255).astype(np.ubyte)
        rgba[..., 3] = np.where(valid, 255, 0)
        self.image.setImage(rgba, levels=(0, 255))
        x0, x1 = _edges(x)
        y0, y1 = _edges(y)
        self.image.setRect(QRectF(x0, y0, x1 - x0, y1 - y0))
        self.hatch.setVisible(hatch is not None and bool(hatch.any()))
        if hatch is not None:
            rows, columns = np.indices(index.shape)
            stripes = ((rows + columns) // 3) % 3 == 0
            overlay = np.zeros((*index.shape, 4), dtype=np.ubyte)
            overlay[hatch & stripes] = (255, 255, 255, 150)
            overlay[hatch & ~stripes] = (0, 0, 0, 22)
            self.hatch.setImage(overlay, levels=(0, 255))
            self.hatch.setRect(QRectF(x0, y0, x1 - x0, y1 - y0))
        compact = np.where(valid, compact, -1)

        if options.boundaries and len(stable) > 1:
            points = np.array(phase_boundary_segments(compact, x, y)).reshape(-1, 2)
            self.boundaries.setData(points[:, 0], points[:, 1], pen=pg.mkPen("#000000", width=1))
        else:
            self.boundaries.setData([], [])
        for item in (self.her, self.oer, self.plating, self.probe):
            item.setVisible(False)

        for label in self.labels:
            self.removeItem(label)
        self.labels = []
        if options.labels:
            x_grid, y_grid = np.meshgrid(x, y)
            scale_x = max(float(np.ptp(x)), 1e-9)
            scale_y = max(float(np.ptp(y)), 1e-9)
            for display_index, item in enumerate(stable):
                mask = compact == display_index
                if not mask.any():
                    continue
                target = (float(x_grid[mask].mean()), float(y_grid[mask].mean()))
                coordinates = np.column_stack((x_grid[mask], y_grid[mask]))
                distances = ((coordinates[:, 0] - target[0]) / scale_x) ** 2 + (
                    (coordinates[:, 1] - target[1]) / scale_y
                ) ** 2
                px, py = coordinates[int(np.argmin(distances))]
                label = pg.TextItem(
                    html=f'<span style="color:#000; font-size:{LABEL_PT}pt">'
                    f"{to_html(item.species, LABEL_PT)}</span>",
                    anchor=(0.5, 0.5), fill=pg.mkBrush(255, 255, 255, 185),
                )
                label.setPos(float(px), float(py))
                label.setZValue(5)
                self.addItem(label)
                self.labels.append(label)

        self.legend.clear()
        self.legend.setVisible(options.legend)
        if options.legend:
            for item in stable:
                swatch = pg.ScatterPlotItem(
                    symbol="s", size=11, brush=pg.mkBrush(colors[item.record_id]),
                    pen=pg.mkPen("#000000"),
                )
                self.legend.addItem(swatch, to_html(item.species, LEGEND_PT))
            if hatch is not None and self.uncertainty is not None:
                swatch = pg.ScatterPlotItem(symbol="s", size=11, brush=pg.mkBrush(255, 255, 255, 150),
                                            pen=pg.mkPen("#000000", style=Qt.DotLine))
                self.legend.addItem(swatch, f"within {self.uncertainty.confidence_sigma:g}σ of another species")

        view = self.getPlotItem().vb
        view.setLimits(xMin=None, xMax=None, yMin=None, yMax=None)
        if reset_range:
            self.setXRange(x0, x1, padding=0)
            self.setYRange(y0, y1, padding=0)
        view.setLimits(xMin=x0, xMax=x1, yMin=y0, yMax=y1)

    @staticmethod
    def _boltzmann_rgb(diagram: Any, scale: float, colors: dict[str, QColor] | None) -> np.ndarray:
        smoothed = boltzmann_smooth(diagram, scale)
        stable = diagram.stable_species
        colors = dict(colors or record_colors([item.record_id for item in stable]))
        # Stable species keep their hard-minimum colors; the others take the next palette entries
        palette = colormaps["tab20"]
        others = sorted(
            item.record_id for item in diagram.system.species if item.record_id not in colors
        )
        for offset, record_id in enumerate(others, start=len(colors)):
            colors[record_id] = QColor.fromRgbF(*palette(offset % palette.N))
        table = np.array([colors[item.record_id].getRgbF()[:3] for item in diagram.system.species])
        return np.tensordot(smoothed.weights, table, axes=(0, 0))

    def set_water(self, pH: np.ndarray, her_V: np.ndarray, oer_V: np.ndarray, visible: bool) -> None:
        """Water-stability lines for a grid drawn with pH on the x axis and Eh on the y axis."""
        pen = pg.mkPen("#dfe1e5" if self.dark else "#000000", width=1.2, style=Qt.DashLine)
        self.her.setData(pH, her_V, pen=pen)
        self.oer.setData(pH, oer_V, pen=pen)
        self.her.setVisible(visible)
        self.oer.setVisible(visible)

    def set_probe(self, pH: float, eh_V: float) -> None:
        """Place the probe at a potential against the SHE."""
        self.probe.setPos(QPointF(pH, float(to_scale(eh_V, pH, self.scale))))

    def _she(self, pH: float, potential: float) -> float:
        return float(from_scale(potential, pH, self.scale))


    def _species_text(self, x: float, y: float) -> str:
        grid = getattr(self, "_grid", None)
        if grid is None:
            return ""
        if not (self._x[0] <= x <= self._x[-1] and self._y[0] <= y <= self._y[-1]):
            return ""
        column = int(np.abs(self._x - x).argmin())
        row = int(np.abs(self._y - y).argmin())
        if not self._valid[row, column]:
            return ""
        species = self._species[int(grid[row, column])]
        x_name, y_name = (name.split(" (")[0] for name in self._axes)
        return (
            f"{x_name} {x:.2f}, {y_name} {y:+.3f}: {to_html(species.species)} "
            f"({phase_label(species)})"
        )

    def _mouse_moved(self, position) -> None:
        if not self.sceneBoundingRect().contains(position):
            self.cursorMoved.emit("")
            return
        point = self.getPlotItem().vb.mapSceneToView(position)
        self.cursorMoved.emit(self._species_text(point.x(), point.y()))

    def _mouse_clicked(self, event) -> None:
        if not self.probe.isVisible() or event.button() != Qt.LeftButton or event.double():
            return
        point = self.getPlotItem().vb.mapSceneToView(event.scenePos())
        if self._species_text(point.x(), point.y()):
            self.probe.setPos(point)
            self.probeMoved.emit(point.x(), self._she(point.x(), point.y()))

    def _probe_moved(self) -> None:
        position = self.probe.pos()
        self.probeMoved.emit(position.x(), self._she(position.x(), position.y()))


class SpeciationView(pg.PlotWidget):
    """Metal fraction of every species along pH at one Eh."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setLabel("bottom", "pH")
        self.setLabel("left", "Metal fraction")
        self.setYRange(0, 1.02, padding=0)
        self.setMenuEnabled(False)
        self.legend = self.addLegend(offset=(-10, 10), labelTextSize=f"{LEGEND_PT:g}pt")
        self.text_color = "#1f1f1f"
        self.profile: Any = None

    def set_dark(self, dark: bool) -> None:
        self.text_color = "#dfe1e5" if dark else "#1f1f1f"
        apply_plot_theme(self, dark)
        self.show_profile(self.profile)

    def show_profile(self, profile: Any | None) -> None:
        self.profile = profile
        self.clear()
        self.legend.clear()
        if profile is None:
            self.setTitle("Speciation is available in mass-balance mode", color=self.text_color)
            return
        self.setTitle(f"Eh = {profile.eh_V:+.3f} V vs SHE", color=self.text_color)
        colors = record_colors([item.record_id for item in profile.species])
        for species, fraction in zip(profile.species, profile.metal_fraction):
            if float(fraction.max()) < 1e-3:
                continue
            self.plot(
                profile.pH, fraction, name=to_html(species.species, LEGEND_PT),
                pen=pg.mkPen(colors[species.record_id], width=2.2),
            )


class PhaseStripView(pg.PlotWidget):
    """Stable species along pH in labelled rows, one row per data source."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMenuEnabled(False)
        self.setMouseEnabled(x=False, y=False)
        self.hideButtons()
        self.setLabel("bottom", "pH")
        self.getPlotItem().setContentsMargins(4, 6, 14, 4)
        self.image = pg.ImageItem(axisOrder="row-major")
        self.addItem(self.image)
        self.labels: list[pg.TextItem] = []
        self.getAxis("left").setWidth(130)

    def set_dark(self, dark: bool) -> None:
        apply_plot_theme(self, dark)

    def show_rows(self, pH: np.ndarray, rows: list[tuple[str, np.ndarray, tuple, dict[str, QColor]]]) -> None:
        """``rows`` holds ``(title, species index along pH, species list, colors)`` per source."""
        for label in self.labels:
            self.removeItem(label)
        self.labels = []
        rgb = np.zeros((len(rows), pH.size, 3))
        for row, (_title, indices, species, colors) in enumerate(rows):
            table = np.array([colors.get(item.record_id, QColor("#cccccc")).getRgbF()[:3] for item in species])
            rgb[len(rows) - 1 - row] = table[indices]
            start = 0
            for column in range(1, pH.size + 1):
                if column == pH.size or indices[column] != indices[start]:
                    if column - start >= max(pH.size // 40, 2):
                        middle = (pH[start] + pH[column - 1]) / 2
                        label = pg.TextItem(
                            html=f'<span style="color:#000; font-size:{LABEL_PT}pt">'
                            f"{to_html(species[int(indices[start])].species, LABEL_PT)}</span>",
                            anchor=(0.5, 0.5),
                        )
                        label.setPos(float(middle), len(rows) - 1 - row + 0.5)
                        self.addItem(label)
                        self.labels.append(label)
                    start = column
        self.image.setImage((rgb * 255).astype(np.ubyte), levels=(0, 255))
        x0, x1 = _edges(pH)
        self.image.setRect(QRectF(x0, 0, x1 - x0, len(rows)))
        self.getAxis("left").setTicks([[(len(rows) - 1 - row + 0.5, title) for row, (title, *_rest) in enumerate(rows)]])
        self.setXRange(x0, x1, padding=0)
        self.setYRange(0, len(rows), padding=0)
        self.setFixedHeight(46 + 34 * len(rows))
