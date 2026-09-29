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
    window = MainWindow(symbol=argv[0] if argv else None)
    window.show()
    return app.exec()
