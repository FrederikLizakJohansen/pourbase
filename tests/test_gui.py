from __future__ import annotations

import os
import tempfile
import time
import unittest
from unittest import mock

import numpy as np

import support  # noqa: F401
from mp_fixtures import PYMATGEN, fake_fetcher

from pourbase.gui.state import LigandSetting, Session, Settings, SweepSettings

try:
    import pourbase.gui.dft  # noqa: F401  (patched below)
except ImportError:
    pass

try:
    from PySide6.QtWidgets import QApplication
except ImportError:
    QApplication = None


class StateTests(unittest.TestCase):
    """The Qt-independent application state."""

    def test_settings_round_trip_and_reject_invalid_values(self) -> None:
        settings = Settings(symbol="Zn", mode="mass_balance", davies=True)
        settings.ligands["chloride-cl"] = LigandSetting(enabled=True)
        restored = Settings.from_dict({**settings.to_dict(), "obsolete": 1})
        self.assertEqual(restored.scenario(), settings.scenario())
        self.assertEqual(Settings.from_dict({"pH_min": 20}).pH_min, 0.0)
        self.assertTrue(Settings().allow_incomplete)

    def test_python_code_reproduces_the_diagram(self) -> None:
        settings = Settings(symbol="Ag", concentration=10.0, concentration_unit="ppm", pH_points=41, eh_points=43)
        settings.ligands["chloride-cl"] = LigandSetting(enabled=True, mode="total", use_pKa=True)
        namespace: dict = {}
        exec(settings.python_code().replace("pb.plot_diagram(calculation.diagram)", ""), namespace)
        expected = Session().calculate(settings.scenario()).diagram.stable_species_index
        np.testing.assert_array_equal(namespace["calculation"].diagram.stable_species_index, expected)

    def test_session_caches_calculations_and_sweeps(self) -> None:
        session = Session()
        scenario = Settings(pH_points=21, eh_points=21).scenario()
        self.assertIs(session.calculate(scenario), session.calculate(scenario))
        sweep_settings = SweepSettings(levels=4, pH_points=21, eh_points=21)
        sweep = session.sweep(sweep_settings.scenario(Settings()), sweep_settings)
        self.assertIs(session.cached("sweep", (sweep_settings.scenario(Settings()), sweep_settings)), sweep)


@unittest.skipIf(QApplication is None, "PySide6 is not installed")
class WindowTestCase(unittest.TestCase):
    """A fresh window per test class, with isolated stored settings."""

    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtCore import QSettings

        from pourbase.gui.window import MainWindow

        cls.app = QApplication.instance() or QApplication([])
        cls.directory = tempfile.TemporaryDirectory()
        stored = QSettings(os.path.join(cls.directory.name, "settings.ini"), QSettings.IniFormat)
        # Keep the user's stored Materials Project key out of the tests: no network access.
        cls._no_key = mock.patch("pourbase.gui.dft.load_key", return_value=("", ""))
        cls._no_key.start()
        cls.window = MainWindow(settings=stored)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.window.close()
        cls._no_key.stop()
        cls.directory.cleanup()

    def open(self, symbol: str, **values) -> None:
        settings = Settings(symbol=symbol, **values)
        self.window.panel.set_settings(settings)
        self.window.recalculate()

    def wait(self, condition, timeout: float = 30) -> None:
        deadline = time.monotonic() + timeout
        while not condition() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        self.app.processEvents()


