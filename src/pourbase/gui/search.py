"""Search everything (Ctrl+K): elements, species, sources and commands."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout

SCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789" "0123456789" "+-")


def normalize(text: str) -> str:
    """Lower-case ASCII with plain digits, so that ``fe2o3`` finds Fe₂O₃."""
    text = text.translate(SCRIPTS)
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


@dataclass(frozen=True)
class Entry:
    kind: str  # Element, Species, Source or Command
    title: str
    detail: str
    terms: str
    activate: Callable[[], None]


def rank(entries: list[Entry], query: str, limit: int = 60) -> list[Entry]:
    """Entries matching every word of ``query``, best matches first."""
    words = normalize(query).split()
    if not words:
        return []
    order = {"Element": 0, "Species": 1, "Command": 2, "Source": 3}
    scored = []
    for entry in entries:
        terms = entry.terms
        if all(word in terms for word in words):
            title = normalize(entry.title)
            score = (0 if title == words[0] else 1 if title.startswith(words[0]) else 2, order[entry.kind], len(title))
            scored.append((score, entry))
    scored.sort(key=lambda item: item[0])
    return [entry for _score, entry in scored[:limit]]


class SearchDialog(QDialog):
    """A search field over every element, species, source and command."""

    def __init__(self, entries: list[Entry], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Search")
        self.resize(640, 440)
        self.entries = entries
        self.field = QLineEdit()
        self.field.setPlaceholderText("Element, species, formula, source or command…")
        self.field.setClearButtonEnabled(True)
        self.results = QListWidget()
        self.hint = QLabel("Enter opens the selected result; ↑ and ↓ move through the list.")
        self.hint.setStyleSheet("color: gray;")
        layout = QVBoxLayout(self)
        layout.addWidget(self.field)
        layout.addWidget(self.results, 1)
        layout.addWidget(self.hint)
        self.field.textChanged.connect(self.update_results)
        self.field.returnPressed.connect(self.activate_current)
        self.results.itemActivated.connect(lambda _item: self.activate_current())
        self.field.installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:
        from PySide6.QtCore import QEvent

        if watched is self.field and event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Up, Qt.Key_Down):
            row = self.results.currentRow() + (1 if event.key() == Qt.Key_Down else -1)
            self.results.setCurrentRow(max(0, min(row, self.results.count() - 1)))
            return True
        return False

    def update_results(self, text: str) -> None:
        self.results.clear()
        for entry in rank(self.entries, text):
            item = QListWidgetItem(f"{entry.title}    {entry.detail}")
            item.setData(Qt.UserRole, entry)
            item.setToolTip(f"{entry.kind}: {entry.detail}")
            self.results.addItem(item)
        if self.results.count():
            self.results.setCurrentRow(0)

    def activate_current(self) -> None:
        item = self.results.currentItem()
        if item is None:
            return
        entry = item.data(Qt.UserRole)
        self.accept()
        entry.activate()
