"""Pressure, material and equilibrium conventions for precipitated MnCO3."""
import json
import math
import unittest
from dataclasses import replace

import numpy as np
import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K, FARADAY_C_MOL
from pourbase.engine import transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature
from pourbase.uncertainty import stability_uncertainty

RID = 'r11m-mn-mnco3-precipitated'
G = 'gibbs_energy_of_formation'
H = 'enthalpy_of_formation'
RTL = GAS_CONSTANT_J_MOL_K * 298.15 * math.log(10)


class SyntheticManganeseCarbonateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()
        cls.system = cls.db.load_system('Mn', ligand_ids=('carbonate-co3',))
        cls.precipitate = next(s for s in cls.system.species if s.record_id == RID)
        cls.crystal = next(s for s in cls.system.species if s.record_id == 'r07-mn-mnco3-rhodochrosite')

    def test_formation_pressure_conversion_preserves_the_original_number(self):
        details = json.loads(self.db.metadata['R11m_precipitated_MnCO3_observations'])
        d = next(x for x in details if x['property'] == G)
        self.assertEqual((d['source_value'], d['source_unit'], d['source_pressure_bar']),
                         (-194.7, 'kcal/mol', 1.01325))
        self.assertEqual((d['source_printed_page'], d['source_pdf_page']), (402, 1))
        self.assertEqual(d['delta_gas_mol_per_mol'], -1.5)
        # Lowering the O2 reference chemical potential raises this formation G.
        oxygen_mu_change = GAS_CONSTANT_J_MOL_K * 298.15 * math.log(1 / 1.01325)
        expected = -194.7 * 4184 - 1.5 * oxygen_mu_change
        original = next(r for r in self.db.species_records((RID,))[0].reported
                        if r.source.source_id == 'R11m_Garrels1960_precipitated_pressure_adaptation')
        self.assertAlmostEqual(original.value, expected)
        self.assertAlmostEqual(d['pressure_correction_J_mol'], 48.9457169698282)
        self.assertIsNone(d['total_uncertainty'])

    def test_material_identity_and_open_enthalpy_keep_missing_properties_explicit(self):
        record = self.db.species_records((RID,))[0]
        self.assertEqual(len(record.reported), 3)
        self.assertEqual(self.db.selections[(RID, G)].chosen.evidence_class, 'E')
        self.assertEqual(self.db.selections[(RID, H)].chosen.evidence_class, 'B')
        self.assertEqual(self.db.selections[(RID, H)].chosen.value, -883200)
        self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
        self.assertTrue(all(r.uncertainty is None for r in record.reported))
        self.assertEqual(self.crystal.gibbs_energy_J_mol, -819100)
        with self.db.connect() as c:
            phase = c.execute('SELECT * FROM phases WHERE record_id=?', (RID,)).fetchone()
            self.assertEqual(phase['identity_status'], 'phase_identity_incomplete')
            self.assertIsNone(phase['spacegroup_number'])
        self.assertNotIn(RID, {s.record_id for s in self.db.load_system('Mn').species})
        self.assertNotIn(RID, {s.record_id for s in at_temperature(self.db, 323.15).load_system(
            'Mn', ligand_ids=('carbonate-co3',)).species})

    def test_transformed_energy_keeps_the_precipitate_above_crystalline_rhodochrosite(self):
        s = self.precipitate
        self.assertEqual((s.formula_ascii, s.metal_count, s.ligand_count, s.ligand_charge,
                          s.electrons_per_metal, s.protons_per_metal), ('MnCO3', 1, 1, -2, 2, 0))
        for loga in (-6, -3, -1):
            cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('carbonate-co3', log10_free_activity=loga),)))
            for ph, potential in ((0, -1), (7, 0), (14, 1)):
                energy = float(transformed_gibbs_J_mol_metal(s, self.db.reference_state, cfg, ph, potential))
                expected = s.gibbs_energy_J_mol + 527810 - RTL*loga - 2*FARADAY_C_MOL*potential
                self.assertAlmostEqual(energy, expected)
                crystal = float(transformed_gibbs_J_mol_metal(
                    self.crystal, self.db.reference_state, cfg, ph, potential))
                self.assertAlmostEqual(energy - crystal, 3883.7812686586985)

    def test_restricted_precipitate_solubility_and_metal_boundary_match_thermodynamics(self):
        solid = self.precipitate
        ion = next(s for s in self.system.species if s.formula_ascii == 'Mn' and s.charge == 2)
        metal = next(s for s in self.system.species if s.formula_ascii == 'Mn' and s.phase == 'solid')
        ksp = math.exp(-(ion.gibbs_energy_J_mol + solid.ligand_gibbs_energy_J_mol -
                          solid.gibbs_energy_J_mol) / (GAS_CONSTANT_J_MOL_K*298.15))
        self.assertAlmostEqual(math.log10(ksp), -10.39)
        for loga in (-6, -3, -1):
            cfg = pb.PourbaixConditions(pH_points=3, U_points=3,
                ligand_activities=pb.LigandActivityModel((
                    pb.LigandActivity('carbonate-co3', log10_free_activity=loga),)))
            inventory = pb.MassBalanceEngine(self.db).calculate_system(
                replace(self.system, species=(ion, solid), excluded=()), cfg, pb.TotalMetalConcentration(1e-6))
            np.testing.assert_allclose(inventory.dissolved_metal_mol_L, min(1e-6, ksp/10**loga), rtol=1e-11)
            np.testing.assert_allclose(inventory.dissolved_metal_mol_L +
                1e-6*inventory.precipitated_metal_fraction, 1e-6, rtol=1e-11)
            boundary = (solid.gibbs_energy_J_mol + 527810 - RTL*loga)/(2*FARADAY_C_MOL)
            for shift, winner in ((-.01, metal), (.01, solid)):
                diagram = pb.PourbaixEngine(self.db).calculate_system(
                    replace(self.system, species=(metal, solid), excluded=()),
                    replace(cfg, U_min_V=boundary+shift-.001, U_max_V=boundary+shift+.001))
                self.assertEqual({diagram.system.species[int(i)].record_id
                                  for i in diagram.stable_species_index.flat}, {winner.record_id})

    def test_uncertainty_bands_identify_the_assumed_precipitate_interval(self):
        cfg = pb.PourbaixConditions(pH_points=3, U_points=3,
            ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('carbonate-co3', log10_free_activity=-3),)))
        diagram = pb.PourbaixEngine(self.db).calculate_system(
            replace(self.system, species=(self.crystal, self.precipitate), excluded=()), cfg)
        self.assertFalse(stability_uncertainty(diagram).uncertain.any())
        wider = stability_uncertainty(diagram, confidence_sigma=3)
        self.assertTrue(wider.uncertain.all())
        self.assertIn(RID, wider.assumed_record_ids)
        self.assertIsNone(self.precipitate.gibbs_uncertainty_J_mol)


if __name__ == '__main__':
    unittest.main()
