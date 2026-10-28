"""Review sampled database values against their sources.

    python verify_app.py

Left: the samples. Middle: the evidence grab, the source itself (PDF at the right page, or the web page)
and the full locator. Right: type the number printed in the source, pick its unit, tick what applies and
save. With blind review on, the database value stays hidden until the entry is saved, so the reading of
the source is not anchored on it. Each save records the outcome and the kind of discrepancy in
results.csv; Statistics summarises them and writes LaTeX macros for the paper.
"""

from __future__ import annotations

import ast
import datetime
import html
import math
import os
import getpass
import json
import random
import re
import shutil
import statistics
import sys
import time
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

from PySide6.QtCore import QEvent, QItemSelectionModel, QPointF, QProcess, QRectF, QSettings, QSize, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QImage, QKeySequence, QPainter, QPalette, QPen, QPixmap, QShortcut
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QToolButton, QGridLayout, QSizePolicy, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSlider,
    QSpinBox, QSplitter, QTableWidget, QTableWidgetItem, QTabWidget, QTextBrowser, QToolBar, QVBoxLayout, QWidget,
)

import draw_sample
from pourbase.gui.theme import THEME_MODES, apply_theme
from audit import (
    CACHE, EVIDENCE, FLAGS, HERE, REPO, RESULT_FIELDS, RESULTS, SAMPLES, UNITS, compare, connect, database_inputs,
    guess_source_unit, parse_number, population, read_csv, recipe, source_family, wilson, write_csv,
)

PROPERTY_LABELS = {"gibbs_energy_of_formation": "ΔfG°", "enthalpy_of_formation": "ΔfH°", "absolute_entropy": "S°"}
OUTCOME_MARKS = {"match": "✓", "rounding": "≈", "mismatch": "✗", "not_found": "?", "not_verifiable": "–", "deferred": "⏸"}
# tests point this elsewhere so they never touch the reviewer's settings
SETTINGS_FILE = Path(os.environ.get("AUDIT_SETTINGS", HERE / "app-settings.ini"))
WRONG_FLAGS = ("wrong_row", "wrong_property", "wrong_conditions")


def evidence_of(sample_id: str) -> dict:
    path = EVIDENCE / f"{sample_id}.json"
    return json.loads(path.read_text()) if path.exists() else {}


class DrawDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Draw a random sample")
        self.count = QSpinBox()
        self.count.setRange(1, 1000)
        self.count.setValue(25)
        self.seed = QSpinBox()
        self.seed.setRange(0, 2_000_000_000)
        self.seed.setValue(random.randrange(1, 2_000_000_000))
        self.stratify = QCheckBox("Proportional to each source family")
        form = QFormLayout(self)
        form.addRow("Number of values", self.count)
        form.addRow("Seed (recorded)", self.seed)
        form.addRow("", self.stratify)
        form.addRow(QLabel("Values already sampled are never drawn again."))
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)


class ZoomImage(QWidget):
    """The evidence picture with zoom and a full-page switch.

    For PDFs the page is drawn here from the file, so the buttons can step through every place the
    database number occurs in the PDF; Redo grab fetches the evidence of the sample again.
    """

    redo = Signal()
    occurrenceShown = Signal(int)  # PDF page index of the occurrence on show

    SCALE = 2.2

    def __init__(self) -> None:
        super().__init__()
        self.label = QLabel(alignment=Qt.AlignCenter)
        self.area = QScrollArea(widgetResizable=False)
        self.area.setWidget(self.label)
        self.zoom = QSlider(Qt.Horizontal, minimum=20, maximum=300, value=100)
        self.zoom.valueChanged.connect(self._show)
        self.page_button = QPushButton("Show full page")
        self.page_button.setCheckable(True)
        self.page_button.toggled.connect(self._show)
        self.previous_button = QPushButton("◀ Previous")
        self.previous_button.clicked.connect(lambda: self._step(-1))
        self.next_button = QPushButton("Next number in PDF ▶")
        self.next_button.setToolTip("Show the next place the database number is printed in the PDF")
        self.next_button.clicked.connect(lambda: self._step(1))
        redo = QPushButton("Redo grab")
        redo.setToolTip("Fetch this sample's evidence again")
        redo.clicked.connect(self.redo)
        self.note = QLabel(wordWrap=True, objectName="muted")
        self.note.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.position = QLabel(objectName="muted")
        self.position.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        top = QHBoxLayout()
        top.addWidget(self.note, 1)
        top.addWidget(QLabel("Zoom"))
        top.addWidget(self.zoom)
        top.addWidget(self.page_button)
        steps = QHBoxLayout()
        steps.addWidget(self.previous_button)
        steps.addWidget(self.next_button)
        steps.addWidget(self.position, 1)
        steps.addWidget(redo)
        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addLayout(steps)
        layout.addWidget(self.area, 1)
        self.crop: QPixmap | None = None
        self.page: QPixmap | None = None
        self.document = QPdfDocument(self)
        self.occurrences: list[dict] = []
        self.index = 0
        self._pages: dict[int, QImage] = {}

    def set_evidence(self, evidence: dict) -> None:
        self.note.setText(evidence.get("note", "No evidence fetched yet: Fetch missing evidence"))
        self.occurrences = evidence.get("occurrences") or []
        self.index = 0
        self._pages = {}
        file = evidence.get("file")
        if self.occurrences and file and Path(file).exists():
            self.document.load(file)
            self._render_occurrence()
        else:
            self.occurrences = []
            crop, page = evidence.get("image"), evidence.get("page_image")
            self.crop = QPixmap(crop) if crop and Path(crop).exists() else None
            self.page = QPixmap(page) if page and Path(page).exists() else None
        self._update_steps()
        self.page_button.setEnabled(self.page is not None)
        self.page_button.setChecked(False)
        if self.crop is not None:
            fit = (self.area.viewport().width() - 20) / max(self.crop.width(), 1)
            self.zoom.blockSignals(True)
            self.zoom.setValue(int(min(max(fit * 100, 20), 300)))
            self.zoom.blockSignals(False)
        self._show()

    def _page_image(self, page: int) -> QImage:
        if page not in self._pages:
            size = self.document.pagePointSize(page)
            render = self.document.render(page, QSize(int(size.width() * self.SCALE), int(size.height() * self.SCALE)))
            image = QImage(render.size(), QImage.Format_RGB32)
            image.fill(QColor("white"))
            painter = QPainter(image)
            painter.drawImage(0, 0, render)
            painter.end()
            self._pages[page] = image
        return self._pages[page]

    def _render_occurrence(self) -> None:
        current = self.occurrences[self.index]
        page = current["page"]
        image = self._page_image(page).copy()
        painter = QPainter(image)
        scale = self.SCALE
        for item in self.occurrences:
            if item["page"] != page:
                continue
            chosen = item is current
            painter.setPen(QPen(QColor("#d62728"), 3.5) if chosen else QPen(QColor(240, 150, 40, 170), 1.5))
            painter.drawRect(QRectF(item["x"] * scale - 4, item["y"] * scale - 3, item["w"] * scale + 8,
                                    item["h"] * scale + 6))
        painter.end()
        self.page = QPixmap.fromImage(image)
        centre = (current["y"] + current["h"] / 2) * scale
        top = max(int(centre - 330), 0)
        self.crop = QPixmap.fromImage(image.copy(0, top, image.width(), min(660, image.height() - top)))
        self.occurrenceShown.emit(page)

    def _update_steps(self) -> None:
        count = len(self.occurrences)
        self.previous_button.setEnabled(count > 1)
        self.next_button.setEnabled(count > 1)
        if count:
            current = self.occurrences[self.index]
            self.position.setText(f"Occurrence {self.index + 1} of {count}, PDF page {current['page'] + 1}"
                                  + ("  ·  on the labelled row" if current["on_row"] else ""))
        else:
            self.position.setText("")

    def _step(self, direction: int) -> None:
        if not self.occurrences:
            return
        self.index = (self.index + direction) % len(self.occurrences)
        self._render_occurrence()
        self._update_steps()
        self._show()

    def _show(self) -> None:
        pixmap = self.page if self.page_button.isChecked() else self.crop
        if pixmap is None:
            self.label.setText("No picture for this source. Use the Source tab or open the link.")
            self.label.adjustSize()
            return
        scaled = pixmap.scaledToWidth(int(pixmap.width() * self.zoom.value() / 100), Qt.SmoothTransformation)
        self.label.setPixmap(scaled)
        self.label.resize(scaled.size())


