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


if __name__ == "__main__":
    unittest.main()
