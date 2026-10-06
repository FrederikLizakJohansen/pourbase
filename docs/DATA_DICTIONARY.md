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
- `not_available`: no admitted value is present for the property.

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

The Miron continuation retains 14 additional Gibbs evaluations and three original conductance-fit
entropies republished in the 2017 paper. Dehydrated silica, silicate and potassium aluminate
formulas are normalized to the stored hydrated formulas with explicitly cited open NBS liquid-water
Gibbs energy. Each locator gives the original value, added water count and resulting value.
The source-defined NBS HSi(OH)6⁻ record retains its separate identity.

Eighteen formation enthalpies are explicitly calculated from verified original Miron G/S and open
NBS elemental reference entropies using `H=G+298.15*(S-sum(n_i*S_element_i)+q*S_H2/2)`.
Their sources contain `NBS-derived`, identify every input and label the result
`source_verified_estimate`. These calculated estimates have unavailable total uncertainty and
G/S covariance. They fill missing enthalpy fields; existing preferred values are preserved.
Native MINES enthalpies with unresolved original reference ancestry remain in the external review.
The NaCl and HSiO3⁻ appendix/download entropy discrepancies remain held, with database warnings.

MINES metal-complex evaluations retain individually verified G, H and S from Akinfiev and Zotov
(2001), Liu and McPhail (2005), and Akinfiev and Tagirov (2014), with a separately verified older
AuCl evaluation from Sverjensky et al. (1997). Each available property has one preferred value;
existing preferences are preserved. Derived enthalpies and correlation estimates retain their
estimate status and unavailable uncertainty. Source/data-file discrepancies awaiting verification
are identified by warnings.

The Au(OH)2- native MINES enthalpy is exactly reproduced from its stored Gibbs energy,
entropy and Au/H/O/charge reference entropies using `H=G+298.15*(S-foS)`. The warning
records this calculation difference and preserves the original 2001 published enthalpy
as preferred. Admission of the native variant requires complete original provenance for
its H/O reference records; its numerical representation is retained in the external review.

Original nickel and iron solubility fits from González-Siso et al. (2018) and Fürst et al.
(2025, 2026) provide derived Gibbs estimates with explicit parent-ion and water references.
New aqueous Ni(OH)2, crystalline Fe(OH)2 and aqueous Fe(OH)4²⁻ records have one preferred
Gibbs estimate. Existing-species evaluations remain alternatives. Warnings record crystallite
size, nominal temperature and pressure, fitted-model dependencies and unavailable total uncertainty.

The retained Sander (2023) nitrogen triplet is derived from its CC BY 4.0 numerical supplement,
with open NBS molar-mass and gas-entropy references. Its absolute entropy includes N2(g)
reference entropy. The existing preferred entropy's formation/absolute convention defect is
identified by `absolute_entropy_convention_issue`; existing fallback preferences are preserved.

The dehydrated source formulas ZnO(aq) and HZnO2⁻ correspond to the existing Zn(OH)2(aq) and
Zn(OH)3⁻ representations after adding one H2O(l) formula unit. Their property locators document
the original value, exact calorie conversion, water adjustment and openly licensed NBS water
reference. Every normalized property uses the species formula stored in `species`.

The `carbonate-co3` ligand reference uses the existing NBS CO₃²⁻ formation energy. Its complexes
are available when a buffered free carbonate activity is supplied. This activity is distinct from
a total dissolved carbonate concentration, which also depends on protonation and mass balance.

The `silicate-h3sio4` and `aluminate-aloh4` ligand references use the selected H₃SiO₄⁻ and
Al(OH)₄⁻ Gibbs energies, respectively, with their source attribution. Their complexes require an
explicit buffered free-ligand activity. Closed mass-balance calculations conserve the selected
active metal; total silicon or aluminum as a ligand component requires additional acid/base
speciation and component balances. Each complex records its complete formula, ligand count,
formal charge and electron coefficient.

The MINES continuation retains original Migdisov (2009) rare-earth chloride and fluoride
model evaluations. The 14 singly chlorinated species have two entropy fits: Table 7 supplies
the preferred entropy, consistent with the authors' 2016 Table 3, and Table 5 remains available
as an alternative. Shared Gibbs energies republished across tables and versions represent one
evaluation. Source calories are converted using exactly 4.184 J/cal.