class SourceView(QWidget):
    """The source itself: a PDF at its page, or the web page."""

    def __init__(self) -> None:
        super().__init__()
        self.document = QPdfDocument(self)
        self.pdf = QPdfView()
        self.pdf.setDocument(self.document)
        self.pdf.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self.web = None
        self.url = ""
        self.message = QLabel(alignment=Qt.AlignCenter, wordWrap=True)
        browser = QPushButton("Open in browser")
        browser.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.url)))
        in_app = QPushButton("Show in app")
        in_app.setToolTip("Embedded web view (software rendered); use the browser if it fails")
        in_app.clicked.connect(self.show_in_app)
        self.message_box = QWidget()
        box = QVBoxLayout(self.message_box)
        box.addStretch(1)
        box.addWidget(self.message)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(browser)
        row.addWidget(in_app)
        row.addStretch(1)
        box.addLayout(row)
        box.addStretch(1)
        self.layout_ = QVBoxLayout(self)
        self.layout_.addWidget(self.pdf)
        self.layout_.addWidget(self.message_box)
        self.message_box.hide()

    def _web(self):
        if self.web is None:
            try:
                from PySide6.QtWebEngineWidgets import QWebEngineView
            except ImportError:
                return None
            self.web = QWebEngineView()
            self.layout_.addWidget(self.web)
        return self.web

    def show_source(self, sample: dict, evidence: dict) -> None:
        file = evidence.get("file")
        if file and str(file).endswith(".pdf") and Path(file).exists():
            self.message_box.hide()
            if self.document.property("path") != file:
                self.document.load(file)
                self.document.setProperty("path", file)
            self.pdf.show()
            if self.web is not None:
                self.web.hide()
            page = evidence.get("page") or 0
            self.pdf.pageNavigator().jump(int(page), QPointF(), self.pdf.zoomFactor())
            return
        # web pages open in the browser; the embedded view starts only on request, since Qt WebEngine
        # aborts the whole app on some graphics setups
        self.pdf.hide()
        self.url = evidence.get("file") if evidence.get("method") == "janaf" else sample["url"]
        if self.web is not None and self.web.isVisible():
            self.web.load(QUrl(self.url))
            return
        self.message.setText(f"This source is a web page or a paywalled article:\n{self.url}")
        self.message_box.show()

    def show_in_app(self) -> None:
        web = self._web()
        if web is None:
            self.message.setText("Qt WebEngine is not available; open the link in the browser.")
            return
        self.message_box.hide()
        web.show()
        web.load(QUrl(self.url))


STYLE = """
QFrame#card { border: 1px solid palette(mid); background: palette(base); }
QFrame#derivedCard { border: 1px solid rgba(232, 160, 40, 0.6); background: rgba(232, 160, 40, 0.08); }
QLabel#caption { color: #8a8f98; font-size: 10px; letter-spacing: 1.5px; }
QLabel#title { font-size: 20px; }
QLabel#muted { color: #8a8f98; }
QLineEdit#value { font-size: 18px; padding: 4px 6px; }
QLabel#chip { padding: 6px 8px; }
QLineEdit#filled { background: rgba(138, 143, 152, 0.14); }
QLabel#chip[outcome="match"] { background: rgba(46, 160, 67, 0.16); color: #2ea043; }
QLabel#chip[outcome="rounding"] { background: rgba(232, 160, 40, 0.18); color: #c88a1c; }
QLabel#chip[outcome="mismatch"], QLabel#chip[outcome="not_found"] { background: rgba(218, 54, 51, 0.15); color: #da3633; }
QLabel#chip[outcome="not_verifiable"], QLabel#chip[outcome="deferred"] { background: rgba(138, 143, 152, 0.18); color: #8a8f98; }
QHeaderView::section { font-weight: normal; }
"""
OUTCOME_COLORS = {"match": "#2ea043", "rounding": "#c88a1c", "mismatch": "#da3633", "not_found": "#da3633",
                  "not_verifiable": "#8a8f98", "deferred": "#8a8f98"}


def exact(value: float) -> str:
    """A number with every digit it carries (up to 12 significant), never shortened to 6 as :g does."""
    return f"{value:.12g}"


def _value_html(value, depth: int = 0, hide: float | None = None) -> str:
    """A JSON value as nested key–value rows: keys grey on the left, values in a fixed-width font."""
    if isinstance(value, dict):
        rows = "".join(f"<tr><td style='color:#8a8f98; padding:2px 12px 2px 0; vertical-align:top;"
                       f" white-space:nowrap'>{html.escape(str(key))}</td><td style='padding:2px 0'>"
                       f"{_value_html(item, depth + 1, hide)}</td></tr>" for key, item in value.items())
        return f"<table cellspacing=0 style='margin-left:{8 if depth else 0}px'>{rows}</table>"
    if isinstance(value, list):
        if all(not isinstance(item, (dict, list)) for item in value):
            return ", ".join(_value_html(item, depth, hide) for item in value)
        return "".join(f"<div style='margin:2px 0'>{_value_html(item, depth + 1, hide)}</div>" for item in value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if hide is not None and (abs(value - hide) < 1e-6 * max(1, abs(hide)) or abs(value * 1000 - hide) < 1e-3):
            return HIDDEN
        return f"<span style='font-family:monospace'>{exact(value)}</span>"
    if hide is not None:
        return _mask(str(value), hide)
    text = html.escape(str(value))
    return f"<a href='{text}'>{text}</a>" if text.startswith("http") else text


HIDDEN = "<span style='color:#8a8f98'>[hidden until checked]</span>"


def _stored_forms(value: float) -> list[str]:
    """Ways the stored number may be written in a locator (J and kJ, with and without decimals)."""
    forms = set()
    for number in (value, value / 1000):
        for decimals in range(0, 7):
            text = f"{number:.{decimals}f}"
            if abs(float(text) - number) < 0.5 * 10 ** -decimals + 1e-9 and len(text.lstrip("-").replace(".", "")) >= 3:
                forms.add(text)
    return sorted(forms, key=len, reverse=True)


def _text_html(text: str, hide: float | None) -> str:
    """Free text with inline JSON (``anchors={...}``) as tables and, when ``hide`` is set, the stored number masked."""
    out, position = [], 0
    while (start := text.find("{", position)) >= 0:
        try:
            data, end = json.JSONDecoder().raw_decode(text[start:])
        except ValueError:
            out.append(_mask(text[position:start + 1], hide))
            position = start + 1
            continue
        out.append(_mask(text[position:start], hide))
        out.append(_value_html(data, 1, hide))
        position = start + end
    out.append(_mask(text[position:], hide))
    return "".join(out)


def _mask(text: str, hide: float | None) -> str:
    escaped = html.escape(text)
    if hide is None:
        return escaped
    for form in _stored_forms(hide):
        escaped = re.sub(rf"(?<![\d.]){re.escape(form)}(?![\d])", HIDDEN, escaped)
    return escaped


def locator_html(sample: dict, blind: bool = False) -> str:
    """The citation and locator laid out for reading; a JSON locator becomes a table of its keys.

    With ``blind``, the stored number is masked wherever the locator states it.
    """
    hide = float(sample["value"]) if blind else None
    url = html.escape(sample["url"])
    caption = "<p style='color:#8a8f98; font-size:10px; letter-spacing:1.5px'>{}</p>"
    parts = [caption.format("SOURCE"), f"<p>{html.escape(sample['citation'])}<br><a href='{url}'>{url}</a></p>",
             caption.format("LOCATOR")]
    locator = (sample.get("locator") or "").strip()
    data, rest = None, locator
    if locator.startswith("{"):
        try:
            data, end = json.JSONDecoder().raw_decode(locator)
            rest = locator[end:].strip()
        except ValueError:
            data = None
    if data is not None:
        parts.append(_value_html(data, 0, hide))
    if rest:  # free text: one statement per line
        sentences = [part.strip() for part in re.split(r"(?<=[.;])\s+(?=[A-Z(])", rest) if part.strip()]
        parts.append("".join(f"<p style='margin:3px 0'>{_text_html(sentence, hide)}</p>" for sentence in sentences))
    return "".join(parts)


def card(caption: str, name: str = "card") -> tuple[QFrame, QVBoxLayout]:
    """A rounded box with a small spaced caption in place of a bold heading."""
    frame = QFrame(objectName=name)
    frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)  # as tall as its content
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(12, 10, 12, 12)
    layout.setAlignment(Qt.AlignTop)
    layout.setSpacing(8)
    title = QLabel(caption.upper(), objectName="caption")
    layout.addWidget(title)
    return frame, layout


