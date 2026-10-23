"""Source-specific chemistry and reference conventions for the final R11 routes."""
from __future__ import annotations

import json
import unittest

from support import ROOT  # noqa: F401
import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K, LN_10, FARADAY_C_MOL
from pourbase.engine import transformed_gibbs_J_mol_metal

G = "gibbs_energy_of_formation"
H = "enthalpy_of_formation"
S = "absolute_entropy"
RTL = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10


class FinalOriginalRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()
        cls.details = json.loads(cls.db.metadata["R11l_original_route_observations"])

    def test_radium_reference_and_sulfate_retain_open_nbs_cells(self):
        for rid, values in [
            ("r11l-ra-ra-metal", (0, 0, 71)),
            ("r11l-ra-ra-q+2-aqueous", (-561500, -527600, 54)),
            ("r11l-ra-raso4-crystalline", (-1365600, -1471100, 138)),
        ]:
            rows = [r for r in self.db.species_records((rid,))[0].reported
                    if r.source.source_id == "R11l_NBS_PDR_original_routes"]
            self.assertEqual({r.property: r.value for r in rows}, dict(zip((G, H, S), values)))
            self.assertTrue(all(r.uncertainty is None for r in rows))
            self.assertTrue(all("M32124" in r.source.citation for r in rows))
        self.assertIn(("Ra", "Radium (Ra)"), self.db.available_systems())
        history = json.loads(self.db.metadata["R11l_coverage_history"])
        self.assertEqual(history["before"]["coverage_status"], "outside_current_scope")
        self.assertEqual(history["after"]["coverage_status"], "supported")

    def test_radium_concentration_conversion_supports_all_public_views(self):
        converted = pb.convert_concentration("Ra", 226.025, "ppm")
        self.assertAlmostEqual(converted.molar_concentration, .001)
        calculation = pb.calculate(pb.Scenario("Ra", concentration=226.025,
            concentration_unit="ppm", pH_points=5, U_points=7), self.db)
        self.assertEqual(calculation.diagram.system.symbol, "Ra")

    def test_radium_carbonate_preserves_its_estimated_endmember(self):
        record = self.db.species_records(("r11l-ra-raco3-crystalline-estimate",))[0]
        self.assertEqual(len(record.reported), 5)
        value = next(r for r in record.reported
                     if r.source.source_id == "R11l_local_Langmuir1985_original_estimates")
        self.assertEqual(value.status, "source_verified_estimate")
        self.assertIsNone(value.uncertainty)
        self.assertAlmostEqual((value.value + 561500 + 527810) / RTL, -8.3)
        self.assertIn("structure unspecified", record.phase_detail)
        self.assertNotIn(record.record_id, {s.record_id for s in self.db.load_system("Ra").species})

    def test_radium_hydrolysis_retains_two_original_models(self):
        rid = "r11l-ra-raoh-q+1-aqueous"
        record = self.db.species_records((rid,))[0]
        self.assertEqual(len(record.reported), 6)
        self.assertTrue(all(r.status == "source_verified_estimate" and r.uncertainty is None
                            for r in record.reported))
        a = {r.property: r.value for r in record.reported
             if r.source.source_id == "R11l_local_Langmuir1985_original_estimates"}
        b = {r.property: r.value for r in record.reported
             if r.source.source_id == "R11l_local_Nagra2023_original_models"}
        self.assertAlmostEqual((-561500 - 157244 - a[G]) / RTL, .5)
        self.assertAlmostEqual(a[H] + 527600 + 229994, 1.1 * 4184)
        self.assertAlmostEqual((-561500 - 237129 - b[G]) / RTL, -13.7)
        self.assertAlmostEqual(b[H] + 527600 + 285830, 62000)
        self.assertAlmostEqual(b[S] - 54 - 69.91, (62000 + RTL * -13.7) / 298.15)

    def test_high_temperature_niobium_oxide_keeps_its_full_formula(self):
        rid = "r11l-nb-nb2o5-high-temperature"
        s = next(s for s in self.db.load_system("Nb").species if s.record_id == rid)
        self.assertEqual((s.formula_ascii, s.metal_count, s.core_oxygen_count,
                          s.electrons_per_metal, s.protons_per_metal), ("Nb2O5", 2, 5, 5, 5))
        self.assertEqual(s.gibbs_energy_J_mol, -1766000)
        self.assertEqual(self.db.selections[(rid, H)].chosen.value, -1899500)
        self.assertEqual(self.db.selections[(rid, S)].chosen.value, 137.24)
        self.assertIn("high-temperature", s.phase_detail)
        with self.db.connect() as c:
            phase = c.execute("SELECT * FROM phases WHERE record_id=?", (rid,)).fetchone()
            self.assertEqual(phase["identity_status"], "unresolved")
            self.assertIn("Distinct from Peiffert2010 B-Nb2O5", phase["evidence_summary"])

    def test_higher_aluminium_fluorides_use_cumulative_constants(self):
        default = {s.record_id for s in self.db.load_system("Al").species}
        buffered = self.db.load_system("Al", ligand_ids=("fluoride-f",))
        for n, q in [(5, -2), (6, -3)]:
            rid = f"r11l-al-alf{n}-q{q}-aqueous"
            self.assertNotIn(rid, default)
            s = next(s for s in buffered.species if s.record_id == rid)
            self.assertEqual((s.charge, s.ligand_count, s.electrons_per_metal), (q, n, 3))
            self.assertAlmostEqual((-485000 + n * -278790 - s.gibbs_energy_J_mol) / RTL, 20.29)
            self.assertEqual(self.db.selections[(rid, H)].chosen.source_id,
                             "R11r_LatimerJolly1953_qualified_AlF_thermal")

    def test_cyanide_source_triplets_and_protonation_cycle(self):
        for rid, preferred, nbs in [
            ("r11l-c-cn-q-1-aqueous", (166939, 147350, 101.182), (172400, 150600, 94.1)),
            ("r11l-c-hcn-aqueous", (114368, 103750, 131.271), (119700, 107100, 124.7)),
        ]:
            r = self.db.species_records((rid,))[0]
            self.assertEqual(len(r.reported), 6)
            self.assertEqual(tuple(self.db.selections[(rid, p)].chosen.value for p in (G, H, S)), preferred)
            self.assertEqual({x.property: x.value for x in r.reported
                              if x.source.source_id == "R11l_NBS_PDR_original_routes"}, dict(zip((G, H, S), nbs)))
            self.assertTrue(all(self.db.selections[(rid, p)].chosen.evidence_class == "A" for p in (G, H, S)))
        self.assertAlmostEqual((166939 - 114368) / RTL, 9.21, places=3)
        self.assertEqual(147350 - 103750, 43600)

    def test_carbon_nitrogen_reservoir_has_explicit_electron_balance(self):
        system = self.db.load_system("C", ligand_ids=("nitrogen-n2-gas",))
        cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity("nitrogen-n2-gas", log10_free_activity=-2),)))
        for rid, protons in [("r11l-c-cn-q-1-aqueous", 0), ("r11l-c-hcn-aqueous", -1)]:
            self.assertNotIn(rid, {s.record_id for s in self.db.load_system("C").species})
            s = next(s for s in system.species if s.record_id == rid)
            self.assertEqual((s.ligand_count, s.ligand_charge, s.electrons_per_metal,
                              s.protons_per_metal), (.5, 0, -1, protons))
            ph, u = 7, .2
            a = cfg.aqueous_activities.log10_activity_for(s.record_id, s.species, s.formula_ascii)
            expected = s.gibbs_energy_J_mol + RTL*(a + 1 - protons*ph) + FARADAY_C_MOL*u
            self.assertAlmostEqual(float(transformed_gibbs_J_mol_metal(s, self.db.reference_state, cfg, ph, u)),
                                   expected, places=7)

    def test_free_references_preserve_previous_pins_and_ion_alternatives(self):
        histories = json.loads(self.db.metadata["R11l_reference_history"])
        self.assertEqual({x["ligand_id"] for x in histories}, {"sulfide-s", "cyanide-cn"})
        for x in histories:
            with self.db.connect() as c:
                pin = dict(c.execute("SELECT * FROM ligands WHERE ligand_id=?", (x["ligand_id"],)).fetchone())
            self.assertEqual(pin, x["current_pin"])
            self.assertEqual(pin["gibbs_energy_J_mol"], self.db.selections[(x["ion_record_id"], G)].chosen.value)
            old_g = x["previous_pin"]["gibbs_energy_J_mol"]
            r = self.db.species_records((x["ion_record_id"],))[0]
            self.assertTrue(any(y.property == G and y.value == old_g for y in r.reported))
            self.assertAlmostEqual((old_g - pin["gibbs_energy_J_mol"]) / RTL,
                                   x["log10_activity_offset_for_equivalent_chemical_potential"])

    def test_pyrochroite_thermal_mean_is_an_estimate_with_preserved_support(self):
        rid = "gfe-mn-mn-oh-2-q+0-solid-pyrochroite"
        self.assertEqual(self.db.selections[(rid, G)].chosen.source_id, "Bricker_1965_pyrochroite")
        h = self.db.selections[(rid, H)].chosen
        self.assertEqual(h.value, -220750 + 2 * -285830 + 123000)
        self.assertIsNone(h.uncertainty)
        rows = [x for x in self.details if x["record_id"] == rid]
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(x["supporting_model_H_kJ_mol"] == [-122.5, -111.5, -137, -121.4] for x in rows))
        self.assertTrue(all("not source-reported S" in x["scope"] for x in rows))


if __name__ == "__main__":
    unittest.main()
