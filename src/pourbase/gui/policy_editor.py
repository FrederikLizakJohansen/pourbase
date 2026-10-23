"""Edit, check and apply a selection policy as TOML text."""

from __future__ import annotations

import re
import sqlite3
import tomllib
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QRegularExpression, Qt, Signal
from PySide6.QtGui import QColor, QFontDatabase, QKeySequence, QShortcut, QSyntaxHighlighter, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit, QPushButton,
    QVBoxLayout, QWidget,
)

from ..selection import FALLBACK_ESTIMATE, FALLBACK_EXPERIMENTAL, PROPERTIES, TIE_BREAKS, SelectionPolicy

STATUSES = ("verified", "accepted", "source_verified_estimate", "defined_reference_state",
            "superseded_source_value", "terminal_evidence_gap")

@dataclass(frozen=True)
class Issue:
    line: int | None  # 1-based, or None for the whole text
    error: bool  # False for a warning
    message: str


def _line_of(text: str, *needles: str) -> int | None:
    """The first line that contains every needle, 1-based."""
    for number, line in enumerate(text.splitlines(), 1):
        if all(needle in line for needle in needles):
            return number
    return None


def check_policy(text: str, database_path: str | Path | None = None) -> tuple[SelectionPolicy | None, list[Issue]]:
    """Parse ``text`` and list what is wrong with it; the policy is None when it cannot be used."""
    try:
        tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        match = re.search(r"line (\d+)", str(error))
        return None, [Issue(int(match.group(1)) if match else None, True, f"Not valid TOML: {error}")]
    try:
        policy = SelectionPolicy.from_toml(text)
    except (KeyError, TypeError, ValueError) as error:
        # point at the first line that mentions a name from the message, such as an unknown tie-break
        words = re.findall(r"[\w-]{3,}", str(error).split(":")[-1])
        line = next((found for word in words if (found := _line_of(text, word))), None)
        return None, [Issue(line, True, f"Missing or wrong entry: {error}")]
    issues: list[Issue] = []
    names = [item.name for item in policy.classes]
    for name in {name for name in names if names.count(name) > 1}:
        issues.append(Issue(_line_of(text, "name", f'"{name}"'), True, f"Class {name} appears twice"))
    if not policy.classes:
        issues.append(Issue(None, True, "No [[classes]]: nothing can be ranked"))
    for name in policy.tie_breaks:
        if name not in TIE_BREAKS:
            issues.append(Issue(_line_of(text, "tie_breaks"), True,
                                f"Unknown tie-break {name!r}; use {', '.join(TIE_BREAKS)}"))
    if policy.review_threshold_J_mol < 0:
        issues.append(Issue(_line_of(text, "review_threshold"), True, "The review threshold is negative"))
    for status in policy.ineligible_statuses:
        if status not in STATUSES:
            issues.append(Issue(_line_of(text, "ineligible_statuses"), False,
                                f"No value has the status {status!r}, so this entry does nothing"))
    patterns = dict(policy.family_patterns)
    ranked = {family for item in policy.classes for family in item.families}
    for item in policy.classes:
        for family in item.families:
            if family not in patterns and family not in (FALLBACK_ESTIMATE, FALLBACK_EXPERIMENTAL):
                issues.append(Issue(_line_of(text, f'"{family}"'), False,
                                    f"Family {family!r} has no patterns under [families], so no source joins it"))
    for family in patterns:
        if family not in ranked:
            issues.append(Issue(_line_of(text, f'"{family}"', "="), False,
                                f"Family {family!r} is in no class; its sources rank after every class"))
    for kind, entries in (("override", policy.overrides), ("exclusion", policy.exclusions)):
        for entry in entries:
            line = _line_of(text, "record_id", f'"{entry.record_id}"')
            if entry.property_name not in PROPERTIES:
                issues.append(Issue(line, True, f"The {kind} for {entry.record_id} has the unknown property "
                                                f"{entry.property_name!r}"))
    if database_path is not None:
        issues += _check_against_database(text, policy, database_path)
    return (None if any(issue.error for issue in issues) else policy), issues


