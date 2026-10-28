"""pyqtgraph views of Pourbaix diagrams and speciation profiles."""

from __future__ import annotations

import math
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pyqtgraph as pg
from matplotlib import colormaps
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor

from ..boltzmann import boltzmann_smooth
from ..export import diagram_figure
from ..grid import phase_boundary_segments
from ..paths import path_curve
from ..plotting import plot_uncertainty
from ..speciation import dissolved_blend_weights, plot_speciation_profile
from ..uncertainty import stability_uncertainty
from .figure_export import install_export_menu
from .formula import phase_label, species_composition, to_html
from .scales import axis_label, from_scale, nernst_slope_V, resample, to_scale

LABEL_PT = 9.0
LEGEND_PT = 9.0


def record_colors(record_ids: list[str]) -> dict[str, QColor]:
    """Species colors matching ``pourbase.plot_diagram`` (tab20 over sorted record IDs)."""
    palette = colormaps["tab20"]
    return {
        record_id: QColor.fromRgbF(*palette(index % palette.N))
        for index, record_id in enumerate(sorted(set(record_ids)))
    }


def blend_colors(species: tuple, weights: np.ndarray, colors: dict[str, QColor],
                 threshold: float = 0.02) -> tuple[dict[str, QColor], list]:
    """Colors for the species a blend shows, and the blended-in species to add to the legend.

    Species that reach ``threshold`` somewhere without a color of their own get the unused palette
    color whose hue is farthest from every color already shown, so a blend toward a dissolved
    species does not look like a blend toward a solid.
    """
    colors = dict(colors)
    visible = [item for index, item in enumerate(species)
               if item.record_id not in colors and float(weights[index].max()) >= threshold]
    palette = colormaps["tab20"]

    def hue(color: QColor) -> float:
        return color.hsvHueF() if color.hsvSaturationF() > 0.15 else -1.0

    candidates = [QColor.fromRgbF(*palette(index)) for index in range(palette.N)]
    for item in visible:
        used = [hue(color) for color in colors.values() if hue(color) >= 0]
        taken = {color.name() for color in colors.values()}

        def distance(color: QColor) -> float:
            h = hue(color)
            if h < 0:
                return -1.0
            return min((min(abs(h - u), 1 - abs(h - u)) for u in used), default=1.0)

        # the unused palette color whose hue is farthest from every color already shown
        free = [color for color in candidates if color.name() not in taken]
        colors[item.record_id] = max(free, key=distance) if free else QColor("#8c8c8c")
    return colors, visible


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
    blend_width_kJ_mol: float = 2.5
    potential_scale: str = "SHE"
    uncertainty: bool = False
    uncertainty_sigma: float = 1.0
    assumed_uncertainty_kJ_mol: float = 2.0
    overlay_symbol: str = ""  # a second element whose boundaries are drawn over the diagram


class _PathVertex(pg.TargetItem):
    """A draggable point of a path; a click selects it for the arrow keys."""

    def __init__(self, index: int, owner, **options) -> None:
        super().__init__(movable=True, size=11, **options)
        self.index, self.owner = index, owner

    def mouseClickEvent(self, event) -> None:
        if getattr(self.owner, "_pick", None) is not None:  # while picking, a click adds a point
            event.ignore()
            return
        if event.button() == Qt.LeftButton:
            event.accept()
            self.owner.select_vertex(self.index)

    def mouseDragEvent(self, event) -> None:
        if getattr(self.owner, "_pick", None) is not None:
            event.ignore()
            return
        if event.isStart():
            self.owner.select_vertex(self.index)
        super().mouseDragEvent(event)


