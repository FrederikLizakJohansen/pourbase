"""The margin landscape: the periodic table in 3D, each element a column as tall as its stability margin."""

from __future__ import annotations

import math
import time

import numpy as np
from PySide6.QtCore import QEasingCurve, QPointF, QRectF, Qt, QTimer, QVariantAnimation, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QGradient, QLinearGradient, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QSizePolicy, QToolTip, QWidget

from .figure_export import install_export_menu
from .formula import draw_formula, pretty_formula

MAX_MARGIN_KJ = 1000.0  # the top of the height scale
MAX_HEIGHT = 3.2  # column height at MAX_MARGIN_KJ, in table pitches
HALF = 0.5 - 0.045  # half the width of a column; the 2D tiles leave the same inset
RADIUS = 0.12  # corner radius, as on the 2D tiles
DEFAULT_YAW, DEFAULT_ELEVATION = -28.0, 38.0
CAMERA_DISTANCE = 42.0  # perspective strength; larger is flatter
FADE = 0.3  # share of the raise over which the 2D picture fades out
HEIGHT_TWEEN_MS = 450


def margin_height(margin_kJ: float | None) -> float:
    """Column height for a margin in kJ/mol metal, on the same log scale as the margin colors."""
    if margin_kJ is None:
        return 0.0
    return MAX_HEIGHT * math.log10(1 + max(margin_kJ, 0.0)) / math.log10(1 + MAX_MARGIN_KJ)


def grid_point(row: int, column: int) -> tuple[float, float]:
    """Centre of a table cell in pitches, origin at the table centre; the f-block sits 0.35 below row 7."""
    y = row + (0.35 - 1.0 if row >= 8 else 0.0)
    return column - 8.5, y - 4.5


def _outline() -> tuple[np.ndarray, np.ndarray]:
    """Points around a rounded tile and the outward normal of each edge to the next point."""
    inner = HALF - RADIUS
    points, normals = [], []
    for cx, cy, start in ((inner, inner, 0), (-inner, inner, 90), (-inner, -inner, 180), (inner, -inner, 270)):
        for step in range(4):
            angle = math.radians(start + 30 * step)
            points.append((cx + RADIUS * math.cos(angle), cy + RADIUS * math.sin(angle)))
            normals.append((math.cos(angle), math.sin(angle)))
    points, normals = np.array(points), np.array(normals)
    edge_normals = normals + np.roll(normals, -1, axis=0)
    return points, edge_normals / np.linalg.norm(edge_normals, axis=1)[:, None]


OUTLINE, EDGE_NORMALS = _outline()


