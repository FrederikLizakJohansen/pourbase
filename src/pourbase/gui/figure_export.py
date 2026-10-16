"""Right-click export for every figure: the picture as PNG, PDF or SVG, the data as CSV or TXT."""

from __future__ import annotations

import csv
import io
from collections.abc import Callable, Sequence
from pathlib import Path

from PySide6.QtCore import QEvent, QMarginsF, QObject, QPoint, QRect, QRectF, QSize, QSizeF, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPageLayout, QPageSize, QPainter, QPdfWriter
from PySide6.QtSvg import QSvgGenerator
from PySide6.QtWidgets import QAbstractScrollArea, QFileDialog, QGraphicsView, QMenu, QMessageBox, QWidget

Table = tuple[Sequence[str], Sequence[Sequence[object]]]
DataSource = Callable[[], "Table | None"]
FORMATS = {"png": "PNG image", "pdf": "PDF document", "svg": "SVG drawing"}


def _paint(widget: QWidget, painter: QPainter, width: float, height: float) -> None:
    """Paint all of ``widget`` into ``width`` x ``height`` logical units of the painter's device."""
    if isinstance(widget, QGraphicsView):
        # a graphics view maps its viewport onto the target rectangle; give it the whole figure
        widget.render(painter, QRectF(0, 0, width, height), widget.viewport().rect())
    else:
        widget.render(painter, QPoint(0, 0))


def render_png(widget: QWidget, path: str | Path, scale: float = 2.0) -> None:
    """The widget as a PNG at ``scale`` times its screen resolution."""
    size = widget.size()
    image = QImage(QSize(int(size.width() * scale), int(size.height() * scale)), QImage.Format_ARGB32)
    image.setDevicePixelRatio(scale)
    image.fill(widget.palette().window().color())
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    _paint(widget, painter, size.width(), size.height())
    painter.end()
    if not image.save(str(path), "PNG"):
        raise OSError(f"Cannot write {path}")


def render_pdf(widget: QWidget, path: str | Path) -> None:
    """The widget on a PDF page of its own size."""
    writer = QPdfWriter(str(path))
    writer.setResolution(96)
    size = QSizeF(widget.width(), widget.height())
    writer.setPageLayout(QPageLayout(QPageSize(size * 72 / 96, QPageSize.Point), QPageLayout.Portrait,
                                     QMarginsF(0, 0, 0, 0)))
    painter = QPainter(writer)
    painter.setRenderHint(QPainter.Antialiasing)
    _paint(widget, painter, writer.width(), writer.height())
    painter.end()


def render_svg(widget: QWidget, path: str | Path) -> None:
    """The widget as an SVG drawing.

    Diagrams are redrawn with the package's Matplotlib functions, the same ones the exported code
    uses, so lines, labels and text stay editable vectors. Custom-drawn widgets, such as the
    periodic table, are written directly as vector graphics. Other plots, such as a sweep slice,
    embed the figure at twice the screen resolution.
    """
    redraw = getattr(widget, "matplotlib_figure", None)
    figure = redraw() if callable(redraw) else None
    if figure is not None:
        import matplotlib.pyplot as plt

        figure.savefig(path, format="svg", bbox_inches="tight")
        plt.close(figure)
        return
    if isinstance(widget, QGraphicsView):
        import base64
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            png = Path(directory) / "figure.png"
            render_png(widget, png)
            encoded = base64.b64encode(png.read_bytes()).decode("ascii")
        width, height = widget.width(), widget.height()
        Path(path).write_text(
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
            f'<image width="{width}" height="{height}" xlink:href="data:image/png;base64,{encoded}"/>\n</svg>\n',
            encoding="utf-8")
        return
    generator = QSvgGenerator()
    generator.setFileName(str(path))
    generator.setSize(widget.size())
    generator.setViewBox(QRect(0, 0, widget.width(), widget.height()))
    generator.setTitle(widget.window().windowTitle())
    painter = QPainter(generator)
    _paint(widget, painter, widget.width(), widget.height())
    painter.end()


