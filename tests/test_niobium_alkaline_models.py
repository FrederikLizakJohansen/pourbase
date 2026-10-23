"""Supplemental hexaniobate reactions and supported runtime scope."""
import json
import math
import unittest
from dataclasses import replace

import numpy as np
import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K

G='gibbs_energy_of_formation'
IDS={h:f'r11u-nb-h{h}-nb6o19-q{h-8}-aqueous' for h in range(4)}
RTL=GAS_CONSTANT_J_MOL_K*298.15*math.log(10)

class NiobiumAlkalineModelsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()
        cls.system=cls.db.load_system('Nb')
        cls.clusters={h:next(s for s in cls.system.species if s.record_id==rid)
                      for h,rid in IDS.items()}

    def test_full_cluster_formulas_and_pinned_absolute_reference(self):
        recipes=json.loads(self.db.metadata['R11u_hexaniobate_observations'])
        for h,s in self.clusters.items():
            self.assertEqual((s.metal_count,s.core_oxygen_count,s.core_hydrogen_count,s.charge),
                             (6,19,h,h-8))
            self.assertEqual(s.electrons_per_metal,5)
            self.assertAlmostEqual(s.protons_per_metal,(38-h)/6)
            chosen=self.db.selections[s.record_id,G].chosen
            self.assertEqual(chosen.evidence_class,'E')
            self.assertIsNone(chosen.uncertainty)
            self.assertNotIn((s.record_id,'enthalpy_of_formation'),self.db.selections)
            self.assertNotIn((s.record_id,'absolute_entropy'),self.db.selections)
        d=recipes[3]
        neutral=self.db.species_records((d['neutral_record_id'],))[0]
        anchor=next(v for v in neutral.reported if v.value_id==d['neutral_value_id'])
        self.assertEqual(anchor.value,-949742)
        delta=self.clusters[3].gibbs_energy_J_mol+11*d['water_G_J_mol']-6*d['hydrated_NbOH5_G_J_mol']
        self.assertAlmostEqual(-delta/RTL,-20.6)

    def test_cumulative_protonation_and_equal_activity_boundaries(self):
        for h,beta in [(1,14),(2,27),(3,38.6)]:
            self.assertAlmostEqual((self.clusters[0].gibbs_energy_J_mol-
                                    self.clusters[h].gibbs_energy_J_mol)/RTL,beta)
        for a,b,boundary in [(0,1,14),(1,2,13),(2,3,11.6)]:
            pair=replace(self.system,species=(self.clusters[a],self.clusters[b]),excluded=())
            for shift,winner in [(-.02,b),(.02,a)]:
                cfg=pb.PourbaixConditions(pH_min=boundary+shift-.001,pH_max=boundary+shift+.001,
                                          pH_points=3,U_points=3)
                d=pb.PourbaixEngine(self.db).calculate_system(pair,cfg)
                self.assertEqual({d.system.species[int(i)].record_id for i in d.stable_species_index.flat},
                                 {IDS[winner]})

    def test_closed_balance_explicitly_excludes_six_metal_clusters(self):
        cfg=pb.PourbaixConditions(pH_points=7,U_points=9)
        result=pb.MassBalanceEngine(self.db).calculate_system(self.system,cfg,pb.TotalMetalConcentration(1e-6))
        self.assertTrue(set(IDS.values())<={s.record_id for s in result.system.excluded})
        self.assertFalse(set(IDS.values())&{s.record_id for s in result.aqueous_species})
        np.testing.assert_allclose(result.dissolved_metal_mol_L+1e-6*result.precipitated_metal_fraction,
                                   1e-6,rtol=1e-10,atol=1e-15)

    def test_model_limits_and_separate_source_permissions_are_retained(self):
        review=json.loads(self.db.metadata['R11u_alkaline_niobium_review'])
        holds=json.loads(self.db.metadata['R11u_alkaline_niobium_holds'])
        self.assertIn('No open licence asserted',review['reuse']['source_copyright'])
        self.assertIn('CC BY-NC-ND4.0',review['reuse']['excluded_Filella2020'])
        self.assertIn('weak absolute',review['original_model']['original_interpretation']+
                      review['absolute_reference'])
        self.assertIn('18-20C',review['original_model']['conditions'])
        self.assertIn('conditional',holds['R11u2'])
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])

if __name__=='__main__':unittest.main()