class DiagramView(pg.PlotWidget):
    """Phase map with boundaries, water lines, labels, a legend and a draggable probe."""

    cursorMoved = Signal(str)
    probeMoved = Signal(float, float)
    boundaryClicked = Signal(str, str, QPointF)  # the two record IDs and the screen position
    pathEdited = Signal(list)  # the path points, (pH, U vs SHE), after a drag or an arrow-key move

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setLabel("bottom", "pH")
        self.setLabel("left", "U (V vs SHE)")
        self._grid: np.ndarray | None = None
        self._figure_source: tuple | None = None  # (diagram, options) to redraw with matplotlib
        self._legend_key: tuple | None = None
        self._limits: tuple | None = None
        self._path_state: tuple | None = None
        self._pick: tuple | None = None  # (done, smooth) while path points are picked on the diagram
        self.selected_vertex: int | None = None
        self._label_items: dict[str, pg.TextItem] = {}  # kept per species and only moved on a redraw
        self._analyses: OrderedDict[tuple, tuple] = OrderedDict()
        self.getPlotItem().setContentsMargins(4, 12, 14, 4)
        self.setMenuEnabled(False)
        self.showGrid(x=False, y=False)
        install_export_menu(self, self.export_table, self.export_name)
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

    python_code = None  # set by the owner: a callable returning code that reproduces this figure
    preview_mode = False  # True while a coarse preview is drawn during a slider drag
    clickable_boundaries = False  # True where a click on a boundary opens its details
    prepare_labels = True  # False for a quick first picture; the full draw prepares them

    def matplotlib_figure(self):
        """The shown diagram redrawn with the package's Matplotlib functions, or None for a plain grid."""
        source = self._figure_source
        if source is None:
            return None
        diagram, options = source
        figure = diagram_figure(diagram, labels=options.labels, legend=options.legend,
                                boundaries=options.boundaries, water=options.water,
                                blend_width_kJ_mol=options.blend_width_kJ_mol if options.boltzmann else None)
        if options.uncertainty and getattr(diagram, "transformed_gibbs_J_mol_metal", None) is not None:
            plot_uncertainty(diagram, ax=figure.axes[0], confidence_sigma=options.uncertainty_sigma,
                             assumed_uncertainty_kJ_mol=options.assumed_uncertainty_kJ_mol)
        return figure

    def export_name(self) -> str:
        diagram = getattr(self, "diagram", None)
        return f"pourbase-{diagram.system.symbol.lower()}-diagram" if diagram is not None else "pourbase-diagram"

    def export_table(self):
        """Every grid point of the shown map: its coordinates and stable species."""
        if self._grid is None:
            return None
        x_label, y_label = self._axes
        names = [item.species for item in self._species]
        ids = [item.record_id for item in self._species]
        rows = []
        for row, y_value in enumerate(self._y):
            for column, x_value in enumerate(self._x):
                if not self._valid[row, column]:
                    continue
                index = int(self._grid[row, column])
                rows.append((f"{x_value:.6g}", f"{y_value:.6g}", names[index], ids[index]))
        return (x_label, y_label, "stable species", "record_id"), rows

    def show_diagram(
        self,
        diagram: Any,
        options: DisplayOptions,
        plating_V: float | None = None,
        reset_range: bool = False,
        colors: dict[str, QColor] | None = None,
    ) -> None:
        """Draw a pH-U diagram; ``colors`` keeps species colors fixed across several diagrams.

        The diagram is drawn on ``options.potential_scale``; fixed-activity diagrams can hatch
        the points where another species lies within the chosen number of uncertainties.
        """
        self.diagram = diagram
        scale = options.potential_scale
        temperature = diagram.conditions.temperature_K
        axis, rows, valid = resample(diagram.pH, diagram.U_V, scale, temperature)
        columns = np.arange(diagram.pH.size)[np.newaxis, :]
        fixed_activity = getattr(diagram, "transformed_gibbs_J_mol_metal", None) is not None
        rgb = None
        blended_in: list = []
        if options.boltzmann:
            weights = (self._derived(boltzmann_smooth, diagram, options.blend_width_kJ_mol * 1000).weights
                       if fixed_activity else self._derived(dissolved_blend_weights, diagram))
            stable_colors = colors or record_colors([item.record_id for item in diagram.stable_species])
            colors, blended_in = blend_colors(diagram.system.species, weights, stable_colors)
            table = np.array([colors[item.record_id].getRgbF()[:3] if item.record_id in colors else (0.8, 0.8, 0.8)
                              for item in diagram.system.species])
            rgb = np.tensordot(weights, table, axes=(0, 0))[rows, columns]
        hatch = None
        self.uncertainty = None
        if options.uncertainty and fixed_activity:
            self.uncertainty = self._derived(stability_uncertainty, diagram, options.uncertainty_sigma,
                                             options.assumed_uncertainty_kJ_mol * 1000)
            hatch = self.uncertainty.uncertain[rows, columns] & valid
        self.show_grid(
            diagram.stable_species_index[rows, columns], diagram.pH, axis, diagram.system.species,
            options, colors=colors, reset_range=reset_range, rgb=rgb,
            axes=("pH", axis_label(scale) if scale != "SHE" else "U (V vs SHE)"),
            valid=valid, hatch=hatch, scale=scale, blended_in=blended_in,
        )
        self._figure_source = (diagram, options)
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

    def _derived(self, analysis: Callable, diagram: Any, *arguments: Any) -> Any:
        """``analysis(diagram, *arguments)``, kept for the last few diagrams so that toggling a display
        option back on does not repeat the calculation."""
        key = (analysis, id(diagram), arguments)
        entry = self._analyses.get(key)
        if entry is None or entry[0] is not diagram:
            entry = (diagram, analysis(diagram, *arguments))
            self._analyses[key] = entry
            while len(self._analyses) > 8:
                self._analyses.popitem(last=False)
        else:
            self._analyses.move_to_end(key)
        return entry[1]

    def _add_label(self, item) -> pg.TextItem:
        """A domain label for a species, kept for later diagrams."""
        label = pg.TextItem(
            html=f'<span style="color:#000; font-size:{LABEL_PT}pt">{to_html(item.species, LABEL_PT)}</span>',
            anchor=(0.5, 0.5), fill=pg.mkBrush(255, 255, 255, 185),
        )
        label.setZValue(5)
        self.addItem(label)
        self._label_items[item.record_id] = label
        return label

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
        axes: tuple[str, str] = ("pH", "U (V vs SHE)"),
        valid: np.ndarray | None = None,
        hatch: np.ndarray | None = None,
        scale: str = "SHE",
        blended_in: list | None = None,
    ) -> None:
        """Draw any 2D grid of species indices (rows follow ``y``, columns follow ``x``).

        Points where ``valid`` is False stay empty; points where ``hatch`` is True are hatched.
        """
        self._figure_source = None  # a plain grid has no diagram to redraw with matplotlib
        valid = np.ones(index.shape, dtype=bool) if valid is None else valid
        self._grid, self._x, self._y, self._species, self._valid = index, x, y, species, valid
        self._axes = axes
        self.scale = scale
        self.setLabel("bottom", axes[0])
        self.setLabel("left", axes[1])
        stable_indices = sorted(int(value) for value in np.unique(index[valid]))
        stable = [species[item] for item in stable_indices]
        colors = colors or record_colors([item.record_id for item in stable])
        if rgb is None:
            table = np.zeros((len(species), 3))
            for species_index, item in zip(stable_indices, stable, strict=True):
                table[species_index] = colors[item.record_id].getRgbF()[:3]
            rgb = table[index]
        lookup = np.full(len(species), -1)
        lookup[stable_indices] = np.arange(len(stable_indices))
        compact = np.where(valid, lookup[index], -1)  # position in ``stable``, or -1 outside the diagram
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

        if options.boundaries and len(stable) > 1:
            points = np.array(phase_boundary_segments(compact, x, y)).reshape(-1, 2)
            self.boundaries.setData(points[:, 0], points[:, 1], pen=pg.mkPen("#000000", width=1))
        else:
            self.boundaries.setData([], [])
        for item in (self.her, self.oer, self.plating, self.probe):
            item.setVisible(False)

        # label items are kept per species and only moved, so redrawing does not rebuild them
        cache = self._label_items
        shown: set = set()
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
                label = cache.get(item.record_id)
                if label is None:
                    label = self._add_label(item)
                label.setPos(float(px), float(py))
                label.setVisible(True)
                shown.add(item.record_id)
        if options.labels and not self.preview_mode and self.prepare_labels:
            # prepare hidden labels for every species, so that a species appearing during a drag costs nothing
            for item in species:
                if item.record_id not in cache:
                    self._add_label(item).setVisible(False)
        for record_id, label in cache.items():
            if record_id not in shown:
                label.setVisible(False)
        self.labels = [cache[record_id] for record_id in shown]

        legend_key = (options.legend, tuple((item.record_id, colors[item.record_id].name()) for item in stable),
                      tuple(item.record_id for item in blended_in or ()),
                      self.uncertainty.confidence_sigma if hatch is not None and self.uncertainty is not None else None,
                      self.dark)
        # while a slider moves the legend stays as it is; it is rebuilt once with the full result
        rebuild = legend_key != self._legend_key and not self.preview_mode
        if rebuild:
            self._legend_key = legend_key
        if rebuild:
            self.legend.clear()
        self.legend.setVisible(options.legend)
        if options.legend and rebuild:
            for item in stable:
                swatch = pg.ScatterPlotItem(
                    symbol="s", size=11, brush=pg.mkBrush(colors[item.record_id]),
                    pen=pg.mkPen("#000000"),
                )
                self.legend.addItem(swatch, to_html(item.species, LEGEND_PT))
            for item in blended_in or ():
                swatch = pg.ScatterPlotItem(symbol="s", size=11, brush=pg.mkBrush(colors[item.record_id]),
                                            pen=pg.mkPen("#000000", style=Qt.DotLine))
                self.legend.addItem(swatch, to_html(item.species, LEGEND_PT) + " (blended)")
            if hatch is not None and self.uncertainty is not None:
                swatch = pg.ScatterPlotItem(symbol="s", size=11, brush=pg.mkBrush(255, 255, 255, 150),
                                            pen=pg.mkPen("#000000", style=Qt.DotLine))
                self.legend.addItem(swatch, f"within {self.uncertainty.confidence_sigma:g}σ of another species")

        view = self.getPlotItem().vb
        limits = (x0, x1, y0, y1)
        # a coarse preview keeps the axes as they are; changing the limits would redraw them every step
        if reset_range or (limits != self._limits and not self.preview_mode):
            self._limits = limits
            view.setLimits(xMin=None, xMax=None, yMin=None, yMax=None)
            if reset_range:
                self.setXRange(x0, x1, padding=0)
                self.setYRange(y0, y1, padding=0)
            view.setLimits(xMin=x0, xMax=x1, yMin=y0, yMax=y1)

    def set_water(self, pH: np.ndarray, her_V: np.ndarray, oer_V: np.ndarray, visible: bool) -> None:
        """Water-stability lines for a grid drawn with pH on the x axis and U on the y axis."""
        pen = pg.mkPen("#dfe1e5" if self.dark else "#000000", width=1.2, style=Qt.DashLine)
        self.her.setData(pH, her_V, pen=pen)
        self.oer.setData(pH, oer_V, pen=pen)
        self.her.setVisible(visible)
        self.oer.setVisible(visible)

    def set_probe(self, pH: float, U_V: float) -> None:
        """Place the probe at a potential against the SHE."""
        self.probe.setPos(QPointF(pH, float(to_scale(U_V, pH, self.scale))))

    def _she(self, pH: float, potential: float) -> float:
        return float(from_scale(potential, pH, self.scale))


    def _species_text(self, x: float, y: float) -> str:
        grid = self._grid
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
            f"{x_name} {x:.2f}, {y_name} {y:+.3f}: {to_html(species_composition(species))} "
            f"({to_html(phase_label(species))})"
        )

    def show_overlay(self, diagram: Any | None, options: DisplayOptions) -> None:
        """Draw the boundaries and species names of a second element's diagram, dashed, over this one."""
        if not hasattr(self, "overlay_lines"):
            self.overlay_lines = pg.PlotDataItem(connect="pairs")
            self.overlay_lines.setZValue(4.5)
            self.addItem(self.overlay_lines)
            self.overlay_labels: list[pg.TextItem] = []
        for label in self.overlay_labels:
            self.removeItem(label)
        self.overlay_labels = []
        if diagram is None:
            self.overlay_lines.setData([], [])
            return
        scale, temperature = options.potential_scale, diagram.conditions.temperature_K
        color = "#e8a33d" if self.dark else "#8a2be2"
        index = diagram.stable_species_index
        points = np.array(phase_boundary_segments(index, diagram.pH, diagram.U_V)).reshape(-1, 2)
        if len(points):
            y = to_scale(points[:, 1], points[:, 0], scale, temperature)
            self.overlay_lines.setData(points[:, 0], y, pen=pg.mkPen(color, width=1.6, style=Qt.DashLine))
        else:
            self.overlay_lines.setData([], [])
        x_grid, y_grid = np.meshgrid(diagram.pH, diagram.U_V)
        scale_x = max(float(np.ptp(diagram.pH)), 1e-9)
        scale_y = max(float(np.ptp(diagram.U_V)), 1e-9)
        for position, item in enumerate(diagram.system.species):
            mask = index == position
            if not mask.any():
                continue
            xs, ys = x_grid[mask], y_grid[mask]
            nearest = int(np.argmin(((xs - xs.mean()) / scale_x) ** 2 + ((ys - ys.mean()) / scale_y) ** 2))
            label = pg.TextItem(html=f'<span style="color:{color}; font-size:{LABEL_PT}pt; font-style:italic">'
                                     f"{to_html(item.species, LABEL_PT)}</span>", anchor=(0.5, 0.5),
                                fill=pg.mkBrush(40, 40, 40, 170) if self.dark else pg.mkBrush(255, 255, 255, 170))
            label.setZValue(5)
            label.setPos(float(xs[nearest]), float(to_scale(ys[nearest], xs[nearest], scale, temperature)))
            self.addItem(label)
            self.overlay_labels.append(label)

    def _she_to_view(self, pH, U_V):
        temperature = self.diagram.conditions.temperature_K if self.diagram is not None else 298.15
        return to_scale(U_V, pH, self.scale, temperature)

    def show_path(self, path: tuple[list[tuple[float, float]], bool] | None) -> None:
        """Draw a path ``(points, smooth)`` of ``(pH, U vs SHE)`` points with draggable handles, or remove it."""
        if not hasattr(self, "path_item"):
            self.path_item = pg.PlotDataItem()
            self.path_item.setZValue(5.5)
            self.addItem(self.path_item)
            self.vertex_items: list[_PathVertex] = []
            self.setFocusPolicy(Qt.ClickFocus)
        self._path_state = (list(path[0]), path[1]) if path is not None and path[0] else None
        vertices = self._path_state[0] if self._path_state else []
        if len(vertices) == len(self.vertex_items):  # move the handles that exist; rebuilding them is slower
            for item, (pH, U) in zip(self.vertex_items, vertices):
                item.blockSignals(True)
                item.setPos(pH, float(self._she_to_view(pH, U)))
                item.blockSignals(False)
            vertices = []
        else:
            for item in self.vertex_items:
                self.removeItem(item)
            self.vertex_items = []
        if self._path_state is None:
            self.selected_vertex = None
            self.path_item.setData([], [])
            return
        if self.selected_vertex is not None and self.selected_vertex >= len(self._path_state[0]):
            self.selected_vertex = None
        for index, (pH, U) in enumerate(vertices):
            item = _PathVertex(index, self, pos=(pH, float(self._she_to_view(pH, U))))
            item.setZValue(5.7)
            item.sigPositionChanged.connect(lambda item=item: self._vertex_moved(item, finished=False))
            item.sigPositionChangeFinished.connect(lambda item=item: self._vertex_moved(item, finished=True))
            self.addItem(item)
            self.vertex_items.append(item)
        self._style_vertices()
        self._draw_path_line()

    def _draw_path_line(self) -> None:
        vertices, smooth = self._path_state
        color = "#ffffff" if self.dark else "#111111"
        if len(vertices) < 2:
            self.path_item.setData([], [])
            return
        _position, pH, U = path_curve(vertices, smooth, 300)
        self.path_item.setData(pH, np.asarray(self._she_to_view(pH, U)),
                               pen=pg.mkPen(color, width=2, style=Qt.DashLine))

    def _style_vertices(self) -> None:
        color = "#ffffff" if self.dark else "#111111"
        for item in self.vertex_items:
            selected = item.index == self.selected_vertex
            item.setPen(pg.mkPen("#e67e22" if selected else color, width=2.5 if selected else 1.5))
            item.setBrush(pg.mkBrush("#e67e22" if selected else color))

    def select_vertex(self, index: int | None) -> None:
        self.selected_vertex = index
        self._style_vertices()
        if index is not None:
            self.setFocus()

    def _vertex_moved(self, item: _PathVertex, finished: bool) -> None:
        if self._path_state is None or item.index >= len(self._path_state[0]):
            return
        position = item.pos()
        self._path_state[0][item.index] = (position.x(), float(self._she(position.x(), position.y())))
        self._draw_path_line()
        if finished:
            self.pathEdited.emit(list(self._path_state[0]))

    def keyPressEvent(self, event) -> None:
        index = self.selected_vertex
        state = self._path_state
        if index is None or state is None or self._pick is not None:
            super().keyPressEvent(event)
            return
        key = event.key()
        if key == Qt.Key_Escape:
            self.select_vertex(None)
            return
        vertices = state[0]
        if key in (Qt.Key_Delete, Qt.Key_Backspace):
            del vertices[index]
            self.selected_vertex = None
            self.pathEdited.emit(list(vertices))
            return
        factor = 10.0 if event.modifiers() & Qt.ShiftModifier else 1.0
        steps = {Qt.Key_Left: (-0.05, 0.0), Qt.Key_Right: (0.05, 0.0), Qt.Key_Up: (0.0, 0.01), Qt.Key_Down: (0.0, -0.01)}
        if key not in steps:
            super().keyPressEvent(event)
            return
        pH, U = vertices[index]
        vertices[index] = (round(pH + steps[key][0] * factor, 4), round(U + steps[key][1] * factor, 5))
        self.pathEdited.emit(list(vertices))

    def show_points(self, points: list[tuple[str, float, float, bool]]) -> None:
        """Mark measured points, each ``(label, pH, U vs SHE, flagged)``; flagged points are drawn hollow."""
        if not hasattr(self, "points_item"):
            self.points_item = pg.ScatterPlotItem(size=9)
            self.points_item.setZValue(5.6)
            self.addItem(self.points_item)
            self.point_labels: list[pg.TextItem] = []
        for label in self.point_labels:
            self.removeItem(label)
        self.point_labels = []
        color = "#ffffff" if self.dark else "#111111"
        spots = []
        for label, pH, U, flagged in points:
            y = float(self._she_to_view(pH, U))
            spots.append({"pos": (pH, y), "symbol": "s", "pen": pg.mkPen(color, width=1.5),
                          "brush": None if flagged else pg.mkBrush(color)})
            text = pg.TextItem(html=f'<span style="color:{color}; font-size:{LABEL_PT}pt">{label}</span>',
                               anchor=(-0.15, 1.0))
            text.setPos(pH, y)
            text.setZValue(5.6)
            self.addItem(text)
            self.point_labels.append(text)
        self.points_item.setData(spots)

    def pick_points(self, done, smooth=lambda: False) -> None:
        """Collect clicks as ``(pH, U vs SHE)`` points until ``finish_pick`` or a double-click, then pass
        them to ``done``. While picking, the path runs on to the mouse."""
        self._picked: list[tuple[float, float]] = []
        self._pick = (done, smooth)
        self.show_path(None)
        self.viewport().setCursor(Qt.CrossCursor)

    def finish_pick(self) -> None:
        pick = self._pick
        if pick is None:
            return
        points = list(self._picked)
        self.cancel_pick()
        pick[0](points)

    def cancel_pick(self) -> None:
        self._pick = None
        self._picked = []
        self.viewport().setCursor(Qt.ArrowCursor)

    def show_region(self, region) -> None:
        """Shade a ``StabilityRegion`` and outline it, or remove it."""
        if not hasattr(self, "region_image"):
            self.region_image = pg.ImageItem(axisOrder="row-major")
            self.region_image.setZValue(2.5)
            self.addItem(self.region_image)
            self.region_outline = pg.PlotDataItem(connect="pairs")
            self.region_outline.setZValue(3.5)
            self.addItem(self.region_outline)
        if region is None or self.diagram is None:
            self.region_image.clear()
            self.region_outline.setData([], [])
            return
        temperature = self.diagram.conditions.temperature_K
        axis, rows, valid = resample(region.pH, region.U_V, self.scale, temperature)
        columns = np.arange(region.pH.size)[np.newaxis, :]
        inside = region.satisfied[rows, columns] & valid
        overlay = np.zeros((*inside.shape, 4), dtype=np.ubyte)
        overlay[~inside & valid] = (255, 255, 255, 150) if not self.dark else (20, 22, 26, 170)
        self.region_image.setImage(overlay, levels=(0, 255))
        x0, x1 = _edges(region.pH)
        y0, y1 = _edges(axis)
        self.region_image.setRect(QRectF(x0, y0, x1 - x0, y1 - y0))
        points = np.array(phase_boundary_segments(inside.astype(int), region.pH, axis)).reshape(-1, 2)
        self.region_outline.setData(points[:, 0] if len(points) else [], points[:, 1] if len(points) else [],
                                    pen=pg.mkPen("#e67e22", width=2.2))

    def boundary_at(self, x: float, y: float, pixels: float = 5.0) -> tuple[Any, Any] | None:
        """The two species of the boundary within ``pixels`` of a point, nearest first, or None."""
        grid = self._grid
        if grid is None or len(self._x) < 2 or len(self._y) < 2:
            return None
        if not (self._x[0] <= x <= self._x[-1] and self._y[0] <= y <= self._y[-1]):
            return None
        pixel_x, pixel_y = self.getPlotItem().vb.viewPixelSize()
        step_x, step_y = abs(self._x[1] - self._x[0]), abs(self._y[1] - self._y[0])
        reach_x = max(1, math.ceil(pixels * pixel_x / step_x))
        reach_y = max(1, math.ceil(pixels * pixel_y / step_y))
        column = int(np.abs(self._x - x).argmin())
        row = int(np.abs(self._y - y).argmin())
        if not self._valid[row, column]:
            return None
        rows = slice(max(row - reach_y, 0), row + reach_y + 1)
        columns = slice(max(column - reach_x, 0), column + reach_x + 1)
        window = grid[rows, columns]
        other = (window != grid[row, column]) & self._valid[rows, columns]
        if not other.any():
            return None
        found_rows, found_columns = np.nonzero(other)
        distance = ((found_rows + rows.start - row) * step_y / pixel_y) ** 2 + (
            (found_columns + columns.start - column) * step_x / pixel_x) ** 2
        nearest = int(np.argmin(distance))
        neighbour = int(window[found_rows[nearest], found_columns[nearest]])
        return self._species[int(grid[row, column])], self._species[neighbour]

    def _mouse_moved(self, position) -> None:
        if not self.sceneBoundingRect().contains(position):
            self.cursorMoved.emit("")
            return
        point = self.getPlotItem().vb.mapSceneToView(position)
        self.cursorMoved.emit(self._species_text(point.x(), point.y()))
        if self._pick is not None:
            if self._picked:  # the path runs on to the mouse until picking ends
                self.show_path((self._picked + [(point.x(), self._she(point.x(), point.y()))], self._pick[1]()))
            return
        near = self.clickable_boundaries and self.boundary_at(point.x(), point.y())
        self.viewport().setCursor(Qt.PointingHandCursor if near else Qt.ArrowCursor)

    def _mouse_clicked(self, event) -> None:
        if event.button() == Qt.LeftButton and event.double() and self._pick is not None:
            self.finish_pick()  # the first click of the double-click has already added the last point
            return
        if event.button() != Qt.LeftButton or event.double():
            return
        if event.isAccepted() is True and self._pick is None:  # a path point took the click
            return
        if self.selected_vertex is not None and self._pick is None:
            self.select_vertex(None)
        point = self.getPlotItem().vb.mapSceneToView(event.scenePos())
        pick = self._pick
        if pick is not None:  # collecting the points of a path
            self._picked.append((point.x(), self._she(point.x(), point.y())))
            self.show_path((self._picked, pick[1]()))
            return
        pair = self.boundary_at(point.x(), point.y())
        screen = QPointF(self.mapToGlobal(self.mapFromScene(event.scenePos())))
        # empty IDs close an open boundary popup; the same click still moves the probe
        self.boundaryClicked.emit(*((pair[0].record_id, pair[1].record_id) if pair else ("", "")), screen)
        if not self.probe.isVisible():
            return
        if self._species_text(point.x(), point.y()):
            self.probe.setPos(point)
            self.probeMoved.emit(point.x(), self._she(point.x(), point.y()))

    def _probe_moved(self) -> None:
        position = self.probe.pos()
        self.probeMoved.emit(position.x(), self._she(position.x(), position.y()))