def write_table(table: Table, path: str | Path, delimiter: str) -> None:
    header, rows = table
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter=delimiter)
        writer.writerow(header)
        writer.writerows(rows)


def table_text(table: Table, delimiter: str = ",") -> str:
    buffer = io.StringIO()
    header, rows = table
    writer = csv.writer(buffer, delimiter=delimiter)
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()


class _ContextMenu(QObject):
    def __init__(self, widget: QWidget, data: DataSource | None, name: Callable[[], str]) -> None:
        super().__init__(widget)
        self.widget, self.data, self.name = widget, data, name
        self.extra_actions: list[tuple[str, Callable[[], None]]] = []  # listed first, e.g. "Pop out"

    def eventFilter(self, watched, event) -> bool:
        if event.type() == QEvent.ContextMenu:
            self.show_menu(event.globalPos())
            return True
        return False

    def show_menu(self, position) -> None:
        menu = QMenu(self.widget)
        for label, callback in self.extra_actions:
            menu.addAction(label, callback)
        if self.extra_actions:
            menu.addSeparator()
        for suffix, label in FORMATS.items():
            menu.addAction(f"Export figure as {suffix.upper()}…", lambda suffix=suffix: self.save_figure(suffix))
        if callable(getattr(self.widget, "python_code", None)):
            menu.addSeparator()
            menu.addAction("Copy Python code", self.copy_code)
            menu.addAction("Export Python code…", self.save_code)
        if self.data is not None:  # the table itself is built only when it is exported
            menu.addSeparator()
            for suffix, label, delimiter in (("csv", "CSV", ","), ("txt", "TXT (tab separated)", "\t")):
                menu.addAction(f"Export data as {label}…",
                               lambda suffix=suffix, delimiter=delimiter: self.save_data(suffix, delimiter))
        menu.popup(position)

    def _path(self, suffix: str, label: str) -> str:
        path, _ = QFileDialog.getSaveFileName(self.widget, f"Export {label}", f"{self.name()}.{suffix}",
                                              f"{label} (*.{suffix})")
        if path and not path.lower().endswith(f".{suffix}"):
            path += f".{suffix}"
        return path

    def save_figure(self, suffix: str, path: str | None = None) -> None:
        path = path or self._path(suffix, FORMATS[suffix])
        if not path:
            return
        try:
            {"png": render_png, "pdf": render_pdf, "svg": render_svg}[suffix](self.widget, path)
        except OSError as error:
            QMessageBox.warning(self.widget, "Export figure", str(error))

    def copy_code(self) -> None:
        QGuiApplication.clipboard().setText(self.widget.python_code())

    def save_code(self, path: str | None = None) -> None:
        path = path or self._path("py", "Python script")
        if path:
            Path(path).write_text(self.widget.python_code() + "\n", encoding="utf-8")

    def save_data(self, suffix: str, delimiter: str, path: str | None = None) -> None:
        if self.data is None:
            return
        path = path or self._path(suffix, "data")
        if not path:
            return
        table = self.data()
        if table is None:
            QMessageBox.information(self.widget, "Export data", "There is no data in this figure yet.")
            return
        write_table(table, path, delimiter)


def install_export_menu(widget: QWidget, data: DataSource | None = None,
                        name: Callable[[], str] | str = "pourbase-figure") -> _ContextMenu:
    """Add a right-click menu to ``widget`` that exports the figure and, if ``data`` gives one, its table.

    ``data`` returns ``(header, rows)`` or None when there is nothing to export yet.
    """
    handler = _ContextMenu(widget, data, name if callable(name) else (lambda: name))
    widget.setContextMenuPolicy(Qt.DefaultContextMenu)
    widget.installEventFilter(handler)
    if isinstance(widget, QAbstractScrollArea):
        widget.viewport().installEventFilter(handler)
    widget.export_menu = handler
    return handler
