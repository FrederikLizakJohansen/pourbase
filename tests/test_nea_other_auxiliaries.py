"""Auxiliary source identity, buffered reactions and reference-only evidence."""
from dataclasses import replace
import json
import unittest

import numpy as np
import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature

G = 'gibbs_energy_of_formation'
H = 'enthalpy_of_formation'
S = 'absolute_entropy'
HCN = 'r11j3l-c-hcn-gas'
SCN = 'r11j3l-s-scn-q-1-aqueous'
KI = 'r11j3l-k-ki-crystalline'
NBS = 'NBS_PDR_R11j3l_auxiliary_alternatives'


class NEAOtherAuxiliaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()

    def test_HCN_optional_gas_preserves_mixed_evaluation_and_older_alternative(self):
        default = self.db.load_system('C', ligand_ids=('nitrogen-n2-gas',))
        self.assertNotIn(HCN, {x.record_id for x in default.species})
        system = self.db.load_system('C', ligand_ids=('nitrogen-n2-gas',), include_optional_gases=True)
        phase = next(x for x in system.species if x.record_id == HCN)
        self.assertEqual((phase.metal_count, phase.core_hydrogen_count, phase.electrons_per_metal), (1, 1, -1))
        self.assertEqual([(x.ligand_id, x.count) for x in phase.components], [('nitrogen-n2-gas', .5)])
        record = self.db.species_records((HCN,))[0]
        old = next(x for x in record.reported if x.property == G and x.source.source_id == NBS)
        self.assertEqual(old.value, 124700)
        self.assertIsNone(old.uncertainty)
        chosen = self.db.selections[HCN, G].chosen
        self.assertEqual((chosen.value, chosen.uncertainty, chosen.evidence_class), (119517, 2500, 'A'))
        selected = next(x for x in record.reported if x.value_id == chosen.value_id)
        self.assertIn('computational', json.loads(selected.source.locator)['numerical_ancestry'])
        shifted = at_temperature(self.db, 323.15).load_system('C', ligand_ids=('nitrogen-n2-gas',), include_optional_gases=True)
        self.assertNotIn(HCN, {x.record_id for x in shifted.species})

    def test_SCN_zero_electron_reaction_and_buffered_sulfur_balance(self):
        system = self.db.load_system('S', ligand_ids=('cyanide-cn',))
        phase = next(x for x in system.species if x.record_id == SCN)
        self.assertEqual((phase.formula_ascii, phase.charge, phase.electrons_per_metal, phase.protons_per_metal), ('SCN', -1, 0, 0))
        self.assertEqual([(x.ligand_id, x.count, x.charge) for x in phase.components], [('cyanide-cn', 1, -1)])
        conditions = pb.PourbaixConditions(pH_points=7, U_points=9,
            ligand_activities=pb.LigandActivityModel((pb.LigandActivity('cyanide-cn', log10_free_activity=-3),)))
        expected = 92700 - phase.components[0].gibbs_energy_J_mol + 3 * GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        for pH, potential in [(0, -1), (7, 0), (14, 1)]:
            self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase, self.db.reference_state, conditions, pH, potential)), expected)
        supported = replace(system, species=tuple(x for x in system.species if not x.is_gas))
        result = pb.MassBalanceEngine(self.db).calculate_system(supported, conditions, pb.TotalMetalConcentration(1e-3))
        np.testing.assert_allclose(result.dissolved_metal_mol_L + 1e-3 * result.precipitated_metal_fraction, 1e-3, rtol=1e-10, atol=1e-15)

    def test_potassium_recalculation_keeps_original_NBS_and_KI_qualification(self):
        for rid in ['r13-k-nbs-record12202', 'r11j3l-k-kbr-crystalline', KI]:
            self.assertEqual(self.db.selections[rid, H].chosen.source_id, 'NEA_2005_R11j3l_nickel_potassium')
            record = self.db.species_records((rid,))[0]
            self.assertTrue(any(x.property == H and x.source.source_id in (NBS, 'R13_NBS_PDR_salt_properties') for x in record.reported))
        record = self.db.species_records((KI,))[0]
        source = next(x for x in record.reported if x.property == G and x.source.source_id == NBS)
        self.assertEqual(source.value, -324892)
        self.assertIn('constraint has been relaxed', json.loads(source.source.locator)['source_qualification'])
        self.assertTrue(any(x.type == 'r11j3l_NBS_relaxed_GHS_constraint' for x in record.warnings))

    def test_reference_only_peroxide_stays_outside_primary_inventory(self):
        context = json.loads(self.db.metadata['R11j3l_H2O2_reference_observations'])
        self.assertEqual(context['NEA']['value_J_mol'], -191170)
        self.assertEqual(context['NEA']['uncertainty_J_mol'], 100)
        self.assertEqual(context['NBS']['properties'], {G: -134030, H: -191170, S: 143.9})
        with self.db.connect() as c:
            self.assertEqual(c.execute("SELECT count(*) FROM species WHERE formula_ascii='H2O2'").fetchone()[0], 0)
            self.assertEqual(c.execute('SELECT count(*) FROM ligands').fetchone()[0], 31)

    def test_reprint_link_and_direct_copy_hold_remain_distinct(self):
        review = json.loads(self.db.metadata['R11j3l_NEA_auxiliary_review'])
        self.assertEqual((review['source_cells'], review['new_observations'], review['new_species'], review['newly_available_properties']), (23, 36, 5, 15))
        self.assertEqual((review['NEA_primary_observations'], review['independent_open_NBS_observations'], review['already_retained_cells'], review['new_direct_Glushko_holds']), (18, 18, 1, 3))
        self.assertEqual(self.db.selections['gfe-ni-ni-q+0-solid-metal', S].chosen.value_id, 'gfe-ni-ni-q+0-solid-metal:absolute_entropy:nea02a-selected')
        rows = json.loads(self.db.metadata['R11j3l_auxiliary_observations'])
        self.assertEqual(len(rows), 36)
        self.assertTrue(all(x['source_id'] == NBS for x in rows if x['record_id'] == 'r05-na-naf-villiaumite'))
        tl = self.db.species_records(('gfe-tl-tl-q+1-aqueous-aq',))[0]
        self.assertTrue(any(x.type == 'r11j3l_Tl_discussion_sign_typo' for x in tl.warnings))
        self.assertEqual(self.db.selections[tl.record_id, G].chosen.value, -32400)
        self.assertEqual(self.db.policy.fingerprint, 'f8ee0083e857')
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])


if __name__ == '__main__':
    unittest.main()
