"""Source-scoped modern radium solubility adaptations and scientific effects."""
import json
import math
import unittest
from dataclasses import replace

import numpy as np
import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K, FARADAY_C_MOL
from pourbase.temperature import at_temperature

G = 'gibbs_energy_of_formation'
SID = 'R11o_Brown2022_CC_BY_solubility_adaptations'
CARB = 'r11l-ra-raco3-crystalline-estimate'
SULF = 'r11l-ra-raso4-crystalline'
RTL = GAS_CONSTANT_J_MOL_K * 298.15 * math.log(10)


class ModernRadiumFitsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()
        cls.system = cls.db.load_system('Ra', ligand_ids=('carbonate-co3',))
        cls.solid = next(s for s in cls.system.species if s.record_id == CARB)
        cls.ion = next(s for s in cls.system.species if s.charge == 2 and s.phase == 'aqueous')

    def test_open_evaluations_reconstruct_the_source_constants_and_keep_intervals_scoped(self):
        for rid, anion, k in ((CARB, -527810, -7.49), (SULF, -744530, -10.24)):
            record = self.db.species_records((rid,))[0]
            v = next(r for r in record.reported if r.source.source_id == SID)
            self.assertAlmostEqual((v.value + 561500 - anion) / RTL, k)
            self.assertEqual(v.status, 'source_verified_estimate')
            self.assertIsNone(v.uncertainty)
        self.assertEqual(self.db.selections[(CARB, G)].chosen.source_id, SID)
        self.assertEqual(self.db.selections[(CARB, G)].chosen.evidence_class, 'E')
        self.assertEqual(self.db.selections[(SULF, G)].chosen.value, -1365600)
        record = self.db.species_records((CARB,))[0]
        self.assertTrue(any(abs(r.value + 1136686.4788710426) < 1e-8 for r in record.reported))
        details = json.loads(self.db.metadata['R11o_radium_observations'])
        for d in details:
            self.assertEqual(d['source_pdf_page'], 5)
            self.assertEqual(d['source_article_page_AOP'], 4)
            self.assertAlmostEqual(d['logK_partial_interval_J_mol'], RTL*d['source_logK_plus_minus'])
            self.assertIsNone(d['source_pressure_bar'])
            self.assertIsNone(d['total_uncertainty'])
        basis = json.loads(self.db.metadata['source_reuse_R11o_modern_radium'])
        self.assertEqual(basis['licence_url'], 'https://creativecommons.org/licenses/by/4.0/')
        self.assertIn('No JAEA', basis['ancestry'])

    def test_carbonate_solubility_and_boundary_match_the_new_evaluation(self):
        pair = replace(self.system, species=(self.ion, self.solid), excluded=())
        metal = next(s for s in self.system.species if s.formula_ascii == 'Ra' and s.phase == 'solid')
        for loga in (-3, -2, -1):
            cfg = pb.PourbaixConditions(pH_points=3, U_points=3,
                ligand_activities=pb.LigandActivityModel((
                    pb.LigandActivity('carbonate-co3', log10_free_activity=loga),)))
            d = pb.MassBalanceEngine(self.db).calculate_system(pair, cfg, pb.TotalMetalConcentration(1e-6))
            np.testing.assert_allclose(d.dissolved_metal_mol_L, min(1e-6, 10**(-7.49-loga)), rtol=1e-10)
            np.testing.assert_allclose(d.dissolved_metal_mol_L + 1e-6*d.precipitated_metal_fraction,
                                      1e-6, rtol=1e-10)
            boundary = (self.solid.gibbs_energy_J_mol + 527810 - RTL*loga)/(2*FARADAY_C_MOL)
            for offset, winner in ((-.01, metal), (.01, self.solid)):
                diagram = pb.PourbaixEngine(self.db).calculate_system(
                    replace(self.system, species=(metal, self.solid), excluded=()),
                    replace(cfg, U_min_V=boundary+offset-.001, U_max_V=boundary+offset+.001))
                self.assertEqual({diagram.system.species[int(i)].record_id
                                  for i in diagram.stable_species_index.flat}, {winner.record_id})
        # At free carbonate10^-2 the new Ksp leaves a1uM inventory dissolved;
        # the older -8.3 evaluation would precipitate approximately half.
        self.assertLess(10**(-8.3+2), 1e-6)
        self.assertGreater(10**(-7.49+2), 1e-6)

    def test_source_and_thermal_holds_stay_distinct_from_the_new_gibbs_estimates(self):
        for prop in ('enthalpy_of_formation', 'absolute_entropy'):
            self.assertNotIn((CARB, prop), self.db.selections)
        holds = json.loads(self.db.metadata['R11o_radium_source_holds'])
        self.assertEqual(holds['R11l3_2019_status'], 'held_original_full_numerical_table_and_thermal_basis')
        self.assertIn('Ba-containing', holds['separate_R11l4'])
        self.assertNotIn(CARB, {s.record_id for s in self.db.load_system('Ra').species})
        for t in (323.15, 373.15):
            self.assertNotIn(CARB, {s.record_id for s in at_temperature(self.db, t).load_system(
                'Ra', ligand_ids=('carbonate-co3',)).species})


if __name__ == '__main__':
    unittest.main()
