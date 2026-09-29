"""Painted periodic table colored by the stable species at one pH and potential."""

from __future__ import annotations

import math
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush, QColor, QFont, QFontMetricsF, QLinearGradient, QPainter, QPainterPath, QPen,
)
from PySide6.QtWidgets import QSizePolicy, QToolTip, QWidget

from .formula import draw_formula

CATEGORY_COLORS = {
    "dissolved_or_gas": "#5b9bd5",
    "solid_oxide": "#ee7d4f",
    "hydroxide_or_oxyhydroxide": "#f5b75a",
    "elemental_solid": "#a0aab5",
    "elemental_liquid": "#b79ddb",
    "other_solid": "#79c07f",
    "incomplete": "#f2a0a0",
}
CALCULATED_CATEGORIES = tuple(CATEGORY_COLORS)
COLOR_MODES = {"category": "Stable species category", "margin": "Stability margin"}

UNIT_LABELS = {"log10_molar": "log₁₀ M", "molar": "M", "ppm": "ppm", "wt_percent": "wt %"}
GROUP_LABELS = [str(number) for number in range(1, 19)]
F_BLOCK_MARKERS = {(5, 2): "57–71", (6, 2): "89–103"}
CARD_COLUMNS = (2, 11)  # empty block above the transition metals, used for the detail card
CARD_ROWS = (0, 2)


def table_position(atomic_number: int) -> tuple[int, int]:
    """Return the (row, column) of an element; the f-block occupies rows 8 and 9."""
    if 57 <= atomic_number <= 71:
        return 8, atomic_number - 57 + 3
    if 89 <= atomic_number <= 103:
        return 9, atomic_number - 89 + 3
    periods = ((1, 2), (3, 10), (11, 18), (19, 36), (37, 54), (55, 86), (87, 118))
    for row, (first, last) in enumerate(periods):
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
    """Sequential color for the energy margin to the next species (0 to about 100 kJ/mol)."""
    fraction = min(max(math.log10(1 + max(margin_kJ, 0.0)) / 2.0, 0.0), 1.0)
    stops = ((0.0, (253, 231, 190)), (0.35, (246, 170, 92)), (0.7, (214, 96, 77)), (1.0, (122, 41, 88)))
    for (a, left), (b, right) in zip(stops, stops[1:]):
        if fraction <= b:
            t = (fraction - a) / (b - a)
            return QColor(*(round(l + t * (r - l)) for l, r in zip(left, right)))
    return QColor(*stops[-1][1])


