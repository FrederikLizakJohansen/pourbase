"""PSI hydrosulfide estimates preserve source alternatives and reaction conventions."""

import json
import math
import unittest

import numpy as np

import pourbase as pb
from pourbase.engine import transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature


class PSINickelHydrosulfideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()
        cls.derivations = json.loads(
            cls.database.metadata["R11d_nickel_hydrosulfide_derivations"])

    def test_formation_estimates_reproduce_source_reactions_and_keep_nea_alternative(self):
        for d in self.derivations:
            record = self.database.species_records((d["record_id"],))[0]
            observation = next(v for v in record.reported if v.source.source_id ==
                               "pourbase_R11d_Ni_hydrosulfide_derived_G")
            n = d["stoichiometric_HS"]
            rtln = 8.31446261815324 * 298.15 * math.log(10)
            self.assertAlmostEqual(
                -(observation.value + 45773 - n * 12080) / rtln, d["log10_beta"])
            self.assertIsNone(observation.uncertainty)
            self.assertEqual(observation.status, "source_verified_estimate")
            self.assertIn("further sublicensees", observation.source.locator)
            self.assertEqual(observation.selected_as_recommended, n == 2)
            if n == 1:
                self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.value, -63098)
                self.assertEqual(len(record.reported), 2)

    def test_sulfide_buffer_matches_full_hydrosulfide_formula_and_activity_response(self):
        system = self.database.load_system("Ni", ligand_ids=("sulfide-s",))
        rtln = 8.31446261815324 * 298.15 * math.log(10)
        for d in self.derivations:
            species = next(s for s in system.species if s.record_id == d["record_id"])
            n = d["stoichiometric_HS"]
            self.assertEqual((species.ligand_count, species.core_hydrogen_count,
                              species.core_oxygen_count, species.electrons_per_metal,
                              species.protons_per_metal), (n, n, 0, 2, -n))
            for pH in (7, 10, 14):
                energies = []
                for loghs in (-5, -4):
                    logs = loghs + pH - d["runtime_reference"]["HS_dissociation_pKa"]
                    cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
                        pb.LigandActivity("sulfide-s", log10_free_activity=logs),)))
                    actual = float(transformed_gibbs_J_mol_metal(
                        species, self.database.reference_state, cfg, pH, 0))
                    expected = (species.gibbs_energy_J_mol - n * (12080 + rtln * loghs)
                                + rtln * cfg.aqueous_activities.log10_activity_for(
                                    species.record_id, species.species, species.formula_ascii))
                    self.assertAlmostEqual(actual, expected)
                    energies.append(actual)
                self.assertAlmostEqual(energies[1] - energies[0], -n * rtln)

    def test_g_only_estimates_keep_missing_thermal_properties_and_reference_temperature_scope(self):
        for d in self.derivations:
            record = self.database.species_records((d["record_id"],))[0]
            self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
            self.assertIsNone(record.thermochemistry.formation_enthalpy_J_mol.value)
            self.assertNotIn(record.record_id, {s.record_id for s in
                at_temperature(self.database, 323.15).load_system(
                    "Ni", ligand_ids=("sulfide-s",)).species})

    def test_closed_balance_conserves_nickel_with_hydrosulfide_complex_present(self):
        cfg = pb.PourbaixConditions(pH_min=7, pH_max=14, pH_points=7, U_points=9,
            ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity("sulfide-s", log10_free_activity=-8),)))
        system = self.database.load_system("Ni", ligand_ids=("sulfide-s",))
        self.assertIn("r11d-ni-ni-hs-2-aqueous", {s.record_id for s in system.species})
        for model in (pb.IdealActivityCoefficientModel(), pb.DaviesActivityCoefficientModel(0.01)):
            result = pb.MassBalanceEngine(self.database, activity_coefficient_model=model).calculate(
                "Ni", cfg, pb.TotalMetalConcentration(1e-4))
            np.testing.assert_allclose(
                result.dissolved_metal_mol_L + 1e-4 * result.precipitated_metal_fraction,
                1e-4, rtol=1e-11, atol=1e-15)
