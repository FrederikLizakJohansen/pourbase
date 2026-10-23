"""NASA property ancestry,gas selection and nominal wustite evidence."""
import json
import math
import unittest
from importlib.resources import files
import pourbase as pb

G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
NASA='R08_NASA2002_original_atomic_entropy';NBS='R08_NBS_PDR_atomic_and_wustite'
OXIDE='r08-fe-fe0-947o-wustite'

class NasaThermochemistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()
        cls.review=json.loads(cls.db.metadata['R08_NASA_source_review'])

    def test_original_298K_entropy_is_independent_of_newer_fit_bound(self):
        atoms=self.review['atomic_records']
        self.assertEqual(len(atoms),118)
        self.assertEqual(sum(not a['valid_upstream_fit_298'] for a in atoms),42)
        ag=next(a for a in atoms if a['name']=='Ag')
        value=next(v for v in self.db.species_records((ag['record_id'],))[0].reported
                   if v.source.source_id==NASA)
        self.assertEqual((value.property,value.value,value.temperature_K,value.pressure_bar),
                         (S,172.998,298.15,1))
        self.assertIsNone(value.uncertainty)
        entropy_recipe=json.loads(value.source.locator)
        self.assertNotIn('row',entropy_recipe['source_locator'])
        self.assertEqual(entropy_recipe['source_locator']['column'],'So(T),J/K-mol;T=298.15K')
        for a in atoms:
            if a['charge']:
                self.assertNotIn((a['record_id'],G),self.db.selections)
                self.assertNotIn((a['record_id'],H),self.db.selections)

    def test_new_gases_are_explicit_and_do_not_substitute_for_aqueous_ions(self):
        for symbol in ['Ag','Fe','Nb']:
            a=next(a for a in self.review['atomic_records'] if a['symbol']==symbol and not a['charge'])
            self.assertNotIn(a['record_id'],{s.record_id for s in self.db.load_system(symbol).species})
            explicit=self.db.load_system(symbol,include_optional_gases=True)
            self.assertIn(a['record_id'],{s.record_id for s in explicit.species})
            charged={a['record_id'] for a in self.review['atomic_records'] if a['symbol']==symbol and a['charge']}
            self.assertFalse(charged&{s.record_id for s in explicit.species})

    def test_conflicting_G_cells_are_held_and_local_recipes_close(self):
        recipes=json.loads(self.db.metadata['R08_NASA_observations'])
        self.assertEqual({x['symbol'] for x in self.review['NBS_conflicting_G_held']},{'Ba','V'})
        for symbol in ['Ba','V']:
            a=next(a for a in self.review['atomic_records'] if a['symbol']==symbol and not a['charge'])
            chosen=self.db.selections[a['record_id'],G].chosen
            self.assertEqual(chosen.evidence_class,'E')
            d=next(x['recipe'] for x in recipes if x['value_id']==chosen.value_id)
            self.assertAlmostEqual(chosen.value,d['Hf_gas_J_mol']-298.15*(d['S_gas_J_mol_K']-d['S_element_J_mol_K']))
            self.assertNotEqual(chosen.value,d['rejected_digitized_G_J_mol'])
            self.assertFalse(any(v.property==G and v.source.source_id==NBS
                                 for v in self.db.species_records((a['record_id'],))[0].reported))

    def test_existing_mercury_evidence_is_linked_without_duplication(self):
        links=self.review['prior_same_source_links']
        self.assertEqual(len(links),3)
        self.assertEqual({x['property'] for x in links},{G,H,S})
        record=self.db.species_records(('gfe-hg-hg-q+0-gas-g',))[0]
        self.assertEqual(len(record.reported),4)
        self.assertFalse(any(v.source.source_id==NBS for v in record.reported))

    def test_wustite_composition_and_metastable_formation_G(self):
        s=next(s for s in self.db.load_system('Fe').species if s.record_id==OXIDE)
        self.assertEqual((s.formula_ascii,s.metal_count,s.core_oxygen_count),('Fe0.947O',.947,1))
        self.assertAlmostEqual(s.electrons_per_metal,2/.947)
        record=self.db.species_records((OXIDE,))[0]
        self.assertEqual(len(record.reported),6)
        for p,value in [(G,-245120),(H,-266270),(S,57.49)]:
            self.assertEqual(self.db.selections[OXIDE,p].chosen.value,value)
            self.assertEqual(self.db.selections[OXIDE,p].chosen.evidence_class,'B')
        self.assertIn('unstable below833K',self.review['wustite_phase']['notes'])
        with self.db.connect() as c:
            row=c.execute('SELECT source_locator FROM reported_thermochemistry WHERE record_id=? AND property=? AND source_id=?',
                          (OXIDE,G,'R08_NASA_wustite_fit_local_model')).fetchone()
        d=json.loads(row[0]);v=d['NASA_eval']
        expected=v['H_J_mol']-298.15*(v['S_J_mol_K']-.947*d['Fe_reference_S_J_mol_K']-.5*d['O2_reference_S_J_mol_K'])
        self.assertAlmostEqual(d['Gfit_J_mol'],expected)
        self.assertNotAlmostEqual(expected,v['H_J_mol']-298.15*v['S_J_mol_K'])
        self.assertEqual(d['R_J_mol_K'],8.314510)

    def test_upstream_notices_are_distributed_and_permissions_stay_separate(self):
        data=files('pourbase').joinpath('data')
        self.assertIn('Apache License',data.joinpath('nasa-cea-LICENSE.txt').read_text())
        notice=data.joinpath('nasa-cea-NOTICE.txt').read_text()
        self.assertIn('data/thermo.inp',notice)
        self.assertIn('Copyright (c) 2025',notice)
        self.assertIn('No blanket retroactive licence',self.review['licence']['legacy'])
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])

if __name__=='__main__':unittest.main()
