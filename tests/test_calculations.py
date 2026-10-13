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
        fixed = pb.calculate(pb.Scenario("Fe", allow_incomplete=True, **SMALL), self.database)
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

    def test_species_without_gibbs_energy_are_left_out_unless_strict(self) -> None:
        for symbol in ("Pt", "Fe", "Ni"):
            with self.subTest(symbol=symbol), self.assertRaises(pb.IncompleteSystemError):
                pb.calculate(pb.Scenario(symbol, allow_incomplete=False, **SMALL), self.database)
            calculation = pb.calculate(pb.Scenario(symbol, **SMALL), self.database)
            self.assertTrue(calculation.diagram.system.missing_gibbs)
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
        calculation = pb.calculate(pb.Scenario("Fe", pH_points=81, eh_points=81, allow_incomplete=True), self.database)
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
        diagram = pb.PourbaixEngine(self.database).calculate("Fe", pb.PourbaixConditions(pH_points=19, eh_points=21), allow_incomplete=True)
        smoothed = pb.boltzmann_smooth(diagram, blend_all_phases=True)
        np.testing.assert_allclose(smoothed.weights.sum(axis=0), 1.0, atol=1e-14)
        np.testing.assert_array_equal(np.argmax(smoothed.weights, axis=0), diagram.stable_species_index)
        # by default a stable solid keeps the whole weight: edges with solids stay sharp
        sharp = pb.boltzmann_smooth(diagram)
        solid = np.array([not item.is_aqueous for item in diagram.system.species])[diagram.stable_species_index]
        self.assertTrue(solid.any())
        np.testing.assert_array_equal(sharp.dominant_weight[solid], 1.0)
        np.testing.assert_array_equal(np.argmax(sharp.weights, axis=0), diagram.stable_species_index)
        first, second = np.argsort(smoothed.weights[:, 10, 9])[-2:]
        energies = diagram.transformed_gibbs_J_mol_metal
        self.assertAlmostEqual(
            np.log(smoothed.weights[first, 10, 9] / smoothed.weights[second, 10, 9]),
            -(energies[first, 10, 9] - energies[second, 10, 9]) / smoothed.effective_thermal_energy_J_mol,
            places=12,
        )
        compact = pb.PourbaixEngine(self.database).calculate(
            "Fe", pb.PourbaixConditions(pH_points=19, eh_points=21), store_energies=False, allow_incomplete=True
        )
        np.testing.assert_array_equal(compact.stable_species_index, diagram.stable_species_index)
        with self.assertRaises(ValueError):
            pb.boltzmann_smooth(compact)

    def test_blend_at_rt_equals_aqueous_fractions_without_a_solid(self) -> None:
        conditions = pb.PourbaixConditions(pH_points=29, eh_points=31)
        fixed = pb.PourbaixEngine(self.database).calculate("Fe", conditions, allow_incomplete=True)
        balance = pb.MassBalanceEngine(self.database).calculate(
            "Fe", conditions, pb.TotalMetalConcentration(1e-6), allow_incomplete=True)
        smoothed = pb.boltzmann_smooth(fixed)
        self.assertAlmostEqual(smoothed.width_J_mol, 8.314462618 * 298.15, places=3)
        ids = [item.record_id for item in fixed.system.species]
        common = [item.record_id for item in balance.aqueous_species]
        dissolved_stable = np.array([item.is_aqueous for item in fixed.system.species])[fixed.stable_species_index]
        rows, columns = np.nonzero((balance.precipitated_metal_fraction == 0) & dissolved_stable)
        self.assertTrue(rows.size)
        for row, column in zip(rows[::25], columns[::25], strict=True):
            weights = np.array([smoothed.weights[ids.index(item), row, column] for item in common])
            dissolved = balance.aqueous_concentration_mol_L[:, row, column]
            np.testing.assert_allclose(weights / weights.sum(), dissolved / dissolved.sum(), rtol=1e-9, atol=1e-12)
        with self.assertWarns(DeprecationWarning):
            legacy = pb.boltzmann_smooth(fixed, thermal_scale=2.0)
        self.assertAlmostEqual(legacy.width_J_mol, 2 * smoothed.width_J_mol)

    def test_sweeps_are_compact_and_cancellable(self) -> None:
        engine = pb.ConcentrationSweepEngine(self.database)
        sweep = engine.calculate("Fe", pb.PourbaixConditions(**SMALL), -8.0, -2.0, 4, allow_incomplete=True)
        self.assertEqual(len(sweep.diagrams), 4)
        self.assertIsNone(sweep.diagrams[0].transformed_gibbs_J_mol_metal)
        with self.assertRaises(pb.CalculationCancelled):
            engine.calculate("Fe", pb.PourbaixConditions(**SMALL), -8.0, -2.0, 4,
                             progress=lambda fraction: fraction < 0.5, allow_incomplete=True)

    def test_periodic_screen_statuses_and_rhe(self) -> None:
        strict = pb.screen_periodic_table(self.database, pH=14, potential_V=1.6, reference="RHE",
                                          allow_incomplete=False)
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
        experimental = pb.PourbaixEngine(self.database).calculate("Fe", conditions, allow_incomplete=True)
        np.testing.assert_allclose(official.oer_V, experimental.oer_V)

        class StubClient:
            def calculate(self, *_args, **_kwargs):
                return official

        comparison = pb.OfficialMaterialsProjectComparator(pb.PourbaixEngine(self.database), StubClient()).compare(
            "Fe", conditions, allow_incomplete=True
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
        cls.calculation = pb.calculate(pb.Scenario("Fe", allow_incomplete=True, **SMALL))

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
        calculation = pb.calculate(pb.Scenario("Fe", mode="mass_balance", allow_incomplete=True, **SMALL))
        with self.assertRaises(ValueError):
            pb.stability_uncertainty(calculation.diagram)


try:
    import pymatgen.analysis.pourbaix_diagram  # noqa: F401
    HAS_PYMATGEN = True
except ImportError:
    HAS_PYMATGEN = False


@unittest.skipUnless(HAS_PYMATGEN, "pymatgen is not installed")
class PymatgenCrossCheckTests(unittest.TestCase):
    def test_every_system_matches_pymatgen_with_aligned_constants(self) -> None:
        from pourbase.crosscheck import crosscheck

        database = pb.open_database()
        water = database.reference_state.water_gibbs_energy_J_mol
        for symbol, _name in database.available_systems():
            with self.subTest(symbol=symbol):
                diagram = pb.calculate(pb.Scenario(symbol, allow_incomplete=True, **SMALL), database).diagram
                result = crosscheck(diagram, water, aligned=True)
                self.assertEqual(result.agreement, 1.0)
                self.assertLess(result.max_energy_difference_eV, 1e-9)


class UserSpeciesTests(unittest.TestCase):
    def test_csv_species_are_added_or_replace_bundled_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "own.csv"
            path.write_text(
                "symbol,species,formula,charge,phase,gibbs_energy_kJ_mol,uncertainty_kJ_mol,citation,replaces\n"
                "Cu,CuO (own),CuO,0,solid,-140.0,1.5,Lab notebook,\n"
                "Cu,Cu⁺ (own),Cu,1,aqueous,40.0,,Example 2024,gfe-cu-cu-q+1-aqueous-aq\n",
                encoding="utf-8",
            )
            database = pb.with_user_species(pb.open_database(), path)
            species = pb.calculate(pb.Scenario("Cu", allow_incomplete=True, **SMALL), database).diagram.system.species
        own = {item.species: item for item in species if item.gibbs_status is pb.EvidenceStatus.USER_SUPPLIED}
        self.assertEqual(set(own), {"CuO (own)", "Cu⁺ (own)"})
        self.assertEqual(own["CuO (own)"].electrons_per_metal, 2)
        self.assertEqual(own["CuO (own)"].gibbs_uncertainty_J_mol, 1500.0)
        self.assertNotIn("gfe-cu-cu-q+1-aqueous-aq", {item.record_id for item in species})

    def test_formulas_with_other_elements_are_rejected(self) -> None:
        species = pb.UserSpecies("Cu", "CuCl", "CuCl", 0, "solid", -120_000.0, "test")
        with self.assertRaises(ValueError):
            pb.with_user_species(pb.open_database(), [species])


class SelectionPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = pb.open_database()
        cls.policy = pb.SelectionPolicy.default()
        cls.selection = pb.select(cls.database, cls.policy)

    def test_ineligible_values_are_never_chosen(self) -> None:
        for item in self.selection.values():
            self.assertNotIn(item.chosen.status, self.policy.ineligible_statuses)

    def test_classes_and_families_follow_the_policy_order(self) -> None:
        for item in self.selection.values():
            best = min(self.policy.rank_of(candidate.family) for candidate in item.candidates)
            if not item.basis.startswith("override"):
                self.assertEqual(self.policy.rank_of(item.chosen.family), best, item.record_id)
        contested = [item for item in self.selection.values()
                     if {"NBS Tables", "NIST-JANAF"} <= {candidate.family for candidate in item.candidates}]
        self.assertTrue(contested)
        self.assertTrue(all(item.chosen.family == "NBS Tables" for item in contested))

    def test_reordering_families_changes_the_selection_and_the_energies(self) -> None:
        janaf_first = self.policy.with_family_order(
            "B", ["NIST-JANAF", "NBS Tables", "NBS Technical Notes", "Robie & Hemingway", "Miron", "NIST WebBook"])
        changes = pb.compare_policies(self.database, self.policy, janaf_first, ("gibbs_energy_of_formation",))
        self.assertTrue(changes)
        self.assertTrue(all(change.second.family == "NIST-JANAF" for change in changes))
        change = changes[0]
        symbol = self.database._rows("SELECT symbol FROM species WHERE record_id = ?", (change.record_id,))[0][0]
        species = {item.record_id: item for item in pb.with_policy(self.database, janaf_first)
                   .load_system(symbol).species}
        self.assertEqual(species[change.record_id].gibbs_energy_J_mol, change.second.value)

    def test_overrides_win_and_keep_their_reason(self) -> None:
        item = next(selection for selection in self.selection.values() if len(selection.candidates) > 1
                    and selection.property_name == "gibbs_energy_of_formation")
        other = next(candidate for candidate in item.candidates if candidate.value_id != item.chosen.value_id)
        policy = self.policy.with_override(item.record_id, item.property_name, other.source_id, "test reason")
        chosen = pb.select(self.database, policy)[(item.record_id, item.property_name)]
        self.assertEqual(chosen.chosen.source_id, other.source_id)
        self.assertEqual(chosen.basis, "override: test reason")

    def test_a_policy_file_round_trips_and_combines_with_user_species(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.toml"
            text = self.policy.source_text.replace('name = "pourbase default"', 'name = "mine"')
            path.write_text(text, encoding="utf-8")
            loaded = pb.SelectionPolicy.load(path)
            own = Path(directory) / "own.csv"
            own.write_text("symbol,species,formula,charge,phase,gibbs_energy_kJ_mol,uncertainty_kJ_mol,citation,replaces\n"
                           "Cu,CuO (own),CuO,0,solid,-140.0,,test,\n", encoding="utf-8")
            both = pb.with_user_species(pb.with_policy(self.database, loaded), own)
            other_way = pb.with_policy(pb.with_user_species(self.database, own), loaded)
            for database in (both, other_way):
                self.assertIn("CuO (own)", {item.species for item in database.load_system("Cu").species})
        self.assertEqual(loaded.name, "mine")
        self.assertNotEqual(loaded.fingerprint, self.policy.fingerprint)
        self.assertEqual(pb.select(self.database, loaded).keys(), self.selection.keys())


class DatasetTests(unittest.TestCase):
    def test_a_csv_becomes_a_database_of_only_its_species(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "zinc.csv"
            path.write_text("symbol,species,formula,charge,phase,gibbs_energy_kJ_mol,uncertainty_kJ_mol,citation,replaces\n"
                            "Zn,Zn,Zn,0,solid,0,,reference,\nZn,Zn²⁺,Zn,2,aqueous,-147.1,0.2,notes,\n"
                            "Zn,ZnO,ZnO,0,solid,-320.5,,notes,\n", encoding="utf-8")
            database = pb.open_dataset(path)
            self.assertEqual(database.available_systems(), (("Zn", "Zinc (Zn)"),))
            self.assertEqual(len(database.load_system("Zn").species), 3)
            calculation = pb.calculate(pb.Scenario("Zn", **SMALL), database)
            self.assertEqual({item.species for item in calculation.stable_species}, {"Zn", "Zn²⁺", "ZnO"})
            self.assertEqual(database.reference_state, pb.open_database().reference_state)
            record = database.species_records((calculation.stable_species[0].record_id,))[0]
            self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.source.citation in {"reference", "notes"}, True)
            self.assertEqual(pb.open_dataset(database.path).available_systems(), database.available_systems())


class SensitivityAndSourcesTests(unittest.TestCase):
    def test_selection_sensitivity_reproduces_the_paper(self) -> None:
        database = pb.ThermodynamicDatabase.bundled()
        diagram = pb.calculate(pb.Scenario("Gd"), database).diagram
        result = pb.selection_sensitivity(diagram, database.selections, samples=300)
        self.assertAlmostEqual(result.unfixed_fraction, 0.256, delta=0.01)
        critical = pb.selection_sensitivity(pb.calculate(pb.Scenario("Fe"), database).diagram, database.selections,
                                            samples=300, classes={"A", "B", "C"})
        self.assertAlmostEqual(critical.unfixed_fraction, 0.020, delta=0.005)

    def test_diagram_sources_group_publications(self) -> None:
        from pourbase.citations import diagram_sources, to_bibtex

        calculation = pb.calculate(pb.Scenario("Co"))
        publications = diagram_sources(calculation)
        labels = [item.label for item in publications]
        self.assertEqual(len(labels), len(set(labels)))
        self.assertEqual(to_bibtex(publications).count("@misc{"), len(publications))

