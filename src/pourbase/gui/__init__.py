"""Desktop GUI for pourbase (Qt, via PySide6 and pyqtgraph).

Start it with ``pourbase-gui [element]``, ``pourbase gui`` or ``python -m pourbase.gui``.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        import pyqtgraph as pg
        from PySide6.QtWidgets import QApplication
    except ImportError:
        sys.stderr.write(
            "The pourbase GUI needs PySide6 and pyqtgraph. Install them with\n"
            '    pip install "pourbase[gui]"\n'
        )
        return 1

    from .window import MainWindow

    pg.setConfigOptions(antialias=True)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("pourbase")
    app.setWindowIcon(application_icon())
    window = MainWindow(symbol=argv[0] if argv else None)
    window.show()
    return app.exec()


def application_icon():
    """The logo, clipped to its rounded tile (Qt's SVG renderer ignores clip paths)."""
    from pathlib import Path

    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QIcon, QPainter, QPainterPath, QPixmap
    from PySide6.QtSvg import QSvgRenderer

    renderer = QSvgRenderer(str(Path(__file__).parent / "assets" / "logo.svg"))
    icon = QIcon()
    for size in (16, 32, 64, 128, 256):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        scale = size / 128
        tile = QPainterPath()
        tile.addRoundedRect(QRectF(6.5, 6.5, 115, 115), 19.5, 19.5)
        painter.scale(scale, scale)
        painter.setClipPath(tile)
        painter.scale(1 / scale, 1 / scale)
        renderer.render(painter)
        painter.end()
        icon.addPixmap(pixmap)
    return icon
