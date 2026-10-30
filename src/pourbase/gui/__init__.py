"""Desktop GUI for pourbase (Qt, via PySide6 and pyqtgraph).

Start it with ``pourbase-gui [element | session.pourbase.json | dataset.csv | dataset.sqlite]``, ``pourbase gui`` or
``python -m pourbase.gui``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_ID = "pourbase"
LOGO = Path(__file__).parent / "assets" / "logo.svg"


def _load_pyqtgraph():
    """Use the same Qt binding as the rest of the GUI, even in mixed environments."""
    # pyqtgraph selects its binding at import time. Restore the caller's environment
    # afterwards; an already-imported incompatible binding cannot be changed safely.
    previous = os.environ.get("PYQTGRAPH_QT_LIB")
    os.environ["PYQTGRAPH_QT_LIB"] = "PySide6"
    try:
        import pyqtgraph as pg
    finally:
        if previous is None:
            os.environ.pop("PYQTGRAPH_QT_LIB", None)
        else:
            os.environ["PYQTGRAPH_QT_LIB"] = previous
    if pg.Qt.QT_LIB != "PySide6":
        raise RuntimeError(
            f"pourbase requires pyqtgraph to use PySide6; it already uses {pg.Qt.QT_LIB}. "
            "Start pourbase in a fresh Python process."
        )
    return pg


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        from PySide6.QtWidgets import QApplication
        pg = _load_pyqtgraph()
    except ImportError as error:
        sys.stderr.write(
            "Could not load the pourbase GUI dependencies.\n"
            f"Python interpreter: {sys.executable}\n"
            f"Import error: {type(error).__name__}: {error}\n"
            "Install the GUI dependencies with the same interpreter:\n"
            f'    "{sys.executable}" -m pip install "pourbase[gui]"\n'
        )
        return 1

    from .window import MainWindow

    _register_with_desktop()
    pg.setConfigOptions(antialias=True)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName(APP_ID)
    QApplication.setDesktopFileName(APP_ID)
    app.setWindowIcon(application_icon())
    argument = argv[0] if argv else None
    lowered = (argument or "").lower()
    session = argument if lowered.endswith(".json") else None
    dataset = argument if lowered.endswith((".csv", ".sqlite", ".db")) else None
    if dataset:
        from ..user_data import open_dataset

        window = MainWindow(database=open_dataset(dataset), dataset_name=Path(dataset).name)
    else:
        window = MainWindow(symbol=None if session else argument)
    window.show()
    if session:
        window.load_session(session)
    return app.exec()


def logo_pixmap(size: int, device_pixel_ratio: float = 1.0):
    """The logo at ``size`` logical pixels, clipped to its rounded tile.

    Qt's SVG renderer ignores clip paths, so the tile is clipped here.
    """
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QPainter, QPainterPath, QPixmap
    from PySide6.QtSvg import QSvgRenderer

    pixels = round(size * device_pixel_ratio)
    pixmap = QPixmap(pixels, pixels)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    scale = pixels / 128
    tile = QPainterPath()
    tile.addRoundedRect(QRectF(6.5, 6.5, 115, 115), 19.5, 19.5)
    painter.scale(scale, scale)
    painter.setClipPath(tile)
    painter.scale(1 / scale, 1 / scale)
    QSvgRenderer(str(LOGO)).render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(device_pixel_ratio)
    return pixmap


def application_icon():
    from PySide6.QtGui import QIcon

    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(logo_pixmap(size))
    return icon


def _register_with_desktop() -> None:
    """Make the operating system show the pourbase logo for the running application.

    GNOME, KDE and other Linux desktops on Wayland take the taskbar icon from a desktop entry whose
    name matches the application ID, so a user-level entry and icon are installed under
    ``$XDG_DATA_HOME``. Windows groups the taskbar button by an application user model ID.
    """
    if sys.platform.startswith("linux"):
        _install_desktop_entry()
    elif sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except (AttributeError, OSError):
            pass


def _install_desktop_entry() -> None:
    data = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    entry = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=pourbase\n"
        "Comment=Pourbaix diagrams from source-linked experimental thermochemistry\n"
        f'Exec="{sys.executable}" -m pourbase.gui\n'
        f"Icon={APP_ID}\n"
        f"StartupWMClass={APP_ID}\n"
        "Terminal=false\n"
        "Categories=Science;Chemistry;\n"
    )
    files = {
        data / "icons" / "hicolor" / "scalable" / "apps" / f"{APP_ID}.svg": LOGO.read_text(encoding="utf-8"),
        data / "applications" / f"{APP_ID}.desktop": entry,
    }
    try:
        for path, text in files.items():
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    except OSError:
        pass