class Calculator(QWidget):
    """Arithmetic for derived values and unit conversions; the result can go into the Value box."""

    use = Signal(str)
    NAMES = {"T": 298.15, "R": 8.314462618, "F": 96485.33212, "ln10": math.log(10), "cal": 4.184, "pi": math.pi}
    FUNCTIONS = {"ln": math.log, "log10": math.log10, "exp": math.exp, "sqrt": math.sqrt}

    def __init__(self) -> None:
        super().__init__()
        self.expression = QLineEdit()
        self.expression.setPlaceholderText("e.g. -527.6 + -285.83 + 62   or   -R*T*ln10*(-13.7)/1000")
        self.expression.textChanged.connect(self._evaluate)
        self.result = QLabel()
        self.result.setTextInteractionFlags(Qt.TextSelectableByMouse)
        use = QPushButton("Use as value")
        use.clicked.connect(lambda: self.result.property("value") is not None and self.use.emit(self.result.property("value")))
        hint = QLabel("T = 298.15 K, R = 8.314462618 J/(mol K), F, ln10, cal = 4.184; ln, log10, exp, sqrt")
        hint.setWordWrap(True)
        hint.setObjectName("muted")
        row = QHBoxLayout()
        row.addWidget(self.result, 1)
        row.addWidget(use)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 0, 0, 0)
        layout.addWidget(self.expression)
        layout.addLayout(row)
        layout.addWidget(hint)

    def _evaluate(self) -> None:
        text = self.expression.text().replace("−", "-").replace("×", "*").replace("^", "**").replace(",", ".")
        try:
            value = self._value(ast.parse(text, mode="eval").body) if text.strip() else None
        except Exception:
            value = None
        if value is None:
            self.result.setText("" if not text.strip() else "…")
            self.result.setProperty("value", None)
            return
        shown = f"{value:.10g}"
        self.result.setText(f"= {shown}")
        self.result.setProperty("value", shown)

    def _value(self, node) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id in self.NAMES:
            return self.NAMES[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            value = self._value(node.operand)
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.BinOp):
            left, right = self._value(node.left), self._value(node.right)
            operations = {ast.Add: lambda: left + right, ast.Sub: lambda: left - right, ast.Mult: lambda: left * right,
                          ast.Div: lambda: left / right, ast.Pow: lambda: left ** right}
            return operations[type(node.op)]()
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in self.FUNCTIONS:
            return self.FUNCTIONS[node.func.id](*(self._value(argument) for argument in node.args))
        raise ValueError("unsupported")


