from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path
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
        settings = Settings(symbol="Ag", concentration=10.0, concentration_unit="ppm", pH_points=41, U_points=43)
        settings.ligands["chloride-cl"] = LigandSetting(enabled=True, mode="total", use_pKa=True)
        namespace: dict = {}
        exec(settings.python_code().replace("pb.plot_diagram(calculation.diagram)", ""), namespace)
        expected = Session().calculate(settings.scenario()).diagram.stable_species_index
        np.testing.assert_array_equal(namespace["calculation"].diagram.stable_species_index, expected)

    def test_session_caches_calculations_and_sweeps(self) -> None:
        session = Session()
        scenario = Settings(pH_points=21, U_points=21).scenario()
        self.assertIs(session.calculate(scenario), session.calculate(scenario))
        sweep_settings = SweepSettings(levels=4, pH_points=21, U_points=21)
        sweep = session.sweep(sweep_settings.scenario(Settings()), sweep_settings)
        self.assertIs(session.cached("sweep", (sweep_settings.scenario(Settings()), sweep_settings)), sweep)


@unittest.skipIf(QApplication is None, "PySide6 is not installed")
class SpeciesLabelTests(unittest.TestCase):
    def test_composition_preserves_ionic_charge_and_fractional_formula_units(self):
        from pourbase.gui.formula import composition_text

        self.assertEqual(composition_text("Al(OH)3"), "Al(OH)₃")
        self.assertEqual(composition_text("Al", 3), "Al³⁺")
        self.assertEqual(composition_text("Fe(CN)6", -4), "Fe(CN)₆⁴⁻")
        self.assertEqual(composition_text("Fe0.932O"), "Fe₀.₉₃₂O")
        self.assertEqual(composition_text("CaSO4(H2O)0.5"), "CaSO₄(H₂O)₀.₅")

    def test_phase_parentheses_and_distinct_identities_are_preserved(self):
        from types import SimpleNamespace
        from pourbase.gui.formula import phase_label, species_label

        phase = "bunsenite (average cubic rocksalt)"
        self.assertEqual(phase_label(SimpleNamespace(phase_detail=phase, phase="solid")), phase)
        self.assertEqual(species_label("Al(OH)3", 0, "gibbsite"), "Al(OH)₃ — gibbsite")
        self.assertEqual(species_label("Al(OH)3", 0, "bayerite"), "Al(OH)₃ — bayerite")

    def test_reaction_formulas_come_from_composition_and_charge(self):
        from PySide6.QtGui import QTextDocument
        import pourbase as pb
        from pourbase.gui.diagram_tools import reaction_html

        document = QTextDocument()
        document.setHtml(reaction_html("nitrogen-n2-gas + nickel-ni2 + silica-sio2-component",
                                       pb.ThermodynamicDatabase.bundled()))
        text = document.toPlainText()
        self.assertEqual(text, "N2 + Ni2+ + SiO2")


