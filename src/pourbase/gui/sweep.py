"""Concentration sweep: stacked 3D slices painted with QPainter, and the selected 2D slice."""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPolygonF, QTransform
from PySide6.QtWidgets import (
    QButtonGroup, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QSlider, QSpinBox, QSplitter, QVBoxLayout,
    QWidget,
)

from .plots import DiagramView, DisplayOptions, record_colors
from ..sweeps import MAX_SWEEP_POINTS
from .state import MAX_GRID_POINTS, SweepSettings

SLICES_SHOWN = 24  # evenly spaced slices drawn in the 3D view, plus the selected one
AXES = {
    "level": ("log₁₀ a", "log₁₀ activity"),
    "pH": ("pH", "pH"),
    "eh": ("Eh", "Eh (V vs SHE)"),
}


class SweepVolume:
    """Stable species indices on the (log a, Eh, pH) grid of a sweep, sliceable along each axis."""

    def __init__(
        self, levels: np.ndarray, pH: np.ndarray, eh_V: np.ndarray, index: np.ndarray,
        species: tuple, colors: dict[str, QColor], her_V: np.ndarray, oer_V: np.ndarray,
    ) -> None:
        self.index = index  # (log a, Eh, pH)
        self.species = species
        self.colors = colors
        self.her_V, self.oer_V = her_V, oer_V
        self.table = np.zeros((len(self.species), 4), dtype=np.ubyte)
        for position, item in enumerate(self.species):
            color = colors.get(item.record_id, QColor("#cccccc"))
            self.table[position] = (color.red(), color.green(), color.blue(), 255)
        self.values = {
            "level": np.asarray(levels, dtype=float),
            "eh": np.asarray(eh_V, dtype=float),
            "pH": np.asarray(pH, dtype=float),
        }
        # Repeat the coarse activity axis so that images and boundaries stay crisp
        self.repeat = max(1, math.ceil(120 / len(self.values["level"])))
        self._images: dict[tuple[str, int], QImage] = {}

    @classmethod
    def from_sweep(cls, sweep: Any, colors: dict[str, QColor]) -> SweepVolume:
        first = sweep.diagrams[0]
        return cls(
            sweep.log10_activities, sweep.pH, sweep.eh_V,
            np.stack([diagram.stable_species_index for diagram in sweep.diagrams]),
            first.system.species, colors, first.her_V, first.oer_V,
        )

    def count(self, axis: str) -> int:
        return len(self.values[axis])

    def value(self, axis: str, position: int) -> float:
        return float(self.values[axis][position])

    def coordinate(self, axis: str, position: int) -> float:
        return -0.5 + position / max(self.count(axis) - 1, 1)

    def plane(self, axis: str, position: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, tuple[str, str]]:
        """2D grid for a slice with rows ascending in y: ``(index, x values, y values, axis labels)``."""
        if axis == "level":
            return self.index[position], self.values["pH"], self.values["eh"], (AXES["pH"][1], AXES["eh"][1])
        if axis == "pH":
            return (self.index[:, :, position].T, self.values["level"], self.values["eh"],
                    (AXES["level"][1], AXES["eh"][1]))
        return (self.index[:, position, :], self.values["pH"], self.values["level"],
                (AXES["pH"][1], AXES["level"][1]))

    def corners(self, axis: str, position: int) -> tuple[tuple, tuple, tuple]:
        """3D corners (top left, top right, bottom left) of a slice image in normalized coordinates."""
        t = self.coordinate(axis, position)
        if axis == "level":
            return (-0.5, t, 0.5), (0.5, t, 0.5), (-0.5, t, -0.5)
        if axis == "pH":
            return (t, -0.5, 0.5), (t, 0.5, 0.5), (t, -0.5, -0.5)
        return (-0.5, 0.5, t), (0.5, 0.5, t), (-0.5, -0.5, t)

    def image(self, axis: str, position: int) -> QImage:
        """RGBA image of a slice, top row first, with darkened phase boundaries."""
        key = (axis, position)
        if key not in self._images:
            grid = self.plane(axis, position)[0][::-1]
            if axis == "pH":
                grid = np.repeat(grid, self.repeat, axis=1)
            elif axis == "eh":
                grid = np.repeat(grid, self.repeat, axis=0)
            rgba = self.table[grid].copy()
            edge = np.zeros(grid.shape, dtype=bool)
            edge[:, 1:] |= grid[:, 1:] != grid[:, :-1]
            edge[1:, :] |= grid[1:, :] != grid[:-1, :]
            rgba[edge, :3] = (rgba[edge, :3] * 0.35).astype(np.ubyte)
            rgba = np.ascontiguousarray(rgba)
            height, width = grid.shape
            self._images[key] = QImage(rgba.data, width, height, 4 * width, QImage.Format_RGBA8888).copy()
        return self._images[key]

    def shown(self, axis: str, selected: int, limit: int | None = None) -> list[int]:
        """Every slice, or ``limit`` evenly spaced slices plus the selected one."""
        count = self.count(axis)
        if limit is None or count <= limit:
            return list(range(count))
        positions = {int(round(value)) for value in np.linspace(0, count - 1, limit)}
        return sorted(positions | {selected})


