"""The app's screenshots in docs/assets/screens, in the light theme, and in docs/assets/screens/dark.

    QT_QPA_PLATFORM=offscreen python docs/screens.py            # both themes
    QT_QPA_PLATFORM=offscreen python docs/screens.py Dark       # one theme

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

THEMES = {"Light": Path(__file__).parent / "assets" / "screens", "Dark": Path(__file__).parent / "assets" / "screens" / "dark"}
themes = sys.argv[1:] or list(THEMES)
work = Path(tempfile.mkdtemp(prefix="pourbase-screens-"))

app = QApplication([])


def settle(ms: int = 400) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(widget, name: str) -> None:
    settle(150)
    widget.grab().save(str(THEMES[theme] / f"{name}.png"))
    print(name)


with mock.patch("pourbase.gui.dft.load_key", return_value=("", "")):
    from pourbase import MeasuredPoint, SelectionPolicy
    from pourbase.gui.policy_compare import PolicyComparisonDialog
    from pourbase.gui.search import SearchDialog
    from pourbase.gui.sources_dialog import SourcesDialog
    from pourbase.gui.window import MainWindow

    for theme in themes:
        THEMES[theme].mkdir(parents=True, exist_ok=True)
        window = MainWindow(settings=QSettings(str(work / "settings.ini"), QSettings.IniFormat))
        window.resize(1600, 940)
        window.show()
        window.set_theme(theme)
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
        for page, name, wait in ((window.species_page, "fe-species", 1500), (window.boundaries_page, "fe-boundaries", 1500),
                                 (window.sensitivity_page, "fe-sensitivity", 25000)):
            window.views.setCurrentWidget(page)
            settle(wait)
            shot(window, name)

        window.pages.setCurrentWidget(window.database_page)
        settle(1500)
        shot(window, "database")

        window.pages.setCurrentWidget(window.policy_page)
        settle(500)
        shot(window, "selection-policy")

        # the other color modes of the periodic table
        window.pages.setCurrentIndex(0)
        for key, name in (("margin", "periodic-table-margin"), ("window", "periodic-table-window")):
            color = window.overview.color
            color.setCurrentIndex(color.findData(key))
            settle(2500)
            shot(window, name)
        color.setCurrentIndex(color.findData("category"))
        settle(1000)

        # the settings tabs and the tools under the iron diagram
        window.open_element("Fe")
        settle(2000)
        panel, page = window.panel, window.diagram_page
        window.views.setCurrentWidget(page)
        for index, name in ((1, "settings-axes"), (2, "settings-display"), (0, "settings-system")):
            panel.setCurrentIndex(index)
            settle(400)
            shot(window, name)
        page.tools.setCurrentWidget(page.path_panel)
        page.path_panel.set_vertices([(2.0, 1.2), (6.0, 0.2), (12.0, -0.7)])
        settle(1500)
        shot(window, "fe-path")
        page.path_panel.set_vertices([])
        page.tools.setCurrentWidget(page.points_panel)
        page.points_panel.set_points([MeasuredPoint("A", 3.0, 0.9), MeasuredPoint("B", 7.0, -0.2),
                                      MeasuredPoint("C", 9.5, -0.75), MeasuredPoint("D", 12.0, 0.4)])
        settle(1500)
        shot(window, "fe-points")
        page.points_panel.set_points([])
        page.tools.setCurrentWidget(page.region_panel)
        target = page.region_panel.target
        target.setCurrentIndex(target.findData("passivation"))
        page.region_panel.margin.setValue(5.0)
        settle(1500)
        shot(window, "fe-region")
        target.setCurrentIndex(0)
        page.tools.setCurrentIndex(0)

        # display options
        panel.setCurrentIndex(2)
        panel.uncertainty.setChecked(True)
        settle(1500)
        shot(window, "fe-hatching")
        panel.uncertainty.setChecked(False)
        panel.boltzmann.setChecked(True)
        settle(1500)
        shot(window, "fe-blend")
        panel.boltzmann.setChecked(False)
        panel.setCurrentIndex(0)
        panel.overlay.setCurrentIndex(panel.overlay.findData("Ni"))
        settle(1500)
        shot(window, "fe-overlay")
        panel.overlay.setCurrentIndex(0)
        settle(800)

        # the views that need other settings
        window.views.setCurrentWidget(window.compare_page)
        window.compare_page.symbol.setCurrentIndex(window.compare_page.symbol.findData("Ni"))
        settle(3000)
        shot(window, "fe-compare")
        window.views.setCurrentWidget(window.sweep_stack)
        settle(6000)
        shot(window, "fe-sweep")
        window.views.setCurrentWidget(window.fixed_page)
        settle(2000)
        shot(window, "fe-solubility")
        panel.mode.setCurrentIndex(panel.mode.findData("mass_balance"))
        settle(2500)
        window.views.setCurrentWidget(window.speciation_page)
        settle(2500)
        shot(window, "fe-speciation")
        window.views.setCurrentWidget(page)
        settle(2000)
        shot(window, "fe-mass-balance")
        panel.mode.setCurrentIndex(panel.mode.findData("fixed_activity"))
        settle(1500)

        # silver in seawater: ligand predominance at the probe potential
        window.open_element("Ag")
        settle(2000)
        panel.apply_water("seawater")
        window.set_probe(8.1, 0.6)
        settle(2000)
        window.views.setCurrentWidget(page)
        settle(2000)
        shot(window, "ag-seawater")
        window.views.setCurrentWidget(window.fixed_page)
        window.fixed_page.predominance_button.setChecked(True)
        ligand = window.fixed_page.ligand
        ligand.setCurrentIndex(max(ligand.findData("chloride-cl"), 0))
        settle(2500)
        shot(window, "ag-ligand-predominance")

        # dialogs
        window.open_element("Fe")
        panel.apply_water("pure")
        settle(2000)
        dialog = SourcesDialog(window.calculation, window.system_name("Fe"), window)
        dialog.show()
        shot(dialog, "sources")
        dialog.close()
        example = Path(__file__).resolve().parents[1] / "paper" / "examples" / "example-policy.toml"
        if example.is_file():
            dialog = PolicyComparisonDialog(window.database, SelectionPolicy.load(example), str(example), window)
            dialog.show()
            settle(2500)
            shot(dialog, "policy-comparison")
            dialog.close()
        dialog = SearchDialog(window._search_entries(), window)
        dialog.show()
        dialog.field.setText("hematite")
        settle(800)
        shot(dialog, "search")
        dialog.close()
        window.close()
