"""Small reusable widgets for the desktop GUI."""

import math

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPropertyAnimation, QSettings, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractScrollArea, QAbstractSlider, QAbstractSpinBox, QComboBox, QDoubleSpinBox, QFrame, QGraphicsOpacityEffect,
    QHBoxLayout, QLabel, QScrollBar, QSizePolicy, QSlider, QStyle, QStyleOptionSlider, QToolButton, QVBoxLayout,
    QWidget,
)


class JumpSlider(QSlider):
    """A slider whose handle jumps to the clicked point and can be dragged from there."""

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            option = QStyleOptionSlider()
            self.initStyleOption(option)
            handle = self.style().subControlRect(QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self)
            if not handle.contains(event.position().toPoint()):
                groove = self.style().subControlRect(QStyle.CC_Slider, option, QStyle.SC_SliderGroove, self)
                if self.orientation() == Qt.Horizontal:
                    span, position = groove.width() - handle.width(), event.position().x() - groove.x() - handle.width() / 2
                else:
                    span, position = groove.height() - handle.height(), event.position().y() - groove.y() - handle.height() / 2
                value = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), int(position), max(span, 1),
                                                       option.upsideDown)
                self.setValue(value)
        super().mousePressEvent(event)


class FloatSlider(QWidget):
    """
    A slider coupled to a spin box, emitting valueChanged(float).

    The slider covers [minimum, maximum]; with hard_maximum set, the spin box accepts values up to hard_maximum,
    a typed value beyond the slider range extends it, and a button doubles the slider range.
    With log=True the slider position maps logarithmically onto the range (minimum > 0).
    """

    valueChanged = Signal(float)

    STEPS = 1000

    def __init__(self, label: str, minimum: float, maximum: float, value: float, decimals: int = 3,
                 step: float | None = None, log: bool = False, unit: str = "", label_width: int = 60,
                 hard_maximum: float | None = None, parent=None):
        super().__init__(parent)
        self._minimum, self._maximum, self._log = minimum, maximum, log
        self._default_maximum = maximum
        self._hard_maximum = hard_maximum if hard_maximum is not None else maximum

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(label)
        self.label.setMinimumWidth(label_width)
        self.slider = JumpSlider(Qt.Horizontal)
        self.slider.setRange(0, self.STEPS)
        self.slider.setMinimumWidth(100)
        self.spin = QDoubleSpinBox()
        self.spin.setDecimals(decimals)
        self.spin.setRange(minimum, self._hard_maximum)
        self.spin.setSingleStep(step if step is not None else (maximum - minimum) / 100)
        self.spin.setKeyboardTracking(False)
        self.spin.setMinimumWidth(95)
        if unit:
            self.spin.setSuffix(f" {unit}")
        layout.addWidget(self.label)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.spin)
        self.default = value
        self.reset_button = QToolButton()
        self.reset_button.setText("↺")
        self.reset_button.setAutoRaise(True)
        self.reset_button.clicked.connect(self.reset)
        layout.addWidget(self.reset_button)

        self.extend_button = None
        if self._hard_maximum > maximum:
            self.extend_button = QToolButton()
            self.extend_button.setText("»")
            self.extend_button.setAutoRaise(True)
            self.extend_button.setToolTip("Extend the slider range (double the maximum).\n"
                                          "Right-click to restore the default range.")
            self.extend_button.clicked.connect(self.extend)
            self.extend_button.setContextMenuPolicy(Qt.CustomContextMenu)
            self.extend_button.customContextMenuRequested.connect(lambda _pos: self.reset_range())
            layout.addWidget(self.extend_button)
            self._update_tooltip()

        self.slider.valueChanged.connect(self._slider_changed)
        self.slider.sliderMoved.connect(self._slider_moved)
        self.spin.valueChanged.connect(self._spin_changed)
        self.setValue(value)
        self.set_default(value)

    def set_default(self, value: float) -> None:
        """The value the reset button restores."""
        self.default = value
        self.reset_button.setToolTip(f"Reset to {self.spin.textFromValue(value)}{self.spin.suffix()}")

    def reset(self) -> None:
        self.setValue(self.default)
        self.valueChanged.emit(self.spin.value())


    def _to_position(self, value: float) -> int:
        lo, hi = self._minimum, self._maximum
        if self._log:
            fraction = (math.log(value) - math.log(lo)) / (math.log(hi) - math.log(lo))
        else:
            fraction = (value - lo) / (hi - lo) if hi > lo else 0.0
        return int(round(min(max(fraction, 0.0), 1.0) * self.STEPS))

    def _from_position(self, position: int) -> float:
        lo, hi = self._minimum, self._maximum
        fraction = position / self.STEPS
        if self._log:
            return math.exp(math.log(lo) + fraction * (math.log(hi) - math.log(lo)))
        return lo + fraction * (hi - lo)


    def _slider_moved(self, position: int) -> None:
        # Keeps the spin box in step while dragging when tracking is off
        if not self.slider.hasTracking():
            self.spin.blockSignals(True)
            self.spin.setValue(self._from_position(position))
            self.spin.blockSignals(False)

    def _slider_changed(self, position: int) -> None:
        self.spin.blockSignals(True)
        self.spin.setValue(self._from_position(position))
        self.spin.blockSignals(False)
        self.valueChanged.emit(self.spin.value())

    def _spin_changed(self, value: float) -> None:
        if value > self._maximum:
            self._set_slider_maximum(value)
        self.slider.blockSignals(True)
        self.slider.setValue(self._to_position(value))
        self.slider.blockSignals(False)
        self.valueChanged.emit(value)


    def value(self) -> float:
        return self.spin.value()

    def setValue(self, value: float) -> None:
        if value > self._maximum:
            self._set_slider_maximum(value)
        self.spin.blockSignals(True)
        self.spin.setValue(value)
        self.spin.blockSignals(False)
        self.slider.blockSignals(True)
        self.slider.setValue(self._to_position(self.spin.value()))
        self.slider.blockSignals(False)

    def set_range(self, minimum: float, maximum: float, log: bool, decimals: int) -> None:
        """Change the slider range and scale without emitting valueChanged."""
        self._minimum, self._maximum, self._log = minimum, maximum, log
        self._default_maximum = self._hard_maximum = maximum
        self.spin.blockSignals(True)
        self.spin.setDecimals(decimals)
        self.spin.setRange(minimum, maximum)
        self.spin.blockSignals(False)
        self._update_tooltip()

    def setTracking(self, tracking: bool) -> None:
        """
        With tracking off, valueChanged is emitted when the slider is released instead of while it moves.
        """
        self.slider.setTracking(tracking)

    def extend(self) -> None:
        self._set_slider_maximum(min(self._maximum * 2, self._hard_maximum))

    def reset_range(self) -> None:
        self._set_slider_maximum(max(self._default_maximum, min(self.value(), self._hard_maximum)))

    def _set_slider_maximum(self, maximum: float) -> None:
        self._maximum = min(max(maximum, self._minimum), self._hard_maximum)
        self.slider.blockSignals(True)
        self.slider.setValue(self._to_position(self.spin.value()))
        self.slider.blockSignals(False)
        self._update_tooltip()

    def _update_tooltip(self) -> None:
        self.slider.setToolTip(f"Slider range {self._minimum:g}–{self._maximum:g}; type a value up to "
                               f"{self._hard_maximum:g} in the box")
        if self.extend_button is not None:
            self.extend_button.setEnabled(self._maximum < self._hard_maximum)