class SweepView3D(QWidget):
    """Orthographic view of the sweep volume as stacked slices along one axis."""

    sliceClicked = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(280, 300)
        self.volume: SweepVolume | None = None
        self.axis = "level"
        self.selected = 0
        self.opacity = 0.35
        self.azimuth = math.radians(-38)
        self.elevation = math.radians(24)
        self.zoom = 1.0
        self.dark = False
        self._drag: QPointF | None = None
        self._moved = False
        self._polygons: list[tuple[int, QPolygonF]] = []

    def set_volume(self, volume: SweepVolume) -> None:
        self.volume = volume
        self.update()

    def set_selected(self, axis: str, index: int) -> None:
        self.axis, self.selected = axis, index
        self.update()

    def set_opacity(self, value: float) -> None:
        self.opacity = value
        self.update()

    def set_dark(self, dark: bool) -> None:
        self.dark = dark
        self.update()

    def reset_view(self) -> None:
        self.azimuth, self.elevation, self.zoom = math.radians(-38), math.radians(24), 1.0
        self.update()


    def _project(self, x: float, y: float, z: float) -> tuple[QPointF, float]:
        """Map normalized (pH, level, Eh) in [-0.5, 0.5] to screen coordinates and view depth."""
        ca, sa = math.cos(self.azimuth), math.sin(self.azimuth)
        ce, se = math.cos(self.elevation), math.sin(self.elevation)
        depth_scale, height_scale = 1.25, 0.85
        y *= depth_scale
        z *= height_scale
        x1 = x * ca - y * sa
        y1 = x * sa + y * ca
        depth = y1 * ce - z * se
        up = y1 * se + z * ce
        scale = min(self.width(), self.height()) * 0.62 * self.zoom
        return QPointF(self.width() / 2 + scale * x1, self.height() * 0.52 - scale * up), depth


    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.fillRect(self.rect(), QColor("#1e1f22" if self.dark else "#ffffff"))
        if self.volume is None:
            return
        line = QColor("#dfe1e5" if self.dark else "#30343a")
        faint = QColor(line)
        faint.setAlpha(70)

        corners = [(x, y, z) for x in (-0.5, 0.5) for y in (-0.5, 0.5) for z in (-0.5, 0.5)]
        edges = [(a, b) for a in corners for b in corners
                 if a < b and sum(1 for i in range(3) if a[i] != b[i]) == 1]
        edge_depth = [
            (self._project(*[(a[i] + b[i]) / 2 for i in range(3)])[1], a, b) for a, b in edges
        ]
        farthest = max(depth for depth, _, _ in edge_depth)
        painter.setPen(QPen(faint, 1, Qt.DashLine))
        for depth, a, b in edge_depth:
            if depth > farthest - 0.3:
                painter.drawLine(self._project(*a)[0], self._project(*b)[0])

        volume, axis = self.volume, self.axis

        def depth(index: int) -> float:
            corner, right, below = volume.corners(axis, index)
            center = [(right[i] + below[i]) / 2 for i in range(3)]
            return self._project(*center)[1]

        shown = volume.shown(axis, self.selected, SLICES_SHOWN)
        order = sorted(shown, key=lambda index: -depth(index))
        opacity = self.opacity
        self._polygons = []
        for index in order:
            corner, right, below = volume.corners(axis, index)
            top_left = self._project(*corner)[0]
            top_right = self._project(*right)[0]
            bottom_left = self._project(*below)[0]
            image = volume.image(axis, index)
            ex = (top_right - top_left) / image.width()
            ev = (bottom_left - top_left) / image.height()
            painter.save()
            painter.setTransform(QTransform(ex.x(), ex.y(), ev.x(), ev.y(), top_left.x(), top_left.y()))
            painter.setOpacity(1.0 if index == self.selected else opacity)
            painter.drawImage(0, 0, image)
            painter.restore()
            polygon = QPolygonF([top_left, top_right, top_right + (bottom_left - top_left), bottom_left])
            self._polygons.append((index, polygon))
            if index == self.selected:
                painter.setPen(QPen(self.palette().highlight().color(), 2.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawPolygon(polygon)

        painter.setPen(QPen(line, 1.2))
        for depth, a, b in edge_depth:
            if depth <= farthest - 0.3:
                painter.drawLine(self._project(*a)[0], self._project(*b)[0])
        self._paint_axes(painter, line)

    def _paint_axes(self, painter: QPainter, color: QColor) -> None:
        font = QFont(self.font())
        font.setPixelSize(11)
        painter.setFont(font)
        painter.setPen(color)
        center = self._project(0, 0, 0)[0]

        def outward(point: QPointF, distance: float) -> QPointF:
            direction = point - center
            length = math.hypot(direction.x(), direction.y()) or 1.0
            return point + direction * (distance / length)

        def label(point: QPointF, text: str, distance: float = 16, horizontal: bool = False) -> None:
            if horizontal:
                side = -1.0 if point.x() < center.x() else 1.0
                position = QPointF(point.x() + side * (distance + 12), point.y())
            else:
                position = outward(point, distance)
            rect = QRectF(position.x() - 45, position.y() - 9, 90, 18)
            rect.moveLeft(min(max(rect.left(), 2), self.width() - rect.width() - 2))
            painter.drawText(rect, Qt.AlignCenter, text)

        def outer_edge(axis: int) -> tuple[float, float]:
            """Fixed coordinates of the box edge along ``axis`` that lies outermost on screen."""
            others = [index for index in range(3) if index != axis]
            best, best_score = (0.0, 0.0), -math.inf
            for u in (-0.5, 0.5):
                for v in (-0.5, 0.5):
                    point = [0.0, 0.0, 0.0]
                    point[others[0]], point[others[1]] = u, v
                    screen, depth = self._project(*point)
                    if axis == 2:
                        score = -screen.x() - 0.01 * depth
                    else:
                        score = screen.y()
                    if score > best_score:
                        best, best_score = (u, v), score
            return best

        def point_on(axis: int, value: float, fixed: tuple[float, float]) -> QPointF:
            coordinates = [0.0, 0.0, 0.0]
            others = [index for index in range(3) if index != axis]
            coordinates[axis] = value
            coordinates[others[0]], coordinates[others[1]] = fixed
            return self._project(*coordinates)[0]

        values = self.volume.values
        pH, eh, levels = values["pH"], values["eh"], values["level"]
        axes = (
            (0, [(value, f"{value:g}") for value in np.linspace(pH[0], pH[-1], 5)], pH[0], pH[-1], "pH"),
            (2, [(value, f"{value:+.1f}") for value in np.linspace(eh[0], eh[-1], 5)], eh[0], eh[-1],
             "Eh (V vs SHE)"),
            (1, [(value, f"{value:g}") for value in levels[:: max(len(levels) // 5, 1)]],
             levels[0], levels[-1], "log₁₀ a"),
        )
        for axis, ticks, low, high, title in axes:
            fixed = outer_edge(axis)
            vertical = axis == 2
            for value, text in ticks:
                position = (value - low) / (high - low) - 0.5
                if not vertical and abs(position) > 0.49:
                    continue  # the corner ticks would collide with the neighbouring axis
                label(point_on(axis, position, fixed), text, horizontal=vertical)
            if vertical:
                label(point_on(axis, 0.64, fixed), title, distance=0, horizontal=True)
            else:
                label(point_on(axis, 0.0, fixed), title, distance=40)


    def mousePressEvent(self, event) -> None:
        self._drag = event.position()
        self._moved = False

    def mouseMoveEvent(self, event) -> None:
        if self._drag is None:
            return
        delta = event.position() - self._drag
        if abs(delta.x()) + abs(delta.y()) > 2:
            self._moved = True
        self.azimuth += delta.x() * 0.01
        self.elevation = min(max(self.elevation + delta.y() * 0.01, math.radians(-5)), math.radians(85))
        self._drag = event.position()
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        self._drag = None
        if self._moved:
            return
        # The last polygon drawn is the frontmost
        for index, polygon in reversed(self._polygons):
            if polygon.containsPoint(event.position(), Qt.OddEvenFill):
                self.sliceClicked.emit(index)
                return

    def wheelEvent(self, event) -> None:
        self.zoom = min(max(self.zoom * (1.1 if event.angleDelta().y() > 0 else 1 / 1.1), 0.4), 3.0)
        self.update()


SOURCES = {
    "experimental": "Experimental",
    "materials_project": "DFT (MP)",
    "agreement": "Agreement",
}
AGREEMENT_COLORS = {"same": QColor("#8fd18f"), "different": QColor("#e8746b")}


def _toggle_row(title: str, items: dict[str, str], group: QButtonGroup, checked: str) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(0)
    row.addWidget(QLabel(title + "  "))
    for key, text in items.items():
        button = QPushButton(text)
        button.setCheckable(True)
        button.setChecked(key == checked)
        button.setProperty("key", key)
        button.setMinimumWidth(64)
        group.addButton(button)
        row.addWidget(button)
    group.setExclusive(True)
    return row


class SweepPage(QWidget):
    """Sweep controls, the 3D stack, the selected slice, and a slice selector."""

    requested = Signal()
    materialsProjectRequested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.minimum = QDoubleSpinBox()
        self.maximum = QDoubleSpinBox()
        for spin, value in ((self.minimum, -10.0), (self.maximum, 0.0)):
            spin.setRange(-14.0, 2.0)
            spin.setSingleStep(1.0)
            spin.setValue(value)
            spin.setKeyboardTracking(False)
            spin.valueChanged.connect(lambda _v: self.requested.emit())
        self.slice_counts: dict[str, QSpinBox] = {}
        for axis, maximum, value, tip in (
            ("level", MAX_SWEEP_POINTS, 21, "activity levels: slices and resolution along log₁₀ a"),
            ("pH", MAX_GRID_POINTS, 141, "pH grid points: slices and resolution along pH"),
            ("eh", MAX_GRID_POINTS, 151, "Eh grid points: slices and resolution along Eh"),
        ):
            spin = QSpinBox()
            spin.setRange(2, maximum)
            spin.setValue(value)
            spin.setKeyboardTracking(False)
            spin.setToolTip(f"Number of {tip}")
            spin.valueChanged.connect(lambda _v: self.requested.emit())
            self.slice_counts[axis] = spin
        self.opacity = QSlider(Qt.Horizontal)
        self.opacity.setRange(5, 100)
        self.opacity.setValue(35)
        self.opacity.setMinimumWidth(120)
        reset = QPushButton("Reset view")

        controls = QHBoxLayout()
        for text, widget in (("log₁₀ a from", self.minimum), ("to", self.maximum)):
            controls.addWidget(QLabel(text))
            controls.addWidget(widget)
        controls.addSpacing(18)
        controls.addWidget(QLabel("Slices:"))
        for axis, widget in self.slice_counts.items():
            controls.addWidget(QLabel(AXES[axis][0]))
            controls.addWidget(widget)
        controls.addStretch(1)

        self.axis_group = QButtonGroup(self)
        self.source_group = QButtonGroup(self)
        view_controls = QHBoxLayout()
        view_controls.addLayout(_toggle_row("Slice along", {k: v[0] for k, v in AXES.items()},
                                            self.axis_group, "level"))
        view_controls.addSpacing(18)
        view_controls.addLayout(_toggle_row("Show", SOURCES, self.source_group, "experimental"))
        view_controls.addSpacing(18)
        view_controls.addWidget(QLabel("Other slices"))
        view_controls.addWidget(self.opacity)
        view_controls.addWidget(reset)
        view_controls.addStretch(1)

        self.view3d = SweepView3D()
        self.view2d = DiagramView()
        self.view2d.setMinimumWidth(260)
        splitter = QSplitter()
        splitter.addWidget(self.view3d)
        splitter.addWidget(self.view2d)
        splitter.setSizes([640, 520])

        self.previous = QPushButton("◀")
        self.next = QPushButton("▶")
        for button in (self.previous, self.next):
            button.setFixedWidth(36)
        self.slider = QSlider(Qt.Horizontal)
        self.slice_label = QLabel()
        self.slice_label.setMinimumWidth(220)
        selector = QHBoxLayout()
        selector.addWidget(self.previous)
        selector.addWidget(self.slider, 1)
        selector.addWidget(self.next)
        selector.addWidget(self.slice_label)
        self.hint = QLabel()
        self.hint.setStyleSheet("color: gray;")
        self.hint.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addLayout(view_controls)
        layout.addWidget(splitter, 1)
        layout.addLayout(selector)
        layout.addWidget(self.hint)

        self.volumes: dict[str, SweepVolume] = {}
        self.source = "experimental"
        self.axis = "level"
        self.positions = {"level": 0, "pH": 0, "eh": 0}
        self.display = DisplayOptions()
        self.mp_note = ""
        self.axis_group.buttonClicked.connect(lambda button: self.set_axis(button.property("key")))
        self.source_group.buttonClicked.connect(lambda button: self.set_source(button.property("key")))
        reset.clicked.connect(self.view3d.reset_view)
        self.opacity.valueChanged.connect(lambda value: self.view3d.set_opacity(value / 100))
        self.slider.valueChanged.connect(self.select)
        self.view3d.sliceClicked.connect(self.slider.setValue)
        self.previous.clicked.connect(lambda: self.slider.setValue(self.slider.value() - 1))
        self.next.clicked.connect(lambda: self.slider.setValue(self.slider.value() + 1))
        self.setFocusPolicy(Qt.StrongFocus)
        self._update_hint()

    @property
    def volume(self) -> SweepVolume | None:
        return self.volumes.get(self.source)

    @property
    def sweep(self) -> Any:
        return self._sweep if self.volumes else None

    def settings(self):
        return SweepSettings(
            self.minimum.value(), self.maximum.value(), self.slice_counts["level"].value(),
            self.slice_counts["pH"].value(), self.slice_counts["eh"].value(),
        )

    def set_sweep(
        self, sweep: Any, display: DisplayOptions, initial_level: float,
        probe: tuple[float, float] = (7.0, 0.0),
    ) -> None:
        """Show a new sweep; slices start at the current activity and the probe pH and Eh."""
        self._sweep = sweep
        self.display = replace(display, boltzmann=False, plating=False)
        stable = {species.record_id for diagram in sweep.diagrams for species in diagram.stable_species}
        colors = record_colors(sorted(stable))
        self.volumes = {"experimental": SweepVolume.from_sweep(sweep, colors)}
        experimental = self.volumes["experimental"]
        for axis, target in (("level", initial_level), ("pH", probe[0]), ("eh", probe[1])):
            self.positions[axis] = int(np.abs(experimental.values[axis] - target).argmin())
        if self.source != "experimental":
            self.materialsProjectRequested.emit()
        self.set_source(self.source, request=False)

    def set_materials_project(self, index: np.ndarray, phases: tuple, colors: dict[str, QColor],
                              same: np.ndarray, note: str) -> None:
        """Add MP stable phases on the sweep grid and the agreement between both sources."""
        from .materials import AGREEMENT

        experimental = self.volumes["experimental"]
        values = experimental.values
        self.volumes["materials_project"] = SweepVolume(
            values["level"], values["pH"], values["eh"], index, phases, colors,
            experimental.her_V, experimental.oer_V,
        )
        agreement_colors = {item.record_id: AGREEMENT_COLORS[item.record_id] for item in AGREEMENT}
        self.volumes["agreement"] = SweepVolume(
            values["level"], values["pH"], values["eh"], np.where(same, 0, 1).astype(np.int16),
            AGREEMENT, agreement_colors, experimental.her_V, experimental.oer_V,
        )
        self.mp_note = note
        self.set_source(self.source, request=False)

    def clear_materials_project(self) -> None:
        self.volumes.pop("materials_project", None)
        self.volumes.pop("agreement", None)

    def set_source(self, source: str, request: bool = True) -> None:
        self.source = source
        for button in self.source_group.buttons():
            button.setChecked(button.property("key") == source)
        if source not in self.volumes:
            if request and self.volumes:
                self.materialsProjectRequested.emit()
            return
        self.view3d.set_volume(self.volumes[source])
        self.set_axis(self.axis, reset_range=True)
        self._update_hint()

    def set_axis(self, axis: str, reset_range: bool = True) -> None:
        self.axis = axis
        for button in self.axis_group.buttons():
            button.setChecked(button.property("key") == axis)
        volume = self.volume
        if volume is None:
            return
        self.slider.blockSignals(True)
        self.slider.setRange(0, volume.count(axis) - 1)
        self.slider.setValue(self.positions[axis])
        self.slider.blockSignals(False)
        self.select(self.positions[axis], reset_range=reset_range)

    def select(self, index: int, reset_range: bool = False) -> None:
        volume = self.volume
        if volume is None:
            return
        axis = self.axis
        self.positions[axis] = index
        self.view3d.set_selected(axis, index)
        grid, x, y, labels = volume.plane(axis, index)
        display = self.display
        if self.source == "agreement":
            display = replace(display, labels=False)
        self.view2d.show_grid(
            grid, x, y, volume.species, display, colors=volume.colors,
            reset_range=reset_range, axes=labels,
        )
        if axis == "level":
            self.view2d.set_water(volume.values["pH"], volume.her_V, volume.oer_V, display.water)
        unit = {"level": "", "pH": "", "eh": " V"}[axis]
        text = f"{AXES[axis][0]} = {volume.value(axis, index):.2f}{unit}"
        if self.source == "agreement":
            share = float(np.mean(grid == 0))
            text += f"  ·  {share:.0%} same species"
        self.view2d.setTitle(f"{SOURCES[self.source]}: {text}")
        self.slice_label.setText(f"{text}  (slice {index + 1} of {volume.count(axis)})")

    def _update_hint(self) -> None:
        text = ("Drag to rotate and scroll to zoom. Click a slice or use ← → to step through "
                "slices; 1, 2 and 3 choose the slice direction.")
        if self.source != "experimental" and self.mp_note:
            text += "  " + self.mp_note
        self.hint.setText(text)

    def set_dark(self, dark: bool) -> None:
        self.view3d.set_dark(dark)
        self.view2d.set_dark(dark)

    def keyPressEvent(self, event) -> None:
        keys = {Qt.Key_1: "level", Qt.Key_2: "pH", Qt.Key_3: "eh"}
        if event.key() in keys:
            self.set_axis(keys[event.key()])
        elif event.key() in (Qt.Key_Left, Qt.Key_Down):
            self.slider.setValue(self.slider.value() - 1)
        elif event.key() in (Qt.Key_Right, Qt.Key_Up):
            self.slider.setValue(self.slider.value() + 1)
        else:
            super().keyPressEvent(event)
