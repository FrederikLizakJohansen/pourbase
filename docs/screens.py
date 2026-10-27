"""The app's screenshots in docs/assets/screens, in the light theme, as the tour walks through them.

    QT_QPA_PLATFORM=offscreen python docs/screens.py

The app keeps its settings in a temporary folder, so the screenshots do not depend on the user's own.
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QSettings, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "assets" / "screens"
out.mkdir(parents=True, exist_ok=True)
work = Path(tempfile.mkdtemp(prefix="pourbase-screens-"))

app = QApplication([])


def settle(ms: int = 400) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(widget, name: str) -> None:
    settle(150)
    widget.grab().save(str(out / f"{name}.png"))
    print(name)


with mock.patch("pourbase.gui.dft.load_key", return_value=("", "")):
    from pourbase.gui.window import MainWindow

    window = MainWindow(settings=QSettings(str(work / "settings.ini"), QSettings.IniFormat))
    window.resize(1600, 940)
    window.show()
    window.set_theme("Light")
    settle(1500)

    # the periodic table at pH 7 and 0 V, with iron selected
    window.pages.setCurrentIndex(0)
    window.overview.pH.setValue(7.0)
    window.overview.potential.setValue(0.0)
    window.update_overview()
    window.overview.canvas.set_selected("Fe")
    window.overview.canvas.hovered = "Fe"
    settle(800)
    shot(window, "periodic-table")

    # the same in 3D, columns as tall as the stability margin
    window.overview.canvas.hovered = None
    window.overview.set_3d(True)
    settle(1300)
    shot(window, "periodic-table-3d")
    window.overview.set_3d(False)
    settle(1300)

    # iron: the diagram with a probe, then the other views of the system
    window.open_element("Fe")
    settle(2500)
    window.set_probe(7.0, 0.0)
    settle(800)
    shot(window, "fe-diagram")
    for page, name in ((window.species_page, "fe-species"), (window.boundaries_page, "fe-boundaries"),
                       (window.sensitivity_page, "fe-sensitivity"), (window.speciation_page, "fe-speciation")):
        window.views.setCurrentWidget(page)
        settle(1500)
        shot(window, name)

    window.pages.setCurrentWidget(window.database_page)
    settle(1500)
    shot(window, "database")

    window.pages.setCurrentWidget(window.policy_page)
    settle(500)
    shot(window, "selection-policy")
    window.close()