Fifty-six formation enthalpies are explicitly derived from those original G/S fits and open
NBS elemental entropies. They retain `source_verified_estimate`, their input locators, the
conventional proton-reference correction and unavailable total uncertainty. The two entropy
fits also produce two separately labelled enthalpy estimates. Native MINES enthalpies retain
their own source-resolution requirements.

The fluoride ligand reference matches the existing preferred F⁻ Gibbs energy, −278790 J/mol,
and cites NBS PDR CSV logical record 119. Fluoride complexes use a supplied free-fluoride
activity. Modeling total fluoride requires its acid-base speciation and component balance.

Forty-one additional USGS Bulletin 2131 properties retain their property-specific reference
columns and source uncertainty intervals. Boehmite and diaspore have separate AlOOH species
and phase records. Adding diaspore changes the aluminum equilibrium diagram where it becomes
the lowest-energy phase. Existing preferred fields remain selected. New values inherited from
JANAF or unresolved CODATA compilations are held in the source review.

The sulfate continuation retains 118 crystalline properties from the openly released NBS
PDR, DOI 10.18434/M32124, and nine USGS properties with individually reviewed ancestry.
Each source identifies the exact CSV record or printed table row. Hydrates retain every water
in their formula unit; distinct calcium sulfate forms and green tetragonal nickel hexahydrate
have separate phase records. The original NBS notes for thenardite, mirabilite and arcanite
state that their G-H-S constraint was relaxed. These reported properties remain independent
selections. All prior preferences are preserved; each available property has one preferred value.

Eleven additional crystalline hydrate records retain their available NBS formation enthalpies.
Seven now also have sourced entropies and derived Gibbs estimates, described below. The other
four retain `not_available` G and S and require a sourced Gibbs energy for equilibrium calculations.
The blue monoclinic nickel
hexahydrate retains its own enthalpy and identity separately from green tetragonal retgersite.

Fifteen rare-earth monosulfate Gibbs estimates use the original Schijf and Byrne (2004)
Table 3 constants extrapolated to zero ionic strength. Their locators record
`G_complex=G_metal+G_sulfate-R*T*ln(10)*log10(beta1)` and every open NBS parent reference.
The source constant precision describes the reaction; total Gibbs uncertainty is unavailable.
Ambient laboratory pressure is represented as nominal 1 bar with an unquantified correction.
The preserved yttrium-ion preference differs from the NBS parent used in its derivation;
a warning records the resulting shift in the implied constant. Entropy and enthalpy remain
unavailable for these complexes. The 2016 neodymium constant discrepancy and the original
2008 disulfate constants measured at 100 bar retain separate source/state holds.

One crystalline ferric sulfate Gibbs estimate uses open NBS formation enthalpy, independently
sourced USGS entropy and open elemental entropy references. Its locator gives the complete
`G=H-T*formation_entropy` derivation and labels the total uncertainty unavailable. The native
USGS H/G evaluation retains its separate ancestry review. Sulfate species participate when
a buffered free sulfate activity is supplied; the existing model conserves the active metal.

Seven sulfate hydrates retain individual DeKock (1982), Bureau of Mines IC 8910 entropy
evaluations or estimates: MnSO4 with one, four, five or seven waters, FeSO4 with one or four
waters, and NiSO4 with four waters. Source calories are converted using exactly 4.184 J/cal.
Their Gibbs energies are explicit estimates from the preserved open NBS enthalpies and
elemental reference entropies: `G=H-298.15*(S-sum(n_i*S_element_i))`. Every locator records
the full hydrate formula and all input references. The source entropy pressure is 1 atm;
its correction to nominal 1 bar is unquantified. Total uncertainty and covariance are
unavailable. Updated warnings record the filled properties and preserve the original H source.
The report's native G/H values retain their separate CODATA/SRD ancestry review.