def _check_against_database(text: str, policy: SelectionPolicy, database_path: str | Path) -> list[Issue]:
    issues = []
    with sqlite3.connect(f"file:{database_path}?mode=ro", uri=True) as connection:
        records = {row[0] for row in connection.execute("SELECT record_id FROM species")}
        values = {tuple(row) for row in connection.execute(
            "SELECT record_id, property, source_id FROM reported_thermochemistry")}
    for kind, entries in (("override", policy.overrides), ("exclusion", policy.exclusions)):
        for entry in entries:
            line = _line_of(text, "record_id", f'"{entry.record_id}"')
            if entry.property_name not in PROPERTIES:
                continue  # already an error
            if entry.record_id not in records:
                issues.append(Issue(line, False, f"The {kind} names {entry.record_id}, which is not in the database"))
            elif (entry.record_id, entry.property_name, entry.source_id) not in values:
                issues.append(Issue(line, False, f"The {kind} for {entry.record_id} names the source "
                                                 f"{entry.source_id}, which has no {entry.property_name} for it"))
    return issues


class TomlHighlighter(QSyntaxHighlighter):
    """Comments, table headers, keys and strings."""

    def __init__(self, document, dark: bool = False) -> None:
        super().__init__(document)
        self.set_dark(dark)

    def set_dark(self, dark: bool) -> None:
        def style(color: str, italic: bool = False) -> QTextCharFormat:
            text_format = QTextCharFormat()
            text_format.setForeground(QColor(color))
            text_format.setFontItalic(italic)
            return text_format

        self.rules = [
            (QRegularExpression(r'^\s*[\w"-][\w" .-]*(?==)'), style("#79b8ff" if dark else "#1f5fa8")),
            (QRegularExpression(r'"[^"\n]*"'), style("#9ecb8b" if dark else "#3d7a2a")),
            (QRegularExpression(r"^\s*\[\[?[^\]]+\]\]?"), style("#e3a95c" if dark else "#a8561f")),
            (QRegularExpression(r"#.*$"), style("#8a8f98", italic=True)),
        ]
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        for expression, text_format in self.rules:
            matches = expression.globalMatch(text)
            while matches.hasNext():
                match = matches.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), text_format)


