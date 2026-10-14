from __future__ import annotations

import os
import tempfile
import unittest

import numpy as np

import support  # noqa: F401

import pourbase as pb
from pourbase.measurements import MeasuredPoint


class FixedPotentialTests(unittest.TestCase):
    def test_solubility_equals_the_mass_balance_saturation(self) -> None:
        for symbol in ("Fe", "Cu", "Zn"):
            calculation = pb.calculate(pb.Scenario(symbol, mode="mass_balance", concentration=-2.0))
            diagram = calculation.diagram
            row = int(np.abs(diagram.eh_V).argmin())
            result = pb.solubility(calculation, float(diagram.eh_V[row]))
            saturation = np.log10(diagram.saturation_dissolved_metal_mol_L[row])
            finite = np.isfinite(saturation)
            np.testing.assert_allclose(result.log10_total_mol_L[finite], saturation[finite], atol=1e-9)

    def test_ligand_predominance_at_low_activity_matches_the_ligand_free_diagram(self) -> None:
        calculation = pb.calculate(pb.Scenario("Cu"))
        result = pb.ligand_predominance(calculation, "chloride-cl", 0.0, np.array([-12.0, 0.0]))
        plain = pb.calculate(pb.Scenario("Cu", eh_min_V=-1e-4, eh_max_V=1e-4, eh_points=2)).diagram
        names = [result.species[i].species for i in result.stable_species_index[0]]
        self.assertEqual(names, [plain.system.species[i].species for i in plain.stable_species_index[0]])
        self.assertIn("CuCl₂⁻", {result.species[i].species for i in result.stable_species_index[1]})


class PathTests(unittest.TestCase):
    def test_crossings_lie_on_the_analytical_boundaries(self) -> None:
        calculation = pb.calculate(pb.Scenario("Fe"))
        path = pb.phase_path(calculation, (4.0, -1.0), (4.0, 1.0))
        self.assertGreaterEqual(len(path.crossings), 2)
        for crossing in path.crossings:
            boundary = crossing.boundary
            self.assertIsNotNone(boundary)
            if boundary.kind == "nernst":
                expected = boundary.eh_intercept_V + boundary.eh_slope_V_per_pH * crossing.pH
                self.assertAlmostEqual(crossing.eh_V, expected, places=6)

    def test_paths_through_several_points(self) -> None:
        calculation = pb.calculate(pb.Scenario("Fe"))
        vertices = ((2.0, -1.0), (7.0, 0.5), (12.0, -0.5))
        _position, pH, eh = pb.path_curve(vertices, smooth=True, points=401)
        for vertex in vertices:  # the smooth curve passes through every point
            self.assertLess(np.min(np.hypot(pH - vertex[0], eh - vertex[1])), 0.03)
        straight = pb.phase_path(calculation, *vertices)
        self.assertEqual([c.after.species for c in straight.crossings][:2], ["Fe²⁺", "Fe₂O₃"])


class MeasurementTests(unittest.TestCase):
    def test_points_are_assessed_and_converted_from_the_reference_electrode(self) -> None:
        from pourbase.gui.diagram_tools import read_points

        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "points.csv")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("label,pH,potential_V,reference\nA,7,0.0,SHE\nB,7,0.0,SCE\nC,7,-0.0,RHE\n")
            points = read_points(path)
        self.assertAlmostEqual(points[1].eh_V, 0.241)
        self.assertAlmostEqual(points[2].eh_V, -0.059159 * 7, places=4)
        calculation = pb.calculate(pb.Scenario("Fe"))
        results = pb.assess_points(calculation, points + [MeasuredPoint("out", 20.0, 0.0)])
        self.assertEqual(results[0].species.species, "Fe₂O₃")
        self.assertFalse(results[-1].inside)


class WaterPresetTests(unittest.TestCase):
    def test_presets_use_database_ligands(self) -> None:
        ligands = {item.ligand_id for item in pb.ThermodynamicDatabase.bundled().available_ligands()}
        for preset in pb.WATER_PRESETS.values():
            self.assertLessEqual({ligand_id for ligand_id, _value in preset.concentrations_mol_L}, ligands)
            pb.calculate(pb.Scenario("Cu", ligands=preset.ligands, pH_points=21, eh_points=21))


if __name__ == "__main__":
    unittest.main()