Thirteen crystalline rare-earth trifluorides retain individually verified original solubility-fit
Gibbs estimates from Migdisov et al. (2009), as published in the authors' 2016 Table 11.
Each source identifies its formula row, G column and J/mol units. Calibration dependencies
on Konings/Kovacs entropy and heat capacity are recorded; those copied handbook properties
retain their separate source holds. The native MINES G differences have warnings. LuF3 uses
the original LuF3 row; the native Lu-labelled YbF3 formula conflict remains documented.
Synthetic crystalline phases have the original XRD evidence and no inferred spacegroup.

Open NBS independently supplies four trifluoride enthalpies and CeF3 entropy. One CeF3
enthalpy is explicitly derived from its original G fit and open NBS entropy references,
with estimate status and unavailable total uncertainty. Independent property evaluations
can disagree with each other; no G-H-S consistency constraint is imposed.
Seven separate rare-earth trifluoride monohydrates retain their open NBS enthalpies.
Their unavailable G and S remain explicit. Fluoride solids enter calculations when a
buffered free fluoride activity is supplied, and complete hydrate formulas retain every water.

Two ferrihydrite records retain the original Majzlan et al. (2004) nominal Fe(OH)3 models,
distinguished by their 2-line and 6-line XRD character. Each retains the original formation
enthalpy, both published Gibbs bounds and both estimated entropy bounds. Bound observations
share a physical/model range; they are not independent measurements or a statistical sample.
The source's enthalpy uncertainty is propagated two standard deviations of the mean. Its
Gibbs uncertainty omits unknown entropy error, and the entropy range has no scalar uncertainty.
The ±0.6 entropy estimate for hypothetical ordered Fe(OH)3 is distinct from ferrihydrite.

Each phase has two explicit NBS-reference Gibbs estimates from `G=H-298.15*(S-S_elements)`,
using open NBS Fe(cr), H2(g) and O2(g) entropies. Lower-bound S=122.2 supplies the preferred
G as an explicitly labelled least-stable limiting case; the upper-S result remains an
alternative. This selection expresses a calculation policy, with no claim of a measured
central value. Derived Gibbs uncertainty and covariance are unavailable. Source H/S are
represented at nominal 298.15 K/1 bar with unquantified ambient-state corrections. Original
published G bounds retain unspecified pressure as `NULL` in `reported_thermochemistry`.
Their exact source conditions and interpretation are recorded in each source locator.

The distinct Gysi–Stefansson (2011) Psat model, borrowed Holland–Powell volume/heat capacity
and native MINES Gibbs variant retain separate source/state holds. Existing preferred values
are preserved. Both nominal ferrihydrite phases have balanced three-oxygen/three-hydrogen
formula units and formal Fe(III). They remain metastable to the existing goethite/water
reference across the tested bounds; omitting more stable solids exposes their range-sensitive
precipitation boundaries. Natural ferrihydrite with differing hydration, adsorbates,
substitution or aggregation requires its own phase model.

Two aqueous yttrium fluoride records distinguish YF²⁺ (one fluoride, charge +2) and
YF₂⁺ (two fluorides, charge +1). Their Gibbs energies and entropies are individually
verified author-published model outputs in Migdisov et al. (2016), Table 5, manuscript
p. 46 / OSTI PDF p. 47, attributed to Loges et al. (2013). Exact calorie-to-joule
conversions use 4.184 J/cal. The conventional HKF reference state is represented at
nominal 298.15 K/1 bar on the conventional ionic entropy scale. Full original 2013
fit methods, calibration references and numerical uncertainties remain source follow-ups.
The measured high-temperature constants retain their saturated-vapor-pressure state.

Both enthalpies are separately labelled new NBS-reference estimates from
`H=G+298.15*(S-S(Y,cr)-nF*S(F2,g)/2+q*S(H2,g)/2)`.
The positive-ion charge term accounts for the conventional `S(H+)=0` scale. NIST is
acknowledged; the derivations date from 6 October 2026 and use open NBS PDR data,
DOI 10.18434/M32124. Total uncertainty and covariance are unavailable. All six
observations have `source_verified_estimate` status and exact source/input locators.
Native MINES rounded G/S representations remain in the external ledger; native H
and its unresolved reference anchors retain their hold. Existing preferences are
preserved. These article-derived values use the individually cited research-fact
route; neither article is represented as an openly licensed database. The complexes
enter calculations when buffered free fluoride is selected.
