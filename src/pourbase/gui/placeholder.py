"""A page shown in place of a view that the current settings cannot produce."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget


class _Badge(QWidget):
    """A circular badge with one glyph, drawn in the palette's highlight color."""

    def __init__(self, glyph: str, parent=None) -> None:
        super().__init__(parent)
        self.glyph = glyph
        self.setFixedSize(64, 64)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        accent = QColor(self.palette().highlight().color())
        fill = QColor(accent)
        fill.setAlpha(40)
        painter.setBrush(fill)
        painter.setPen(QPen(accent, 2))
        painter.drawEllipse(QRectF(3, 3, 58, 58))
        font = QFont(self.font())
        font.setPointSize(22)
        font.setWeight(font.Weight.Normal)
        painter.setFont(font)
        painter.setPen(accent)
        painter.drawText(QRectF(0, 0, 64, 64), Qt.AlignCenter, self.glyph)


class Placeholder(QWidget):
    """Centered badge, title, explanation and an optional action button."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addStretch(2)
        self.badge = _Badge("i")
        layout.addWidget(self.badge, 0, Qt.AlignHCenter)
        self.title = QLabel()
        font = self.title.font()
        font.setPointSizeF(font.pointSizeF() * 1.35)
        font.setWeight(font.Weight.Normal)
        self.title.setFont(font)
        self.title.setAlignment(Qt.AlignCenter)
        self.message = QLabel()
        self.message.setWordWrap(True)
        self.message.setAlignment(Qt.AlignCenter)
        self.message.setFixedWidth(560)
        self.message.setTextFormat(Qt.RichText)
        self.message.setOpenExternalLinks(True)
        self.button = QPushButton()
        self.button.setMinimumWidth(220)
        self._action: Callable[[], None] | None = None
        self.button.clicked.connect(lambda: self._action and self._action())
        layout.addSpacing(8)
        layout.addWidget(self.title)
        layout.addWidget(self.message, 0, Qt.AlignHCenter)
        layout.addSpacing(10)
        layout.addWidget(self.button, 0, Qt.AlignHCenter)
        layout.addStretch(3)

    def show_message(
        self,
        title: str,
        message: str,
        action: tuple[str, Callable[[], None]] | None = None,
        glyph: str = "i",
    ) -> None:
        self.badge.glyph = glyph
        self.badge.update()
        self.title.setText(title)
        self.message.setText(message)
        # A word-wrapped label in a box layout does not grow to its wrapped height by itself
        self.message.setFixedHeight(self.message.heightForWidth(self.message.width()))
        self.button.setVisible(action is not None)
        if action is not None:
            self.button.setText(action[0])
            self._action = action[1]


class StackedView(QStackedWidget):
    """A view paired with a :class:`Placeholder`; ``show_view`` and ``show_message`` switch them."""

    def __init__(self, view: QWidget, parent=None) -> None:
        super().__init__(parent)
        self.view = view
        self.placeholder = Placeholder()
        self.addWidget(view)
        self.addWidget(self.placeholder)

    def show_view(self) -> None:
        self.setCurrentWidget(self.view)

    def show_message(self, *args, **kwargs) -> None:
        self.placeholder.show_message(*args, **kwargs)
        self.setCurrentWidget(self.placeholder)
