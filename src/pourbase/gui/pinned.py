"""Diagrams popped out into their own windows, with probes linked across all of them."""

from __future__ import annotations

import copy

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QVBoxLayout, QWidget

from ..citations import diagram_sources
from .plots import DiagramView
from .scales import to_scale
from .sources_dialog import SourcesDialog


class PinnedDiagram(QWidget):
    """One calculated diagram in its own window. It keeps its result while the main window changes."""

    probeMoved = Signal(float, float)  # pH and Eh against the SHE

    def __init__(self, calculation, display, title: str, context: str, dark: bool, parent=None) -> None:
        super().__init__(parent, Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(f"{title} — pourbase")
        self.title = title
        self.calculation = calculation
        self.display = copy.deepcopy(display)
        self.display.overlay_symbol = ""
        self.display.legend = False  # domain labels name the species; a legend would cover a small window
        self._probe: tuple[float | None, float | None] = (None, None)
        self.context = QLabel(context)
        self.context.setWordWrap(True)
        self.context.setStyleSheet("color: gray;")
        self.view = DiagramView()
        self.view.set_dark(dark)
        self.readout = QLabel(" ")
        self.readout.setTextFormat(Qt.RichText)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.addWidget(self.context)
        layout.addWidget(self.view, 1)
        footer = QHBoxLayout()
        footer.addWidget(self.readout, 1)
        count = len(diagram_sources(calculation))
        self.sources = QToolButton()
        self.sources.setAutoRaise(True)
        self.sources.setCursor(Qt.PointingHandCursor)
        self.sources.setText(f"{count} source{'s' if count != 1 else ''}")
        self.sources.setToolTip("The publications behind this diagram, with BibTeX export")
        self.sources.setStyleSheet("QToolButton { color: gray; }")
        self.sources.clicked.connect(self.show_sources)
        footer.addWidget(self.sources)
        layout.addLayout(footer)
        self.view.export_menu.extra_actions.append(("Sources behind this diagram…", self.show_sources))
        self.view.probeMoved.connect(self.probeMoved)
        self.view.cursorMoved.connect(lambda text: self.readout.setText(text or self._probe_text()))
        self._draw(reset_range=True)
        self.resize(560, 480)

    def show_sources(self) -> None:
        dialog = SourcesDialog(self.calculation, self.title, self)
        dialog.setAttribute(Qt.WA_DeleteOnClose)
        dialog.show()

    def _draw(self, reset_range: bool = False) -> None:
        plating = self.calculation.plating[0].potential_V_vs_SHE if self.calculation.plating else None
        self.view.show_diagram(self.calculation.diagram, self.display, plating, reset_range=reset_range)

    def set_dark(self, dark: bool) -> None:
        self.view.set_dark(dark)
        self._draw()
        if self._probe[0] is not None:
            self.set_probe(*self._probe)

    def _probe_text(self) -> str:
        pH, eh_V = self._probe
        if pH is None:
            return " "
        y = float(to_scale(eh_V, pH, self.display.potential_scale, self.calculation.diagram.conditions.temperature_K))
        return self.view._species_text(pH, y) or f"pH {pH:.2f}, Eh {eh_V:+.3f} V: outside this diagram"

    def set_probe(self, pH: float, eh_V: float) -> None:
        """Move the probe without emitting ``probeMoved``."""
        self._probe = (pH, eh_V)
        self.view.set_probe(pH, eh_V)
        self.readout.setText(self._probe_text())
