"""Corrected cobalt G retains its erratum, alternatives and thermal basis."""
import json
import math
import unittest
from dataclasses import replace

import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K
from pourbase.temperature import at_temperature

G = 'gibbs_energy_of_formation'
RID = 'gfe-co-hcoo2-q-1-aqueous-aq'
SID = 'NBS_PDR_M32124_MP17_HCoO2_corrected'


class CobaltCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()

    def test_corrected_nbs_cell_is_selected_and_shock_evidence_remains(self):
        c = self.db.selections[(RID, G)].chosen
        self.assertEqual((c.value, c.source_id, c.family, c.evidence_class),
                         (-345500, SID, 'NBS Tables', 'B'))
        self.assertIsNone(c.uncertainty)
        basis = json.loads(self.db.metadata['source_reuse_MP17_cobalt_check'])
        self.assertEqual((basis['logical_record_1_based'], basis['csv_column_1_based'],
                          basis['source_record'][8], basis['original_marker']), (5482, 9, '-345.5*', '*'))
        record = self.db.species_records((RID,))[0]
        old = next(x for x in record.reported if x.property == G and x.source is not None and x.source.source_id == 'WORM_SSWS97_HCoO2')
        self.assertEqual((old.value, old.status), (-348945.6, 'source_verified_estimate'))
        self.assertFalse(old.selected_as_recommended)
        self.assertIsNone(old.supersedes_value_id)
        corrected = next(x for x in record.reported if x.value_id == c.value_id)
        self.assertIsNone(corrected.supersedes_value_id)
        self.assertFalse(any(x.property == G and x.value < -400000 for x in record.reported))

    def test_balanced_hydrolysis_boundary_uses_full_formula_and_charge(self):
        system = self.db.load_system('Co')
        co = next(s for s in system.species if s.record_id == 'gfe-co-co-q+2-aqueous-aq')
        hco = next(s for s in system.species if s.record_id == RID)
        self.assertEqual((hco.formula_ascii, hco.charge, hco.core_oxygen_count,
                          hco.core_hydrogen_count, hco.electrons_per_metal, hco.protons_per_metal),
                         ('HCoO2', -1, 2, 1, 2, 3))
        rtl = GAS_CONSTANT_J_MOL_K * 298.15 * math.log(10)
        ph = (hco.gibbs_energy_J_mol - co.gibbs_energy_J_mol -
              2 * self.db.reference_state.water_gibbs_energy_J_mol) / (3 * rtl)
        restricted = replace(system, species=(co, hco), excluded=())
        for offset, expected in [(-.05, co.record_id), (.05, hco.record_id)]:
            cfg = pb.PourbaixConditions(pH_min=ph + offset, pH_max=ph + offset + .001,
                                        pH_points=2, U_points=2)
            diagram = pb.PourbaixEngine(self.db).calculate_system(restricted, cfg)
            self.assertEqual({diagram.system.species[int(i)].record_id
                              for i in diagram.stable_species_index.flat}, {expected})

    def test_thermal_fallback_and_hafnium_hold_remain_explicit(self):
        entropy = self.db.selections[(RID, 'absolute_entropy')].chosen
        self.assertEqual((entropy.value, entropy.source_id), (-106.692, 'WORM_SSWS97_HCoO2'))
        self.assertNotIn((RID, 'enthalpy_of_formation'), self.db.selections)
        thermal = at_temperature(self.db, 323.15)
        delta_s, route = thermal.formation_entropies()[RID]
        self.assertEqual(route, 'S°, another source')
        species = next(s for s in thermal.load_system('Co').species if s.record_id == RID)
        self.assertAlmostEqual(species.gibbs_energy_J_mol, -345500 - 25 * delta_s)
        hf = self.db.selections[('gfe-hf-hf-q+4-aqueous-aq', G)].chosen
        self.assertEqual((hf.value, hf.source_id), (-554798.4, 'WORM_SSWS97_Hf+4'))
        self.assertIn('Commercial compilations excluded',
                      json.loads(self.db.metadata['source_reuse_MP17_cobalt_check'])['hafnium_hold'])