class SpeciationView(pg.PlotWidget):
    """Metal fraction of every species along pH at one U."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setLabel("bottom", "pH")
        self.setLabel("left", "Metal fraction")
        self.setYRange(0, 1.02, padding=0)
        self.setMenuEnabled(False)
        install_export_menu(self, self.export_table, 'pourbase-speciation')
        self.legend = self.addLegend(offset=(-10, 10), labelTextSize=f"{LEGEND_PT:g}pt")
        self.text_color = "#1f1f1f"
        self.profile: Any = None

    def set_dark(self, dark: bool) -> None:
        self.text_color = "#dfe1e5" if dark else "#1f1f1f"
        apply_plot_theme(self, dark)
        self.show_profile(self.profile)

    python_code = None

    def matplotlib_figure(self):
        profile = getattr(self, "profile", None)
        if profile is None:
            return None
        return plot_speciation_profile(profile).figure

    def export_table(self):
        """Metal fractions of every species along pH."""
        profile = getattr(self, "profile", None)
        if profile is None:
            return None
        header = ("pH", *(f"{item.species} ({item.record_id})" for item in profile.species))
        rows = [(f"{pH:.6g}", *(f"{fraction:.6g}" for fraction in profile.metal_fraction[:, column]))
                for column, pH in enumerate(profile.pH)]
        return header, rows

    def show_profile(self, profile: Any | None) -> None:
        self.profile = profile
        self.clear()
        self.legend.clear()
        if profile is None:
            self.setTitle("Speciation is available in mass-balance mode", color=self.text_color)
            return
        self.setTitle(f"U = {profile.U_V:+.3f} V vs SHE", color=self.text_color)
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
        install_export_menu(self, self.export_table, 'pourbase-phase-strip')
        self._rows: tuple | None = None
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

    def export_table(self):
        """The stable species along pH for every row of the strip."""
        shown = self._rows
        if not shown:
            return None
        pH, rows = shown
        header = ("pH", *(title for title, *_rest in rows))
        table = [(f"{value:.6g}", *(species[int(indices[column])].species for _title, indices, species, _colors in rows))
                 for column, value in enumerate(pH)]
        return header, table

    def show_rows(self, pH: np.ndarray, rows: list[tuple[str, np.ndarray, tuple, dict[str, QColor]]]) -> None:
        """``rows`` holds ``(title, species index along pH, species list, colors)`` per source."""
        self._rows = (pH, rows)
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
