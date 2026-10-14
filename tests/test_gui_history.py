from __future__ import annotations

import unittest
import unittest.mock

import numpy as np

import support  # noqa: F401

from pourbase.gui.history import History

try:
    from test_gui import QApplication, WindowTestCase
except ImportError:  # pragma: no cover
    QApplication = None
    WindowTestCase = unittest.TestCase


class HistoryTests(unittest.TestCase):
    def test_undo_redo_and_branching(self) -> None:
        history = History()
        state = {"value": 1}
        self.assertTrue(history.record(state))
        self.assertFalse(history.record(state))
        state["value"] = 2  # the recorded snapshot is a copy
        history.record(state)
        self.assertEqual(history.undo(), {"value": 1})
        self.assertTrue(history.can_redo())
        history.record({"value": 3})
        self.assertFalse(history.can_redo())
        self.assertEqual(history.undo(), {"value": 1})


@unittest.skipIf(QApplication is None, "PySide6 is not installed")
class UndoBoundaryOverlayTests(WindowTestCase):
    def test_undo_restores_settings_and_display(self) -> None:
        window = self.window
        self.open("Fe")
        window._record_history()
        window.panel.mode.setCurrentIndex(1)
        window._record_history()  # each change is one step once the debounce timer has fired
        window.panel.display_checks["labels"].setChecked(False)
        window.undo()
        self.assertTrue(window.display.labels)
        self.assertEqual(window.settings.mode, "mass_balance")
        window.undo()
        self.assertEqual(window.settings.mode, "fixed_activity")
        window.redo()
        self.assertEqual(window.settings.mode, "mass_balance")
        window.undo()

    def test_boundary_click_finds_the_two_species(self) -> None:
        window = self.window
        self.open("Fe")
        view = window.diagram_page.diagram
        pair = next(found for e in np.linspace(-1, 1, 801) if (found := view.boundary_at(4.0, e)))
        self.assertEqual({pair[0].species, pair[1].species}, {"Fe", "Fe²⁺"})
        self.assertIsNone(view.boundary_at(7.0, 0.5))

    def test_one_click_closes_the_popup_and_moves_the_probe(self) -> None:
        from PySide6.QtCore import QPointF, Qt

        window = self.window
        self.open("Fe")
        view = window.diagram_page.diagram
        e = next(e for e in np.linspace(-1, 1, 801) if view.boundary_at(4.0, e))

        def click(x, y):
            position = view.getPlotItem().vb.mapViewToScene(QPointF(x, y))
            event = unittest.mock.Mock(button=lambda: Qt.LeftButton, double=lambda: False,
                                       scenePos=lambda: position)
            view._mouse_clicked(event)

        click(4.0, e)
        self.assertIsNotNone(window.diagram_page.boundary_popup)
        click(7.0, 0.5)
        self.assertIsNone(window.diagram_page.boundary_popup)
        self.assertAlmostEqual(view.probe.pos().x(), 7.0, places=1)

    def test_second_element_overlay(self) -> None:
        window = self.window
        self.open("Fe")
        window.panel.overlay.setCurrentIndex(window.panel.overlay.findData("Cr"))
        view = window.diagram_page.diagram
        self.wait(lambda: getattr(view, "overlay_labels", []))
        self.assertIn("Cr2O3", [label.textItem.toPlainText() for label in view.overlay_labels])
        window.panel.overlay.setCurrentIndex(0)
        self.assertEqual(view.overlay_labels, [])

    def test_popped_out_diagrams_share_the_probe(self) -> None:
        window = self.window
        for concentration in (-6.0, -2.0):
            self.open("Fe", concentration=concentration)
            window.pop_out_diagram()
        self.assertEqual(len(window.pinned), 2)
        self.assertNotEqual(window.pinned[0].windowTitle(), window.pinned[1].windowTitle())
        window.pinned[1].probeMoved.emit(10.0, -0.5)
        self.assertEqual((window.settings.probe_pH, window.settings.probe_eh_V), (10.0, -0.5))
        self.assertTrue(window.pinned[0].readout.text().startswith("pH 10.00, Eh -0.500"))
        self.assertTrue(window.pinned[0].sources.text().endswith("sources"))
        window.close_pinned()
        self.wait(lambda: not window.pinned, timeout=2)
        self.assertEqual(window.pinned, [])

    def test_water_path_points_and_fixed_potential(self) -> None:
        from pourbase.measurements import MeasuredPoint

        window = self.window
        self.open("Cu")
        self.assertEqual(window.panel.water.currentData(), "pure")
        window.panel.apply_water("seawater")
        window.recalculate()
        self.assertEqual(window.panel.water.currentData(), "seawater")
        self.assertEqual(window.settings.probe_pH, 8.1)
        self.assertTrue(window.settings.ligands["chloride-cl"].enabled)
        page = window.diagram_page
        page.path_panel._from_probe("eh")
        self.assertIn("CuCl", page.path_panel.crossings.toPlainText())
        self.assertNotIn("chloride-cl", page.path_panel.crossings.toPlainText())
        view = page.diagram

        def click(x, y, double=False):
            from PySide6.QtCore import QPointF, Qt

            scene = view.getPlotItem().vb.mapViewToScene(QPointF(x, y))
            view._mouse_clicked(unittest.mock.Mock(button=lambda: Qt.LeftButton, double=lambda: double,
                                                   scenePos=lambda: scene))

        page.path_panel.pick.setChecked(True)
        self.assertEqual(page.path_panel.vertices, [])  # the previous path is gone at once
        for x, y in ((2.0, -1.0), (7.0, 0.5), (12.0, -0.5)):
            click(x, y)
        click(12.0, -0.5, double=True)
        self.assertEqual(len(page.path_panel.vertices), 3)
        self.assertFalse(page.path_panel.pick.isChecked())
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QKeyEvent

        view.select_vertex(1)
        view.keyPressEvent(QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Up, Qt.ShiftModifier))
        self.assertAlmostEqual(page.path_panel.vertices[1][1], 0.6, places=3)
        view.vertex_items[0].setPos(3.0, -1.0)
        view.vertex_items[0].sigPositionChangeFinished.emit(view.vertex_items[0])
        self.assertAlmostEqual(page.path_panel.vertices[0][0], 3.0)
        page.path_panel.along.setValue(500)
        self.assertIn("is stable", page.path_panel.here.text())
        view.select_vertex(2)
        view.keyPressEvent(QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier))
        self.assertEqual(len(page.path_panel.vertices), 2)
        page.points_panel.set_points([MeasuredPoint("A", 8.1, 0.05)])
        self.assertEqual(page.points_panel.table.item(0, 3).text(), "CuCl₂⁻")
        window.views.setCurrentWidget(window.fixed_page)
        self.assertIsNotNone(window.fixed_page.result)
        window.fixed_page.predominance_button.setChecked(True)
        self.assertEqual(window.fixed_page.ligand.currentData() is not None, True)
        window.views.setCurrentWidget(page)
        window.panel.apply_water("pure")
        self.assertFalse(window.settings.use_ligands)
        page.path_panel.set_vertices([])
        page.points_panel.set_points([])

    def test_temperature_reaches_every_view(self) -> None:
        window = self.window
        self.open("Fe")
        window.panel.temperature.spin.setValue(90.0)
        window.recalculate()
        self.assertAlmostEqual(window.calculation.scenario.temperature_K, 363.15)
        self.assertIn("90 °C", window.context_bar.text())
        self.assertAlmostEqual(window._screen_arguments()["temperature_K"], 363.15)
        right = window.compare_page.right_settings(window.settings)
        self.assertEqual(right.temperature_C, window.compare_page.temperature.value())
        window.views.setCurrentWidget(window.fixed_page)
        self.assertIsNotNone(window.fixed_page.result)
        window.views.setCurrentWidget(window.dft_stack)
        self.assertIs(window.dft_stack.currentWidget(), window.dft_stack.placeholder)
        window.views.setCurrentWidget(window.diagram_page)
        window.overview.temperature.spin.setValue(60.0)  # the periodic table sets the same temperature
        self.assertEqual(window.settings.temperature_C, 60.0)
        self.assertEqual(window.panel.temperature.value(), 60.0)
        window.update_overview()
        self.assertIn("60 °C", window.overview.note.text())
        window.panel.temperature.spin.setValue(25.0)
        window.update_overview()
        self.assertEqual(window.overview.temperature.value(), 25.0)
        window.recalculate()


if __name__ == "__main__":
    unittest.main()
