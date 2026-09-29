"""Chemical formulas with readable subscripts and superscripts.

Species names in the database use Unicode sub- and superscript characters (Fe₂O₃, FeO₄²⁻). Most
fonts draw those glyphs very small. These helpers render them as scaled text instead: as Qt rich
text for labels, legends and tables, and directly with QPainter for painted widgets.
"""

from __future__ import annotations

import html

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QFont, QFontMetricsF, QPainter

SUPERSCRIPTS = dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾", "0123456789+−=()"))
SUBSCRIPTS = dict(zip("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎", "0123456789+−=()"))

# Qt rich text draws vertical-align:sub/super at about two thirds of the requested size, so the
# requested size is scaled up to give scripts at roughly 80 % of the base size.
RICH_TEXT_SCALE = 1.22
PAINTED_SCALE = 0.78


def segments(text: str) -> list[tuple[str, str]]:
    """Split text into ``("base" | "sup" | "sub", text)`` runs."""
    runs: list[tuple[str, str]] = []
    for character in text:
        if character in SUPERSCRIPTS:
            kind, value = "sup", SUPERSCRIPTS[character]
        elif character in SUBSCRIPTS:
            kind, value = "sub", SUBSCRIPTS[character]
        else:
            kind, value = "base", character
        if runs and runs[-1][0] == kind:
            runs[-1] = (kind, runs[-1][1] + value)
        else:
            runs.append((kind, value))
    return runs


def to_html(text: str, base_pt: float = 9.0) -> str:
    """Rich text with enlarged sub- and superscripts, for a surrounding font of ``base_pt``."""
    size = base_pt * RICH_TEXT_SCALE
    parts = []
    for kind, value in segments(text):
        value = html.escape(value)
        if kind == "base":
            parts.append(value)
        else:
            align = "super" if kind == "sup" else "sub"
            parts.append(f'<span style="vertical-align:{align}; font-size:{size:.1f}pt">{value}</span>')
    return "".join(parts)


def phase_label(species) -> str:
    """Phase description without surrounding parentheses, e.g. "aq" or "hematite"."""
    return (species.phase_detail or species.phase).strip().strip("()")


def formula_width(text: str, font: QFont) -> float:
    base = QFontMetricsF(font)
    script = QFontMetricsF(_script_font(font))
    return sum(
        (base if kind == "base" else script).horizontalAdvance(value) for kind, value in segments(text)
    )


def draw_formula(
    painter: QPainter, rect: QRectF, text: str, font: QFont, alignment=Qt.AlignCenter
) -> None:
    """Draw ``text`` in ``rect`` with scaled scripts, shrinking the font if it does not fit."""
    font = QFont(font)
    width = formula_width(text, font)
    while width > rect.width() and font.pixelSize() > 6:
        font.setPixelSize(font.pixelSize() - 1)
        width = formula_width(text, font)
    script_font = _script_font(font)
    base, script = QFontMetricsF(font), QFontMetricsF(script_font)
    if alignment & Qt.AlignLeft:
        x = rect.left()
    elif alignment & Qt.AlignRight:
        x = rect.right() - width
    else:
        x = rect.center().x() - width / 2
    if alignment & Qt.AlignTop:
        baseline = rect.top() + base.ascent()
    else:
        baseline = rect.center().y() + (base.ascent() - base.descent()) / 2
    for kind, value in segments(text):
        if kind == "base":
            painter.setFont(font)
            painter.drawText(QPointF(x, baseline), value)
            x += base.horizontalAdvance(value)
        else:
            shift = -base.ascent() * 0.42 if kind == "sup" else base.descent() * 0.9
            painter.setFont(script_font)
            painter.drawText(QPointF(x, baseline + shift), value)
            x += script.horizontalAdvance(value)
    painter.setFont(font)


def _script_font(font: QFont) -> QFont:
    script = QFont(font)
    if font.pixelSize() > 0:
        script.setPixelSize(max(round(font.pixelSize() * PAINTED_SCALE), 6))
    else:
        script.setPointSizeF(font.pointSizeF() * PAINTED_SCALE)
    return script


def formula_delegate(parent=None):
    """Item delegate that draws a table cell's text as a formula with scaled scripts."""
    from PySide6.QtGui import QPalette
    from PySide6.QtWidgets import QStyle, QStyledItemDelegate

    class FormulaDelegate(QStyledItemDelegate):
        def paint(self, painter, option, index) -> None:
            text = index.data() or ""
            self.initStyleOption(option, index)
            option.text = ""
            option.widget.style().drawControl(QStyle.CE_ItemViewItem, option, painter, option.widget)
            painter.save()
            role = QPalette.HighlightedText if option.state & QStyle.State_Selected else QPalette.Text
            color = index.data(Qt.ForegroundRole)
            painter.setPen(color.color() if color is not None and not option.state & QStyle.State_Selected
                           else option.palette.color(role))
            draw_formula(painter, QRectF(option.rect).adjusted(4, 0, -4, 0), text, option.font,
                         Qt.AlignLeft | Qt.AlignVCenter)
            painter.restore()

        def sizeHint(self, option, index):
            size = super().sizeHint(option, index)
            size.setWidth(int(formula_width(index.data() or "", option.font)) + 12)
            return size

    return FormulaDelegate(parent)
