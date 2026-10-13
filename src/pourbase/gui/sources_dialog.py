"""The publications behind the shown diagram, ready to cite."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout,
)

from ..citations import diagram_sources, to_bibtex, to_text


class SourcesDialog(QDialog):
    """Every publication supplying a Gibbs energy to the diagram, one entry per publication."""

    def __init__(self, calculation, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sources behind this diagram")
        self.resize(1000, 520)
        self.publications = diagram_sources(calculation)
        summary = QLabel(f"{title}: {len(self.publications)} publications supply the Gibbs energies of the "
                         f"{len(calculation.diagram.system.species)} species in this calculation, and of its ligands. "
                         "BibTeX keeps each full citation as a note, with year, DOI and URL where known.")
        summary.setWordWrap(True)
        self.table = QTableWidget(len(self.publications), 3)
        self.table.setHorizontalHeaderLabels(["Publication", "Used for", "Link"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setWordWrap(True)
        for row, item in enumerate(self.publications):
            for column, value in enumerate((item.citation, ", ".join(item.species), item.url or "")):
                cell = QTableWidgetItem(value)
                cell.setToolTip(value)
                self.table.setItem(row, column, cell)
        self.table.resizeRowsToContents()
        buttons = QHBoxLayout()
        for label, action in (("Copy BibTeX", self.copy_bibtex), ("Save BibTeX…", self.save_bibtex),
                              ("Save as text…", self.save_text)):
            button = QPushButton(label)
            button.clicked.connect(action)
            buttons.addWidget(button)
        buttons.addStretch(1)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        layout = QVBoxLayout(self)
        layout.addWidget(summary)
        layout.addWidget(self.table, 1)
        layout.addLayout(buttons)

    def bibtex(self) -> str:
        return to_bibtex(self.publications)

    def copy_bibtex(self) -> None:
        QGuiApplication.clipboard().setText(self.bibtex())

    def save_bibtex(self, path: str | None = None) -> None:
        path = path or QFileDialog.getSaveFileName(self, "Save BibTeX", "pourbase-sources.bib", "BibTeX (*.bib)")[0]
        if path:
            Path(path).write_text(self.bibtex(), encoding="utf-8")

    def save_text(self, path: str | None = None) -> None:
        path = path or QFileDialog.getSaveFileName(self, "Save sources", "pourbase-sources.txt", "Text (*.txt)")[0]
        if path:
            Path(path).write_text(to_text(self.publications), encoding="utf-8")
