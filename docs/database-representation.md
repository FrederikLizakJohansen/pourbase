# Species representation and field contract

The 28 October 2026 pass checks **all 1,771 species and 5,297 observations**
against the same representation rules. The [per-species CSV](database-species-review.csv)
lists each formula, phase, charge, atom count, phase-identity status and error count.
It has **zero representation errors** after the corrections below.

This is a consistency check of the stored records and their existing evidence.
The recorded uncertainties, unresolved phase identities and source-permission
holds retain their meaning. Completed source reviews carry forward.

## What belongs in each field

| Fields | Representation |
| --- | --- |
| `species.record_id`, `sources.source_id`, `reported_thermochemistry.value_id`, `ligands.ligand_id` | Stable identifiers. Their spelling supplies no evidence class, licence or chemical identity. Links refer to existing records. |
| `species.symbol`, `system` | An element symbol from `element_coverage`, and its single system label ending in that symbol in parentheses. |
| `species.species` | A readable display name. Unicode formulas, hydrate dots and established mineral/endmember names are allowed. `formula_ascii` supplies the machine-readable composition. |
| `species.formula_ascii`, `ligands.formula_ascii` | Complete formula units with element symbols, positive numeric occupancies and balanced `()` or `[]` groups. Hydrates use forms such as `CaSO4(H2O)0.5`. Charge and native oxidation annotations have separate fields. |
| `species.phase` | Controlled values: `solid`, `aqueous`, `gas`, `liquid`. |
| `species.phase_detail` | A concise phase, polymorph or chemical-identity label. Generic aqueous/gas labels are `aqueous` and `gas`. Named phases and physical qualifiers such as vitreous, precipitated, nominal or supercooled remain distinct. Source citations and evaluation-method notes belong in provenance. |
| `atom_count`, `metal_count`, `core_oxygen_count`, `core_hydrogen_count` | Finite numbers per complete formula unit. Primary atoms, residual O/H and all buffered components together reproduce every atom. `metal_count` denotes the primary element, including nonmetals. |
| `charge`, `metal_oxidation_state`, `electron_coefficient_per_metal` | Finite numbers with separate meanings. The electron coefficient balances the reaction against the stored component references. Formal oxidation state remains independently documented, including mixed-valence and disulfide cases. |
| `species.ligand_id`, `ligand_count`, `ligand_charge` | All `NULL` when the first buffered reference is unused. Otherwise an existing reference ID, a positive count and that reference's charge. Further references live in `additional_components` and are counted once. |
| `additional_components.component_count` | Positive numeric count of an existing reference per full species formula. |
| `reported_thermochemistry.property`, `unit` | Controlled pairs: `gibbs_energy_of_formation` and `enthalpy_of_formation` use `J/mol`; `absolute_entropy` uses `J/(mol K)`. |
| `value`, `uncertainty`, `temperature_K`, `pressure_bar` | Finite numbers where supplied. Missing values use `NULL`. Uncertainty is nonnegative and requires a value; its interpretation stays in provenance. Actual observation conditions stay explicit, including excluded nonstandard observations. |
| Thermochemical `status` and `ligands.gibbs_status` | Controlled evidence terms: `verified`, `accepted`, `source_verified_estimate`, `defined_reference_state`, `superseded_source_value`, `terminal_evidence_gap`, `not_available`. The source meaning and property eligibility still apply. |
| `phases.identity_status` | Controlled phase-identity terms defined below, separate from thermochemical evidence status. |
| `phases.source_phase_label` | Original source label, retained as readable text. |
| `identified_phase`, `possible_phases` | Readable identity/candidate descriptions. Unknown optional fields use `NULL`; a missing description supplies no structural assignment. |
| `spacegroup_symbol`, `spacegroup_number` | A documented symbol and International Tables number, supplied together. Number is stored as digit text from 1–230 for API compatibility. Documented alternate settings retain their symbols. Unknown pairs are `NULL`. |
| `citation`, `evidence_summary`, `notes`, warning `message` | Readable prose. Formatting variations in these narrative fields do not change their role. |
| `url`, `source_url` | One HTTP(S) URL. Optional missing URLs use `NULL`. |
| `sources.locator`, `reported_thermochemistry.source_locator` | Either readable locator text or one complete JSON object. Extra prose accompanying JSON is stored inside `additional_locator_notes`. A missing per-value locator falls back to the source locator. Existing versioned `evaluation_lineage` objects retain their schema and links. |
| `supersedes_value_id` | Optional existing observation ID for the same species and property. Legacy links retain their documented direction. |

