"""The periodic-table overview: a painted table of stable species and its controls."""

from __future__ import annotations

import math
import re

import numpy as np
from matplotlib import colormaps
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetricsF, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QMenu, QSizePolicy, QStackedWidget, QToolButton, QToolTip,
    QVBoxLayout, QWidget,
)

from ..inverse import KINDS
from ..overview import Category, ElementResult, ElementStatus, PeriodicScreen
from .figure_export import install_export_menu
from .formula import draw_formula, phase_label, pretty_formula
from .landscape import HEIGHT_TWEEN_MS, MarginLandscape
from .widgets import FloatSlider

CATEGORY_COLORS = {
    Category.DISSOLVED_OR_GAS: "#5b9bd5",
    Category.SOLID_OXIDE: "#ee7d4f",
    Category.HYDROXIDE: "#f5b75a",
    Category.ELEMENTAL_SOLID: "#a0aab5",
    Category.ELEMENTAL_LIQUID: "#b79ddb",
    Category.OTHER_SOLID: "#79c07f",
    Category.INCOMPLETE: "#f2a0a0",
}
COLOR_MODES = {"category": "Stable species category", "margin": "Stability margin",
               "window": "Share of a pH–potential window"}
UNIT_LABELS = {"log10_molar": "log₁₀ M", "molar": "M", "ppm": "ppm", "wt_percent": "wt %"}
F_BLOCK_MARKERS = {(5, 2): "57–71", (6, 2): "89–103"}
CARD_CELLS = ((0, 2), (2, 11))
PROVISIONAL_LABEL = "Some species are left out for missing data"


def formula_only(name: str) -> str:
    """The formula of a species name without a trailing qualifier: ``Y₂(CO₃)₃ (crystalline, NBS)`` → ``Y₂(CO₃)₃``."""
    return re.sub(r"\s+\([^()]*\)$", "", name)


def window_color(fraction: float) -> QColor:
    """Sequential color for the share of a window where a criterion holds, 0 to 1."""
    red, green, blue, _alpha = colormaps["YlGn"](0.12 + 0.83 * max(0.0, min(fraction, 1.0)))
    return QColor.fromRgbF(red, green, blue)


def table_position(atomic_number: int) -> tuple[int, int]:
    """(row, column) of an element; the f-block occupies rows 8 and 9."""
    if 57 <= atomic_number <= 71:
        return 8, atomic_number - 54
    if 89 <= atomic_number <= 103:
        return 9, atomic_number - 86
    for row, (first, last) in enumerate(((1, 2), (3, 10), (11, 18), (19, 36), (37, 54), (55, 86), (87, 118))):
        if first <= atomic_number <= last:
            offset = atomic_number - first
            if row == 0:
                return 0, 0 if offset == 0 else 17
            if row in (1, 2):
                return row, offset if offset < 2 else offset + 10
            if row in (3, 4):
                return row, offset
            return row, offset if offset < 2 else offset - 14
    raise ValueError(f"Unknown atomic number {atomic_number}")


def margin_color(margin_kJ: float) -> QColor:
    """Sequential color for the energy margin to the next species, 0 to about 100 kJ/mol."""
    fraction = min(max(math.log10(1 + max(margin_kJ, 0.0)) / 2.0, 0.0), 1.0)
    stops = ((0.0, (253, 231, 190)), (0.35, (246, 170, 92)), (0.7, (214, 96, 77)), (1.0, (122, 41, 88)))
    for (a, left), (b, right) in zip(stops, stops[1:]):
        if fraction <= b:
            t = (fraction - a) / (b - a)
            return QColor(*(round(low + t * (high - low)) for low, high in zip(left, right)))
    return QColor(*stops[-1][1])