class WindowTests(WindowTestCase):
    def test_every_view_updates(self) -> None:
        window = self.window
        self.open("Fe", mode="mass_balance")
        window.set_probe(10.0, -0.3)
        self.assertIn("hematite", window.diagram_page.probe.toPlainText())
        for index in range(window.views.count()):
            window.views.setCurrentIndex(index)
            self.app.processEvents()
        window.views.setCurrentWidget(window.species_page)
        window.species_page.table.selectRow(0)
        self.assertTrue(window.species_page.details.toPlainText())

    def test_unavailable_views_explain_and_offer_the_change(self) -> None:
        window = self.window
        self.open("Fe")
        window.views.setCurrentWidget(window.speciation_page)
        self.assertIs(window.speciation_page.currentWidget(), window.speciation_page.placeholder)
        window.speciation_page.placeholder.button.click()
        self.assertEqual(window.settings.mode, "mass_balance")
        self.assertIs(window.speciation_page.currentWidget(), window.speciation_page.view)
        window.views.setCurrentWidget(window.boundaries_page)
        self.assertIs(window.boundaries_page.currentWidget(), window.boundaries_page.placeholder)

    def test_incomplete_system_offers_an_exploratory_diagram(self) -> None:
        window = self.window
        self.open("Pt", allow_incomplete=False)
        self.assertIs(window.diagram_page.currentWidget(), window.diagram_page.placeholder)
        window.diagram_page.placeholder.button.click()
        window.recalculate()
        self.assertEqual(window.calculation.diagram.system.symbol, "Pt")

    def test_unit_change_keeps_the_concentration(self) -> None:
        window = self.window
        self.open("Fe")
        molar = window.calculation.concentration.molar_concentration
        for index in range(window.panel.unit.count()):
            window.panel.unit.setCurrentIndex(index)
            window.recalculate()
            self.assertAlmostEqual(window.calculation.concentration.molar_concentration / molar, 1.0, places=6)

    def test_ligands_are_shown_for_the_element_and_add_complexes(self) -> None:
        window = self.window
        self.open("Ag")
        rows = window.panel.ligands.rows
        self.assertTrue(rows["chloride-cl"].isVisibleTo(window.panel))
        self.assertFalse(rows["cyanide-cn"].isVisibleTo(window.panel))
        rows["chloride-cl"].enabled.setChecked(True)
        window.recalculate()
        self.assertTrue({"AgCl", "AgCl₂⁻"} & {item.species for item in window.calculation.stable_species})

    def test_periodic_table_opens_every_system_it_shows(self) -> None:
        window = self.window
        for allow, fallbacks in ((False, False), (True, False), (False, True)):
            self.open("Fe", allow_incomplete=allow, use_mp_fallbacks=fallbacks)
            window.pages.setCurrentIndex(0)
            window.overview.pH.setValue(12.0)
            window.update_overview()
            screen = window.overview.canvas.screen
            self.assertEqual(screen.pH, 12.0)
            self.assertTrue(screen.element("In").status.has_system)
            self.assertIs(window.overview.allow_incomplete.isChecked(), allow)
        window.overview.allow_incomplete.setChecked(True)
        self.assertTrue(window.settings.allow_incomplete)
        window.open_element("Cu")
        self.assertEqual((window.settings.symbol, window.pages.currentIndex()), ("Cu", 1))
        self.assertAlmostEqual(window.settings.probe_pH, 12.0)

    def test_sweep_runs_in_the_background_and_is_cached(self) -> None:
        window = self.window
        self.open("Fe")
        window.views.setCurrentWidget(window.sweep_stack)
        self.wait(lambda: window.sweep_stack.currentWidget() is window.sweep_page)
        page = window.sweep_page
        sweep = page.sweep
        self.assertEqual(len(sweep.diagrams), page.slice_counts["level"].value())
        for axis, count in (("pH", sweep.pH.size), ("eh", sweep.eh_V.size)):
            page.set_axis(axis)
            self.assertEqual(page.slider.maximum(), count - 1)
            page.slider.setValue(10)
            self.assertIsNotNone(page.volume.image(axis, 10))
        page.set_axis("level")
        window.views.setCurrentIndex(0)
        window.views.setCurrentWidget(window.sweep_stack)
        self.assertIs(page.sweep, sweep)
        page.slice_counts["level"].setValue(41)
        self.wait(lambda: page.sweep is not sweep and len(page.sweep.diagrams) == 41)
        self.assertEqual(len(page.sweep.diagrams), 41)

    def test_database_tab(self) -> None:
        window = self.window
        window.pages.setCurrentWidget(window.database_page)
        window.database_page.tables.setCurrentText("sources")
        window.database_page.filter.setText("JANAF")
        self.assertGreater(window.database_page.proxy.rowCount(), 0)


@unittest.skipUnless(QApplication is not None and PYMATGEN, "PySide6 or pymatgen is not installed")
class DftTests(WindowTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._available = mock.patch("pourbase.gui.dft.client_available", return_value=True)
        cls._available.start()
        super().setUpClass()
        cls.window.dft.api_key = "test-key"
        cls.window.dft.source.fetcher = fake_fetcher

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls._available.stop()

    def test_comparison_speciation_and_sweep(self) -> None:
        window = self.window
        self.open("Fe")
        window.views.setCurrentWidget(window.dft_stack)
        self.wait(lambda: window.dft_stack.currentWidget() is window.dft_page)
        self.assertEqual(window.comparison.materials_project.database_version, "test-db")
        self.assertGreater(window.dft_page.pairs.rowCount(), 0)
        window.views.setCurrentWidget(window.diagram_page)
        window.set_probe(7.0, 0.0)
        self.assertIn("DFT (MP)", window.diagram_page.probe.toPlainText())
        self.open("Fe", mode="mass_balance")
        window.views.setCurrentWidget(window.speciation_page)
        self.assertTrue(window.speciation_page.button.isHidden())
        window.views.setCurrentWidget(window.sweep_stack)
        self.wait(lambda: window.sweep_page.sweep is not None and window.sweep_stack.currentWidget() is window.sweep_page)
        window.sweep_page.set_source("materials_project")
        self.wait(lambda: "materials_project" in window.sweep_page.volumes)
        window.sweep_page.set_source("agreement")
        window.sweep_page.set_axis("pH")
        self.assertIs(window.sweep_page.view3d.volume, window.sweep_page.volumes["agreement"])


if __name__ == "__main__":
    unittest.main()
