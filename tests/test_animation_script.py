import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "animate_periodic_table.py"


def load_script():
    spec = importlib.util.spec_from_file_location("animate_periodic_table", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses look their module up here
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(SCRIPT.exists(), "the script is not in this distribution")
class AnimationScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = load_script()

    def test_every_sweep_loops_within_the_supported_temperatures(self):
        for name, sweep in self.script.SWEEPS.items():
            with self.subTest(name):
                self.script.check_sweep(name, sweep)

    def test_a_path_that_does_not_close_is_rejected(self):
        sweep = self.script.Sweep(lambda t: (7.0, t, 25.0), 12, "")
        with self.assertRaisesRegex(ValueError, "does not loop"):
            self.script.check_sweep("open", sweep)

    def test_a_path_outside_the_supported_temperatures_is_rejected(self):
        sweep = self.script.Sweep(lambda t: (7.0, 0.0, self.script.cycle(t, 25.0, 150.0)), 12, "")
        with self.assertRaisesRegex(ValueError, "pourbase supports"):
            self.script.check_sweep("hot", sweep)

    def test_short_runs_show_the_species_before_them(self):
        keys = ["a"] * 10 + ["b"] * 2 + ["a"] * 10
        self.assertEqual({keys[i] for i in self.script.merge_short_runs(keys)}, {"a"})
        keys = ["a"] * 10 + ["b"] * 5 + ["a"] * 10
        self.assertEqual([keys[i] for i in self.script.merge_short_runs(keys)], keys)

    def test_formula_labels(self):
        self.assertEqual(self.script.formula_mathtext("Fe2O3", 0), "$\\mathregular{Fe_{2}O_{3}}$")
        self.assertEqual(self.script.formula_mathtext("Fe(OH)2", 1), "$\\mathregular{Fe(OH)_{2}^{+}}$")
        self.assertEqual(self.script.concentration_label(-6), "10⁻⁶ M")

    def preview(self, directory, compose=None):
        job = self.script.Job("orbit", "1x1", "dark", Path(directory), preview=(0.25,), seconds=0.5)
        # The logo starts a Qt application, which would take the place of the one the GUI tests create.
        with mock.patch.object(self.script, "render_logo", return_value=None), \
                mock.patch.object(self.script, "compose", compose or self.script.compose):
            return self.script.render(job)

    def test_a_new_part_can_read_each_frame(self):
        seen = []

        def draw_count(scene):
            label = scene.canvas.text(60, 195, "", fontsize=14)

            def update(frame):
                seen.append(len(scene.screens[frame].elements))
                label.set_text(str(seen[-1]))

            return update

        original = self.script.compose
        with tempfile.TemporaryDirectory() as directory:
            self.preview(directory, lambda scene: [*original(scene), draw_count(scene)])
        self.assertEqual(seen, [118])

    def test_parts_can_be_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            (path,) = self.preview(directory, lambda scene: [self.script.draw_table(scene)])
            self.assertTrue(path.exists())

    def test_preview_writes_a_still_of_the_format_size(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as directory:
            (path,) = self.preview(directory)
            with Image.open(path) as image:
                self.assertEqual(image.size, (1080, 1080))


if __name__ == "__main__":
    unittest.main()