class LoadingOverlay(QObject):
    """Tracks whether a view waits for a background result; ``changed`` reports the state.

    The view keeps its previous picture while it waits and cross-fades to the new one, so
    nothing is drawn over it.
    """

    changed = Signal(bool)

    def __init__(self, target: QWidget, delay_ms: int = 300) -> None:
        super().__init__(target)
        self._waiting = False
        self._delay = QTimer(self, singleShot=True, interval=delay_ms)
        self._delay.timeout.connect(lambda: self.changed.emit(True))

    @property
    def active(self) -> bool:
        return self._waiting

    def isVisible(self) -> bool:
        return self._waiting and not self._delay.isActive()

    def start(self) -> None:
        if not self._waiting:
            self._waiting = True
            self._delay.start()

    def stop(self) -> None:
        was_shown = self._waiting and not self._delay.isActive()
        self._waiting = False
        self._delay.stop()
        if was_shown:
            self.changed.emit(False)


class WheelGuard(QObject):
    """Keeps the mouse wheel from changing value inputs; the wheel scrolls the surrounding panel.

    Installed on the application, it covers every spin box, drop-down list and slider. Scroll
    bars and plots keep their wheel behaviour.
    """

    def eventFilter(self, watched, event) -> bool:
        if event.type() != _WHEEL or not isinstance(watched, _VALUE_INPUTS) or isinstance(watched, QScrollBar):
            return False
        parent = watched.parentWidget()
        while parent is not None and not isinstance(parent, QAbstractScrollArea):
            parent = parent.parentWidget()
        if parent is not None:
            QCoreApplication.sendEvent(parent.verticalScrollBar(), event)
        return True


