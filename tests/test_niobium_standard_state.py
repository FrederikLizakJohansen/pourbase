"""Niobium hydration, finite-medium eligibility and fitted-model thermodynamics."""
import json
import math
import unittest
from dataclasses import replace

import numpy as np
import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K
from pourbase.engine import transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature

G = 'gibbs_energy_of_formation'
H = 'enthalpy_of_formation'
S = 'absolute_entropy'
IDS = {4: 'r11n-nb-nb-oh-4-q+1-infinite-dilution',
       5: 'gfe-nb-hnbo3-q+0-aqueous-aq',
       6: 'r11n-nb-nb-oh-6-q-1-infinite-dilution',
       7: 'r11n-nb-nb-oh-7-q-2-infinite-dilution'}
RTL = GAS_CONSTANT_J_MOL_K * 298.15 * math.log(10)


class NiobiumStandardStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()
        cls.system = cls.db.load_system('Nb')
        cls.ions = {n: next(s for s in cls.system.species if s.record_id == rid)
                    for n, rid in IDS.items()}

    def test_finite_medium_evidence_is_retained_outside_standard_state_selection(self):
        history = json.loads(self.db.metadata['R11n_niobium_route_history'])
        for rid, raw in zip(history['finite_I_records'], [-1208600, -1448300, -932100]):
            record = self.db.species_records((rid,))[0]
            self.assertTrue(any(v.property == G and v.value == raw for v in record.reported))
            self.assertNotIn((rid, G), self.db.selections)
            self.assertIn(rid, {s.record_id for s in self.system.excluded})
            exclusion = next(e for e in self.db.policy.exclusions if e.record_id == rid)
            self.assertIn('I=1M', exclusion.reason)
        oxide = self.db.species_records(('r11l-nb-nb2o5-high-temperature',))[0]
        self.assertEqual(oxide.thermochemistry.gibbs_energy_J_mol.value, -1766000)
        self.assertIn('high-temperature', oxide.phase_detail)

    def test_neutral_water_equivalent_normalization_preserves_the_transformed_energy(self):
        neutral = self.ions[5]
        hydrated = replace(neutral, formula_ascii='Nb(OH)5', core_oxygen_count=5,
                           core_hydrogen_count=5, gibbs_energy_J_mol=-1424000)
        cfg = pb.PourbaixConditions()
        for ph, potential in ((0, -1), (7, 0), (14, 1)):
            self.assertAlmostEqual(float(transformed_gibbs_J_mol_metal(
                neutral, self.db.reference_state, cfg, ph, potential)),
                float(transformed_gibbs_J_mol_metal(
                    hydrated, self.db.reference_state, cfg, ph, potential)))
        self.assertEqual(self.db.selections[(IDS[5], H)].chosen.value, -1652000 + 2*285830)
        self.assertAlmostEqual(self.db.selections[(IDS[5], S)].chosen.value, 110 - 2*69.91)
        record = self.db.species_records((IDS[5],))[0]
        self.assertEqual(len(record.reported), 6)
        self.assertTrue(any(v.value == -990771.2 for v in record.reported))
        for n, rid in IDS.items():
            chosen = self.db.selections[(rid, G)].chosen
            self.assertEqual(chosen.evidence_class, 'E')
            self.assertEqual(chosen.uncertainty, 8000)
            self.assertEqual((self.ions[n].charge, self.ions[n].electrons_per_metal,
                              self.ions[n].protons_per_metal), (5-n, 5, n))
        basis = json.loads(self.db.metadata['source_reuse_R11n_niobium'])
        self.assertIn('own explicit phase assumption', json.dumps(
            self.db.metadata['R11n_niobium_route_history']))
        self.assertIn('no separate confidence footnote', basis['uncertainty_scope'])

    def test_hydrolysis_ratios_and_metal_balance_follow_the_rounded_source_model(self):
        aqueous = replace(self.system, species=tuple(self.ions.values()), excluded=())
        cfg = pb.PourbaixConditions(pH_points=9, U_points=3)
        for model in (pb.IdealActivityCoefficientModel(), pb.DaviesActivityCoefficientModel(.01)):
            diagram = pb.MassBalanceEngine(self.db, activity_coefficient_model=model).calculate_system(
                aqueous, cfg, pb.TotalMetalConcentration(1e-6))
            index = {s.record_id: i for i, s in enumerate(diagram.aqueous_species)}
            np.testing.assert_allclose(diagram.aqueous_concentration_mol_L.sum(axis=0), 1e-6, rtol=1e-11)
            for n, m, published_logk in ((4, 5, -1.7), (5, 6, -5), (6, 7, -9.8)):
                def hydrated_g(k):
                    return self.ions[k].gibbs_energy_J_mol + (-2*237129 if k == 5 else 0)
                reaction_g = hydrated_g(m) - hydrated_g(n) + 237129
                self.assertLess(abs(reaction_g + RTL*published_logk), 1100,
                                'Table7 formation energies are rounded to1kJ/mol')
                ratio = (diagram.aqueous_activity[index[IDS[m]]] /
                         diagram.aqueous_activity[index[IDS[n]]])
                expected = np.broadcast_to(10**(-reaction_g/RTL + diagram.pH), ratio.shape)
                np.testing.assert_allclose(ratio, expected, rtol=1e-10)
                boundary = reaction_g/RTL
                pair = replace(aqueous, species=(self.ions[n], self.ions[m]))
                for shift, winner in ((-.02, n), (.02, m)):
                    fixed = pb.PourbaixEngine(self.db).calculate_system(pair, replace(
                        cfg, pH_min=boundary+shift-.001, pH_max=boundary+shift+.001, pH_points=3))
                    self.assertEqual({fixed.system.species[int(i)].record_id
                                      for i in fixed.stable_species_index.flat}, {IDS[winner]})

    def test_temperature_uses_same_source_enthalpy_with_explicit_model_limits(self):
        for temp in (323.15, 343.15):
            td = at_temperature(self.db, temp)
            system = td.load_system('Nb')
            for rid in IDS.values():
                item = next(s for s in system.species if s.record_id == rid)
                g = self.db.selections[(rid, G)].chosen.value
                h = self.db.selections[(rid, H)].chosen.value
                self.assertAlmostEqual(item.gibbs_energy_J_mol, g - (temp-298.15)*(h-g)/298.15)
                self.assertGreater(item.temperature_uncertainty_J_mol, 0)
        basis = json.loads(self.db.metadata['source_reuse_R11n_niobium'])
        self.assertIn('limited data', basis['model_scope'])
        self.assertIn('Solids change atpH>9', basis['model_scope'])


if __name__ == '__main__':
    unittest.main()
