from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from support import FakeMPEntry

import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.models import ReferenceState

SMALL = dict(pH_points=21, eh_points=23)


class CalculationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_scenario_calculates_fixed_activity_and_mass_balance(self) -> None:
        fixed = pb.calculate(pb.Scenario("Fe", **SMALL), self.database)
        self.assertEqual(fixed.diagram.stable_species_index.shape, (23, 21))
        self.assertTrue(fixed.boundaries and fixed.plating)
        balance = pb.calculate(pb.Scenario("Zn", mode="mass_balance", concentration=1e-6,
                                           concentration_unit="molar", **SMALL), self.database)
        self.assertEqual(balance.boundaries, ())
        probe = balance.probe(7.0, 0.0)
        self.assertAlmostEqual(sum(item["metal_fraction"] for item in probe.speciation), 1.0)

    def test_mass_balance_conserves_metal_and_activities(self) -> None:
        diagram = pb.MassBalanceEngine(self.database, pb.DaviesActivityCoefficientModel(0.05)).calculate(
            "Zn", pb.PourbaixConditions(**SMALL), pb.TotalMetalConcentration(2e-4)
        )
        np.testing.assert_allclose(diagram.aqueous_concentration_mol_L.sum(axis=0),
                                   diagram.dissolved_metal_mol_L, rtol=1e-12)
        np.testing.assert_allclose(
            diagram.dissolved_metal_mol_L + diagram.precipitated_metal_fraction * 2e-4, 2e-4, rtol=1e-12
        )
        np.testing.assert_allclose(
            diagram.aqueous_activity,
            diagram.aqueous_activity_coefficient[:, None, None] * diagram.aqueous_concentration_mol_L,
            rtol=1e-12,
        )
        np.testing.assert_allclose(pb.metal_fraction_grid(diagram).sum(axis=0), 1.0, atol=1e-12)
        self.assertAlmostEqual(sum(item["metal_fraction"] for item in pb.speciation_at(diagram, 7, 0)), 1.0)

    def test_incomplete_systems_need_an_explicit_choice(self) -> None:
        with self.assertRaises(pb.IncompleteSystemError):
            pb.calculate(pb.Scenario("Pt", **SMALL), self.database)
        gaps = pb.calculate(pb.Scenario("Pt", allow_incomplete=True, **SMALL), self.database)
        self.assertTrue(gaps.diagram.system.missing_gibbs)
        fallback = pb.calculate(pb.Scenario("Pt", energy_policy="experimental_then_mp", **SMALL), self.database)
        self.assertTrue(fallback.fallback_species)
        self.assertTrue(all(item.gibbs_status is pb.EvidenceStatus.MATERIALS_PROJECT_FALLBACK
                            for item in fallback.fallback_species))

    def test_ligands_and_gas_fugacity_enter_the_energies(self) -> None:
        plain = pb.calculate(pb.Scenario("Ag", **SMALL), self.database)
        self.assertIn(pb.ExclusionReason.LIGAND_NOT_SELECTED, {item.reason for item in plain.excluded})
        chloride = pb.calculate(pb.Scenario(
            "Ag", ligands=(pb.LigandActivity("chloride-cl", log10_free_activity=-1),), **SMALL
        ), self.database)
        self.assertTrue({"AgCl", "AgCl₂⁻"} & {item.species for item in chloride.stable_species})
        species = pb.ThermodynamicSpecies(
            record_id="test-n2", system="Nitrogen (N)", symbol="N", species="N2", formula_ascii="N2",
            phase="gas", phase_detail="gas", charge=0.0, metal_count=2.0, core_oxygen_count=0.0,
            core_hydrogen_count=0.0, ligand_id=None, ligand_count=0.0, ligand_charge=0.0,
            gibbs_energy_J_mol=0.0, gibbs_status="verified", source_id="test",
        )
        reference = ReferenceState(298.15, 1.0, -237129.0)
        standard = pb.PourbaixEngine.transformed_gibbs_J_mol_metal(species, reference, pb.PourbaixConditions(), 7, 0)
        dilute = pb.PourbaixEngine.transformed_gibbs_J_mol_metal(
            species, reference, pb.PourbaixConditions(gas_fugacities=pb.GasFugacityModel(-2.0)), 7, 0
        )
        self.assertAlmostEqual(float(dilute - standard), -GAS_CONSTANT_J_MOL_K * 298.15 * LN_10, places=9)

    def test_ligand_protonation_is_vectorized_and_stable(self) -> None:
        pool = pb.LigandActivity("cyanide-cn", total_unbound_mol_L=0.01, acid_pKa=9.21)
        values = pool.log10_activity(np.array([0.0, 9.21, 14.0, 400.0]))
        self.assertAlmostEqual(values[1], -2 - np.log10(2))
        self.assertAlmostEqual(values[2], -2, places=4)
        self.assertTrue(np.all(np.isfinite(values)))

    def test_miron_silicate_hydration_preserves_transformed_energy(self) -> None:
        hydrated = next(s for s in self.database.load_system("Si").species
                        if s.record_id == "gfe-si-h3sio4-q-1-aqueous-aq")
        original = replace(hydrated, formula_ascii="HSiO3", core_oxygen_count=3.0,
                           core_hydrogen_count=1.0, gibbs_energy_J_mol=-1015175.0)
        conditions = pb.PourbaixConditions(**SMALL)
        ph, eh = np.meshgrid(np.linspace(0, 14, 21), np.linspace(-1.5, 2, 23))
        energies = [pb.PourbaixEngine.transformed_gibbs_J_mol_metal(
            s, self.database.reference_state, conditions, ph, eh
        ) for s in (hydrated, original)]
        np.testing.assert_allclose(*energies, rtol=0, atol=1e-8)

    def test_buffered_silicate_and_aluminate_complexes_conserve_active_metal(self) -> None:
        for metal, ligand, formula, oxidation in (
            ("Al", "silicate-h3sio4", "AlH3SiO4", 3),
            ("Ca", "silicate-h3sio4", "CaH3SiO4", 2),
            ("Mg", "silicate-h3sio4", "MgH3SiO4", 2),
            ("Na", "silicate-h3sio4", "NaH3SiO4", 1),
            ("Na", "aluminate-aloh4", "NaAl(OH)4", 1),
            ("K", "aluminate-aloh4", "KAl(OH)4", 1),
        ):
            with self.subTest(metal=metal, ligand=ligand):
                conditions = pb.PourbaixConditions(
                    **SMALL, ligand_activities=pb.LigandActivityModel((
                        pb.LigandActivity(ligand, log10_free_activity=-3.0),
                    )),
                )
                diagram = pb.MassBalanceEngine(self.database).calculate(
                    metal, conditions, pb.TotalMetalConcentration(1e-6)
                )
                species = next(s for s in diagram.system.species if s.formula_ascii == formula)
                self.assertEqual((species.core_oxygen_count, species.core_hydrogen_count), (0, 0))
                self.assertEqual((species.ligand_count, species.electrons_per_metal), (1, oxidation))
                self.assertEqual(species.charge, oxidation + species.ligand_charge)
                np.testing.assert_allclose(
                    diagram.dissolved_metal_mol_L + diagram.precipitated_metal_fraction * 1e-6,
                    1e-6, rtol=1e-12,
                )

    def test_boundary_equations_match_the_energies(self) -> None:
        calculation = pb.calculate(pb.Scenario("Fe", pH_points=81, eh_points=81), self.database)
        nernst = next(item for item in calculation.boundaries if item.kind == "nernst")
        species = {item.record_id: item for item in calculation.diagram.system.species}
        eh = nernst.eh_intercept_V + nernst.eh_slope_V_per_pH * 5.0
        energies = [
            float(pb.PourbaixEngine.transformed_gibbs_J_mol_metal(
                species[record_id], self.database.reference_state, calculation.diagram.conditions, 5.0, eh
            ))
            for record_id in (nernst.left_record_id, nernst.right_record_id)
        ]
        self.assertAlmostEqual(*energies, places=6)
        self.assertTrue(all("e-" in item.reaction for item in calculation.plating))

    def test_boltzmann_weights_follow_the_energies(self) -> None:
        diagram = pb.PourbaixEngine(self.database).calculate("Fe", pb.PourbaixConditions(pH_points=19, eh_points=21))
        smoothed = pb.boltzmann_smooth(diagram)
        np.testing.assert_allclose(smoothed.weights.sum(axis=0), 1.0, atol=1e-14)
        np.testing.assert_array_equal(np.argmax(smoothed.weights, axis=0), diagram.stable_species_index)
        first, second = np.argsort(smoothed.weights[:, 10, 9])[-2:]
        energies = diagram.transformed_gibbs_J_mol_metal
        self.assertAlmostEqual(
            np.log(smoothed.weights[first, 10, 9] / smoothed.weights[second, 10, 9]),
            -(energies[first, 10, 9] - energies[second, 10, 9]) / smoothed.effective_thermal_energy_J_mol,
            places=12,
        )
        compact = pb.PourbaixEngine(self.database).calculate(
            "Fe", pb.PourbaixConditions(pH_points=19, eh_points=21), store_energies=False
        )
        np.testing.assert_array_equal(compact.stable_species_index, diagram.stable_species_index)
        with self.assertRaises(ValueError):
            pb.boltzmann_smooth(compact)

    def test_sweeps_are_compact_and_cancellable(self) -> None:
        engine = pb.ConcentrationSweepEngine(self.database)
        sweep = engine.calculate("Fe", pb.PourbaixConditions(**SMALL), -8.0, -2.0, 4)
        self.assertEqual(len(sweep.diagrams), 4)
        self.assertIsNone(sweep.diagrams[0].transformed_gibbs_J_mol_metal)
        with self.assertRaises(pb.CalculationCancelled):
            engine.calculate("Fe", pb.PourbaixConditions(**SMALL), -8.0, -2.0, 4,
                             progress=lambda fraction: fraction < 0.5)

    def test_periodic_screen_statuses_and_rhe(self) -> None:
        strict = pb.screen_periodic_table(self.database, pH=14, potential_V=1.6, reference="RHE")
        slope = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10 / 96485.33212
        self.assertAlmostEqual(strict.potential_V_vs_SHE, 1.6 - slope * 14)
        self.assertIs(strict.element("Pt").status, pb.ElementStatus.INCOMPLETE)
        self.assertTrue(strict.element("Pt").status.has_system)
        relaxed = pb.screen_periodic_table(self.database, pH=14, potential_V=1.6, reference="RHE",
                                           allow_incomplete=True)
        platinum = relaxed.element("Pt")
        self.assertTrue(platinum.status.is_calculated and platinum.status.is_provisional)
        self.assertEqual(relaxed.calculated_count, relaxed.supported_count)
        self.assertFalse(relaxed.element("He").status.has_system)

    def test_species_records_carry_sources_and_warnings(self) -> None:
        record = self.database.species_records(["gfe-fe-fe-oh-2-q+1-aqueous-aq", "unknown"])[0]
        self.assertTrue(record.thermochemistry.gibbs_energy_J_mol.source.citation)
        self.assertTrue(record.warnings)
        self.assertTrue(record.reported)

    def test_exports(self) -> None:
        calculation = pb.calculate(pb.Scenario("Zn", mode="mass_balance", **SMALL), self.database)
        lines = pb.grid_csv(calculation.diagram).splitlines()
        self.assertEqual(len(lines), 1 + 21 * 23)
        self.assertIn("dissolved_metal_mol_L", lines[0])
        with tempfile.TemporaryDirectory() as directory:
            path = pb.save_figure(pb.diagram_figure(calculation.diagram), Path(directory) / "zn.png", dpi=50)
            self.assertGreater(path.stat().st_size, 1000)

    def test_phase_boundaries_are_emitted_once(self) -> None:
        segments = pb.phase_boundary_segments(np.array([[0, 2], [1, 2]]), np.array([0.0, 1.0]), np.array([-1.0, 1.0]))
        self.assertEqual(segments.shape, (3, 2, 2))
        self.assertEqual(len({segment.tobytes() for segment in segments}), 3)

    def test_concentration_units(self) -> None:
        self.assertAlmostEqual(pb.convert_concentration("Fe", 55.845, "ppm").molar_concentration, 0.001)
        weight = pb.convert_concentration("Fe", 1.0, "wt_percent", solution_density_kg_L=1.2)
        self.assertAlmostEqual(weight.molar_concentration, 12.0 / 55.845)

    def test_official_mp_evaluation_offline(self) -> None:
        conditions = pb.PourbaixConditions(pH_points=15, eh_points=17)
        official = pb.evaluate_official_materials_project_entries(
            "Fe", conditions,
            [FakeMPEntry("mp-metal", "Fe(s)", "Solid", "Fe", {"Fe": 1}, 0, 0, 0),
             FakeMPEntry("ion-fe2", "Fe[+2]", "Ion", "Fe", {"Fe": 1}, -0.9, 0, -2)],
            database_version="test-db", mp_api_version="test", pymatgen_version="test",
            filter_solids=True, use_gibbs_300K=False,
        )
        experimental = pb.PourbaixEngine(self.database).calculate("Fe", conditions)
        np.testing.assert_allclose(official.oer_V, experimental.oer_V)

        class StubClient:
            def calculate(self, *_args, **_kwargs):
                return official

        comparison = pb.OfficialMaterialsProjectComparator(pb.PourbaixEngine(self.database), StubClient()).compare(
            "Fe", conditions
        )
        self.assertTrue(0.0 <= comparison.equivalent_domain_fraction <= 1.0)
        import matplotlib.pyplot as plt

        figure, axes = pb.plot_official_materials_project_comparison(comparison)
        self.assertEqual(len(axes), 3)
        plt.close(figure)

    def test_public_api(self) -> None:
        for name in ("IdealMassBalanceEngine", "TotalElementConcentration", "ElementSystem",
                     "IdealTotalMetalConcentration", "GibbsPourbaixError"):
            self.assertFalse(hasattr(pb, name), name)
        self.assertEqual(pb.__data_version__, self.database.data_version)
        with self.assertRaises(TypeError):
            pb.PourbaixConditions(log10_aqueous_activity=-4)