class PeriodicTableCanvas(QWidget):
    elementClicked = Signal(str)
    redrawn = Signal()  # new screen, colors or selection; the margin landscape follows

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(760, 520)
        install_export_menu(self, self.export_table, "pourbase-periodic-table")
        self.screen: PeriodicScreen | None = None
        self.elements: dict[str, ElementResult] = {}
        self.hovered: str | None = None
        self.selected: str | None = None
        self.highlight_category: Category | None = None
        self.color_mode = "category"
        self.window: dict | None = None  # symbol → WindowResult of the window search
        self.window_label = ""
        self.dark = False
        self._tiles: dict[str, QRectF] = {}
        self._chips: dict[Category, QRectF] = {}
        self._static: QPixmap | None = None

    def show_screen(self, screen: PeriodicScreen) -> None:
        self.screen = screen
        self.elements = {item.symbol: item for item in screen.elements}
        self._redraw()

    def set_selected(self, symbol: str | None) -> None:
        self.selected = symbol
        self._redraw()

    def show_window(self, results: dict | None, label: str) -> None:
        self.window, self.window_label = results, label
        self._redraw()

    def _window_fraction(self, symbol: str) -> float | None:
        result = (self.window or {}).get(symbol)
        return None if result is None else result.fraction

    def set_color_mode(self, mode: str) -> None:
        self.color_mode = mode
        self._redraw()

    def set_dark(self, dark: bool) -> None:
        self.dark = dark
        self._redraw()

    def _redraw(self) -> None:
        self._static = None
        self.update()
        self.redrawn.emit()

    def resizeEvent(self, event) -> None:
        self._static = None
        super().resizeEvent(event)

    def _layout(self) -> tuple[float, QPointF, float]:
        """Tile pitch, grid origin, and the gap before the f-block rows."""
        pitch = min((self.width() - 40) / 18.6, (self.height() - 94) / 9.8)
        origin = QPointF((self.width() - 18 * pitch) / 2 + pitch * 0.3, 22 + pitch * 0.35)
        return pitch, origin, pitch * 0.35

    def _cell(self, row: int, column: int) -> QRectF:
        pitch, origin, gap = self._layout()
        y = origin.y() + row * pitch + (gap - pitch if row >= 8 else 0)
        inset = pitch * 0.045
        return QRectF(origin.x() + column * pitch + inset, y + inset, pitch - 2 * inset, pitch - 2 * inset)

    def _text_color(self) -> QColor:
        return QColor("#dfe1e5" if self.dark else "#1f2328")

    def _muted(self) -> QColor:
        return QColor("#7d828a" if self.dark else "#8a9099")

    def _fill(self, element: ElementResult) -> QColor | None:
        if element.category not in CATEGORY_COLORS:
            return None
        if self.color_mode == "window":
            fraction = self._window_fraction(element.symbol)
            return QColor(128, 128, 128, 40) if fraction is None else window_color(fraction)
        if self.color_mode == "margin" and element.energy_margin_J_mol_metal is not None:
            color = margin_color(element.energy_margin_J_mol_metal / 1000)
        else:
            color = QColor(CATEGORY_COLORS[element.category])
        if self.highlight_category and element.category != self.highlight_category:
            color.setAlphaF(0.22)
        return color

    def paintEvent(self, _event) -> None:
        if self.screen is None:
            return
        if self._static is None or self._static.size() != self.size() * self.devicePixelRatioF():
            self._static = self._paint_static()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(0, 0, self._static)
        pitch = self._layout()[0]
        base = QFont(self.font())
        if self.hovered in self.elements:
            cell = self._tiles[self.hovered].adjusted(-pitch * 0.06, -pitch * 0.06, pitch * 0.06, pitch * 0.06)
            self._paint_tile(painter, self.elements[self.hovered], cell, pitch, base, raised=True)
        card = self._cell(*CARD_CELLS[0]).united(self._cell(*CARD_CELLS[1])).adjusted(
            pitch * 0.15, pitch * 0.05, -pitch * 0.15, -pitch * 0.2
        )
        self._paint_card(painter, card, pitch, base)

    def _paint_static(self) -> QPixmap:
        """Everything that does not change on hover: labels, tiles and legend."""
        ratio = self.devicePixelRatioF()
        pixmap = QPixmap(self.size() * ratio)
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        pitch = self._layout()[0]
        base = QFont(self.font())
        painter.setPen(self._muted())
        label_font = QFont(base)
        label_font.setPixelSize(max(int(pitch * 0.2), 8))
        painter.setFont(label_font)
        for column in range(18):
            row = 0 if column in (0, 17) else 1 if column in (1, 12, 13, 14, 15, 16) else 3
            cell = self._cell(row, column)
            painter.drawText(QRectF(cell.left(), cell.top() - pitch * 0.34, cell.width(), pitch * 0.3),
                             Qt.AlignHCenter | Qt.AlignBottom, str(column + 1))
        for row in range(7):
            cell = self._cell(row, 0)
            painter.drawText(QRectF(cell.left() - pitch * 0.42, cell.top(), pitch * 0.34, cell.height()),
                             Qt.AlignRight | Qt.AlignVCenter, str(row + 1))
        painter.setPen(QPen(self._muted(), 1, Qt.DashLine))
        for (row, column), text in F_BLOCK_MARKERS.items():
            cell = self._cell(row, column)
            painter.drawRoundedRect(cell, pitch * 0.1, pitch * 0.1)
            painter.drawText(cell, Qt.AlignCenter, text)
        self._tiles = {}
        for symbol, element in self.elements.items():
            cell = self._cell(*table_position(element.atomic_number))
            self._tiles[symbol] = cell
            self._paint_tile(painter, element, cell, pitch, base)
        self._paint_legend(painter, QRectF(12, self._cell(9, 0).bottom() + 14, self.width() - 24, 50), base)
        painter.end()
        return pixmap

    def _paint_tile(
        self, painter: QPainter, element: ElementResult, cell: QRectF, pitch: float, base: QFont,
        raised: bool = False,
    ) -> None:
        radius = pitch * 0.12
        fill = self._fill(element)
        path = QPainterPath()
        path.addRoundedRect(cell, radius, radius)
        if raised:
            shadow = QPainterPath()
            shadow.addRoundedRect(cell.translated(0, pitch * 0.05), radius, radius)
            painter.fillPath(shadow, QColor(0, 0, 0, 70))
        if fill is not None:
            gradient = QLinearGradient(cell.topLeft(), cell.bottomLeft())
            gradient.setColorAt(0.0, fill.lighter(112))
            gradient.setColorAt(1.0, fill.darker(104))
            painter.fillPath(path, QBrush(gradient))
            border = fill.darker(135)
            border.setAlpha(fill.alpha())
            painter.setPen(QPen(border, 1))
            dimmed = self.highlight_category and element.category != self.highlight_category
            dark_fill = fill.alpha() > 200 and fill.lightnessF() < 0.42  # white text on dark tiles
            text = self._muted() if dimmed else QColor("#ffffff" if dark_fill else "#15181c")
        else:
            painter.fillPath(path, QColor("#2b2d30" if self.dark else "#f4f5f7"))
            painter.setPen(QPen(self._muted(), 0.8, Qt.DotLine))
            text = self._muted()
        painter.drawPath(path)
        if element.status.is_provisional:
            dark_fill = fill is not None and fill.lightness() < 110
            outline = QColor(255, 255, 255, 200) if dark_fill else QColor(20, 20, 20, 150)
            painter.setPen(QPen(outline, max(pitch * 0.025, 1.2), Qt.DashLine))
            painter.drawRoundedRect(cell.adjusted(3, 3, -3, -3), radius * 0.7, radius * 0.7)
        if element.symbol == self.selected:
            painter.setPen(QPen(self.palette().highlight().color(), max(pitch * 0.06, 2)))
            painter.drawRoundedRect(cell.adjusted(1, 1, -1, -1), radius, radius)
        if raised:
            painter.setPen(QPen(self._text_color(), 1.6))
            painter.drawPath(path)
        pad = cell.width() * 0.08
        painter.setPen(text)
        small = QFont(base)
        small.setPixelSize(max(int(cell.height() * 0.16), 7))
        painter.setFont(small)
        painter.drawText(cell.adjusted(pad, pad * 0.6, -pad, 0), Qt.AlignLeft | Qt.AlignTop,
                         str(element.atomic_number))
        large = QFont(base)
        large.setPixelSize(max(int(cell.height() * 0.36), 9))
        painter.setFont(large)
        painter.drawText(QRectF(cell.left(), cell.top() + cell.height() * 0.14, cell.width(), cell.height() * 0.5),
                         Qt.AlignCenter, element.symbol)
        if self.color_mode == "window" and self._window_fraction(element.symbol) is not None:
            painter.setFont(small)
            painter.drawText(QRectF(cell.left() + pad, cell.bottom() - cell.height() * 0.34,
                                    cell.width() - 2 * pad, cell.height() * 0.28), Qt.AlignCenter,
                             f"{self._window_fraction(element.symbol):.0%}")
        elif element.stable is not None:
            draw_formula(painter, QRectF(cell.left() + pad, cell.bottom() - cell.height() * 0.34,
                                         cell.width() - 2 * pad, cell.height() * 0.28), pretty_formula(formula_only(element.stable.species)), small)

    def _paint_card(self, painter: QPainter, card: QRectF, pitch: float, base: QFont) -> None:
        screen = self.screen
        element = self.elements.get(self.hovered or "") or self.elements.get(self.selected or "")
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 12) if self.dark else QColor(0, 0, 0, 8))
        painter.drawRoundedRect(card, pitch * 0.15, pitch * 0.15)
        pad = pitch * 0.2
        inner = card.adjusted(pad, pad * 0.7, -pad, -pad * 0.5)
        title = QFont(base)
        title.setPixelSize(max(int(pitch * 0.34), 10))
        body = QFont(base)
        body.setPixelSize(max(int(pitch * 0.2), 8))
        if element is None:
            painter.setPen(self._text_color())
            painter.setFont(title)
            painter.drawText(inner, Qt.AlignLeft | Qt.AlignTop, "Stable species across the periodic table")
            painter.setFont(body)
            painter.setPen(self._muted())
            painter.drawText(
                inner.adjusted(0, pitch * 0.5, 0, 0), Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                f"pH {screen.pH:g}  ·  {screen.potential_V_vs_SHE:+.3f} V vs SHE  ·  "
                f"{screen.concentration:g} {UNIT_LABELS.get(screen.concentration_unit, '')}\n"
                f"{screen.calculated_count} of {screen.supported_count} supported systems calculated. "
                "Hover over an element for details; click to open its Pourbaix diagram.",
            )
            return
        swatch = self._fill(element) or QColor(self._muted())
        swatch.setAlpha(255)
        painter.setBrush(swatch)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(inner.left(), inner.top() + pitch * 0.05, pitch * 0.18, pitch * 0.36), 3, 3)
        painter.setPen(self._text_color())
        painter.setFont(title)
        painter.drawText(inner.adjusted(pitch * 0.3, 0, 0, 0), Qt.AlignLeft | Qt.AlignTop,
                         element.system or element.symbol)
        lines: list[str | tuple[str, str]] = [element.category.label]
        if self.color_mode == "window" and self.window is not None:
            result = self.window.get(element.symbol)
            if result is not None and result.fraction is not None:
                text = f"{self.window_label}: {result.fraction:.0%} of the window"
                if result.minimum_margin_J_mol_metal is not None and np.isfinite(result.minimum_margin_J_mol_metal):
                    text += f"; smallest margin {result.minimum_margin_J_mol_metal / 1000:+.1f} kJ/mol metal"
                lines.append(text)
            elif result is not None:
                lines.append(f"Not calculated in the window: {result.note}")
        if element.stable is not None:
            phase = phase_label(element.stable)
            phase = phase if len(phase) <= 48 else phase[:46].rstrip(" ,;(") + "…"
            lines.append(("formula", f"Stable: {element.stable.species}  ({phase})"))
            if element.energy_margin_J_mol_metal is not None:
                lines.append(f"Margin to the next species: {element.energy_margin_J_mol_metal / 1000:.2f} kJ/mol metal")
            if element.gibbs_source and element.gibbs_source.citation:
                lines.append(f"ΔfG°: {element.gibbs_source.citation}")
        elif element.reason:
            lines.append(element.reason)
        if element.status is ElementStatus.CALCULATED_WITH_FALLBACK:
            lines.append("Materials Project 300 K estimates replace the missing experimental formation energies")
        if element.missing_record_ids:
            count = len(element.missing_record_ids)
            lines.append(f"{count} species without a recommended formation energy {'is' if count == 1 else 'are'} "
                         "left out of this calculation")
        painter.setFont(body)
        metrics = QFontMetricsF(body)
        top = inner.top() + pitch * 0.5
        painter.save()
        painter.setClipRect(inner)
        flags = Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap
        for line in lines:
            if top + metrics.height() > inner.bottom():
                break
            if isinstance(line, tuple):
                painter.setPen(self._text_color())
                draw_formula(painter, QRectF(inner.left(), top, inner.width(), metrics.height() * 1.3),
                             line[1], body, Qt.AlignLeft | Qt.AlignTop)
                top += metrics.height() * 1.3
                continue
            painter.setPen(self._muted())
            # at most two wrapped lines per entry; longer text, such as a full citation, ends in "…"
            bounds = painter.boundingRect(QRectF(inner.left(), top, inner.width(), 1000), flags, line)
            if bounds.height() > metrics.lineSpacing() * 2.2:
                line = metrics.elidedText(line, Qt.ElideRight, inner.width() * 1.85)
                bounds = painter.boundingRect(QRectF(inner.left(), top, inner.width(), 1000), flags, line)
            bounds.setBottom(min(bounds.bottom(), inner.bottom()))
            painter.drawText(bounds, flags, line)
            top = bounds.bottom() + metrics.height() * 0.15
        painter.restore()

    def _paint_legend(self, painter: QPainter, area: QRectF, base: QFont) -> None:
        self._chips = {}
        font = QFont(base)
        font.setPixelSize(12)
        painter.setFont(font)
        metrics = QFontMetricsF(font)
        provisional = sum(item.status.is_provisional for item in self.elements.values())
        key_text = f"{PROVISIONAL_LABEL}  {provisional}"
        key_width = metrics.horizontalAdvance(key_text) + 40 if provisional else 0.0
        if self.color_mode == "window":
            width = min(area.width() * 0.5, 420)
            bar = QRectF(area.center().x() - width / 2, area.top() + 6, width, 12)
            for step in range(100):
                painter.fillRect(QRectF(bar.left() + step * width / 100, bar.top(), width / 100 + 1, bar.height()),
                                 window_color(step / 99))
            painter.setPen(self._muted())
            for value in (0, 25, 50, 75, 100):
                x = bar.left() + width * value / 100
                painter.drawText(QRectF(x - 30, bar.bottom() + 2, 60, 16), Qt.AlignCenter, f"{value}%")
            caption = f"Share of the window: {self.window_label}" if self.window is not None else \
                "Set a window and a criterion above"
            painter.drawText(QRectF(bar.left() - 100, bar.bottom() + 18, width + 200, 16), Qt.AlignCenter, caption)
            x = bar.right() + 36
        elif self.color_mode == "margin":
            width = min(area.width() * 0.5, 420)
            bar = QRectF(area.center().x() - width / 2, area.top() + 6, width, 12)
            for step in range(100):
                painter.fillRect(QRectF(bar.left() + step * width / 100, bar.top(), width / 100 + 1, bar.height()),
                                 margin_color(10 ** (2 * step / 99) - 1))
            painter.setPen(self._muted())
            for value in (0, 1, 10, 100):
                x = bar.left() + width * math.log10(1 + value) / math.log10(101)
                painter.drawText(QRectF(x - 30, bar.bottom() + 2, 60, 16), Qt.AlignCenter, f"{value}")
            painter.drawText(QRectF(bar.left(), bar.bottom() + 18, width, 16), Qt.AlignCenter,
                             "Energy margin to the next species (kJ/mol metal)")
            x = bar.right() + 36
        else:
            counts = self.screen.category_counts
            chips = [(key, f"{key.label}  {counts[key]}") for key in CATEGORY_COLORS if counts.get(key)]
            widths = [metrics.horizontalAdvance(text) + 34 for _, text in chips]
            x = area.center().x() - (sum(widths) + 8 * (len(widths) - 1) + (key_width + 16 if key_width else 0)) / 2
            for (key, text), width in zip(chips, widths):
                chip = QRectF(x, area.top() + 4, width, 26)
                self._chips[key] = chip
                active = self.highlight_category in (None, key)
                background = QColor(255, 255, 255, 18) if self.dark else QColor(0, 0, 0, 10)
                if self.highlight_category == key:
                    background = QColor(self.palette().highlight().color())
                    background.setAlpha(60)
                painter.setPen(Qt.NoPen)
                painter.setBrush(background)
                painter.drawRoundedRect(chip, 13, 13)
                swatch = QColor(CATEGORY_COLORS[key])
                if not active:
                    swatch.setAlphaF(0.3)
                painter.setBrush(swatch)
                painter.drawEllipse(QRectF(chip.left() + 9, chip.center().y() - 6, 12, 12))
                painter.setPen(self._text_color() if active else self._muted())
                painter.drawText(chip.adjusted(27, 0, -6, 0), Qt.AlignVCenter | Qt.AlignLeft, text)
                x += width + 8
            x += 8
        if provisional:
            chip = QRectF(x, area.top() + 4, key_width, 26)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, 18) if self.dark else QColor(0, 0, 0, 10))
            painter.drawRoundedRect(chip, 13, 13)
            painter.setPen(QPen(self._text_color(), 1.3, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(QRectF(chip.left() + 9, chip.center().y() - 7, 16, 14), 3, 3)
            painter.setPen(self._text_color())
            painter.drawText(chip.adjusted(32, 0, -6, 0), Qt.AlignVCenter | Qt.AlignLeft, key_text)

    def _symbol_at(self, position: QPointF) -> str | None:
        return next((symbol for symbol, cell in self._tiles.items() if cell.contains(position)), None)

    def mouseMoveEvent(self, event) -> None:
        symbol = self._symbol_at(event.position())
        over_chip = any(rect.contains(event.position()) for rect in self._chips.values())
        opens = symbol is not None and self.elements[symbol].status.has_system
        self.setCursor(Qt.PointingHandCursor if over_chip or opens else Qt.ArrowCursor)
        if symbol != self.hovered:
            self.hovered = symbol
            self.update()

    def leaveEvent(self, _event) -> None:
        self.hovered = None
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return
        for key, rect in self._chips.items():
            if rect.contains(event.position()):
                self.highlight_category = None if self.highlight_category == key else key
                self._redraw()
                return
        symbol = self._symbol_at(event.position())
        if symbol is not None and self.elements[symbol].status.has_system:
            self.elementClicked.emit(symbol)
        elif symbol is not None:
            QToolTip.showText(event.globalPosition().toPoint(), "No pourbase system for this element", self)


def _export_table(canvas) -> object:
    screen = canvas.screen
    if screen is None:
        return None
    rows = []
    for element in screen.elements:
        stable = element.stable
        rows.append((element.atomic_number, element.symbol, element.system or "", element.status.value,
                     stable.species if stable else "", phase_label(stable) if stable else "",
                     element.category.label,
                     f"{element.energy_margin_J_mol_metal / 1000:.3f}" if element.energy_margin_J_mol_metal is not None else "",
                     element.gibbs_source.citation if element.gibbs_source and element.gibbs_source.citation else ""))
    header = ("Z", "symbol", "system", "status", "stable species", "phase", "category",
              "margin to next species (kJ/mol metal)", "Formation energy source")
    return header, rows


PeriodicTableCanvas.export_table = _export_table


class OverviewPage(QWidget):
    """Point conditions and the periodic table; ``changed`` asks for a new screen."""

    changed = Signal()
    ligandToggled = Signal(str, bool)  # ligand ID, or "" for every reservoir at once
    temperatureChanged = Signal(float)  # °C; the same setting as System → Temperature

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.pH = FloatSlider("pH", -2.0, 16.0, 7.0, decimals=2, step=0.25, label_width=24)
        self.potential = FloatSlider("U", -2.5, 2.5, 0.0, decimals=3, step=0.05, unit="V", label_width=14)
        self.reference = QComboBox()
        self.reference.addItems(["vs SHE", "vs RHE"])
        self.temperature = FloatSlider("T", 0.0, 100.0, 25.0, decimals=1, step=5.0, unit="°C", label_width=14)
        self.temperature.setToolTip("Temperature of every element; the same setting as System → Temperature")
        self.color = QComboBox()
        for key, label in COLOR_MODES.items():
            self.color.addItem(label, key)
        self.ligand_button = QToolButton()
        self.ligand_button.setText("Ligands: off")
        self.ligand_button.setPopupMode(QToolButton.InstantPopup)
        self.ligand_menu = QMenu(self.ligand_button)
        self.ligand_button.setMenu(self.ligand_menu)
        self.ligand_actions: dict[str, object] = {}
        self.note = QLabel()
        self.note.setStyleSheet("color: gray;")
        self.window_bar = self._window_controls()
        self.canvas = PeriodicTableCanvas()
        self.landscape = MarginLandscape(self.canvas)
        self.landscape.elementClicked.connect(self.canvas.elementClicked)
        self.landscape.animationFinished.connect(self._landscape_settled)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.canvas)
        self.stack.addWidget(self.landscape)
        self.view_button = QToolButton()
        self.view_button.setText("3D")
        self.view_button.setCheckable(True)
        self.view_button.setToolTip("Raise the table into a 3D landscape of stability margins")
        self.view_button.toggled.connect(self.set_3d)
        self.sweep_bar = self._sweep_controls()
        self.sweep_button = QToolButton()
        self.sweep_button.setText("Sweep")
        self.sweep_button.setCheckable(True)
        self.sweep_button.setToolTip("Play the table through a range of pH or potential")
        self.sweep_button.toggled.connect(self._sweep_shown)
        self.screener = None  # (pH, potential) → PeriodicScreen at the current System settings; set by the window
        for slider in (self.pH, self.potential):
            slider.valueChanged.connect(lambda _value: self.changed.emit())
        self.reference.currentIndexChanged.connect(lambda _index: self.changed.emit())
        self.temperature.valueChanged.connect(self.temperatureChanged)
        self.color.currentIndexChanged.connect(self._color_mode_changed)
        controls = QHBoxLayout()
        controls.addWidget(self.pH, 3)
        controls.addSpacing(16)
        controls.addWidget(self.potential, 3)
        controls.addWidget(self.reference)
        controls.addSpacing(16)
        controls.addWidget(self.temperature, 2)
        controls.addSpacing(16)
        controls.addWidget(self.ligand_button)
        controls.addSpacing(16)
        controls.addWidget(QLabel("Color by"))
        controls.addWidget(self.color)
        controls.addSpacing(16)
        controls.addWidget(self.view_button)
        controls.addWidget(self.sweep_button)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 8)
        layout.addLayout(controls)
        layout.addWidget(self.note)
        layout.addWidget(self.window_bar)
        layout.addWidget(self.sweep_bar)
        layout.addWidget(self.stack, 1)
        self.window_bar.hide()
        self.sweep_bar.hide()

    def set_ligands(self, references, settings) -> None:
        """Show the ligand reservoirs of ``settings`` for the ligands in ``references``."""
        if not self.ligand_actions:
            master = self.ligand_menu.addAction("Use ligand reservoirs")
            master.setCheckable(True)
            master.toggled.connect(lambda checked: self.ligandToggled.emit("", checked))
            self.ligand_actions[""] = master
            self.ligand_menu.addSeparator()
            for reference in sorted(references, key=lambda item: item.name):
                action = self.ligand_menu.addAction(reference.name)
                action.setCheckable(True)
                action.toggled.connect(lambda checked, key=reference.ligand_id: self.ligandToggled.emit(key, checked))
                self.ligand_actions[reference.ligand_id] = action
        enabled = [key for key, setting in settings.ligands.items() if setting.enabled]
        for key, action in self.ligand_actions.items():
            action.blockSignals(True)
            if key == "":
                action.setChecked(settings.use_ligands)
            else:
                action.setChecked(key in enabled)
                action.setEnabled(settings.use_ligands)
            action.blockSignals(False)
        names = [self.ligand_actions[key].text() for key in sorted(enabled) if key in self.ligand_actions]
        active = settings.use_ligands and names
        self.ligand_button.setText(f"Ligands: {len(names)} on" if active else "Ligands: off")
        self.ligand_button.setToolTip("Buffered ligand reservoirs for every element, here and in the element "
                                      "view: " + (", ".join(names) if active else "none"))

    windowChanged = Signal()

    def _window_controls(self) -> QWidget:
        """pH and potential limits, a criterion and a margin for the window search."""
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)

        def spin(low, high, value, decimals, step, suffix=""):
            box = QDoubleSpinBox()
            box.setRange(low, high)
            box.setDecimals(decimals)
            box.setSingleStep(step)
            box.setValue(value)
            box.setSuffix(suffix)
            box.setKeyboardTracking(False)
            box.valueChanged.connect(lambda _value: self.windowChanged.emit())
            return box

        self.window_pH = (spin(-2, 16, 2.0, 2, 0.5), spin(-2, 16, 4.0, 2, 0.5))
        self.window_U = (spin(-2.5, 2.5, 0.8, 3, 0.05, " V"), spin(-2.5, 2.5, 1.2, 3, 0.05, " V"))
        self.window_kind = QComboBox()
        for key, label in KINDS.items():
            self.window_kind.addItem(label, key)
        self.window_kind.setCurrentIndex(self.window_kind.findData("passivation"))
        self.window_kind.currentIndexChanged.connect(lambda _index: self.windowChanged.emit())
        self.window_margin = spin(0.0, 100.0, 0.0, 1, 1.0, " kJ/mol")
        self.window_margin.setToolTip("The criterion holds where its species lie at least this far below all others")
        for widget in (QLabel("Window: pH"), self.window_pH[0], QLabel("to"), self.window_pH[1],
                       QLabel("  U vs SHE"), self.window_U[0], QLabel("to"), self.window_U[1],
                       QLabel("  Criterion"), self.window_kind, QLabel("  Margin at least"), self.window_margin):
            row.addWidget(widget)
        row.addStretch(1)
        return bar

    def set_3d(self, on: bool) -> None:
        """Raise the table into the margin landscape, or lower it back to the flat table."""
        if self.view_button.isChecked() != on:
            self.view_button.setChecked(on)  # calls back here through toggled
            return
        self.landscape.snapshot = self.canvas.grab()  # faded into the columns as they rise, and back
        if on:
            self.landscape.refresh()
            self.stack.setCurrentWidget(self.landscape)
            self.landscape.animate_to(1.0)
        else:
            self.landscape.animate_to(0.0)

    def _landscape_settled(self, amount: float) -> None:
        if amount <= 0.0 and not self.view_button.isChecked():
            self.stack.setCurrentWidget(self.canvas)

    def _sweep_controls(self) -> QWidget:
        """Play the table through a range of pH or potential, in 2D or 3D."""
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        self.sweep_variable = QComboBox()
        self.sweep_variable.addItem("pH", "pH")
        self.sweep_variable.addItem("Potential", "U")
        self.sweep_range = (QDoubleSpinBox(), QDoubleSpinBox())
        self.sweep_steps = QDoubleSpinBox()
        self.sweep_steps.setDecimals(0)
        self.sweep_steps.setRange(5, 400)
        self.sweep_steps.setValue(80)
        self.sweep_steps.setToolTip("Number of frames from start to end")
        self.sweep_variable.currentIndexChanged.connect(self._sweep_variable_changed)
        self.play_button = QToolButton()
        self.play_button.setText("▶ Play")
        self.play_button.setCheckable(True)
        self.play_button.toggled.connect(self._play_toggled)
        self.loop_button = QToolButton()
        self.loop_button.setText("Loop")
        self.loop_button.setCheckable(True)
        self.loop_button.setToolTip("Run back and forth until stopped")
        for widget in (QLabel("Sweep"), self.sweep_variable, QLabel("from"), self.sweep_range[0], QLabel("to"),
                       self.sweep_range[1], QLabel("  Frames"), self.sweep_steps, self.play_button,
                       self.loop_button):
            row.addWidget(widget)
        row.addStretch(1)
        self._sweep_timer = QTimer(self, interval=40, timeout=self._sweep_step)
        self._sweep_frame, self._sweep_direction = 0, 1
        self._sweep_variable_changed()
        return bar

    def _sweep_shown(self, shown: bool) -> None:
        self.sweep_bar.setVisible(shown)
        if not shown:
            self.play_button.setChecked(False)

    def _sweep_variable_changed(self) -> None:
        pH = self.sweep_variable.currentData() == "pH"
        for box, value in zip(self.sweep_range, (0.0, 14.0) if pH else (-1.5, 2.0)):
            box.setRange(-2.0, 16.0) if pH else box.setRange(-2.5, 2.5)
            box.setDecimals(2 if pH else 3)
            box.setSingleStep(0.5 if pH else 0.05)
            box.setSuffix("" if pH else " V")
            box.setValue(value)

    def _play_toggled(self, playing: bool) -> None:
        self.play_button.setText("■ Stop" if playing else "▶ Play")
        if playing and self.screener is not None:
            self._sweep_frame, self._sweep_direction = 0, 1
            self.landscape.tween_ms = self._sweep_timer.interval()  # columns glide from frame to frame
            self._sweep_timer.start()
        else:
            self._sweep_timer.stop()
            self.landscape.tween_ms = HEIGHT_TWEEN_MS
            if not playing:
                self.changed.emit()  # the window takes the last frame as the current conditions

    def _sweep_step(self) -> None:
        frames = int(self.sweep_steps.value())
        start, end = self.sweep_range[0].value(), self.sweep_range[1].value()
        value = start + (end - start) * self._sweep_frame / max(frames - 1, 1)
        slider = self.pH if self.sweep_variable.currentData() == "pH" else self.potential
        slider.setValue(value)
        conditions = self.conditions()
        try:
            screen = self.screener(conditions["pH"], conditions["potential_V"])
        except Exception:
            self.play_button.setChecked(False)
            raise
        self.canvas.show_screen(screen)
        self._sweep_frame += self._sweep_direction
        if not 0 <= self._sweep_frame < frames:
            if self.loop_button.isChecked():
                self._sweep_direction *= -1
                self._sweep_frame += 2 * self._sweep_direction
            else:
                self.play_button.setChecked(False)

    def window(self) -> dict:
        return {"kind": self.window_kind.currentData(),
                "pH": (self.window_pH[0].value(), self.window_pH[1].value()),
                "U_V": (self.window_U[0].value(), self.window_U[1].value()),
                "min_margin_J_mol": self.window_margin.value() * 1000}

    def _color_mode_changed(self) -> None:
        mode = self.color.currentData()
        self.window_bar.setVisible(mode == "window")
        self.canvas.set_color_mode(mode)
        if mode == "window":
            self.windowChanged.emit()

    def conditions(self) -> dict[str, object]:
        return {
            "pH": self.pH.value(), "potential_V": self.potential.value(),
            "reference": "RHE" if self.reference.currentIndex() == 1 else "SHE",
        }