class MarginLandscape(QWidget):
    """Draws the elements of a :class:`PeriodicTableCanvas` as columns; drag to rotate, scroll to zoom.

    ``raise_amount`` runs from 0 (flat, seen from above, tile for tile on the 2D table) to 1 (columns at full
    height under the chosen camera); :meth:`animate_to` moves it smoothly. Heights move to each new screen over
    ``tween_ms``, so a pH or potential sweep shows the columns growing and shrinking.
    """

    elementClicked = Signal(str)
    animationFinished = Signal(float)

    def __init__(self, canvas, parent=None) -> None:
        super().__init__(parent)
        self.canvas = canvas
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        install_export_menu(self, lambda: canvas.export_table(), "pourbase-margin-landscape")
        self.yaw, self.elevation, self.zoom = DEFAULT_YAW, DEFAULT_ELEVATION, 1.0
        self.raise_amount = 0.0
        self.hovered: str | None = None
        self.snapshot: QPixmap | None = None  # the 2D table, faded out at the start of a raise
        self.tween_ms = HEIGHT_TWEEN_MS
        self._symbols: list[str] = []
        self._heights = np.zeros(0)
        self._start = np.zeros(0)
        self._targets = np.zeros(0)
        self._tween_started = 0.0
        self._hits: list[tuple[str, QPolygonF]] = []
        self._fonts: dict[int, QFont] = {}
        self._styles: dict = {}
        self._press: QPointF | None = None
        self._dragged = False
        self._grow = QTimer(self, interval=15, timeout=self._step_heights)
        self._animation = QVariantAnimation(self, duration=900, easingCurve=QEasingCurve.InOutCubic)
        self._animation.valueChanged.connect(self._set_raise)
        self._animation.finished.connect(self._settled)
        canvas.redrawn.connect(self.refresh)

    # data
    def refresh(self) -> None:
        """Take new target heights from the canvas; columns move to them over ``tween_ms``."""
        elements = self.canvas.elements
        symbols = list(elements)
        targets = np.array([margin_height(None if elements[s].energy_margin_J_mol_metal is None
                                          else elements[s].energy_margin_J_mol_metal / 1000) for s in symbols])
        if symbols != self._symbols or not self.isVisible():
            self._symbols, self._heights = symbols, targets.copy()
            self._targets = targets
            self._grow.stop()
        else:
            self._start, self._targets = self._heights.copy(), targets
            self._tween_started = time.perf_counter()
            self._grow.start()
        self.update()

    def _step_heights(self) -> None:
        fraction = min((time.perf_counter() - self._tween_started) * 1000 / max(self.tween_ms, 1), 1.0)
        eased = 1 - (1 - fraction) ** 3
        self._heights = self._start + (self._targets - self._start) * eased
        if fraction >= 1.0:
            self._grow.stop()
        self.update()

    # camera
    def animate_to(self, amount: float) -> None:
        self._animation.stop()
        self._animation.setStartValue(self.raise_amount)
        self._animation.setEndValue(float(amount))
        self._animation.start()

    def _settled(self) -> None:
        self.update()  # with numbers and formulas again
        self.animationFinished.emit(self.raise_amount)

    def _set_raise(self, value) -> None:
        self.raise_amount = float(value)
        self.update()

    def reset_camera(self) -> None:
        self.yaw, self.elevation, self.zoom = DEFAULT_YAW, DEFAULT_ELEVATION, 1.0
        self.update()

    def _view(self):
        """Rotation, elevation sines and the screen mapping; at raise 0 the 2D table's own layout."""
        t = self.raise_amount
        yaw = math.radians(self.yaw * t)
        elevation = math.radians(90.0 - t * (90.0 - self.elevation))
        pitch, origin, _gap = self.canvas._layout()
        scale = pitch * (1 + (self.zoom - 1) * t)
        centre = (origin.x() + 9 * pitch, origin.y() + 5 * pitch)
        return math.cos(yaw), math.sin(yaw), math.sin(elevation), math.cos(elevation), scale, centre

    def _project(self, view, x, y, z):
        cos_yaw, sin_yaw, sin_el, cos_el, scale, (cx, cy) = view
        xr = x * cos_yaw - y * sin_yaw
        yr = x * sin_yaw + y * cos_yaw
        depth = -yr * cos_el - z * sin_el  # larger is farther from the viewer
        factor = scale * CAMERA_DISTANCE / (CAMERA_DISTANCE + depth)
        return cx + xr * factor, cy + (yr * sin_el - z * cos_el) * factor, depth

    def _font(self, pixel: int) -> QFont:
        if pixel not in self._fonts:
            font = QFont(self.font())
            font.setPixelSize(pixel)
            self._fonts[pixel] = font
        return self._fonts[pixel]

    # painting
    def paintEvent(self, _event) -> None:
        canvas = self.canvas
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.palette().window())
        if canvas.screen is None or not self._symbols:
            return
        from .periodic import table_position

        view = self._view()
        t = self.raise_amount
        elements = [canvas.elements[symbol] for symbol in self._symbols]
        centres = np.array([grid_point(*table_position(item.atomic_number)) for item in elements])
        heights = self._heights * t + 0.02 * t
        # every point of every outline, bottom and top
        xs = centres[:, 0:1] + OUTLINE[None, :, 0]
        ys = centres[:, 1:2] + OUTLINE[None, :, 1]
        bottom_x, bottom_y, _ = self._project(view, xs, ys, 0.0)
        top_x, top_y, _ = self._project(view, xs, ys, heights[:, None])
        # columns stand on a grid without overlapping, so their footprints order them back to front
        order = np.argsort(-self._project(view, centres[:, 0], centres[:, 1], 0.0)[2], kind="stable")
        # a side faces the camera when the camera lies in front of it; under perspective this differs from
        # column to column, and the facing sides of one column form one run around its outline
        cos_yaw, sin_yaw, _sin_el, cos_el = view[:4]
        middles = (OUTLINE + np.roll(OUTLINE, -1, axis=0)) / 2
        mid_x = centres[:, 0:1] + middles[None, :, 0]
        mid_y = centres[:, 1:2] + middles[None, :, 1]
        mid_xr, mid_yr = mid_x * cos_yaw - mid_y * sin_yaw, mid_x * sin_yaw + mid_y * cos_yaw
        normal_xr = EDGE_NORMALS[:, 0] * cos_yaw - EDGE_NORMALS[:, 1] * sin_yaw
        normal_yr = EDGE_NORMALS[:, 0] * sin_yaw + EDGE_NORMALS[:, 1] * cos_yaw
        facing = (-mid_xr * normal_xr + (CAMERA_DISTANCE * cos_el - mid_yr) * normal_yr) > 1e-9
        count = facing.shape[1]
        starts = np.argmax(facing & ~np.roll(facing, 1, axis=1), axis=1).tolist()
        lengths = facing.sum(axis=1).tolist()
        bands = [[] if t <= 0 or length == 0 else
                 list(range(count)) + [0] if length == count else
                 [(start + k) % count for k in range(length + 1)]
                 for start, length in zip(starts, lengths)]
        self._paint_floor(painter, view)
        self._hits = []
        # text anchors on each top face: symbol, atomic number and formula
        offsets = np.array(((0.0, -0.045), (-0.32, -0.33), (0.0, 0.29)))
        anchor_x, anchor_y, _ = self._project(view, centres[:, 0:1] + offsets[None, :, 0],
                                              centres[:, 1:2] + offsets[None, :, 1], heights[:, None])
        bottom = np.stack((bottom_x, bottom_y), axis=2).tolist()  # plain floats build points much faster
        top = np.stack((top_x, top_y), axis=2).tolist()
        anchors = np.stack((anchor_x, anchor_y), axis=2).tolist()
        for index in order.tolist():
            self._paint_column(painter, elements[index], bottom[index], top[index], bands[index], anchors[index])
        if self.snapshot is not None and t < FADE:
            painter.setOpacity(1 - t / FADE)
            painter.drawPixmap(0, 0, self.snapshot)
            painter.setOpacity(1.0)
        self._paint_overlay(painter)

    def _paint_floor(self, painter: QPainter, view) -> None:
        if self.raise_amount <= 0:
            return
        corners = [self._project(view, x, y, 0.0) for x, y in ((-9.3, -5.3), (9.3, -5.3), (9.3, 5.15), (-9.3, 5.15))]
        floor = QColor(255, 255, 255, 12) if self.canvas.dark else QColor(0, 0, 0, 9)
        floor.setAlphaF(floor.alphaF() * self.raise_amount)
        painter.setPen(Qt.NoPen)
        painter.setBrush(floor)
        painter.drawPolygon(QPolygonF([QPointF(x, y) for x, y, _depth in corners]))

    def _paint_column(self, painter, element, bottom, top, band, anchors) -> None:
        canvas = self.canvas
        symbol = element.symbol
        fill = canvas._fill(element)
        empty = fill is None
        if empty:
            fill = QColor("#2b2d30" if canvas.dark else "#f4f5f7")
        side_brush, top_brush, top_pen = self._style(fill, empty)
        if band:
            side = QPolygonF([QPointF(*bottom[i]) for i in band] + [QPointF(*top[i]) for i in reversed(band)])
            painter.setPen(Qt.NoPen)
            painter.setBrush(side_brush)
            painter.drawPolygon(side)
            self._hits.append((symbol, side))
        top = QPolygonF([QPointF(x, y) for x, y in top])
        bounds = top.boundingRect()
        painter.setBrush(top_brush)
        painter.setPen(top_pen)
        if symbol == canvas.selected:
            painter.setPen(QPen(self.palette().highlight().color(), 2.2))
        elif symbol == self.hovered:
            painter.setPen(QPen(canvas._text_color(), 1.6))
        painter.drawPolygon(top)
        self._hits.append((symbol, top))
        size = min(bounds.width(), bounds.height() * 1.5)
        if size < 14:
            return
        dark_fill = not empty and fill.alpha() > 200 and fill.lightnessF() < 0.42
        dimmed = empty or (canvas.highlight_category and element.category != canvas.highlight_category)
        painter.setPen(canvas._muted() if dimmed else QColor("#ffffff" if dark_fill else "#15181c"))
        large = int(size * 0.36)
        painter.setFont(self._font(large))
        anchor = QPointF(*anchors[0])
        painter.drawText(QRectF(anchor.x() - large * 2, anchor.y() - large * 0.7, large * 4, large * 1.4),
                         Qt.AlignCenter, symbol)
        if size < 40 or self._moving():  # numbers and formulas wait until the view settles
            return
        small = max(int(size * 0.16), 7)
        painter.setFont(self._font(small))
        anchor = QPointF(*anchors[1])
        painter.drawText(QRectF(anchor.x() - small * 0.4, anchor.y() - small * 0.7, small * 3, small * 1.4),
                         Qt.AlignLeft | Qt.AlignVCenter, str(element.atomic_number))
        if element.stable is not None:
            from .periodic import formula_only

            anchor = QPointF(*anchors[2])
            draw_formula(painter, QRectF(anchor.x() - size * 0.42, anchor.y() - size * 0.14, size * 0.84, size * 0.28),
                         pretty_formula(formula_only(element.stable.species)), self._font(small))

    def _moving(self) -> bool:
        return (self._grow.isActive() or self._animation.state() == QVariantAnimation.Running
                or (self._press is not None and self._dragged))

    def _style(self, fill: QColor, empty: bool):
        """Side brush, top brush and top outline for a fill color, built once per color."""
        key = (fill.rgba(), empty, self.canvas.dark)
        if key not in self._styles:
            if empty:
                top_brush = QBrush(fill)
                pen = QPen(self.canvas._muted(), 0.8, Qt.DotLine)
            else:
                gradient = QLinearGradient(0, 0, 0, 1)
                gradient.setCoordinateMode(QGradient.ObjectBoundingMode)
                gradient.setColorAt(0.0, fill.lighter(112))
                gradient.setColorAt(1.0, fill.darker(104))
                top_brush = QBrush(gradient)
                edge = fill.darker(135)
                edge.setAlpha(fill.alpha())
                pen = QPen(edge, 1)
            self._styles[key] = (QBrush(fill.darker(128)), top_brush, pen)
        return self._styles[key]

    def _paint_overlay(self, painter: QPainter) -> None:
        canvas = self.canvas
        screen = canvas.screen
        opacity = min(max((self.raise_amount - FADE) / (1 - FADE), 0.0), 1.0)
        if opacity <= 0:
            return
        painter.setOpacity(opacity)
        painter.setFont(self._font(13))
        painter.setPen(canvas._text_color())
        painter.drawText(QRectF(16, 10, self.width() - 32, 20), Qt.AlignLeft | Qt.AlignVCenter,
                         f"pH {screen.pH:.2f}   ·   {screen.potential_V_vs_SHE:+.3f} V vs SHE")
        element = canvas.elements.get(self.hovered or "")
        if element is not None:
            lines = [element.system or element.symbol, element.category.label]
            if element.stable is not None:
                lines.append(f"Stable: {pretty_formula(element.stable.species)}")
            if element.energy_margin_J_mol_metal is not None:
                lines.append(f"Margin: {element.energy_margin_J_mol_metal / 1000:.1f} kJ/mol metal")
            elif element.reason:
                lines.append(element.reason)
            for index, line in enumerate(lines):
                painter.setPen(canvas._text_color() if index == 0 else canvas._muted())
                painter.drawText(QRectF(16, 34 + 18 * index, self.width() / 2, 18), Qt.AlignLeft | Qt.AlignVCenter,
                                 line)
        painter.setPen(canvas._muted())
        painter.setFont(self._font(12))
        painter.drawText(
            QRectF(16, self.height() - 26, self.width() - 32, 20), Qt.AlignCenter,
            f"Height: energy margin to the next species, log scale up to {MAX_MARGIN_KJ:g} kJ/mol metal  ·  "
            "color as in the table  ·  drag to rotate, scroll to zoom, double-click to reset",
        )
        painter.setOpacity(1.0)

    # interaction
    def _symbol_at(self, position: QPointF) -> str | None:
        for symbol, polygon in reversed(self._hits):
            if polygon.containsPoint(position, Qt.OddEvenFill):
                return symbol
        return None

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._press, self._dragged = event.position(), False

    def mouseMoveEvent(self, event) -> None:
        if self._press is not None and event.buttons() & Qt.LeftButton:
            delta = event.position() - self._press
            if self._dragged or abs(delta.x()) + abs(delta.y()) > 4:
                self._dragged = True
                self._press = event.position()
                self._animation.stop()
                self.raise_amount = 1.0
                self.yaw = (self.yaw - delta.x() * 0.4 + 180) % 360 - 180
                self.elevation = min(max(self.elevation + delta.y() * 0.3, 8.0), 90.0)
                self.update()
            return
        symbol = self._symbol_at(event.position())
        if symbol != self.hovered:
            self.hovered = symbol
            element = self.canvas.elements.get(symbol or "")
            opens = element is not None and element.status.has_system
            self.setCursor(Qt.PointingHandCursor if opens else Qt.OpenHandCursor)
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.LeftButton or self._press is None:
            return
        self._press = None
        if self._dragged:
            self.update()  # with numbers and formulas again
            return
        symbol = self._symbol_at(event.position())
        if symbol is not None and self.canvas.elements[symbol].status.has_system:
            self.elementClicked.emit(symbol)
        elif symbol is not None:
            QToolTip.showText(event.globalPosition().toPoint(), "No pourbase system for this element", self)

    def mouseDoubleClickEvent(self, _event) -> None:
        self.reset_camera()

    def wheelEvent(self, event) -> None:
        self.zoom = min(max(self.zoom * 1.0015 ** event.angleDelta().y(), 0.4), 4.0)
        self.update()

    def leaveEvent(self, _event) -> None:
        self.hovered = None
        self.update()

    def set_dark(self, _dark: bool) -> None:
        self.update()