@unittest.skipIf(QApplication is None, "PySide6 is not installed")
class ScaleAndSessionTests(unittest.TestCase):
    """Potential scales and session files, without Qt widgets."""

    def test_scales_round_trip_and_rhe_resampling(self) -> None:
        from pourbase.gui.scales import REFERENCE_ELECTRODES_V, from_scale, resample, to_scale

        for scale in REFERENCE_ELECTRODES_V:
            self.assertAlmostEqual(float(from_scale(to_scale(0.3, 9.0, scale), 9.0, scale)), 0.3)
        self.assertAlmostEqual(float(to_scale(0.0, 0.0, "SCE (sat. KCl)")), -0.241)
        pH, U = np.linspace(0, 14, 15), np.linspace(-1, 1, 201)
        axis, rows, valid = resample(pH, U, "RHE")
        self.assertTrue(valid[:, 0].all())
        self.assertFalse(valid[:, -1].all())
        column = 7
        self.assertAlmostEqual(U[rows[150, column]], float(from_scale(axis[150], pH[column], "RHE")), delta=0.006)

    @unittest.skipIf(QApplication is None, "PySide6 is not installed")
    def test_session_round_trip_and_rejects_other_files(self) -> None:
        from pourbase.gui.plots import DisplayOptions
        from pourbase.gui.session import SessionError, read_session, sidecar_path, write_session

        settings = Settings(symbol="Cu", concentration=-4.0, probe_pH=9.0)
        display = DisplayOptions(potential_scale="RHE", uncertainty=True, uncertainty_sigma=2.0)
        sweep = SweepSettings(levels=11)
        with tempfile.TemporaryDirectory() as directory:
            path = write_session(os.path.join(directory, "a.pourbase.json"), settings, display, sweep)
            self.assertEqual(read_session(path), (settings, display, sweep))
            other = os.path.join(directory, "other.json")
            with open(other, "w") as handle:
                handle.write('{"format": "something else"}')
            with self.assertRaises(SessionError):
                read_session(other)
        self.assertEqual(sidecar_path("/tmp/fe.png").name, "fe.pourbase.json")


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

    def test_scale_uncertainty_probe_and_compare(self) -> None:
        window = self.window
        self.open("Fe")
        panel = window.panel
        panel.potential_scale.setCurrentIndex(panel.potential_scale.findData("RHE"))
        panel.uncertainty.setChecked(True)
        self.app.processEvents()
        view = window.diagram_page.diagram
        self.assertEqual(view.scale, "RHE")
        self.assertIsNotNone(view.uncertainty)
        # The probe is placed and reported against the SHE whatever the axis shows
        window.set_probe(7.0, 0.1)
        view._probe_moved()
        self.assertAlmostEqual(window.settings.probe_U_V, 0.1, places=6)
        text = window.diagram_page.probe.toPlainText()
        self.assertIn("Next lowest is", text)
        self.assertIn("V vs RHE", text)
        window.views.setCurrentWidget(window.compare_page)
        self.app.processEvents()
        self.assertIn("differs on", window.compare_page.summary.text())
        compare = window.compare_page
        compare.views[0].probe.setPos(compare.views[0].probe.pos().__class__(10.0, 0.8))
        compare.views[0]._probe_moved()
        self.assertAlmostEqual(compare.point[0], 10.0)
        self.assertIn("species", compare.details.toPlainText())
        self.assertAlmostEqual(compare.views[1].probe.pos().x(), 10.0)
        panel.set_display(type(window.display)())
        window.refresh_view()

    def test_session_file_restores_the_settings(self) -> None:
        from pourbase.gui.plots import DisplayOptions
        from pourbase.gui.session import write_session

        window = self.window
        path = os.path.join(self.directory.name, "zn.pourbase.json")
        write_session(path, Settings(symbol="Zn", concentration=-5.0),
                      DisplayOptions(potential_scale="SCE (sat. KCl)"), SweepSettings(levels=9))
        self.assertTrue(window.load_session(path))
        self.assertEqual(window.settings.symbol, "Zn")
        self.assertEqual(window.display.potential_scale, "SCE (sat. KCl)")
        self.assertEqual(window.sweep_page.settings().levels, 9)
        window.panel.set_display(DisplayOptions())

    def test_a_custom_selection_policy_changes_the_calculation_and_the_species_tab(self) -> None:
        import pourbase as pb

        window = self.window
        text = pb.SelectionPolicy.default().source_text.replace(
            'families = ["NBS Tables", "NBS Technical Notes", "NIST-JANAF"',
            'families = ["NIST-JANAF", "NBS Tables", "NBS Technical Notes"').replace(
            'name = "pourbase default"', 'name = "JANAF first"')
        text += ('\n[[overrides]]\nrecord_id = "gfe-fe-fe2o3-q+0-solid-hematite"\n'
                 'property = "gibbs_energy_of_formation"\nsource_id = "NIST_JANAF_Fe-030"\n'
                 'reason = "Test selects the retained JANAF hematite evaluation"\n')
        path = os.path.join(self.directory.name, "janaf-first.toml")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        self.open("Fe")
        hematite = "gfe-fe-fe2o3-q+0-solid-hematite"
        default_value = next(item for item in window.calculation.diagram.system.species
                             if item.record_id == hematite).gibbs_energy_J_mol
        self.assertTrue(window.load_policy(path))
        species = {item.record_id: item for item in window.calculation.diagram.system.species}
        self.assertEqual(species[hematite].gibbs_energy_J_mol, -743523.0)
        self.assertNotEqual(default_value, -743523.0)
        window.views.setCurrentWidget(window.species_page)
        self.app.processEvents()
        row = next(index for index in range(window.species_page.table.rowCount())
                   if window.species_page.table.item(index, window.species_page.RECORD).text() == hematite)
        window.species_page.table.selectRow(row)
        self.assertIn("JANAF first", window.species_page.details.toPlainText())
        self.assertIn("Test selects the retained JANAF hematite evaluation",
                      window.species_page.details.toPlainText())
        self.assertTrue(window.load_policy(None))
        species = {item.record_id: item for item in window.calculation.diagram.system.species}
        self.assertEqual(species[hematite].gibbs_energy_J_mol, default_value)

    def test_a_dataset_opens_on_its_own_in_a_new_window(self) -> None:
        path = os.path.join(self.directory.name, "copper.csv")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("symbol,species,formula,charge,phase,gibbs_energy_kJ_mol,uncertainty_kJ_mol,citation,replaces\n"
                         "Cu,Cu,Cu,0,solid,0,,reference,\nCu,Cu²⁺,Cu,2,aqueous,65.49,,notes,\n"
                         "Cu,CuO,CuO,0,solid,-129.7,,notes,\n")
        window = self.window.open_dataset(path)
        try:
            self.app.processEvents()
            self.assertEqual(list(window.systems), ["Cu"])
            self.assertEqual(window.settings.symbol, "Cu")
            self.assertEqual({item.species for item in window.calculation.diagram.system.species}, {"Cu", "Cu²⁺", "CuO"})
            self.assertIn("copper.csv", window.windowTitle())
        finally:
            window.close()

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
        self.assertTrue(window.panel.require_complete.isChecked())
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

    def test_component_names_and_activity_explanations_preserve_saved_settings(self) -> None:
        window = self.window
        rows = window.panel.ligands.rows
        expected = {"ammonia-nh3": "Ammonia (NH₃)", "calcium-ca2": "Calcium (Ca²⁺)",
                    "chloride-cl": "Chloride (Cl⁻)", "phosphate-po4": "Orthophosphate (PO₄³⁻)",
                    "nickel-ni2": "Nickel (Ni²⁺)", "potassium-k": "Potassium (K⁺)"}
        for key, label in expected.items():
            self.assertEqual(rows[key].enabled.text(), label)
        for key in ("carbon-graphite", "elemental-te-cr", "nitrogen-n2-gas"):
            self.assertIn("reservoir", rows[key].enabled.text())
        for key in ("ammonia-nh3", "carbon-graphite", "nitrogen-n2-gas"):
            row = rows[key]
            old = row.setting
            setting = LigandSetting(enabled=True, log10_free_activity=0.0)
            row.set_setting(setting)
            self.assertEqual(row.mode.currentData(), "free")
            self.assertEqual(row.setting.activity(key), setting.activity(key))
            self.assertTrue(row.value.toolTip())
            if key == "ammonia-nh3":
                self.assertIn("unbound", row.mode.toolTip())
                pool = LigandSetting(enabled=True, mode="total", total_unbound_mol_L=.03,
                                     use_pKa=True, acid_pKa=9.25)
                row.set_setting(pool)
                self.assertEqual(row.mode.currentData(), "total")
                self.assertIn("excluding ligand bound", row.value.toolTip())
                self.assertEqual(Settings.from_dict(Settings(ligands={key: pool}).to_dict()).ligands[key], pool)
            elif key == "nitrogen-n2-gas":
                self.assertIn("Fugacity", row.mode.currentText())
                self.assertIn("1 bar", row.value.toolTip())
            else:
                self.assertEqual(row.mode.currentText(), "Activity (log₁₀ a)")
                self.assertIn("unit activity", row.value.toolTip())
            row.set_setting(old)

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
        self.open("Fe")
        window.open_element("Cu")
        self.assertEqual((window.settings.symbol, window.pages.currentIndex()), ("Cu", 1))
        self.assertAlmostEqual(window.settings.probe_pH, 12.0)

    def test_ligands_switch_globally_from_the_periodic_table(self) -> None:
        window = self.window
        self.open("Cu")
        window.pages.setCurrentIndex(0)
        window.update_overview()
        menu = window.overview.ligand_actions
        self.assertIn("chloride-cl", menu)
        menu["chloride-cl"].setChecked(True)
        window.update_overview()
        self.assertTrue(window.settings.ligands["chloride-cl"].enabled)
        self.assertIn("chloride-cl", [item.ligand_id for item in window.settings.ligand_activities()])
        self.assertIn("1 on", window.overview.ligand_button.text())
        self.assertTrue(window.panel.ligands.rows["chloride-cl"].enabled.isChecked())
        window.recalculate()
        self.assertTrue(any(item.ligand_id == "chloride-cl" for item in window.calculation.diagram.system.species))
        menu[""].setChecked(False)
        window.update_overview()
        self.assertEqual(window.settings.ligand_activities(), ())
        self.assertTrue(window.settings.ligands["chloride-cl"].enabled)
        self.assertFalse(window.panel.use_ligands.isChecked())
        menu[""].setChecked(True)
        menu["chloride-cl"].setChecked(False)
        window.update_overview()

    def test_calculations_run_in_the_background_behind_a_loading_overlay(self) -> None:
        window = self.window
        self.open("Fe")
        settings = window.settings
        settings.concentration = -2.5
        window.panel.set_settings(settings)
        window.calculate_in_background()
        self.assertTrue(window.views_loading.active)
        self.wait(lambda: not window.views_loading.active)
        self.assertAlmostEqual(window.calculation.scenario.concentration, -2.5)
        window.views.setCurrentWidget(window.compare_page)
        self.app.processEvents()
        window.compare_page.concentration.setValue(-7.25)
        window._show_compare()
        self.wait(lambda: not window.compare_loading.active)
        right = window.compare_page.calculations[1]
        self.assertAlmostEqual(right.concentration.log10_standard_activity, -7.25)
        window.pages.setCurrentIndex(0)
        window.overview.pH.setValue(3.5)
        window.screen_in_background()
        self.wait(lambda: not window.overview_loading.active)
        self.assertEqual(window.overview.canvas.screen.pH, 3.5)
        window.pages.setCurrentIndex(1)

    def test_the_margin_landscape_rises_follows_a_sweep_and_lowers(self) -> None:
        window = self.window
        window.pages.setCurrentIndex(0)
        overview = window.overview
        overview.pH.setValue(0.0)
        overview.potential.setValue(1.6)
        window.update_overview()
        overview.set_3d(True)
        self.wait(lambda: overview.landscape.raise_amount == 1.0)
        self.assertIs(overview.stack.currentWidget(), overview.landscape)
        landscape = overview.landscape
        self.assertGreater(landscape._targets[landscape._symbols.index("Ir")], 0.0)
        overview.sweep_steps.setValue(5)
        overview.play_button.setChecked(True)
        self.wait(lambda: not overview.play_button.isChecked())
        self.assertAlmostEqual(overview.canvas.screen.pH, 14.0)
        overview.set_3d(False)
        self.wait(lambda: overview.stack.currentWidget() is overview.canvas)
        window.pages.setCurrentIndex(1)

    def test_the_policy_editor_checks_applies_and_reverts(self) -> None:
        from PySide6.QtWidgets import QMessageBox

        from pourbase.gui.policy_editor import check_policy
        from pourbase.selection import SelectionPolicy

        window = self.window
        page = window.policy_page
        default = SelectionPolicy.default().source_text
        self.assertEqual(page.text(), default)
        policy, issues = check_policy(default.replace('"recency"]', '"recentcy"]'))
        self.assertIsNone(policy)
        self.assertTrue(issues[0].error)
        self.assertEqual(issues[0].line, default[:default.index("tie_breaks =")].count("\n") + 1)
        a, b, c = (default.index(f'[[classes]]\nname = "{name}"') for name in "ABC")
        page.editor.setPlainText(default[:a] + default[b:c] + default[a:b] + default[c:])
        page.apply()
        self.assertEqual(Path(window.policy_path), window._edited_policy_path())
        self.assertEqual(window.policy.classes[0].name, "B")
        with mock.patch.object(QMessageBox, "warning", return_value=QMessageBox.Yes):
            page.revert()
        self.assertIsNone(window.policy_path)
        self.assertEqual(page.text(), default)

    def test_the_mouse_wheel_does_not_change_value_inputs(self) -> None:
        from PySide6.QtCore import QPoint, QPointF, Qt
        from PySide6.QtGui import QWheelEvent

        window = self.window
        self.open("Fe")
        for widget in (window.panel.concentration.spin, window.panel.concentration.slider,
                       window.panel.mode, window.compare_page.symbol):
            before = widget.value() if hasattr(widget, "value") else widget.currentIndex()
            event = QWheelEvent(QPointF(5, 5), QPointF(5, 5), QPoint(0, 0), QPoint(0, -120),
                                Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
            QApplication.sendEvent(widget, event)
            after = widget.value() if hasattr(widget, "value") else widget.currentIndex()
            self.assertEqual(before, after, type(widget).__name__)

    def test_every_figure_exports_its_picture_and_data(self) -> None:
        window = self.window
        self.open("Fe")
        window.views.setCurrentWidget(window.diagram_page)
        self.app.processEvents()
        handler = window.diagram_page.diagram.export_menu
        for suffix, magic in (("png", b"\x89PNG"), ("pdf", b"%PDF"), ("svg", b"<?xml")):
            path = os.path.join(self.directory.name, f"diagram.{suffix}")
            handler.save_figure(suffix, path)
            with open(path, "rb") as handle:
                self.assertTrue(handle.read(8).startswith(magic), suffix)
        for suffix, delimiter in (("csv", ","), ("txt", "\t")):
            path = os.path.join(self.directory.name, f"diagram.{suffix}")
            handler.save_data(suffix, delimiter, path)
            with open(path, encoding="utf-8") as handle:
                lines = handle.read().splitlines()
            self.assertEqual(lines[0].split(delimiter)[2], "stable species")
            self.assertGreater(len(lines), 1000)
        svg = os.path.join(self.directory.name, "diagram.svg")
        handler.save_figure("svg", svg)
        with open(svg, encoding="utf-8") as handle:
            text = handle.read()
        # redrawn with Matplotlib: axes, text, boundaries and legend are vectors, the domains one image
        self.assertGreater(text.count("<path"), 100)
        self.assertIn("Matplotlib", text)
        code = os.path.join(self.directory.name, "diagram.py")
        handler.save_code(code)
        namespace: dict = {}
        with open(code, encoding="utf-8") as handle:
            exec(handle.read().split("\nax = ")[0], namespace)
        self.assertTrue(np.array_equal(namespace["calculation"].diagram.stable_species_index,
                                       window.calculation.diagram.stable_species_index))
        for view in (window.compare_page.views[1], window.speciation_page.profile, window.overview.canvas):
            self.assertTrue(callable(view.python_code))
        window.pages.setCurrentIndex(0)
        window.update_overview()
        header, rows = window.overview.canvas.export_table()
        self.assertEqual(len(rows), 118)
        self.assertTrue(hasattr(window.compare_page.views[0], "export_menu"))
        self.assertTrue(hasattr(window.sweep_page.view3d, "export_menu"))
        window.pages.setCurrentIndex(1)

    def test_dragging_a_slider_previews_on_a_coarse_grid(self) -> None:
        window = self.window
        self.open("Fe")
        full = window.calculation.diagram.stable_species_index.shape
        with mock.patch.object(type(window), "_dragging", staticmethod(lambda: True)):
            window.settings.concentration = -3.0
            window._settings_changed(False)
            preview = window.calculation.diagram.stable_species_index.shape
            self.assertLess(preview[0] * preview[1], full[0] * full[1] / 4)
            self.assertAlmostEqual(window.calculation.scenario.concentration, -3.0)
        window.calculate_in_background()
        self.wait(lambda: window.calculation.diagram.stable_species_index.shape == full)
        self.assertEqual(window.calculation.diagram.stable_species_index.shape, full)

    def test_the_context_bar_states_what_the_result_is_calculated_from(self) -> None:
        window = self.window
        self.open("Fe")
        text = window.context_bar.text()
        for part in ("Iron (Fe)", "Fixed activity · a = 10⁻⁶", "Bundled data", "Default selection policy", "No ligands"):
            self.assertIn(part, text)
        self.assertIn("species left out", text)  # aqueous Fe(OH)₃ has no Gibbs energy
        window._overview_ligand_toggled("chloride-cl", True)
        window.recalculate()
        self.assertIn("Ligands: Chloride", window.context_bar.text())
        window.panel.setCurrentIndex(1)
        window.context_bar.chips["ligands"].click()
        self.assertEqual(window.panel.currentIndex(), 0)
        self.assertTrue(window.panel.ligands_section.expanded)
        minimum = window.minimumSizeHint().width()
        ligands = [item.ligand_id for item in window.database.available_ligands()]
        for ligand in ligands:
            window._overview_ligand_toggled(ligand, True)
        window.recalculate()
        self.assertIn(f"Ligands: {len(ligands)} on", window.context_bar.text())
        self.assertLessEqual(window.minimumSizeHint().width(), minimum)  # the bar never widens the window
        for ligand in ligands:
            window._overview_ligand_toggled(ligand, False)
        self.open("Zn", mode="mass_balance")
        self.assertIn("Mass balance · c_T = 10⁻⁶ M", window.context_bar.text())
        self.open("Fe")

    def test_sliders_jump_to_the_click_and_reset_to_their_default(self) -> None:
        from PySide6.QtCore import QPointF, Qt
        from PySide6.QtGui import QMouseEvent

        window = self.window
        self.open("Fe")
        control = window.panel.concentration
        control.slider.resize(400, 24)
        before = control.value()
        point = QPointF(control.slider.width() * 0.9, control.slider.height() / 2)
        for kind in (QMouseEvent.MouseButtonPress, QMouseEvent.MouseButtonRelease):
            QApplication.sendEvent(control.slider, QMouseEvent(kind, point, point, Qt.LeftButton, Qt.LeftButton,
                                                               Qt.NoModifier))
        self.assertGreater(control.value(), before + 3)  # one page step would move it by far less
        self.assertAlmostEqual(window.settings.concentration, control.value())
        control.reset_button.click()
        self.assertAlmostEqual(control.value(), -6.0)
        self.assertAlmostEqual(window.settings.concentration, -6.0)

    def test_opening_an_element_switches_the_page_at_once_and_loads_in_stages(self) -> None:
        window = self.window
        window.pages.setCurrentIndex(0)
        window.update_overview()
        window.open_element("Mn")
        self.assertEqual(window.pages.currentIndex(), 1)
        self.assertIs(window.diagram_page.currentWidget(), window.diagram_page.placeholder)
        full = (window.settings.U_points, window.settings.pH_points)
        self.wait(lambda: window.calculation is not None and window.calculation.diagram.system.symbol == "Mn"
                  and window.calculation.diagram.stable_species_index.shape == full)
        self.assertEqual(window.calculation.diagram.stable_species_index.shape, full)
        self.assertIs(window.diagram_page.currentWidget(), window.diagram_page.view)

    def test_sensitivity_tab_maps_where_the_data_do_not_fix_the_diagram(self) -> None:
        window = self.window
        self.open("Co")
        window.views.setCurrentWidget(window.sensitivity_page)
        self.wait(lambda: window.sensitivity_page.result is not None
                  and window.sensitivity_page.result.pH.size == window.settings.pH_points)
        result = window.sensitivity_page.result
        self.assertAlmostEqual(result.unfixed_fraction, 0.079, delta=0.01)  # the paper's cobalt value
        self.assertEqual(result.species[0].species, "Co₃O₄")
        self.assertEqual(window.sensitivity_page.table.item(0, 0).text(), "Co₃O₄")
        window.views.setCurrentWidget(window.diagram_page)

    def test_sources_dialog_lists_publications_and_writes_bibtex(self) -> None:
        from pourbase.gui.sources_dialog import SourcesDialog

        window = self.window
        self.open("Fe")
        dialog = SourcesDialog(window.calculation, "Iron (Fe)")
        self.assertGreater(dialog.table.rowCount(), 3)
        path = os.path.join(self.directory.name, "sources.bib")
        dialog.save_bibtex(path)
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        self.assertEqual(text.count("@misc{"), dialog.table.rowCount())
        self.assertIn("Lemire", text)
        dialog.close()

    def test_search_finds_elements_species_sources_and_commands(self) -> None:
        from pourbase.gui.search import rank

        window = self.window
        self.open("Fe")
        entries = window._search_entries()
        self.assertEqual(rank(entries, "copper")[0].title, "Copper (Cu)")
        self.assertEqual(rank(entries, "fe2o3")[0].title, "Fe₂O₃ — hematite")
        self.assertEqual(rank(entries, "robie")[0].kind, "Source")
        self.assertEqual(rank(entries, "export figure")[0].kind, "Command")
        species = next(entry for entry in rank(entries, "cuprite") if entry.kind == "Species")
        species.activate()
        self.wait(lambda: window.settings.symbol == "Cu" and window.calculation.diagram.system.symbol == "Cu"
                  and window.calculation.diagram.stable_species_index.shape
                  == (window.settings.U_points, window.settings.pH_points))
        table = window.species_page.table
        self.assertEqual(table.item(table.currentRow(), 2).text(), "cuprite")
        self.open("Fe")

    def test_species_show_composition_state_and_phase_with_searchable_aliases(self) -> None:
        from pourbase.gui.search import rank

        window = self.window
        self.open("Al")
        window.views.setCurrentWidget(window.species_page)
        self.app.processEvents()
        page = window.species_page
        phases = {
            "gfe-al-al-oh-3-q+0-solid-gibbsite": "gibbsite",
            "r14e-al-bayerite": "bayerite",
            "r09-al-alohmic": "microcrystalline aluminium hydroxide",
        }
        for record_id, phase in phases.items():
            row = next(i for i in range(page.table.rowCount())
                       if page.table.item(i, page.RECORD).text() == record_id)
            self.assertEqual([page.table.item(row, i).text() for i in range(3)],
                             ["Al(OH)₃", "solid", phase])
        page.table.selectRow(row)
        details = page.details.toPlainText()
        self.assertIn("Al(OH)3 — microcrystalline aluminium hydroxide", details)
        self.assertIn("Alias: AlOHmic", details)
        self.assertIn("19-month", details)
        for column in ("formation Gibbs energy", "formation enthalpy", "absolute entropy S"):
            self.assertEqual(details.count(f'"column": "{column}"'), 1)
        match = rank(window._search_entries(), "alohmic")[0]
        self.assertEqual(match.title, "Al(OH)₃ — microcrystalline aluminium hydroxide")
        self.assertIn("AlOHmic", match.detail)
        self.open("Fe")

    def test_sweep_runs_in_the_background_and_is_cached(self) -> None:
        window = self.window
        self.open("Fe")
        window.views.setCurrentWidget(window.sweep_stack)
        self.wait(lambda: window.sweep_stack.currentWidget() is window.sweep_page)
        page = window.sweep_page
        sweep = page.sweep
        self.assertEqual(len(sweep.diagrams), page.slice_counts["level"].value())
        for axis, count in (("pH", sweep.pH.size), ("U", sweep.U_V.size)):
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
        window.database_page.filter.setText("")
        window.database_page.tables.setCurrentText("selected_thermochemistry")
        self.assertEqual(window.database_page.proxy.rowCount(), 1771)
        self.assertFalse(window.database_page.note.isHidden())

    def test_copied_code_reproduces_the_diagram_with_policy_and_own_species(self) -> None:
        import pourbase as pb

        window = self.window
        policy = os.path.join(self.directory.name, "janaf.toml")
        with open(policy, "w", encoding="utf-8") as handle:
            handle.write(pb.SelectionPolicy.default().source_text.replace(
                'families = ["NBS Tables", "NBS Technical Notes", "NIST-JANAF"',
                'families = ["NIST-JANAF", "NBS Tables", "NBS Technical Notes"'))
        own = os.path.join(self.directory.name, "own-fe.csv")
        with open(own, "w", encoding="utf-8") as handle:
            handle.write("symbol,species,formula,charge,phase,gibbs_energy_kJ_mol,uncertainty_kJ_mol,citation,replaces\n"
                         "Fe,Fe(OH)2 (fresh),Fe(OH)2,0,solid,-500.0,,test,\n")
        self.open("Fe", concentration=-4.0)
        self.assertTrue(window.load_policy(policy))
        self.assertTrue(window.load_user_species(own))
        code = window.python_code()
        self.assertIn("pb.with_policy(database", code)
        self.assertIn("pb.with_user_species(database", code)
        namespace: dict = {}
        exec(code.split("\nax = ")[0], namespace)
        ours = window.calculation.diagram.stable_species_index
        theirs = namespace["calculation"].diagram.stable_species_index
        self.assertTrue(np.array_equal(ours, theirs))
        self.assertEqual([item.record_id for item in window.calculation.diagram.system.species],
                         [item.record_id for item in namespace["calculation"].diagram.system.species])
        window.load_user_species(None)
        window.load_policy(None)

    def test_policy_comparison_lists_every_changed_value(self) -> None:
        import pourbase as pb
        from pourbase.gui.policy_compare import PolicyComparisonDialog

        policy = pb.SelectionPolicy.default().with_family_order(
            "B", ["NIST-JANAF", "NBS Tables", "NBS Technical Notes", "Robie & Hemingway", "Miron"])
        dialog = PolicyComparisonDialog(self.window.database, policy, "janaf.toml")
        expected = pb.compare_policies(self.window.database, pb.SelectionPolicy.default(), policy)
        self.assertEqual(dialog.table.rowCount(), len(expected))
        self.assertGreater(len(expected), 0)
        dialog.close()

    def test_species_tab_flags_disagreeing_sources_and_boundaries_cite_them(self) -> None:
        window = self.window
        self.open("Co")
        window.views.setCurrentWidget(window.species_page)
        self.app.processEvents()
        page = window.species_page
        flagged = [page.table.item(row, 0).text() for row in range(page.table.rowCount())
                   if page.table.item(row, page.SPREAD).toolTip()]
        self.assertIn("Co₃O₄", flagged)
        statuses = {page.table.item(row, page.STATUS).text() for row in range(page.table.rowCount())}
        self.assertFalse(any("_" in status for status in statuses))
        window.views.setCurrentWidget(window.boundaries_page)
        self.app.processEvents()
        sources = window.boundaries_page.table.item(0, 3).text()
        self.assertRegex(sources, r"\(\d{4}\)")


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
        self.assertIn("Materials Project:", window.diagram_page.probe.toPlainText())
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