For example, the aged aluminium hydroxide entry now uses
**microcrystalline aluminium hydroxide** in both its phase-detail and identified-phase
labels. Its evidence summary, phase notes and existing record warning retain the
**19-month ageing fit and the 5–60 °C model range**. The early-age amorphous
material keeps its separate identity. This cleanup preserves the recorded model
scope; it adds no model-domain enforcement to the temperature calculator.

Label length alone does not determine correctness. A long chemical or mineral
name can belong in the label. Preparation history, fitting method, evidence class
and applicability limits belong with the source/model explanation. Phase-defining
qualifiers such as amorphous, microcrystalline, hydration and polymorph remain
in the identity.

An observation marked `terminal_evidence_gap` may retain an unverified legacy
number for traceability. The selection policy excludes that observation; it
supplies no admitted value. A genuinely absent numeric value is `NULL`.

## Phase identity and missing information

`resolved` records a named solid-phase identity in the existing review. It does
not by itself establish a space group, specimen-level DFT match or complete
thermochemical coverage. `aqueous_species_identified` describes an aqueous
identity. `unresolved`, `ambiguous`, `phase_identity_incomplete` and
`reported_composition_disputed` retain their specific limitations.

| Recorded status | Species |
| --- | ---: |
| `resolved` | 491 |
| `aqueous_species_identified` | 211 |
| `unresolved` | 428 |
| `ambiguous` | 8 |
| `phase_identity_incomplete` | 2 |
| `reported_composition_disputed` | 1 |
| No separate phase-identity row | 630 |

The last group comprises 389 aqueous species, 169 gases, five liquids and
67 elemental solid reference states. Their species rows still record the
physical phase; the CSV makes the absent additional identity record explicit.
The solid reference states receive no inferred space group in this pass.

## Corrections made

- Corrected the mononitrate machine formula from native nitrogen oxidation
  notation `N|5|2` to `N2`. Its atom counts, full formula-unit energies and
  original source annotation are preserved.
- Standardized 1,248 phase-detail labels, retaining named phases, hydration,
  polymorph, nominal-composition and metastability distinctions.
- Moved ageing-fit and validity qualifications from aluminium-hydroxide labels
  into visible evidence descriptions and record notes. Matching identified-phase
  labels were shortened consistently; source labels stay verbatim.
- Standardized unused ligand fields in 19 species and 82 empty optional phase
  fields to `NULL`.
- Moved ten misleading `resolved_thermochemistry_gap` phase statuses to
  `unresolved`, following their existing evidence. Two identified aqueous
  complexes now use `aqueous_species_identified`.
- Replaced four legacy component-status labels with `accepted`; their values
  retain the published-compilation qualification and receive no new verification claim.
- Repaired 119 observation locators and three source locators containing a JSON
  object followed by free prose. Existing object fields and trailing notes are
  retained in complete JSON objects. No evaluation-lineage object was activated
  by this repair.

Original text and each before/after field change are retained in database
metadata under `species_representation_review_20261028`. The underlying
numerical observations, uncertainties, source citations, eligibility and
preferred observations remain unchanged. Comparison of all 75 runtime systems
with every buffered reference and optional gas enabled gives identical
calculation inputs. Statistics count **491 resolved solid-phase identities**,
using the exact identity status; the previous 503 also counted ten unresolved
structures and two aqueous identities.

## Repeat the checks

From a repository checkout or source distribution:

```sh
python scripts/audit_database_representation.py
python scripts/audit_database_representation.py --json /tmp/representation.json --csv /tmp/species.csv
python -m unittest discover -s tests
```

The audit is read-only and exits unsuccessfully when a representation error is
found. It checks database integrity, numeric storage, controlled terms, URLs,
formula-unit composition, component charge and electron balance, duplicate
identities, observation units/statuses, provenance formats and observation links.
The regression tests also introduce malformed imports to verify their detection.