class PeriodicTableCanvas(QWidget):
    elementClicked = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(760, 520)
        self.screen: dict[str, Any] | None = None
        self.elements: dict[str, dict[str, Any]] = {}
        self.hovered: str | None = None
        self.selected: str | None = None
        self.highlight_category: str | None = None
        self.color_mode = "category"
        self.dark = False
        self._tiles: dict[str, QRectF] = {}
        self._chips: dict[str, QRectF] = {}

    # -- data --------------------------------------------------------------------------------

    def show_screen(self, screen: dict[str, Any]) -> None:
        self.screen = screen
        self.elements = {item["symbol"]: item for item in screen["elements"]}
        self.update()

    def set_selected(self, symbol: str | None) -> None:
        self.selected = symbol
        self.update()

    def set_color_mode(self, mode: str) -> None:
        self.color_mode = mode
        self.update()

    def set_dark(self, dark: bool) -> None:
        self.dark = dark
        self.update()

    @staticmethod
    def clickable(element: dict[str, Any]) -> bool:
        """Calculated systems (also with gaps or MP fallbacks) and withheld incomplete systems."""
        return element["status"].startswith("calculated") or element["status"] == "incomplete"

    @staticmethod
    def provisional(element: dict[str, Any]) -> bool:
        """The result omits species without Gibbs data or uses MP fallback estimates."""
        return element["status"] in ("calculated_with_gaps", "calculated_with_fallback")

    # -- geometry ----------------------------------------------------------------------------

    def _layout(self) -> tuple[float, QPointF, float]:
        """Tile pitch, origin of the grid, and the gap before the f-block rows."""
        legend_height = 64.0
        width = self.width() - 40
        height = self.height() - legend_height - 30
        pitch = min(width / 18.6, height / 9.8)
        gap = pitch * 0.35
        grid_width = 18 * pitch
        origin = QPointF((self.width() - grid_width) / 2 + pitch * 0.3, 22 + pitch * 0.35)
        return pitch, origin, gap

    def _cell(self, row: int, column: int, pitch: float, origin: QPointF, gap: float) -> QRectF:
        y = origin.y() + row * pitch + (gap - pitch if row >= 8 else 0)
        inset = pitch * 0.045
        return QRectF(origin.x() + column * pitch + inset, y + inset, pitch - 2 * inset, pitch - 2 * inset)

    # -- colors ------------------------------------------------------------------------------

    def _text_color(self) -> QColor:
        return QColor("#dfe1e5" if self.dark else "#1f2328")

    def _muted(self) -> QColor:
        return QColor("#7d828a" if self.dark else "#8a9099")

    def _fill(self, element: dict[str, Any]) -> QColor | None:
        category = element["category"]
        if category not in CALCULATED_CATEGORIES:
            return None
        if self.color_mode == "margin" and element.get("energy_margin_J_mol_metal") is not None:
            color = margin_color(element["energy_margin_J_mol_metal"] / 1000)
        else:
            color = QColor(CATEGORY_COLORS[category])
        if self.highlight_category and category != self.highlight_category:
            color.setAlphaF(0.22)
        return color

    # -- painting ----------------------------------------------------------------------------

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        if self.screen is None:
            return
        pitch, origin, gap = self._layout()
        self._tiles = {}
        base = QFont(self.font())

        # Group and period labels
        painter.setPen(self._muted())
        label_font = QFont(base)
        label_font.setPixelSize(max(int(pitch * 0.2), 8))
        painter.setFont(label_font)
        for column, text in enumerate(GROUP_LABELS):
            row = 0 if column in (0, 17) else (1 if column in (1, 12, 13, 14, 15, 16) else 3)
            cell = self._cell(row, column, pitch, origin, gap)
            painter.drawText(QRectF(cell.left(), cell.top() - pitch * 0.34, cell.width(), pitch * 0.3),
                             Qt.AlignHCenter | Qt.AlignBottom, text)
        for row in range(7):
            cell = self._cell(row, 0, pitch, origin, gap)
            painter.drawText(QRectF(cell.left() - pitch * 0.42, cell.top(), pitch * 0.34, cell.height()),
                             Qt.AlignRight | Qt.AlignVCenter, str(row + 1))

        # f-block markers
        for (row, column), text in F_BLOCK_MARKERS.items():
            cell = self._cell(row, column, pitch, origin, gap)
            painter.setPen(QPen(self._muted(), 1, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(cell, pitch * 0.1, pitch * 0.1)
            painter.drawText(cell, Qt.AlignCenter, text)

        for symbol, element in self.elements.items():
            row, column = table_position(element["atomic_number"])
            cell = self._cell(row, column, pitch, origin, gap)
            self._tiles[symbol] = cell
            if symbol != self.hovered:
                self._paint_tile(painter, symbol, element, cell, pitch, base)
        if self.hovered in self.elements:
            cell = self._tiles[self.hovered].adjusted(-pitch * 0.06, -pitch * 0.06, pitch * 0.06, pitch * 0.06)
            self._paint_tile(painter, self.hovered, self.elements[self.hovered], cell, pitch, base, raised=True)

        card = self._cell(CARD_ROWS[0], CARD_COLUMNS[0], pitch, origin, gap).united(
            self._cell(CARD_ROWS[1], CARD_COLUMNS[1], pitch, origin, gap)
        ).adjusted(pitch * 0.15, pitch * 0.05, -pitch * 0.15, -pitch * 0.2)
        self._paint_card(painter, card, pitch, base)
        bottom = self._cell(9, 0, pitch, origin, gap).bottom()
        self._paint_legend(painter, QRectF(12, bottom + 14, self.width() - 24, 50), base)

    def _paint_tile(
        self, painter: QPainter, symbol: str, element: dict[str, Any], cell: QRectF,
        pitch: float, base: QFont, raised: bool = False,
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
            text = QColor("#15181c")
            if self.highlight_category and element["category"] != self.highlight_category:
                text = self._muted()
        else:
            background = QColor("#2b2d30" if self.dark else "#f4f5f7")
            painter.fillPath(path, background)
            painter.setPen(QPen(self._muted(), 0.8, Qt.DotLine))
            text = self._muted()
        painter.drawPath(path)
        if self.provisional(element):
            # Dashed inner outline: provisional result (species left out or MP estimates used)
            outline = QColor(255, 255, 255, 200) if fill is not None and fill.lightness() < 110 else QColor(20, 20, 20, 150)
            painter.setPen(QPen(outline, max(pitch * 0.025, 1.2), Qt.DashLine))
            painter.drawRoundedRect(cell.adjusted(3, 3, -3, -3), radius * 0.7, radius * 0.7)
        if symbol == self.selected:
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
                         str(element["atomic_number"]))
        large = QFont(base)
        large.setPixelSize(max(int(cell.height() * 0.36), 9))
        painter.setFont(large)
        painter.drawText(QRectF(cell.left(), cell.top() + cell.height() * 0.14, cell.width(), cell.height() * 0.5),
                         Qt.AlignCenter, symbol)
        species = element.get("stable_species")
        if species:
            draw_formula(
                painter,
                QRectF(cell.left() + pad, cell.bottom() - cell.height() * 0.34, cell.width() - 2 * pad,
                       cell.height() * 0.28),
                species, small,
            )

    def _paint_card(self, painter: QPainter, card: QRectF, pitch: float, base: QFont) -> None:
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
        conditions = self.screen["conditions"]
        condition_text = (
            f"pH {conditions['pH']:g}  ·  {conditions['potential_V_vs_SHE']:+.3f} V vs SHE"
            f"  ·  {conditions['concentration_input_value']:g} {UNIT_LABELS.get(conditions['concentration_input_unit'], '')}"
        )
        if element is None:
            painter.setPen(self._text_color())
            painter.setFont(title)
            painter.drawText(inner, Qt.AlignLeft | Qt.AlignTop, "Stable species across the periodic table")
            painter.setFont(body)
            painter.setPen(self._muted())
            painter.drawText(
                inner.adjusted(0, pitch * 0.5, 0, 0), Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                f"{condition_text}\n{self.screen['calculated_system_count']} of "
                f"{self.screen['supported_system_count']} supported systems calculated. "
                "Hover over an element for details; click to open its Pourbaix diagram.",
            )
            return
        swatch = self._fill(element) or QColor(self._muted())
        swatch.setAlpha(255)
        painter.setBrush(swatch)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(inner.left(), inner.top() + pitch * 0.05, pitch * 0.18, pitch * 0.36),
                                3, 3)
        painter.setPen(self._text_color())
        painter.setFont(title)
        name = element.get("system") or element["symbol"]
        painter.drawText(inner.adjusted(pitch * 0.3, 0, 0, 0), Qt.AlignLeft | Qt.AlignTop, name)
        labels = self.screen["category_labels"]
        lines = [labels.get(element["category"], element["category"])]
        if element.get("stable_species"):
            phase = element.get("phase_detail") or element.get("phase") or ""
            lines.append(("formula", f"Stable: {element['stable_species']}  ({phase})"))
            margin = element.get("energy_margin_J_mol_metal")
            if margin is not None:
                lines.append(f"Margin to the next species: {margin / 1000:.2f} kJ/mol metal")
            source = (element.get("gibbs_source") or {}).get("citation")
            if source:
                lines.append(f"ΔfG°: {source}")
        else:
            reason = element.get("coverage_reason") or element.get("reason")
            if reason:
                lines.append(reason)
        if element["status"] == "calculated_with_gaps":
            lines.append("Provisional: species that lack an experimental Gibbs energy are left out of this calculation")
        elif element["status"] == "calculated_with_fallback":
            lines.append("Provisional: Materials Project 300 K estimates replace the missing experimental Gibbs energies")
        if element.get("missing_record_ids"):
            lines.append(f"{len(element['missing_record_ids'])} species lack a recommended Gibbs energy")
        painter.setFont(body)
        painter.setPen(self._muted())
        metrics = QFontMetricsF(body)
        top = inner.top() + pitch * 0.5
        for line in lines:
            if isinstance(line, tuple):
                row = QRectF(inner.left(), top, inner.width(), metrics.height() * 1.3)
                painter.setPen(self._text_color())
                draw_formula(painter, row, line[1], body, Qt.AlignLeft | Qt.AlignTop)
                painter.setPen(self._muted())
                top += metrics.height() * 1.3
                continue
            bounds = painter.boundingRect(QRectF(inner.left(), top, inner.width(), 1000),
                                          Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, line)
            painter.drawText(bounds, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, line)
            top = bounds.bottom() + metrics.height() * 0.15

    def _paint_legend(self, painter: QPainter, area: QRectF, base: QFont) -> None:
        self._chips = {}
        font = QFont(base)
        font.setPixelSize(12)
        painter.setFont(font)
        metrics = QFontMetricsF(font)
        counts = self.screen["category_counts"]
        if self.color_mode == "margin":
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
            self._paint_provisional_key(painter, QPointF(bar.right() + 36, area.top() + 4), metrics)
            return
        chips = [(key, f"{self.screen['category_labels'][key]}  {counts.get(key, 0)}")
                 for key in CALCULATED_CATEGORIES if counts.get(key)]
        widths = [metrics.horizontalAdvance(text) + 34 for _, text in chips]
        key_width = self._provisional_key_width(metrics)
        total = sum(widths) + 8 * (len(widths) - 1) + (key_width + 16 if key_width else 0)
        x = area.center().x() - total / 2
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
        self._paint_provisional_key(painter, QPointF(x + 8, area.top() + 4), metrics)

    PROVISIONAL_LABEL = "Provisional: some species lack an experimental Gibbs energy"

    def _provisional_count(self) -> int:
        return sum(self.provisional(element) for element in self.elements.values())

    def _provisional_key_width(self, metrics: QFontMetricsF) -> float:
        if not self._provisional_count():
            return 0.0
        return metrics.horizontalAdvance(f"{self.PROVISIONAL_LABEL}  {self._provisional_count()}") + 40

    def _paint_provisional_key(self, painter: QPainter, origin: QPointF, metrics: QFontMetricsF) -> None:
        """Legend entry for the dashed outline, shown when some tiles are exploratory."""
        width = self._provisional_key_width(metrics)
        if not width:
            return
        chip = QRectF(origin.x(), origin.y(), width, 26)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 18) if self.dark else QColor(0, 0, 0, 10))
        painter.drawRoundedRect(chip, 13, 13)
        painter.setPen(QPen(self._text_color(), 1.3, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(chip.left() + 9, chip.center().y() - 7, 16, 14), 3, 3)
        painter.setPen(self._text_color())
        painter.drawText(chip.adjusted(32, 0, -6, 0), Qt.AlignVCenter | Qt.AlignLeft,
                         f"{self.PROVISIONAL_LABEL}  {self._provisional_count()}")

    # -- interaction -------------------------------------------------------------------------

    def _symbol_at(self, position: QPointF) -> str | None:
        for symbol, cell in self._tiles.items():
            if cell.contains(position):
                return symbol
        return None

    def mouseMoveEvent(self, event) -> None:
        symbol = self._symbol_at(event.position())
        chip = any(rect.contains(event.position()) for rect in self._chips.values())
        clickable = chip or (symbol is not None and self.clickable(self.elements[symbol]))
        self.setCursor(Qt.PointingHandCursor if clickable else Qt.ArrowCursor)
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
                self.update()
                return
        symbol = self._symbol_at(event.position())
        if symbol is not None and self.clickable(self.elements[symbol]):
            self.elementClicked.emit(symbol)
        elif symbol is not None:
            QToolTip.showText(event.globalPosition().toPoint(), "No calculated system for this element", self)