class PolicyEditorPage(QWidget):
    """The selection policy as text: edit, check, save, load and apply it.

    ``applyRequested`` carries the text and the file it was saved to (None when it differs from every file);
    ``revertRequested`` asks for the bundled default.
    """

    applyRequested = Signal(str, object)
    revertRequested = Signal()

    def __init__(self, database_path: str | Path | None = None, parent=None) -> None:
        super().__init__(parent)
        self.database_path = database_path
        self.default_text = SelectionPolicy.default().source_text
        self.path: str | None = None  # the file the text was opened from or saved to
        self.saved_text = self.default_text  # the text as it is in that file (or the default)
        self.applied_text = self.default_text  # the text the calculations use

        self.title = QLabel()
        self.state = QLabel()
        self.state.setStyleSheet("color: #8a8f98;")
        buttons = QHBoxLayout()
        for text, slot, tip in (
            ("New from default", self.new_from_default, "Start again from the bundled default"),
            ("Open…", self.open_file, "Load a policy file into the editor"),
            ("Save", self.save, "Save to the current file (Ctrl+S in the editor)"),
            ("Save as…", self.save_as, "Save to a new file"),
            ("Check", self.check, "List problems without applying"),
        ):
            button = QPushButton(text)
            button.setToolTip(tip)
            button.clicked.connect(slot)
            buttons.addWidget(button)
        buttons.addStretch(1)
        self.revert_button = QPushButton("Revert to default…")
        self.revert_button.setToolTip("Calculate with the bundled default policy again")
        self.revert_button.clicked.connect(self.revert)
        self.apply_button = QPushButton("Apply")
        self.apply_button.setToolTip("Recalculate everything with this text")
        self.apply_button.setDefault(True)
        self.apply_button.clicked.connect(self.apply)
        buttons.addWidget(self.revert_button)
        buttons.addWidget(self.apply_button)

        self.editor = QPlainTextEdit()
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.editor.setFont(font)
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.editor.setTabStopDistance(4 * self.editor.fontMetrics().horizontalAdvance(" "))
        self.highlighter = TomlHighlighter(self.editor.document())
        self.editor.textChanged.connect(self._update_state)

        self.issues = QListWidget()
        self.issues.setMaximumHeight(130)
        self.issues.itemActivated.connect(self._jump)
        self.issues.itemClicked.connect(self._jump)
        self.issues.hide()

        right = QWidget()
        column = QVBoxLayout(right)
        column.setContentsMargins(0, 0, 0, 0)
        heading = QHBoxLayout()
        heading.addWidget(self.title)
        heading.addStretch(1)
        heading.addWidget(self.state)
        column.addLayout(heading)
        column.addLayout(buttons)
        column.addWidget(self.editor, 1)
        column.addWidget(self.issues)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.addWidget(right)

        QShortcut(QKeySequence.Save, self.editor, self.save, context=Qt.WidgetShortcut)
        self._set_text(self.default_text)

    # state
    def text(self) -> str:
        return self.editor.toPlainText()

    def _set_text(self, text: str) -> None:
        self.editor.setPlainText(text)
        self.editor.document().setModified(False)
        self.issues.clear()
        self.issues.hide()
        self._update_state()

    def is_modified(self) -> bool:
        return self.text() != self.saved_text

    def _update_state(self) -> None:
        name = Path(self.path).name if self.path else "Bundled default"
        self.title.setText(name + (" (edited)" if self.is_modified() else ""))
        if self.text() == self.applied_text:
            self.state.setText("In use for calculations")
        else:
            self.state.setText("Not applied: calculations use the previous text")

    def set_dark(self, dark: bool) -> None:
        self.highlighter.set_dark(dark)

    def policy_activated(self, path: str | None, text: str) -> None:
        """The window now calculates with ``text`` (from ``path``); show it unless the editor holds other edits."""
        self.applied_text = text
        if not self.is_modified():
            self.path = path
            self.saved_text = text
            self._set_text(text)
        self._update_state()

    def _confirm_discard(self) -> bool:
        if not self.is_modified():
            return True
        answer = QMessageBox.question(self, "Selection policy", "Discard the unsaved edits in the editor?",
                                      QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Cancel)
        return answer == QMessageBox.Discard

    # files
    def new_from_default(self) -> None:
        if self._confirm_discard():
            self.path, self.saved_text = None, self.default_text
            self._set_text(self.default_text)

    def open_file(self, path: str | None = None) -> None:
        if not self._confirm_discard():
            return
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Open selection policy", "", "TOML (*.toml);;All files (*)")
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as error:
            QMessageBox.warning(self, "Open selection policy", str(error))
            return
        self.path, self.saved_text = path, text
        self._set_text(text)

    def save(self) -> bool:
        if self.path is None:
            return self.save_as()
        try:
            Path(self.path).write_text(self.text(), encoding="utf-8")
        except OSError as error:
            QMessageBox.warning(self, "Save selection policy", str(error))
            return False
        self.saved_text = self.text()
        self._update_state()
        return True

    def save_as(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(self, "Save selection policy", "my-selection-policy.toml",
                                              "TOML (*.toml);;All files (*)")
        if not path:
            return False
        self.path = path
        return self.save()

    # checking and applying
    def check(self) -> SelectionPolicy | None:
        policy, issues = check_policy(self.text(), self.database_path)
        self.issues.clear()
        if not issues:
            self.issues.addItem("No problems found.")
        for issue in issues:
            where = f"line {issue.line}: " if issue.line else ""
            item = QListWidgetItem(("Error, " if issue.error else "Warning, ") + where + issue.message)
            item.setData(Qt.UserRole, issue.line)
            item.setForeground(QColor("#da3633" if issue.error else "#c88a1c"))
            self.issues.addItem(item)
        self.issues.show()
        return policy

    def _jump(self, item: QListWidgetItem) -> None:
        line = item.data(Qt.UserRole)
        if not line:
            return
        block = self.editor.document().findBlockByLineNumber(line - 1)
        cursor = QTextCursor(block)
        cursor.select(QTextCursor.LineUnderCursor)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def apply(self) -> None:
        if self.check() is None:
            QMessageBox.warning(self, "Apply selection policy", "Fix the errors listed under the text first.")
            return
        text = self.text()
        self.applyRequested.emit(text, self.path if self.path and text == self.saved_text else None)

    def revert(self) -> None:
        answer = QMessageBox.warning(
            self, "Revert to the default policy",
            "Calculate with the bundled default policy again and put its text in the editor?"
            + ("\n\nYour unsaved edits will be lost." if self.is_modified() else ""),
            QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
        if answer != QMessageBox.Yes:
            return
        self.path, self.saved_text = None, self.default_text
        self._set_text(self.default_text)
        self.revertRequested.emit()
