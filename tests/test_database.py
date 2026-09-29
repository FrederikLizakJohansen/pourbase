from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pourbase import (  # noqa: E402
    boltzmann_smooth,
    calculate_pourbaix,
    calculate_periodic_table,
    ConcentrationSweepEngine,
    GibbsEnergyPolicy,
    MassBalanceEngine,
    OfficialMaterialsProjectComparator,
    PourbaixConditions,
    PourbaixEngine,
    ThermodynamicDatabase,
    TotalMetalConcentration,
    boundary_equations,
    convert_concentration,
    evaluate_official_materials_project_entries,
    metal_fraction_grid,
    open_database,
    plating_potentials,
    plot_official_materials_project_comparison,
    plot_boltzmann_diagram,
    speciation_at,
    write_mp_thermochemistry_bundle,
    thermodynamic_species_equivalence_key,
)
from pourbase.constants import GAS_CONSTANT_J_MOL_K, LN_10  # noqa: E402
from pourbase.models import (  # noqa: E402
    GasFugacityModel,
    ReferenceState,
    ThermodynamicSpecies,
)
from pourbase.plotting import _phase_boundary_segments  # noqa: E402
from pourbase.service import calculate, render_grid_csv  # noqa: E402


class FakeMPComposition:
    def __init__(self, formula: str, amounts: dict[str, float]) -> None:
        self.reduced_formula = formula
        self.amounts = amounts

    def get(self, element: str, default: float = 0.0) -> float:
        return self.amounts.get(element, default)


class FakeMPEntry:
    def __init__(
        self,
        entry_id: str,
        name: str,
        phase_type: str,
        formula: str,
        amounts: dict[str, float],
        energy: float,
        npH: float,
        nPhi: float,
    ) -> None:
        self.entry_id = entry_id
        self.name = name
        self.phase_type = phase_type
        self.composition = FakeMPComposition(formula, amounts)
        self.normalization_factor = 1.0 / amounts["Fe"]
        self.normalized_energy = energy
        self.npH = npH
        self.nPhi = nPhi

    def normalized_energy_at_conditions(self, pH: object, eh_V: object) -> object:
        return (
            self.normalized_energy
            + self.npH * self.normalization_factor * 0.0591 * pH
            + self.nPhi * self.normalization_factor * eh_V
        )


class PublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.path = ROOT / "src" / "pourbase" / "data" / "pourbase.sqlite"
        cls.database = ThermodynamicDatabase(cls.path)

    def test_database_has_only_public_tables(self) -> None:
        with closing(sqlite3.connect(self.path)) as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
            self.assertEqual(
                tables,
                {
                    "metadata",
                    "species",
                    "thermochemistry",
                    "sources",
                    "phases",
                    "warnings",
                    "materials_project_matches",
                    "materials_project_energies",
                    "ligands",
                    "reported_thermochemistry",
                    "computational_fallbacks",
                    "element_coverage",
                },
            )
            self.assertEqual(
                connection.execute("SELECT count(*) FROM species").fetchone()[0], 460
            )
            self.assertEqual(connection.execute("SELECT count(*) FROM reported_thermochemistry").fetchone()[0], 1412)
            self.assertEqual(connection.execute("SELECT count(*) FROM computational_fallbacks").fetchone()[0], 6)
            self.assertEqual(connection.execute("SELECT count(*) FROM element_coverage").fetchone()[0], 118)

            self.assertEqual(
                connection.execute(
                    """SELECT metal_oxidation_state,electron_coefficient_per_metal
                       FROM species WHERE formula_ascii='TiH2'"""
                ).fetchone(),
                (2.0, -2.0),
            )
            self.assertEqual(
                connection.execute("PRAGMA integrity_check").fetchone()[0], "ok"
            )
            self.assertEqual(
                connection.execute("PRAGMA foreign_key_check").fetchall(), []
            )
            metadata = dict(connection.execute("SELECT key,value FROM metadata"))
            self.assertEqual(metadata["dataset_version"], "1.0.0")
            self.assertEqual(metadata["freeze_date"], "2026-09-24")
            self.assertEqual(
                metadata["publication_status"],
                "release_candidate_pending_collaborator_review",
            )
            self.assertNotIn("derived_from", metadata)

        publication_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                ROOT / "README.md",
                ROOT / "docs" / "DATA_DICTIONARY.md",
                ROOT / "CITATION.cff",
            )
        )
        self.assertNotIn("audit", publication_text.lower())

    def test_mp_fallback_is_opt_in_and_completes_supported_systems(self) -> None:
        strict = self.database.load_system("Pt")
        self.assertEqual(
            sum(item.reason == "recommended_gibbs_energy_unavailable" for item in strict.excluded),
            2,
        )
        hybrid = self.database.load_system(
            "Pt", energy_policy=GibbsEnergyPolicy.EXPERIMENTAL_THEN_MP
        )
        fallback = [
            item for item in hybrid.species
            if item.gibbs_status == "materials_project_sisso_300K_fallback"
        ]
        self.assertEqual({item.formula_ascii for item in fallback}, {"PtO", "PtO2"})
        overview = calculate_periodic_table(
            {
                "periodic_pH": 0,
                "periodic_potential_V": 1.6,
                "potential_reference": "RHE",
                "energy_policy": "experimental_then_mp",
            },
            self.database,
        )
        self.assertEqual(overview["periodic_position_count"], 118)
        self.assertEqual(overview["supported_system_count"], 74)
        self.assertEqual(overview["calculated_system_count"], 74)

    def test_fixed_activity_diagram(self) -> None:
        diagram = PourbaixEngine(self.database).calculate("Fe", PourbaixConditions())
        self.assertGreaterEqual(len(diagram.stable_species), 2)
        self.assertEqual(diagram.stable_species_index.shape, (301, 281))

    def test_single_import_convenience_api_uses_bundled_database(self) -> None:
        database = open_database()
        self.assertEqual(len(database.available_systems()), 74)
        diagram = calculate_pourbaix(
            "Fe", PourbaixConditions(pH_points=9, eh_points=11)
        )
        self.assertEqual(diagram.stable_species_index.shape, (11, 9))

    def test_carbon_diagram_exposes_gas_fugacity_settings(self) -> None:
        _, result = calculate(
            {
                "symbol": "C",
                "pH_points": 21,
                "eh_points": 23,
                "log10_gas_fugacity": -2.0,
                "gas_fugacity_overrides": {
                    "gfe-c-co2-q+0-gas-g": -3.5,
                },
            },
            self.database,
        )
        gas_model = result["conditions"]["gas_fugacity_model"]
        self.assertEqual(gas_model["standard_fugacity_bar"], 1.0)
        self.assertEqual(gas_model["default_log10_fugacity"], -2.0)
        self.assertEqual(
            gas_model["overrides"]["gfe-c-co2-q+0-gas-g"], -3.5
        )

    def test_gas_fugacity_uses_the_one_bar_standard_state(self) -> None:
        species = ThermodynamicSpecies(
            record_id="test-n2-gas", system="Nitrogen (N)", symbol="N",
            species="N2", formula_ascii="N2", phase="gas", phase_detail="gas",
            charge=0.0, metal_count=2.0, core_oxygen_count=0.0,
            core_hydrogen_count=0.0, ligand_id=None, ligand_count=0.0,
            ligand_charge=0.0, gibbs_energy_J_mol=0.0, gibbs_status="verified",
            source_id="test-source",
        )
        reference = ReferenceState(298.15, 1.0, -237129.0)
        standard = PourbaixEngine.transformed_gibbs_J_mol_metal(
            species, reference, PourbaixConditions(), 7.0, 0.0
        )
        dilute = PourbaixEngine.transformed_gibbs_J_mol_metal(
            species,
            reference,
            PourbaixConditions(
                gas_fugacities=GasFugacityModel(default_log10_fugacity=-2.0)
            ),
            7.0,
            0.0,
        )
        expected_shift = -GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        self.assertAlmostEqual(float(dilute - standard), expected_shift, places=9)
        self.assertEqual(thermodynamic_species_equivalence_key(species)[0], "gas")

    def test_periodic_table_point_screen_and_rhe_conversion(self) -> None:
        overview = calculate_periodic_table(
            {
                "periodic_pH": 0.0,
                "periodic_potential_V": 1.6,
                "potential_reference": "RHE",
                "concentration_value": -6.0,
                "concentration_unit": "log10_molar",
            },
            self.database,
        )
        self.assertEqual(overview["supported_system_count"], 74)
        self.assertEqual(overview["calculated_system_count"], 69)
        self.assertAlmostEqual(overview["conditions"]["potential_V_vs_SHE"], 1.6)
        by_symbol = {item["symbol"]: item for item in overview["elements"]}
        self.assertEqual(by_symbol["Fe"]["stable_species"], "Fe³⁺")
        self.assertEqual(by_symbol["Fe"]["category"], "dissolved_or_gas")
        self.assertEqual(by_symbol["Ti"]["stable_species"], "TiO₂")
        self.assertEqual(by_symbol["Ti"]["category"], "solid_oxide")
        self.assertEqual(by_symbol["Ti"]["structure_label"], "rutile")
        self.assertEqual(by_symbol["Pt"]["status"], "incomplete")
        self.assertIsNotNone(by_symbol["Ti"]["gibbs_source"])

        alkaline = calculate_periodic_table(
            {
                "periodic_pH": 14.0,
                "periodic_potential_V": 1.6,
                "potential_reference": "RHE",
                "concentration_value": -6.0,
                "concentration_unit": "log10_molar",
                "allow_incomplete": True,
            },
            self.database,
        )
        self.assertAlmostEqual(
            alkaline["conditions"]["potential_V_vs_SHE"],
            1.6 + alkaline["conditions"]["rhe_to_she_offset_V"],
        )
        self.assertEqual(alkaline["calculated_system_count"], 74)

    def test_boltzmann_soft_min_math_and_plot(self) -> None:
        diagram = PourbaixEngine(self.database).calculate(
            "Fe", PourbaixConditions(pH_points=19, eh_points=21)
        )
        smoothed = boltzmann_smooth(diagram)
        np.testing.assert_allclose(smoothed.weights.sum(axis=0), 1.0, atol=1e-14)
        np.testing.assert_array_equal(
            np.argmax(smoothed.weights, axis=0), diagram.stable_species_index
        )
        row, column = 10, 9
        order = np.argsort(smoothed.weights[:, row, column])[-2:]
        first, second = (int(order[0]), int(order[1]))
        observed_log_ratio = np.log(
            smoothed.weights[first, row, column] / smoothed.weights[second, row, column]
        )
        energies = diagram.transformed_gibbs_J_mol_metal
        assert energies is not None
        expected_log_ratio = (
            -(energies[first, row, column] - energies[second, row, column])
            / smoothed.effective_thermal_energy_J_mol
        )
        self.assertAlmostEqual(observed_log_ratio, expected_log_ratio, places=12)
        self.assertTrue(np.all(smoothed.dominant_weight > 0.0))
        self.assertTrue(np.all(smoothed.dominant_weight <= 1.0))
        self.assertIn("not phase fractions", smoothed.interpretation)
        axis = plot_boltzmann_diagram(smoothed, label_domains=False)
        self.assertTrue(axis.images)
        import matplotlib.pyplot as plt

        plt.close(axis.figure)

    def test_mass_balance_diagram(self) -> None:
        diagram = MassBalanceEngine(self.database).calculate(
            "Zn", PourbaixConditions(), TotalMetalConcentration(1e-6)
        )
        state = diagram.state_at(7.0, 0.0)
        self.assertAlmostEqual(
            state.dissolved_metal_mol_L + state.precipitated_metal_mol_L,
            1e-6,
            places=12,
        )

    def test_phase_boundaries_are_emitted_once(self) -> None:
        regions = np.asarray([[0, 2], [1, 2]])
        segments = _phase_boundary_segments(
            regions, np.asarray([0.0, 1.0]), np.asarray([-1.0, 1.0])
        )
        normalized = {
            tuple(point for pair in segment for point in pair) for segment in segments
        }
        self.assertEqual(len(segments), 3)
        self.assertEqual(len(normalized), len(segments))

    def test_calculation_output_contains_publication_details(self) -> None:
        _, result = calculate(
            {"symbol": "Fe", "pH_points": 21, "eh_points": 21}, self.database
        )
        records = result["substances"]["included"]
        self.assertTrue(records)
        self.assertTrue(any(item["stable_on_grid"] for item in records))
        hydrolysis = next(item for item in records if item["species"] == "Fe(OH)₂⁺")
        self.assertIn("citation", hydrolysis["thermochemistry"]["gibbs_source"])
        self.assertTrue(hydrolysis["warnings"])

    def test_concentration_units_and_density(self) -> None:
        ppm = convert_concentration("Fe", 55.845, "ppm")
        self.assertAlmostEqual(ppm.molar_concentration, 0.001)
        weight = convert_concentration(
            "Fe", 1.0, "wt_percent", solution_density_kg_L=1.2
        )
        self.assertAlmostEqual(weight.molar_concentration, 12.0 / 55.845)
        self.assertTrue(weight.assumptions)

    def test_adjacent_equations_and_plating_are_gibbs_derived(self) -> None:
        diagram = PourbaixEngine(self.database).calculate(
            "Fe", PourbaixConditions(pH_points=81, eh_points=81)
        )
        equations = boundary_equations(diagram, self.database)
        self.assertTrue(equations)
        self.assertTrue(all(item.source_ids for item in equations))
        nernst = next(item for item in equations if item.kind == "nernst")
        pH = 5.0
        eh = nernst.eh_intercept_V + nernst.eh_slope_V_per_pH * pH
        left = next(
            item
            for item in diagram.system.species
            if item.record_id == nernst.left_record_id
        )
        right = next(
            item
            for item in diagram.system.species
            if item.record_id == nernst.right_record_id
        )
        reference = self.database.reference_state
        left_g = PourbaixEngine.transformed_gibbs_J_mol_metal(
            left, reference, diagram.conditions, pH, eh
        )
        right_g = PourbaixEngine.transformed_gibbs_J_mol_metal(
            right, reference, diagram.conditions, pH, eh
        )
        self.assertAlmostEqual(float(left_g), float(right_g), places=6)
        plating = plating_potentials(diagram, self.database)
        self.assertTrue(plating)
        self.assertTrue(all("e-" in item.reaction for item in plating))

    def test_database_integrated_speciation_conserves_metal(self) -> None:
        diagram = MassBalanceEngine(self.database).calculate(
            "Zn",
            PourbaixConditions(pH_points=31, eh_points=33),
            TotalMetalConcentration(2e-4),
        )
        fractions = metal_fraction_grid(diagram)
        np.testing.assert_allclose(fractions.sum(axis=0), 1.0, atol=1e-12)
        point = speciation_at(diagram, 7.0, 0.0)
        self.assertAlmostEqual(sum(item["metal_fraction"] for item in point), 1.0)
        self.assertTrue(all(item["gibbs_source_id"] for item in point))

    def test_concentration_sweep_and_csv_export(self) -> None:
        conditions = PourbaixConditions(pH_points=21, eh_points=23)
        sweep = ConcentrationSweepEngine(self.database).calculate(
            "Fe", conditions, -8.0, -2.0, 4
        )
        self.assertEqual(len(sweep.diagrams), 4)
        self.assertGreaterEqual(len(sweep.stable_species), 2)
        csv_text = render_grid_csv(sweep.diagrams[0]).decode("utf-8")
        self.assertEqual(len(csv_text.splitlines()), 1 + 21 * 23)
        self.assertIn("record_id", csv_text.splitlines()[0])

    def test_official_mp_evaluation_and_comparison_are_testable_offline(self) -> None:
        conditions = PourbaixConditions(pH_points=15, eh_points=17)
        entries = [
            FakeMPEntry("mp-metal", "Fe(s)", "Solid", "Fe", {"Fe": 1}, 0, 0, 0),
            FakeMPEntry("ion-fe2", "Fe[+2]", "Ion", "Fe", {"Fe": 1}, -0.9, 0, -2),
        ]
        official = evaluate_official_materials_project_entries(
            "Fe",
            conditions,
            entries,
            database_version="test-db",
            mp_api_version="test-api",
            pymatgen_version="test-pymatgen",
            filter_solids=True,
            use_gibbs_300K=False,
        )
        self.assertEqual(official.stable_phase_index.shape, (17, 15))
        self.assertFalse(official.stable_phase_index.flags.writeable)

        class StubClient:
            def calculate(self, *_: object, **__: object) -> object:
                return official

        comparison = OfficialMaterialsProjectComparator(
            PourbaixEngine(self.database),
            StubClient(),  # type: ignore[arg-type]
        ).compare("Fe", conditions)
        self.assertEqual(comparison.same_thermodynamic_species.shape, (17, 15))
        self.assertGreaterEqual(comparison.equivalent_domain_fraction, 0.0)
        self.assertLessEqual(comparison.equivalent_domain_fraction, 1.0)
        figure, axes = plot_official_materials_project_comparison(comparison)
        self.assertEqual(len(axes), 3)
        import matplotlib.pyplot as plt

        plt.close(figure)

    def test_reviewed_mp_matches_expose_energy_differences(self) -> None:
        matches = self.database.materials_project_comparisons("Fe")
        self.assertTrue(matches)
        self.assertTrue(all(item["mp_id"] for item in matches))
        selected = [
            item for item in matches if item["formation_energy_eV_atom"] is not None
        ]
        self.assertTrue(selected)
        self.assertTrue(
            all(item["mp_minus_experimental_eV_atom"] is not None for item in selected)
        )

    def test_mp_thermochemistry_bundle_is_reproducible_from_database(self) -> None:
        rows = self.database.materials_project_thermochemistry()
        self.assertEqual(len(rows), 299)
        self.assertEqual(len({item["record_id"] for item in rows}), 105)
        self.assertEqual(
            sum(item["experimental_enthalpy_eV_atom"] is not None for item in rows),
            288,
        )
        with tempfile.TemporaryDirectory() as directory:
            metadata = write_mp_thermochemistry_bundle(self.database, directory)
            output = Path(directory)
            self.assertEqual(metadata["materials_project_energy_rows"], 299)
            for name in (
                "mp-enthalpy-comparison.png",
                "mp-enthalpy-comparison.pdf",
                "mp-gibbs-comparison.png",
                "mp-gibbs-comparison.pdf",
                "mp-thermochemistry-points.csv",
                "mp-thermochemistry-metadata.json",
                "README.md",
            ):
                self.assertGreater((output / name).stat().st_size, 100)


if __name__ == "__main__":
    unittest.main()