class RecipeForm(QWidget):
    """One field per printed input of a derived value; the result is worked out as the fields are filled."""

    computed = Signal(str, str)  # value text, unit

    def __init__(self) -> None:
        super().__init__()
        self.equation = QLabel(objectName="muted", wordWrap=True)
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(8)
        self.grid.setVerticalSpacing(2)
        self.grid.setColumnStretch(4, 1)
        self.result = QLabel(wordWrap=True)
        self.legend = QLabel("Shaded inputs are standard values from other sources (hover for which), filled in "
                             "for you; edit them if needed (↺ restores). Type the printed ones. After the check, db "
                             "shows the value the database used, red where it differs.", objectName="muted",
                             wordWrap=True)
        self.note = QLabel(objectName="muted", wordWrap=True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.equation)
        layout.addLayout(self.grid)
        layout.addWidget(self.legend)
        layout.addWidget(self.result)
        layout.addWidget(self.note)
        self.recipe = None
        self.fields: list[QLineEdit] = []

    def set_recipe(self, recipe, unit: str) -> None:
        while self.grid.count():
            widget = self.grid.takeAt(0).widget()
            widget.setParent(None)  # gone at once, not when the event loop gets to deleteLater
            widget.deleteLater()
        self.recipe, self.unit = recipe, unit
        self.fields = []
        self.unit_boxes: list[QComboBox | None] = []
        self.database_labels: list[QLabel] = []
        self.database_values: list | None = None
        self.equation.setText(recipe.equation)
        for row, term in enumerate(recipe.terms):
            coefficient = QLabel(self._coefficient(term), objectName="muted")
            coefficient.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            coefficient.setMinimumWidth(70)
            field = QLineEdit()
            field.setPlaceholderText("as printed")
            field.setMinimumWidth(80)
            field.setMaximumWidth(110)
            label = QLabel(term.label)
            if term.default is not None:  # a standard value the reviewed source does not print; editable
                default = exact(term.default)
                field.setText(default)
                field.setObjectName("filled")
                tip = f"Filled in from {term.default_source}; not printed in the source under review. Edit if needed."
                field.setToolTip(tip)
                label.setToolTip(tip)
                reset = QToolButton(text="↺", autoRaise=True)
                reset.setToolTip(f"Back to {default}")
                reset.clicked.connect(lambda _checked=False, f=field, d=default: f.setText(d))
                self.grid.addWidget(reset, 2 * row + 1, 3)
            field.textChanged.connect(self._compute)
            # name on its own line, so it never truncates; then coefficient, value, unit, ↺ and db
            self.grid.addWidget(label, 2 * row, 0, 1, 5)
            self.grid.addWidget(coefficient, 2 * row + 1, 0)
            self.grid.addWidget(field, 2 * row + 1, 1)
            dimension = next((d for d, options in UNITS.items() if term.unit in options), None)
            if dimension:  # the unit the source prints in can differ from the guess
                unit_box = QComboBox()
                unit_box.addItems(list(UNITS[dimension]))
                unit_box.setCurrentText(term.unit)
                unit_box.setProperty("dimension", dimension)
                unit_box.setProperty("previous", term.unit)
                unit_box.currentTextChanged.connect(lambda new, i=row: self._unit_changed(i, new))
                self.grid.addWidget(unit_box, 2 * row + 1, 2)
            else:
                unit_box = None
                self.grid.addWidget(QLabel(term.unit or "", objectName="muted"), 2 * row + 1, 2)
            self.unit_boxes.append(unit_box)
            database = QLabel()
            database.hide()
            self.grid.addWidget(database, 2 * row + 1, 4)
            self.database_labels.append(database)
            self.fields.append(field)
        self.legend.setVisible(any(term.default is not None for term in recipe.terms))
        self.note.setText(recipe.note)
        self.note.setVisible(bool(recipe.note))
        self.result.setText("")
        empty = next((field for field in self.fields if not field.text()), None)
        self.first_empty = empty

    def _factor(self, index: int) -> float:
        """Input unit of row ``index`` to the database unit, following its unit box."""
        box = self.unit_boxes[index]
        return UNITS[box.property("dimension")][box.currentText()] if box else self.recipe.terms[index].factor

    def _unit_changed(self, index: int, new: str) -> None:
        box, field = self.unit_boxes[index], self.fields[index]
        old = box.property("previous")
        box.setProperty("previous", new)
        if field.objectName() == "filled":  # a filled-in standard value keeps its meaning in the new unit
            try:
                value = parse_number(field.text()) * UNITS[box.property("dimension")][old] / UNITS[box.property("dimension")][new]
                field.setText(exact(value))
            except ValueError:
                pass
        self.show_database(self.database_values)
        self._compute()

    def units(self) -> list[str]:
        return [box.currentText() if box else "" for box in self.unit_boxes]

    def show_database(self, values: list | None) -> None:
        """After the reveal: the value the database used for each input, red where it differs from the field."""
        self.database_values = values
        for index, label in enumerate(self.database_labels):
            value = None if values is None else values[index]
            if value is not None:  # recorded in the term's own unit; show it in the chosen one
                value = value * self.recipe.terms[index].factor / self._factor(index)
            label.setVisible(values is not None)
            label.setText("" if value is None else f"db {exact(value)}")
            label.setToolTip("The value the database used for this input")
        self._mark_differences()

    def _mark_differences(self) -> None:
        if self.database_values is None:
            return
        for index, (field, label, value) in enumerate(zip(self.fields, self.database_labels, self.database_values)):
            if value is not None:
                value = value * self.recipe.terms[index].factor / self._factor(index)
            try:
                typed = parse_number(field.text())
            except ValueError:
                typed = None
            text = field.text().strip().replace("−", "-")
            decimals = len(text.split(".")[1]) if "." in text else 0
            differs = value is not None and typed is not None and abs(typed - value) > 0.5 * 10 ** -decimals + 1e-9
            label.setStyleSheet("color: #da3633;" if differs else "color: #8a8f98;")

    def set_inputs(self, saved: list) -> None:
        """Restore saved inputs: plain texts, or [text, unit] pairs."""
        for index, item in enumerate(saved[:len(self.fields)]):
            text, unit = (item, "") if isinstance(item, str) else item
            box = self.unit_boxes[index]
            if box and unit:
                box.blockSignals(True)
                box.setCurrentText(unit)
                box.setProperty("previous", unit)
                box.blockSignals(False)
            self.fields[index].setText(text)

    @staticmethod
    def _coefficient(term) -> str:
        if not term.unit:  # log K: its contribution in kJ/mol per unit of log K
            return f"× {term.coefficient / 1000:+.4g} kJ/mol"
        value = term.coefficient
        return "×" if value == 1 else "× −1" if value == -1 else f"× {value:+.6g}"

    def _compute(self) -> None:
        try:
            values = [parse_number(field.text()) for field in self.fields]
        except ValueError:
            self.result.setText("")
            return
        self._mark_differences()
        total = sum(term.coefficient * self._factor(i) * value
                    for i, (term, value) in enumerate(zip(self.recipe.terms, values)))
        shown = total / 1000 if self.unit == "kJ/mol" else total
        text = f"{shown:.4f}".rstrip("0").rstrip(".")
        self.result.setText(f"Result  {text} {self.unit}, copied to your reading")
        self.computed.emit(text, self.unit)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("pourbase transcription audit")
        self.settings = QSettings(str(SETTINGS_FILE), QSettings.IniFormat)
        self.samples: list[dict] = []
        self.results: dict[str, dict] = {}
        self.current: dict | None = None
        self.started = time.monotonic()
        self.process: QProcess | None = None
        self._build()
        self.reload()

    # layout
    def _build(self) -> None:
        bar = QToolBar()
        self.addToolBar(bar)
        bar.addAction("Draw sample…", self.draw)
        bar.addAction("Fetch missing evidence", lambda: self.fetch([]))
        bar.addAction("Statistics", self.show_statistics)
        bar.addSeparator()
        bar.addWidget(QLabel(" Reviewer "))
        self.reviewer = QLineEdit(self.settings.value("reviewer", getpass.getuser()))
        self.reviewer.setMaximumWidth(140)
        bar.addWidget(self.reviewer)
        self.blind = QCheckBox("Blind review")
        self.blind.setChecked(self.settings.value("blind", "true") == "true")
        self.blind.setToolTip("Hide the database value until the reading is saved")
        self.blind.toggled.connect(lambda _on: self.show_sample(self.current))
        bar.addWidget(self.blind)
        bar.addWidget(QLabel("  Theme "))
        self.theme = QComboBox()
        self.theme.addItems(THEME_MODES)
        self.theme.setCurrentText(self.settings.value("theme", "System"))
        self.theme.currentTextChanged.connect(self._theme_changed)
        bar.addWidget(self.theme)
        self.pending_only = QCheckBox("Pending only")
        self.pending_only.toggled.connect(lambda _on: self.fill_table())
        bar.addWidget(self.pending_only)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["", "ID", "Species", "Property"])
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        header_font = self.table.horizontalHeader().font()
        header_font.setBold(False)  # no bold text anywhere in the app
        self.table.horizontalHeader().setFont(header_font)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.itemSelectionChanged.connect(self._selected)

        self.evidence = ZoomImage()
        self.evidence.redo.connect(self.redo_grab)
        self.evidence.occurrenceShown.connect(self._occurrence_page)
        self.source = SourceView()
        self.locator = QTextBrowser(openExternalLinks=True)
        self.log = QPlainTextEdit(readOnly=True)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.evidence, "Evidence")
        self.tabs.addTab(self.source, "Source")
        self.tabs.addTab(self.locator, "Citation and locator")
        self.tabs.addTab(self.log, "Fetch log")
        self.tabs.currentChanged.connect(self._tab_changed)

        panel = QWidget()
        panel.setMinimumWidth(390)
        side = QVBoxLayout(panel)
        side.setContentsMargins(10, 8, 10, 10)
        side.setSpacing(10)

        # header: what is being checked
        self.title = QLabel(objectName="title", wordWrap=True)
        self.subtitle = QLabel(objectName="muted", wordWrap=True)
        self.facts = QLabel(objectName="muted", wordWrap=True)
        self.facts.setTextInteractionFlags(Qt.TextSelectableByMouse)
        links = QHBoxLayout()
        links.setSpacing(4)
        self.open_link = QPushButton("Open source")
        self.open_link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.current["url"])))
        attach = QPushButton("Attach PDF…")
        attach.setToolTip("Use a PDF you have (for example through library access) for this source")
        attach.clicked.connect(self.attach_pdf)
        details = QPushButton("Locator")
        details.setToolTip("Full citation and locator")
        details.clicked.connect(lambda: self.tabs.setCurrentWidget(self.locator))
        for button in (self.open_link, attach, details):
            links.addWidget(button)
        links.addStretch(1)
        header = QVBoxLayout()
        header.setSpacing(2)
        header.addWidget(self.title)
        header.addWidget(self.subtitle)
        header.addSpacing(4)
        header.addWidget(self.facts)
        header.addLayout(links)

        # derived values: what to look up
        self.derived_card, derived_layout = card("Derived value", "derivedCard")
        lead = QLabel("The source prints these inputs, not the stored number. Read each one; the result fills "
                      "your reading.", wordWrap=True)
        self.recipe_form = RecipeForm()
        self.recipe_form.computed.connect(self._recipe_result)
        derived_layout.addWidget(lead)
        derived_layout.addWidget(self.recipe_form)
        self.derived_card.hide()

        # the reading
        reading, reading_layout = card("Your reading")
        value_row = QHBoxLayout()
        self.value = QLineEdit(objectName="value")
        self.value.setPlaceholderText("Number as printed")
        self.value.textChanged.connect(self._preview)
        self.value.installEventFilter(self)  # Up and Down move through the samples while typing
        self.unit = QComboBox()
        self.unit.setMinimumWidth(110)
        self.unit.currentIndexChanged.connect(self._preview)
        value_row.addWidget(self.value, 1)
        value_row.addWidget(self.unit)
        reading_layout.addLayout(value_row)
        toggles = QHBoxLayout()
        self.issues_button = QPushButton(checkable=True)
        self.calculator_button = QPushButton("Calculator", checkable=True)
        toggles.addWidget(self.issues_button)
        toggles.addWidget(self.calculator_button)
        toggles.addStretch(1)
        reading_layout.addLayout(toggles)
        self.issues = QWidget()
        issues_layout = QVBoxLayout(self.issues)
        issues_layout.setContentsMargins(4, 0, 0, 0)
        issues_layout.setSpacing(4)
        self.flags = {key: QCheckBox(label) for key, label in FLAGS.items()}
        for box in self.flags.values():
            box.toggled.connect(lambda _on: (self._set_checked(False), self._update_issue_count()))
            issues_layout.addWidget(box)
        self.issues.hide()
        self.issues_button.toggled.connect(self.issues.setVisible)
        self.calculator = Calculator()
        self.calculator.use.connect(self.value.setText)
        self.calculator.hide()
        self.calculator_button.toggled.connect(self.calculator.setVisible)
        reading_layout.addWidget(self.issues)
        reading_layout.addWidget(self.calculator)
        self.notes = QPlainTextEdit()
        self.notes.setPlaceholderText("Notes")
        self.notes.setFixedHeight(54)
        reading_layout.addWidget(self.notes)
        self._update_issue_count()

        # the outcome
        result, result_layout = card("Result")
        self.database = QLabel()  # one line; word wrap made Qt reserve several lines of height
        self.verdict = QLabel(objectName="chip", wordWrap=True)
        self.verdict.hide()
        result_layout.addWidget(self.database)
        result_layout.addWidget(self.verdict)

        # actions
        self.reveal = QPushButton("Reveal value")
        self.reveal.clicked.connect(lambda: self._show_database(True))
        self.save_button = save = QPushButton()
        save.setDefault(True)
        save.clicked.connect(self.save)
        self._set_checked(False)
        self.defer_button = QPushButton()
        self.defer_button.setCheckable(True)
        self.defer_button.setToolTip("Could not locate the value yet; it may be there. Click again to undo. (Ctrl+D)")
        self.defer_button.clicked.connect(self.toggle_defer)
        self._show_deferred(False)
        QShortcut(QKeySequence("Ctrl+D"), self, self.defer_button.click)
        QShortcut(QKeySequence("Ctrl+Return"), self, self.save)
        QShortcut(QKeySequence("Ctrl+Enter"), self, self.save)
        actions = QVBoxLayout()
        secondary = QHBoxLayout()
        secondary.addWidget(self.defer_button)
        secondary.addStretch(1)
        secondary.addWidget(self.reveal)
        actions.addLayout(secondary)
        save.setMinimumHeight(32)
        actions.addWidget(save)

        side.addLayout(header)
        side.addWidget(self.derived_card)
        side.addWidget(reading)
        side.addWidget(result)
        side.addStretch(1)
        scroll = QScrollArea(widgetResizable=True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # the panel narrows with the window instead
        scroll.setWidget(panel)
        scroll.setMinimumWidth(panel.minimumWidth() + scroll.verticalScrollBar().sizeHint().width())
        right = QWidget()  # the actions stay in view below the scrolling panel
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 10, 8)
        right_layout.addWidget(scroll, 1)
        actions.setContentsMargins(10, 4, 0, 0)
        right_layout.addLayout(actions)

        splitter = QSplitter()
        splitter.addWidget(self.table)
        splitter.addWidget(self.tabs)
        splitter.addWidget(right)
        splitter.setChildrenCollapsible(False)  # no pane is squeezed below the size its buttons need
        self.table.setMinimumWidth(250)
        splitter.setSizes([300, 900, 440])
        self.setStyleSheet(STYLE)
        self.setCentralWidget(splitter)
        self.resize(1700, 950)

    def _theme_changed(self, mode: str) -> None:
        apply_theme(mode)
        self.settings.setValue("theme", mode)
        self.settings.sync()  # written now, not only when Qt tears the settings down

    # data
    def reload(self) -> None:
        self.samples = read_csv(SAMPLES)
        self.results = {row["sample_id"]: row for row in read_csv(RESULTS)}
        self.fill_table()

    def fill_table(self, after: str | None = None) -> None:
        selected = self.current["sample_id"] if self.current else None
        rows = [s for s in self.samples if not (self.pending_only.isChecked() and self._done(s["sample_id"]))]
        self.table.blockSignals(True)
        self.table.setRowCount(len(rows))
        for i, sample in enumerate(rows):
            outcome = self.results.get(sample["sample_id"], {}).get("outcome", "")
            for j, text in enumerate((OUTCOME_MARKS.get(outcome, ""), sample["sample_id"], sample["species"],
                                      PROPERTY_LABELS.get(sample["property"], sample["property"]))):
                item = QTableWidgetItem(text)
                item.setData(Qt.UserRole, sample["sample_id"])
                if j == 0 and outcome:
                    item.setForeground(QColor(OUTCOME_COLORS.get(outcome, "#8a8f98")))
                    item.setTextAlignment(Qt.AlignCenter)
                if outcome == "deferred":  # greyed out and skipped until revisited by hand
                    item.setForeground(self.palette().color(QPalette.Disabled, QPalette.Text))
                    item.setToolTip("Deferred: could not locate the value yet")
                self.table.setItem(i, j, item)
        self.table.resizeColumnToContents(0)
        self.table.resizeColumnToContents(1)
        self.table.blockSignals(False)
        deferred = sum(r["outcome"] == "deferred" for r in self.results.values())
        done = sum(self._done(s["sample_id"]) for s in self.samples)
        self.statusBar().showMessage(f"{done} of {len(self.samples)} samples reviewed"
                                     + (f", {deferred} deferred" if deferred else ""))
        target = next((i for i, s in enumerate(rows) if s["sample_id"] == selected), None)
        if target is None and rows:
            # the next sample without any result after the one just saved, wrapping round; deferred ones are
            # never chosen here, only by clicking them
            start = next((i + 1 for i, s in enumerate(rows) if s["sample_id"] == after), 0)
            order = rows[start:] + rows[:start]
            pending = next((s["sample_id"] for s in order if s["sample_id"] not in self.results), None)
            if pending is None:
                pending = after if any(s["sample_id"] == after for s in rows) else rows[0]["sample_id"]
                if deferred:
                    self.statusBar().showMessage(f"All samples reviewed except {deferred} deferred; click one to "
                                                 "return to it")
            target = next(i for i, s in enumerate(rows) if s["sample_id"] == pending)
        if target is not None:
            # replace the selection outright: selectRow adds to it while Ctrl (of Ctrl+Enter) is held
            self.table.selectionModel().select(
                self.table.model().index(target, 0),
                QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
            self.table.scrollToItem(self.table.item(target, 0))
            if self.current is None:  # the row was already selected, so no selection signal came
                self._selected()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.value and event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Up, Qt.Key_Down):
            self.move_selection(-1 if event.key() == Qt.Key_Up else 1)
            return True
        return super().eventFilter(watched, event)

    def move_selection(self, step: int) -> None:
        rows = self.table.selectionModel().selectedRows()
        row = (rows[0].row() if rows else -1) + step
        if 0 <= row < self.table.rowCount():
            self.table.selectionModel().select(self.table.model().index(row, 0),
                                               QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
            self.table.scrollToItem(self.table.item(row, 0))
            self.value.setFocus()

    def _done(self, sample_id: str) -> bool:
        return sample_id in self.results and self.results[sample_id]["outcome"] != "deferred"

    def _selected(self) -> None:
        items = self.table.selectedItems()
        if items:
            sample_id = items[0].data(Qt.UserRole)
            self.show_sample(next(s for s in self.samples if s["sample_id"] == sample_id))

    def show_sample(self, sample: dict | None) -> None:
        self.current = sample
        if sample is None:
            return
        self.started = time.monotonic()
        self._set_checked(False)
        self._blind_reading = None  # the first reading checked while the database value was hidden
        evidence = evidence_of(sample["sample_id"])
        self.title.setText(sample["species"])
        self.subtitle.setText(f"{PROPERTY_LABELS.get(sample['property'], sample['property'])}   ·   {sample['phase']}"
                              f"   ·   {sample['sample_id']}")
        citation = sample["citation"]
        short = citation if len(citation) <= 110 else citation[:108].rsplit(" ", 1)[0] + " …"
        self.facts.setText(f"{short}<br>{source_family(sample['url'])}  ·  {sample['status'].replace('_', ' ')}")
        self.facts.setToolTip(citation)
        self._show_locator()
        self._source_page = None
        self.evidence.set_evidence(evidence)
        self.unit.blockSignals(True)
        self.unit.clear()
        self.unit.addItems(list(UNITS[sample["unit"]]))
        self.unit.setCurrentText(guess_source_unit(sample["unit"], sample["locator"]))
        self.unit.blockSignals(False)
        previous = self.results.get(sample["sample_id"])
        self.value.setText(previous["source_text"] if previous else "")
        if previous:
            self.unit.setCurrentText(previous["source_unit"])
        active = set((previous or {}).get("flags", "").split(";"))
        for key, box in self.flags.items():
            box.setChecked(key in active)
        self.notes.setPlainText(previous["notes"] if previous else "")
        found = recipe(sample)
        self.derived_card.setVisible(found is not None)
        if found:
            self.recipe_form.set_recipe(found, "J/(mol K)" if sample["unit"] == "J/(mol K)" else "kJ/mol")
            if previous is None:
                self.flags["derived"].setChecked(True)
            elif previous.get("inputs"):  # the inputs as they were saved
                self.recipe_form.set_inputs(json.loads(previous["inputs"]))
                self.value.setText(previous["source_text"])
        self.calculator.expression.clear()
        self.calculator_button.setChecked(False)
        self.issues_button.setChecked(any(box.isChecked() and key != "derived" for key, box in self.flags.items()))
        self._show_deferred(previous is not None and previous["outcome"] == "deferred")
        reviewed = previous is not None and previous["outcome"] != "deferred"
        self._show_database(reviewed or not self.blind.isChecked())
        self._show_verdict(previous)
        if self.tabs.currentWidget() is self.source:
            self.source.show_source(sample, self._at_occurrence(evidence))
        self.value.setFocus()

    def _tab_changed(self) -> None:
        if self.tabs.currentWidget() is self.source and self.current:
            self.source.show_source(self.current, self._at_occurrence(evidence_of(self.current["sample_id"])))

    def _show_locator(self) -> None:
        if self.current is not None:
            self.locator.setHtml(locator_html(self.current, blind=(not self.reveal.isHidden()) and self.blind.isChecked()))

    def _show_database(self, shown: bool) -> None:
        sample = self.current
        self.reveal.setVisible(not shown)
        self._show_locator()
        if self.derived_card.isVisibleTo(self) and self.recipe_form.recipe is not None:
            self.recipe_form.show_database(database_inputs(sample, self.recipe_form.recipe) if shown else None)
        if not shown:
            self.database.setText("<span style='color:#8a8f98'>Database value hidden until you check your reading</span>")
            return
        unit = self.unit.currentText() or sample["unit"]
        converted = float(sample["value"]) / UNITS[sample["unit"]][unit]
        self.database.setText(f"<span style='color:#8a8f98'>Database</span>&nbsp;&nbsp;"
                              f"<span style='font-size:17px'>{exact(converted)}</span> {unit}"
                              + (f"<span style='color:#8a8f98'>&nbsp;&nbsp;({exact(float(sample['value']))} {sample['unit']})</span>"
                                 if unit != sample["unit"] else ""))

    def _recipe_inputs(self) -> str:
        if not self.derived_card.isVisible() or not self.recipe_form.fields:
            return ""
        return json.dumps([[field.text(), unit] for field, unit in zip(self.recipe_form.fields, self.recipe_form.units())])

    def _recipe_result(self, text: str, unit: str) -> None:
        self.unit.setCurrentText(unit)
        self.value.setText(text)

    def _show_verdict(self, row: dict | None) -> None:
        if row is None:
            self.verdict.hide()
            return
        self.verdict.setText(self._verdict_text(row))
        self.verdict.setProperty("outcome", row["outcome"])
        self.verdict.style().unpolish(self.verdict)
        self.verdict.style().polish(self.verdict)
        self.verdict.show()

    def _update_issue_count(self) -> None:
        count = sum(box.isChecked() for box in self.flags.values())
        self.issues_button.setText(f"Issues  {count}" if count else "Issues")

    def _set_checked(self, checked: bool) -> None:
        """After a check the next Ctrl+Enter saves; any change to the reading asks for a new check."""
        self._checked = checked
        self.save_button.setText("Save and next  (Ctrl+Enter)" if checked else "Check result  (Ctrl+Enter)")

    def _preview(self) -> None:
        self._set_checked(False)
        if self.current and not (not self.reveal.isHidden()):
            self._show_database(True)

    # deferring
    def _show_deferred(self, deferred: bool) -> None:
        self.defer_button.setChecked(deferred)
        self.defer_button.setText("Undo defer  (Ctrl+D)" if deferred else "Defer for later  (Ctrl+D)")

    def toggle_defer(self) -> None:
        """Mark the sample as deferred (greyed, skipped by Ctrl+Enter) and move to the next one, or undo it."""
        sample = self.current
        if sample is None:
            return
        sample_id = sample["sample_id"]
        if self.results.get(sample_id, {}).get("outcome") == "deferred":
            del self.results[sample_id]
        else:
            row = {"sample_id": sample_id, "reviewer": self.reviewer.text().strip(),
                   "reviewed_on": datetime.datetime.now().isoformat(timespec="seconds"),
                   "seconds": round(time.monotonic() - self.started), "outcome": "deferred",
                   "source_text": self.value.text().strip(), "source_unit": self.unit.currentText(),
                   "database_value_SI": sample["value"], "notes": self.notes.toPlainText().strip(),
                   "inputs": self._recipe_inputs()}
            self.results[sample_id] = {key: row.get(key, "") for key in RESULT_FIELDS}
        self._write_results()
        self.fill_table()  # keeps this sample selected
        deferred = sample_id in self.results
        self._show_deferred(deferred)
        self._show_verdict(self.results[sample_id] if deferred else None)
        if deferred:
            self.move_selection(1)  # on to the next sample in the list; Up arrow goes back to undo

    def _write_results(self) -> None:
        write_csv(RESULTS, RESULT_FIELDS, [self.results[s["sample_id"]] for s in self.samples
                                            if s["sample_id"] in self.results])

    # saving
    def save(self) -> None:
        sample = self.current
        if sample is None:
            return
        flags = [key for key, box in self.flags.items() if box.isChecked()]
        text = self.value.text().strip()
        row = {"sample_id": sample["sample_id"], "reviewer": self.reviewer.text().strip(),
               "reviewed_on": datetime.datetime.now().isoformat(timespec="seconds"),
               "seconds": round(time.monotonic() - self.started), "source_text": text,
               "source_unit": self.unit.currentText(), "database_value_SI": sample["value"],
               "flags": ";".join(flags), "notes": self.notes.toPlainText().strip(), "inputs": self._recipe_inputs()}
        if text:
            try:
                result = compare(text, self.unit.currentText(), float(sample["value"]), sample["unit"])
            except ValueError:
                QMessageBox.warning(self, "Not a number", f"Cannot read “{text}” as a number.")
                return
            outcome = result.outcome
            classes = list(result.classes)
            if any(flag in flags for flag in WRONG_FLAGS):
                outcome = "mismatch"
                classes = [flag.replace("_", " ") for flag in flags if flag in WRONG_FLAGS] + classes
            row.update(outcome=outcome, source_value_SI=exact(result.source_SI),
                       database_in_source_unit=exact(result.database_in_source_unit),
                       difference_SI=exact(result.difference_SI), relative_difference=f"{result.relative:.3g}",
                       classes="; ".join(classes), digit_edits=result.digit_edits, decimals=result.decimals)
        elif "not_found" in flags:
            row.update(outcome="not_found", classes="value not found in source")
        elif "source_unreadable" in flags:
            row.update(outcome="not_verifiable", classes="source unavailable")
        else:
            QMessageBox.information(self, "Nothing to save",
                                    "Type the value printed in the source, or tick “not found” or “not available”.")
            return
        row = {key: row.get(key, "") for key in RESULT_FIELDS}
        if not self._checked:  # first press: show the comparison, save on the next
            if self._blind_reading is None and (not self.reveal.isHidden()):
                self._blind_reading = (text, self.unit.currentText(), ";".join(flags))
            self._show_database(True)
            self._show_verdict(row)
            self._set_checked(True)
            return
        if self._blind_reading is not None and self._blind_reading != (text, self.unit.currentText(), ";".join(flags)):
            row["flags"] = ";".join(filter(None, [row["flags"], "revised_after_reveal"]))
            row["notes"] = (row["notes"] + f" [blind reading: {self._blind_reading[0]} {self._blind_reading[1]}]").strip()
        self.results[sample["sample_id"]] = row
        write_csv(RESULTS, RESULT_FIELDS, [self.results[s["sample_id"]] for s in self.samples
                                            if s["sample_id"] in self.results])
        self.settings.setValue("reviewer", self.reviewer.text())
        self.settings.setValue("blind", "true" if self.blind.isChecked() else "false")
        self.settings.sync()
        self.current = None  # move to the next pending sample
        self.fill_table(after=sample["sample_id"])

    def _verdict_text(self, row: dict) -> str:
        outcome = row["outcome"]
        text = {"match": "✓  Matches the source", "rounding": "≈  Last digit differs", "mismatch": "✗  Mismatch",
                "not_found": "?  Not found in the source", "not_verifiable": "–  Source not available",
                "deferred": "⏸  Deferred for later"}.get(outcome, outcome)
        details = [row["classes"]] if row.get("classes") and outcome != "rounding" else []
        if outcome in ("mismatch", "rounding") and row.get("difference_SI") and self.current:
            details.append(f"database − source = {float(row['difference_SI']):+.4g} {self.current['unit']}")
        return text + "".join(f"\n{line}" for line in details)

    # sampling and evidence
    def draw(self) -> None:
        dialog = DrawDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        rows = draw_sample.draw(dialog.count.value(), dialog.seed.value(), dialog.stratify.isChecked())
        self.reload()
        if rows:
            self.fetch([row["sample_id"] for row in rows])

    def fetch(self, sample_ids: list[str]) -> None:
        if self.process is not None:
            QMessageBox.information(self, "Busy", "Evidence is still being fetched.")
            return
        self.tabs.setCurrentWidget(self.log)
        self.process = QProcess(self)
        self.process.setWorkingDirectory(str(HERE))
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(
            lambda: self.log.appendPlainText(bytes(self.process.readAllStandardOutput()).decode(errors="replace").rstrip()))
        self.process.finished.connect(self._fetched)
        environment = self.process.processEnvironment()
        environment.insert("QT_QPA_PLATFORM", "offscreen")
        environment.insert("PYTHONUNBUFFERED", "1")
        self.process.setProcessEnvironment(environment)
        self.log.appendPlainText(f"Fetching evidence for {len(sample_ids) or 'all missing'} samples…")
        self.process.start(sys.executable, [str(HERE / "fetch_evidence.py"), *sample_ids])

    def _fetched(self) -> None:
        self.log.appendPlainText("Done.")
        self.process = None
        self.tabs.setCurrentWidget(self.evidence)
        self.show_sample(self.current)

    def redo_grab(self) -> None:
        if self.current is not None:
            (EVIDENCE / f"{self.current['sample_id']}.json").unlink(missing_ok=True)
            self.fetch([self.current["sample_id"]])

    def _occurrence_page(self, page: int) -> None:
        """The Source tab opens at the page of the occurrence on show."""
        self._source_page = page

    def _at_occurrence(self, evidence: dict) -> dict:
        return evidence if self._source_page is None else {**evidence, "page": self._source_page}

    def attach_pdf(self) -> None:
        if self.current is None:
            return
        path, _ = QFileDialog.getOpenFileName(self, "PDF of this source", str(Path.home()), "PDF (*.pdf)")
        if not path:
            return
        CACHE.mkdir(exist_ok=True)
        target = CACHE / ("attached-" + hashlib.sha1(self.current["url"].encode()).hexdigest()[:16] + ".pdf")
        shutil.copyfile(path, target)
        same_source = [s["sample_id"] for s in self.samples if s["url"] == self.current["url"]]
        self.fetch(same_source)

    # statistics
    def show_statistics(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Audit statistics")
        text = QTextBrowser()
        text.setHtml(statistics_html(self.samples, self.results))
        export = QPushButton("Write LaTeX macros and summary CSV")
        export.clicked.connect(lambda: QMessageBox.information(dialog, "Written", export_statistics(
            self.samples, self.results)))
        layout = QVBoxLayout(dialog)
        layout.addWidget(text)
        layout.addWidget(export)
        dialog.resize(760, 680)
        dialog.exec()


def summary(samples: list[dict], results: dict[str, dict]) -> dict:
    by_id = {s["sample_id"]: s for s in samples}
    rows = [r for r in results.values() if r["sample_id"] in by_id]
    checked = [r for r in rows if r["outcome"] in ("match", "rounding", "mismatch", "not_found")]
    errors = [r for r in checked if r["outcome"] in ("mismatch", "not_found")]
    strict = [r for r in checked if r["outcome"] != "match"]
    classes = Counter(c.strip() for r in errors for c in r["classes"].split(";") if c.strip())
    families: dict[str, list] = defaultdict(list)
    for r in checked:
        families[source_family(by_id[r["sample_id"]]["url"])].append(r)
    sizes = [abs(float(r["difference_SI"])) for r in errors if r.get("difference_SI")]
    seconds = [int(r["seconds"]) for r in rows if r.get("seconds")]
    return {"reviewed": len(rows), "checked": len(checked), "errors": len(errors), "strict": len(strict),
            "outcomes": Counter(r["outcome"] for r in rows), "classes": classes, "families": families,
            "sizes": sizes, "seconds": seconds, "sampled": len(samples)}


def statistics_html(samples: list[dict], results: dict[str, dict]) -> str:
    s = summary(samples, results)
    if not s["checked"]:
        return "<p>No reviewed samples yet.</p>"
    low, high = wilson(s["errors"], s["checked"])
    slow, shigh = wilson(s["strict"], s["checked"])
    parts = [f"<p style='font-size:16px'>{s['reviewed']} of {s['sampled']} sampled values reviewed</p>",
             f"<p>Error rate (mismatch or not found): {s['errors']}/{s['checked']} = "
             f"{s['errors'] / s['checked']:.1%} (95 % Wilson interval {low:.1%}–{high:.1%})<br>"
             f"Including last-digit differences: {s['strict']}/{s['checked']} = {s['strict'] / s['checked']:.1%} "
             f"({slow:.1%}–{shigh:.1%})</p>", "<p style='font-size:14px'>Outcomes</p><ul>"]
    parts += [f"<li>{OUTCOME_MARKS.get(k, '')} {k}: {v}</li>" for k, v in s["outcomes"].most_common()]
    parts.append("</ul><p style='font-size:14px'>Kinds of error</p><ul>")
    parts += [f"<li>{k}: {v}</li>" for k, v in s["classes"].most_common()] or ["<li>none</li>"]
    parts.append("</ul><p style='font-size:14px'>By source family</p><table cellpadding=4><tr><td>Family</td><td>checked</td>"
                 "<td>errors</td></tr>")
    for name, rows in sorted(s["families"].items()):
        bad = sum(r["outcome"] in ("mismatch", "not_found") for r in rows)
        parts.append(f"<tr><td>{name}</td><td align=center>{len(rows)}</td><td align=center>{bad}</td></tr>")
    parts.append("</table>")
    if s["sizes"]:
        parts.append(f"<p>Size of mismatches (database units): median {statistics.median(s['sizes']):.4g}, "
                     f"largest {max(s['sizes']):.4g}</p>")
    deferred = sum(r["outcome"] == "deferred" for r in results.values())
    parts.append(f"<p>Deferred (not yet located, left out above): {deferred}</p>")
    revised = sum("revised_after_reveal" in r.get("flags", "") for r in results.values())
    parts.append(f"<p>Readings changed after the database value was shown: {revised}</p>")
    if s["seconds"]:
        parts.append(f"<p>Median review time {statistics.median(s['seconds']):.0f} s per value.</p>")
    return "".join(parts)


def export_statistics(samples: list[dict], results: dict[str, dict]) -> str:
    s = summary(samples, results)
    low, high = wilson(s["errors"], s["checked"])
    macros = {"AuditSampled": s["sampled"], "AuditChecked": s["checked"], "AuditErrors": s["errors"],
              "AuditErrorRate": f"{100 * s['errors'] / max(s['checked'], 1):.1f}",
              "AuditErrorLow": f"{100 * low:.1f}", "AuditErrorHigh": f"{100 * high:.1f}",
              "AuditLastDigit": s["outcomes"].get("rounding", 0),
              "AuditNotVerifiable": s["outcomes"].get("not_verifiable", 0)}
    reviewed = [results[x["sample_id"]] for x in samples if x["sample_id"] in results]
    derived = [r for r in reviewed if "derived" in r.get("flags", "")]
    with connect() as connection:
        population_size = len(population(connection))
    provenance_path = HERE / "sampling-provenance.json"
    provenance = json.loads(provenance_path.read_text()) if provenance_path.exists() else {}
    # Filtering a completed audit does not redraw it from today's database.
    population_size = provenance.get("population_at_sampling", population_size)
    macros.update({
        "AuditPopulation": population_size,
        "AuditOriginalSampled": provenance.get("original_sample_size", s["sampled"]),
        "AuditExcludedFromRelease": len(provenance.get("excluded_sample_ids", [])),
        "AuditTranscriptionUpper": f"{100 * wilson(0, s['checked'])[1]:.1f}",
        "AuditRounds": len({x["round"] for x in samples}),
        "AuditMatches": s["outcomes"].get("match", 0),
        "AuditDerived": len(derived),
        "AuditDerivedMatches": sum(r["outcome"] == "match" for r in derived),
        "AuditRevised": sum("revised_after_reveal" in r.get("flags", "") for r in reviewed),
        "AuditMedianSeconds": f"{statistics.median(s['seconds']):.0f}" if s["seconds"] else "0",
        "AuditFamilies": len(s["families"]),
        "AuditSources": len({x["source_id"] for x in samples}),
    })
    # written here, and into the paper's generated folder when there is one
    targets = [HERE] + ([REPO / "paper" / "generated"] if (REPO / "paper" / "generated").is_dir() else [])
    statistics_tex = "% Written by verification/verify_app.py\n" + "".join(
        f"\\newcommand{{\\{key}}}{{{value}}}\n" for key, value in macros.items())
    rows = [{"family": name, "checked": len(rows),
             "errors": sum(r["outcome"] in ("mismatch", "not_found") for r in rows)}
            for name, rows in sorted(s["families"].items())]
    write_csv(HERE / "summary-by-family.csv", ["family", "checked", "errors"], rows)
    # the whole tabular, so that \input inside a table environment needs nothing around it
    lines = [r"\begin{tabular}{lrrr}", r"\toprule",
             r"Source family & Checked & Matches & Mismatches \\", r"\midrule"]
    for row in rows:
        lines.append(f"{row['family']} & {row['checked']} & {row['checked'] - row['errors']} & {row['errors']} \\\\")
    total_errors = sum(row["errors"] for row in rows)
    total = sum(row["checked"] for row in rows)
    lines += [r"\midrule", f"Total & {total} & {total - total_errors} & {total_errors} \\\\", r"\bottomrule",
              r"\end{tabular}"]
    table_tex = "% Written by verification/verify_app.py\n" + "\n".join(lines) + "\n"
    for target in targets:
        (target / "audit-statistics.tex").write_text(statistics_tex)
        (target / "audit-table.tex").write_text(table_tex)
    return ("Wrote audit-statistics.tex, audit-table.tex and summary-by-family.csv to "
            + " and ".join(str(target.relative_to(REPO)) for target in targets))


def main() -> None:
    # Qt WebEngine without the GPU: on Wayland sessions without EGL it otherwise aborts the app
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu --disable-gpu-compositing")
    from PySide6.QtQuick import QQuickWindow, QSGRendererInterface
    QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.Software)
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication.instance() or QApplication(sys.argv)
    apply_theme(QSettings(str(SETTINGS_FILE), QSettings.IniFormat).value("theme", "System"))
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
