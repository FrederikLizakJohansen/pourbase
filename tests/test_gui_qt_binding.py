"""Check GUI startup when another Qt binding is selected in the environment."""

import importlib.util
import os
import subprocess
import sys
import unittest


@unittest.skipUnless(importlib.util.find_spec("PySide6") and importlib.util.find_spec("pyqtgraph"), "GUI dependencies absent")
class QtBindingTest(unittest.TestCase):
    def test_gui_uses_pyside_with_conflicting_pyqtgraph_setting(self):
        env = os.environ.copy()
        env.update(PYQTGRAPH_QT_LIB="PyQt6", QT_QPA_PLATFORM="offscreen")
        script = """
from PySide6.QtWidgets import QApplication
from pourbase.gui.plots import DiagramView
import pyqtgraph
app = QApplication([])
view = DiagramView()
assert pyqtgraph.Qt.QT_LIB == 'PySide6'
assert view.export_menu is not None
view.close()
"""
        result = subprocess.run([sys.executable, "-c", script], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