if __name__ == "__main__":
    unittest.main()


class UncertaintyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.calculation = pb.calculate(pb.Scenario("Fe", **SMALL))

    def test_margin_finds_the_exact_redox_boundary(self) -> None:
        diagram = self.calculation.diagram
        margin = pb.stability_margin(diagram, 1.0, 0.5)
        self.assertEqual(margin.species.species, "Fe²⁺")
        self.assertEqual(margin.higher_potential.species.species, "Fe³⁺")
        species = {item.species: item for item in diagram.system.species}
        # Both ions share one activity, so the boundary is the standard potential
        standard = (species["Fe³⁺"].gibbs_energy_J_mol - species["Fe²⁺"].gibbs_energy_J_mol) / 96485.33212
        self.assertAlmostEqual(0.5 + margin.higher_potential.distance, standard, places=6)
        self.assertGreater(margin.margin_J_mol_metal, 0)

    def test_hatched_region_grows_with_the_assumed_uncertainty(self) -> None:
        diagram = self.calculation.diagram
        small = pb.stability_uncertainty(diagram, 1.0, 100.0)
        large = pb.stability_uncertainty(diagram, 1.0, 20_000.0)
        self.assertLessEqual(small.uncertain_fraction, large.uncertain_fraction)
        self.assertTrue(np.all(large.uncertain[small.uncertain]))
        self.assertTrue(large.assumed_record_ids)

    def test_mass_balance_diagrams_are_rejected(self) -> None:
        calculation = pb.calculate(pb.Scenario("Fe", mode="mass_balance", **SMALL))
        with self.assertRaises(ValueError):
            pb.stability_uncertainty(calculation.diagram)
