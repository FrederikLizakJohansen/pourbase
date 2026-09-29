from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pourbase.gui.engine import Engine, Parameters  # noqa: E402

try:
    import pyqtgraph  # noqa: F401
    from PySide6.QtWidgets import QApplication
except ImportError:
    QApplication = None


class GuiEngineTests(unittest.TestCase):
    """The Qt-independent calculation layer of the desktop application."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = Engine()

    def test_parameters_round_trip_and_ignore_unknown_keys(self) -> None:
        parameters = Parameters(symbol="Zn", mode="mass_balance", davies=True)
        restored = Parameters.from_dict({**parameters.to_dict(), "obsolete": 1, "resolution": "?"})
        self.assertEqual(restored.symbol, "Zn")
        self.assertTrue(restored.davies)
        self.assertEqual(restored.resolution, "Standard")

    def test_display_only_changes_reuse_the_calculated_grid(self) -> None:
        parameters = Parameters(resolution="Preview")
        diagram, _ = self.engine.compute(parameters)
        parameters.probe_pH = 3.0
        self.assertIs(self.engine.compute(parameters)[0], diagram)
        parameters.concentration_value = -4.0
        self.assertIsNot(self.engine.compute(parameters)[0], diagram)

    def test_mass_balance_probe_reports_inventory(self) -> None:
        parameters = Parameters(mode="mass_balance", resolution="Preview")
        diagram, _ = self.engine.compute(parameters)
        probe = self.engine.probe(diagram, 10.0, 0.0)
        self.assertIn("dissolved_metal_mol_L", probe)
        self.assertAlmostEqual(sum(item["metal_fraction"] for item in probe["speciation"]), 1.0)

    def test_python_code_reproduces_the_diagram(self) -> None:
        parameters = Parameters(symbol="Cu", concentration_value=10.0, concentration_unit="ppm",
                                resolution="Preview")
        diagram, _ = self.engine.compute(parameters)
        namespace: dict = {}
        exec(parameters.python_code().replace("plot_diagram(diagram)", ""), namespace)
        self.assertTrue(
            (namespace["diagram"].stable_species_index == diagram.stable_species_index).all()
        )


@unittest.skipIf(QApplication is None, "PySide6 and pyqtgraph are not installed")
class GuiWindowTests(unittest.TestCase):
    """Drive the main window offscreen through every view."""

    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtCore import QSettings

        from pourbase.gui.window import MainWindow

        cls.app = QApplication.instance() or QApplication([])
        cls.directory = tempfile.TemporaryDirectory()
        settings = QSettings(os.path.join(cls.directory.name, "settings.ini"), QSettings.IniFormat)
        cls.window = MainWindow(settings=settings)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.window.close()
        cls.directory.cleanup()

    def setUp(self) -> None:
        window = self.window
        window.incomplete_check.setChecked(False)
        for row in window.ligand_panel.rows.values():
            row.enabled.setChecked(False)
        window.mode_combo.setCurrentIndex(window.mode_combo.findData("fixed_activity"))
        window.symbol_combo.setCurrentIndex(window.symbol_combo.findData("Fe"))
        window.recalculate()

    def _wait_for_sweep(self) -> None:
        import time

        deadline = time.monotonic() + 20
        while self.window._sweep_pending and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        self.app.processEvents()

    def test_views_update_without_errors(self) -> None:
        window = self.window
        window.set_probe(10.0, -0.3)
        self.assertIn("hematite", window.probe_text.toPlainText())
        window.mode_combo.setCurrentIndex(window.mode_combo.findData("mass_balance"))
        window.recalculate()
        for index in range(window.views.count()):
            window.views.setCurrentIndex(index)
            self.app.processEvents()
        window.species_table.selectRow(0)
        self.assertTrue(window.species_details.toPlainText())
        window.table_combo.setCurrentText("sources")
        window.table_filter.setText("JANAF")
        self.assertGreater(window.table_proxy.rowCount(), 0)

    def test_unavailable_views_show_an_explanation_with_an_action(self) -> None:
        window = self.window
        window.views.setCurrentWidget(window.speciation_stack)
        self.assertIs(window.speciation_stack.currentWidget(), window.speciation_stack.placeholder)
        window.speciation_stack.placeholder.button.click()
        self.assertEqual(window.params.mode, "mass_balance")
        self.assertIs(window.speciation_stack.currentWidget(), window.speciation_stack.view)
        window.views.setCurrentWidget(window.boundary_stack)
        self.assertIs(window.boundary_stack.currentWidget(), window.boundary_stack.placeholder)

    def test_periodic_table_opens_a_system(self) -> None:
        window = self.window
        window.pages.setCurrentIndex(0)
        window.periodic_pH.setValue(12.0)
        window.update_periodic_table()
        self.assertEqual(window.periodic_canvas.screen["conditions"]["pH"], 12.0)
        window.open_element("Cu")
        self.assertEqual(window.params.symbol, "Cu")
        self.assertEqual(window.pages.currentIndex(), 1)
        self.assertAlmostEqual(window.params.probe_pH, 12.0)

    def test_every_calculated_tile_opens_its_system(self) -> None:
        window = self.window
        canvas = window.periodic_canvas
        for allow, fallbacks in ((False, False), (True, False), (False, True)):
            window.incomplete_check.setChecked(allow)
            window.fallback_check.setChecked(fallbacks)
            window.update_periodic_table()
            for element in canvas.screen["elements"]:
                if element["status"].startswith("calculated") or element["status"] == "incomplete":
                    self.assertTrue(canvas.clickable(element), element["symbol"])
            self.assertTrue(canvas.clickable(canvas.elements["In"]))
        window.fallback_check.setChecked(False)

    def test_sweep_is_calculated_in_the_background_and_cached(self) -> None:
        window = self.window
        window.views.setCurrentWidget(window.sweep_stack)
        self._wait_for_sweep()
        self.assertIs(window.sweep_stack.currentWidget(), window.sweep_page)
        sweep = window.sweep_page.sweep
        self.assertEqual(len(sweep.diagrams), window.sweep_page.points.value())
        window.sweep_page.slider.setValue(2)
        self.assertEqual(window.sweep_page.view3d.selected, 2)
        for axis, count in (("pH", sweep.pH.size), ("eh", sweep.eh_V.size)):
            window.sweep_page.set_axis(axis)
            self.assertEqual(window.sweep_page.slider.maximum(), count - 1)
            window.sweep_page.slider.setValue(10)
            self.assertEqual(window.sweep_page.view3d.axis, axis)
            self.assertIsNotNone(window.sweep_page.volume.image(axis, 10))
        window.sweep_page.set_axis("level")
        self.assertEqual(window.sweep_page.slider.value(), 2)
        window.views.setCurrentIndex(0)
        window.views.setCurrentWidget(window.sweep_stack)
        self.assertIs(window.sweep_page.sweep, sweep)
        window.sweep_page.points.setValue(81)
        self._wait_for_sweep()
        self.assertEqual(len(window.sweep_page.sweep.diagrams), 81)
        self.assertEqual(window.sweep_page.sweep.diagrams[0].stable_species_index.dtype.itemsize, 2)

    def test_database_is_a_global_tab(self) -> None:
        window = self.window
        window.pages.setCurrentWidget(window.database_page)
        window.table_combo.setCurrentText("species")
        self.assertGreater(window.table_proxy.rowCount(), 400)

    def test_ligands_add_complexes(self) -> None:
        window = self.window
        window.symbol_combo.setCurrentIndex(window.symbol_combo.findData("Ag"))
        window.recalculate()
        row = window.ligand_panel.rows["chloride-cl"]
        self.assertTrue(row.enabled.isVisibleTo(window.ligand_panel))
        self.assertFalse(window.ligand_panel.rows["cyanide-cn"].enabled.isVisibleTo(window.ligand_panel))
        row.enabled.setChecked(True)
        window.recalculate()
        self.assertIn("AgCl", [item["species"] for item in window.result["stable_species"]])
        row.enabled.setChecked(False)

    def test_unit_change_keeps_the_concentration(self) -> None:
        window = self.window
        molar = window.result["concentration_input"]["molar_concentration"]
        for index in range(window.unit_combo.count()):
            window.unit_combo.setCurrentIndex(index)
            window.recalculate()
            self.assertAlmostEqual(
                window.result["concentration_input"]["molar_concentration"] / molar, 1.0, places=6
            )

    def test_incomplete_system_reports_an_error_and_keeps_the_last_diagram(self) -> None:
        window = self.window
        window.symbol_combo.setCurrentIndex(window.symbol_combo.findData("Pt"))
        window.recalculate()
        self.assertIs(window.diagram_stack.currentWidget(), window.diagram_stack.placeholder)
        window.diagram_stack.placeholder.button.click()
        window.recalculate()
        self.assertEqual(window.diagram.system.symbol, "Pt")


if __name__ == "__main__":
    unittest.main()


sys.path.insert(0, str(Path(__file__).resolve().parent))
from mp_fixtures import PYMATGEN, fake_fetcher  # noqa: E402


@unittest.skipUnless(PYMATGEN, "pymatgen is not installed")
class MaterialsProjectSourceTests(unittest.TestCase):
    def test_entries_are_evaluated_at_each_activity(self) -> None:
        from pourbase.gui.materials import MaterialsProjectSource, pretty_label
        from pourbase.models import AqueousActivityModel, PourbaixConditions

        source = MaterialsProjectSource(fetcher=fake_fetcher)
        fetched = source.fetch("Fe", "key", True, False)
        self.assertIs(source.fetch("Fe", "key", True, False), fetched)
        shares = []
        for level in (-8.0, -1.0):
            diagram = source.diagram(fetched, PourbaixConditions(
                pH_points=41, eh_points=41,
                aqueous_activities=AqueousActivityModel(default_log10_activity=level),
            ))
            ions = [i for i, phase in enumerate(diagram.phases) if phase.phase_type == "aqueous"]
            shares.append(float((diagram.stable_phase_index[..., None] == ions).any(-1).mean()))
        self.assertGreater(shares[0], shares[1])
        self.assertEqual(pretty_label("FeO4[-2]"), "FeO₄²⁻")
        self.assertEqual(pretty_label("Fe[+2]"), "Fe²⁺")
        self.assertEqual(pretty_label("Fe2O3(s)"), "Fe₂O₃(s)")


@unittest.skipIf(QApplication is None or not PYMATGEN, "PySide6, pyqtgraph or pymatgen missing")
class MaterialsProjectWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtCore import QSettings

        from pourbase.gui.materials import MaterialsProjectSource
        from pourbase.gui.window import MainWindow

        cls.app = QApplication.instance() or QApplication([])
        cls.directory = tempfile.TemporaryDirectory()
        settings = QSettings(os.path.join(cls.directory.name, "settings.ini"), QSettings.IniFormat)
        cls.window = MainWindow(settings=settings)
        cls.window.mp_key = "test-key"
        cls.window.mp_source = MaterialsProjectSource(fetcher=fake_fetcher)
        cls._available = mock.patch("pourbase.gui.window.client_available", return_value=True)
        cls._available.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._available.stop()
        cls.window.close()
        cls.directory.cleanup()

    def wait(self, condition) -> None:
        import time

        deadline = time.monotonic() + 30
        while not condition() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        self.app.processEvents()

    def test_comparison_tab_speciation_and_sweep(self) -> None:
        window = self.window
        window.open_element("Fe")
        window.views.setCurrentWidget(window.mp_stack)
        self.wait(lambda: window.mp_stack.currentWidget() is window.mp_page)
        self.assertIs(window.mp_stack.currentWidget(), window.mp_page)
        comparison = window.mp_comparison
        self.assertEqual(comparison.materials_project.database_version, "test-db")
        self.assertGreater(window.mp_page.pairs.rowCount(), 0)
        window.set_probe(7.0, 0.0)
        self.assertIn("DFT (MP)", window.probe_text.toPlainText())

        window.mode_combo.setCurrentIndex(window.mode_combo.findData("mass_balance"))
        window.recalculate()
        window.views.setCurrentWidget(window.speciation_stack)
        self.assertTrue(window.speciation_mp_button.isHidden())

        window.views.setCurrentWidget(window.sweep_stack)
        self.wait(lambda: not window._sweep_pending and window.sweep_page.sweep is not None)
        window.sweep_page.set_source("materials_project")
        self.wait(lambda: "materials_project" in window.sweep_page.volumes)
        self.assertIn("agreement", window.sweep_page.volumes)
        window.sweep_page.set_source("agreement")
        window.sweep_page.set_axis("pH")
        self.assertEqual(window.sweep_page.view3d.volume, window.sweep_page.volumes["agreement"])
