# Database tables

`src/pourbase/data/pourbase.sqlite` is the database distributed with this publication. All
thermochemical quantities use one formula unit as the molar basis.

| Table | Contents |
|---|---|
| `metadata` | Dataset version, database role, reference temperature, pressure, and water Gibbs energy |
| `species` | Stable record ID, displayed species, ASCII formula, phase, charge, atom counts, ligand encoding, formal metal oxidation state, and signed electron coefficient for the metal/water reaction |
| `thermochemistry` | Recommended Gibbs energy, entropy, formation enthalpy, scientific status, uncertainty, source ID, and exact source locator |
| `reported_thermochemistry` | Every retained original and selected thermochemical value, including its recommendation flag, status, source, uncertainty, and supersession link |
| `computational_fallbacks` | Opt-in 300 K Materials Project SISSO Gibbs estimates for experimental gaps, with phase mapping, confidence, identifiers, versions, and warnings |
| `element_coverage` | One row for every element, recording whether it is supported, a reference component, deferred, or outside the current curated scope |
| `sources` | Full scientific citations, URLs, general locators, and access dates |
| `phases` | Experimental phase label, identity status, polymorph candidates, space group, and evidence summary |
| `warnings` | Readable cautions for estimates, absent recommended values, and phase-identity limitations |
| `materials_project_matches` | Accepted links between an experimental solid phase and a Materials Project structure |
| `materials_project_energies` | Published method-specific Materials Project energy records and calculation provenance |
| `ligands` | Free-ligand reference states available to ligand-aware calculations |

## Units

| Suffix | Unit |
|---|---|
| `_J_mol` | joules per mole of formula units |
| `_J_mol_K` | joules per mole of formula units per kelvin |
| `_eV_atom` | electronvolts per atom |
| `_K` | kelvin |
| `_bar` | bar |

## Thermochemical status

- `defined_reference_state`: an elemental standard state with formation energy zero by definition.
- `verified`: a recommended value supported by the cited source.
- `source_verified_estimate`: a published or evaluated estimate, clearly labelled as such.
- `terminal_evidence_gap`: the source investigation did not establish a defensible value for the
  exact species, phase, and reference state.
- `accepted`: an admitted formation enthalpy.
- `not_available`: no admitted formation enthalpy is present.

Join `thermochemistry` to `species` with `record_id` and join its source fields to `sources` with the
corresponding `source_id`. Property-specific source locators in `thermochemistry` take precedence
over the general locator in `sources`.

`selected_as_recommended=1` in `reported_thermochemistry` identifies the value copied into the
calculation-facing `thermochemistry` table. Other rows preserve earlier reported values. These rows
are observations and source records, not an automatically averaged population.

`computational_fallbacks` never overwrites `thermochemistry`. The package reads it only under the
explicit `experimental_then_mp` energy policy, and only when the recommended experimental Gibbs
field is empty.

`metal_oxidation_state` describes the metal's formal chemical oxidation state.
`electron_coefficient_per_metal` describes the signed number of electrons on the product side of
the formation reaction used by the Pourbaix calculation. A negative value means that the reaction
consumes electrons. These values differ for metal hydrides. For example, TiH2 stores oxidation state
+2 and electron coefficient -2.
