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
- `source_verified_estimate`: a published or evaluated estimate, including a derived formation
  enthalpy whose source locator and warning describe the derivation and reference properties.
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

Verified NBS fallback observations and the USGS plattnerite evaluation are retained as
alternatives with `selected_as_recommended=0`. Each has a property-specific source record
containing the exact table or CSV locator, standard state and reuse attribution. The existing
preferred fields supply calculations. Reported USGS uncertainty intervals retain their source
interpretation; they are not assigned an independent one-sigma convention or covariance.

`computational_fallbacks` never overwrites `thermochemistry`. The package reads it only under the
explicit `experimental_then_mp` energy policy, and only when the recommended experimental Gibbs
field is empty.

`metal_oxidation_state` describes the metal's formal chemical oxidation state.
`electron_coefficient_per_metal` describes the signed number of electrons on the product side of
the formation reaction used by the Pourbaix calculation. A negative value means that the reaction
consumes electrons. These values differ for metal hydrides. For example, TiH2 stores oxidation state
+2 and electron coefficient -2.

## Retained aqueous research evaluations

Miron (2016, 2017) model evaluations retain their publication year, exact property locator,
evidence status and reported uncertainty. Alternate evaluations remain in
`reported_thermochemistry`; calculations use the single preferred value for each available
species/property. Published/data-file discrepancies retain both representations with a warning.
Existing preferred Gibbs energies are preserved. Original fits and correlation estimates use
`source_verified_estimate`; Monte Carlo standard deviations describe parameter dispersion.

MINES metal-complex evaluations retain individually verified G, H and S from Akinfiev and Zotov
(2001), Liu and McPhail (2005), and Akinfiev and Tagirov (2014), with a separately verified older
AuCl evaluation from Sverjensky et al. (1997). Each available property has one preferred value;
existing preferences are preserved. Derived enthalpies and correlation estimates retain their
estimate status and unavailable uncertainty. Source/data-file discrepancies awaiting verification
are identified by warnings.

The dehydrated source formulas ZnO(aq) and HZnO2⁻ correspond to the existing Zn(OH)2(aq) and
Zn(OH)3⁻ representations after adding one H2O(l) formula unit. Their property locators document
the original value, exact calorie conversion, water adjustment and openly licensed NBS water
reference. Every normalized property uses the species formula stored in `species`.

The `carbonate-co3` ligand reference uses the existing NBS CO₃²⁻ formation energy. Its complexes
are available when a buffered free carbonate activity is supplied. This activity is distinct from
a total dissolved carbonate concentration, which also depends on protonation and mass balance.
