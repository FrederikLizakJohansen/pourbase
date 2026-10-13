"""The context bar: what the shown result is calculated from, one clickable chip per aspect."""

from __future__ import annotations

import math
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QMenu, QSizePolicy, QToolButton, QWidget

SUPERSCRIPT = str.maketrans("0123456789-+.", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺·")
SUBSCRIPT = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
NEUTRAL, ACCENT, WARNING = "neutral", "accent", "warning"


def power_of_ten(log10_value: float) -> str:
    """``10⁻⁶`` for whole exponents, otherwise ``3.2 × 10⁻⁵``."""
    if abs(log10_value - round(log10_value)) < 1e-9:
        return "10" + str(int(round(log10_value))).translate(SUPERSCRIPT)
    exponent = math.floor(log10_value)
    mantissa = 10 ** (log10_value - exponent)
    return f"{mantissa:.2g} × 10" + str(exponent).translate(SUPERSCRIPT)


class Chip(QToolButton):
    """One aspect of the context: short text, an explanation on hover, an action on click."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAutoRaise(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self._action: Callable[[], None] | None = None
        self.clicked.connect(lambda: self._action() if self._action else None)

    def configure(self, text: str, tooltip: str, tone: str = NEUTRAL,
                  action: Callable[[], None] | None = None, menu: list[tuple[str, Callable[[], None]]] | None = None,
                  dark: bool = False) -> None:
        if text != self.text():
            self.setText(text)
        if tooltip != self.toolTip():
            self.setToolTip(tooltip)
        self._action = action
        labels = tuple(label for label, _callback in menu or ())
        if labels != getattr(self, "_menu_labels", None):  # menus and styles change rarely; rebuild only then
            self._menu_labels = labels
            if menu:
                popup = QMenu(self)
                for label, callback in menu:
                    popup.addAction(label, callback)
                self.setMenu(popup)
                self.setPopupMode(QToolButton.InstantPopup)
            else:
                self.setMenu(None)
        self.setVisible(bool(text))
        if (tone, dark) == getattr(self, "_style", None):
            return
        self._style = (tone, dark)
        colors = {
            NEUTRAL: ("#3a3d41", "#d6d9dd") if dark else ("#eef0f3", "#c9cdd3"),
            ACCENT: ("#1e3a5c", "#4f86c6") if dark else ("#e3eefb", "#7aa7dc"),
            WARNING: ("#4a3a14", "#c99a2e") if dark else ("#fdf3dc", "#d9a640"),
        }[tone]
        self.setStyleSheet(
            f"QToolButton {{ background: {colors[0]}; border: 1px solid {colors[1]}; border-radius: 9px; "
            "padding: 2px 9px; }"
            "QToolButton::menu-indicator { image: none; width: 0px; }"
        )


class ContextBar(QWidget):
    """A row of chips stating the element, model, data, policy, ligands, omissions and view options."""

    ORDER = ("element", "model", "data", "policy", "ligands", "omitted", "view")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 2)
        layout.setSpacing(6)
        self.chips = {name: Chip() for name in self.ORDER}
        for chip in self.chips.values():
            layout.addWidget(chip)
        layout.addStretch(1)
        # the bar never widens the window: chips that do not fit are clipped
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)

    def minimumSizeHint(self):
        from PySide6.QtCore import QSize

        return QSize(0, super().minimumSizeHint().height())

    def text(self) -> str:
        """The visible chips as one line, for tests and accessibility."""
        return " · ".join(chip.text() for chip in self.chips.values() if not chip.isHidden() and chip.text())