_WHEEL = QEvent.Wheel
_VALUE_INPUTS = (QAbstractSpinBox, QComboBox, QAbstractSlider)


def cross_fade(target: QWidget, duration_ms: int = 180) -> None:
    """Fade from the current picture of ``target`` to whatever it draws next.

    Call it just before ``target`` is redrawn: a snapshot of the old content lies on top and fades
    out over ``duration_ms``, then removes itself.
    """
    if not target.isVisible() or target.width() < 2 or target.height() < 2:
        return
    snapshot = QLabel(target)
    snapshot.setPixmap(target.grab())
    snapshot.setGeometry(target.rect())
    snapshot.setAttribute(Qt.WA_TransparentForMouseEvents)
    effect = QGraphicsOpacityEffect(snapshot)
    snapshot.setGraphicsEffect(effect)
    snapshot.show()
    snapshot.raise_()
    animation = QPropertyAnimation(effect, b"opacity", snapshot)
    animation.setDuration(duration_ms)
    animation.setStartValue(1.0)
    animation.setEndValue(0.0)
    animation.finished.connect(snapshot.deleteLater)
    animation.start()


class Section(QWidget):
    """A titled group of controls that folds away; its open or closed state is remembered.

    Put the controls in ``body``. ``key`` names the stored state; without it the state is not kept.
    """

    def __init__(self, title: str, key: str | None = None, expanded: bool = True, parent=None) -> None:
        super().__init__(parent)
        self._settings = QSettings("pourbase", "pourbase") if key else None
        self._key = f"sections/{key}" if key else None
        if self._settings is not None and self._settings.contains(self._key):
            expanded = self._settings.value(self._key, expanded, type=bool)
        self.header = QToolButton()
        self.header.setText(title)
        self.header.setCheckable(True)
        self.header.setChecked(expanded)
        self.header.setAutoRaise(True)
        self.header.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        font = self.header.font()
        font.setPointSizeF(font.pointSizeF() * 1.05)
        self.header.setFont(font)
        self.header.toggled.connect(self.set_expanded)
        self.body = QFrame()
        self.body.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(2)
        layout.addWidget(self.header)
        layout.addWidget(self.body)
        self.set_expanded(expanded, store=False)

    @property
    def expanded(self) -> bool:
        return self.header.isChecked()

    def set_expanded(self, expanded: bool, store: bool = True) -> None:
        self.header.blockSignals(True)
        self.header.setChecked(expanded)
        self.header.blockSignals(False)
        self.header.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        self.body.setVisible(expanded)
        if store and self._settings is not None:
            self._settings.setValue(self._key, expanded)
