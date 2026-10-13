# Database tables

`src/pourbase/data/pourbase.sqlite` is the database distributed with this publication. All
thermochemical quantities use one formula unit as the molar basis.

| Table | Contents |
|---|---|
| `metadata` | Dataset version, database role, reference temperature, pressure, and water Gibbs energy |
| `species` | Stable record ID, displayed species, ASCII formula, phase, charge, atom counts, ligand encoding, formal metal oxidation state, and signed electron coefficient for the metal/water reaction |
| `selected_thermochemistry` | Derived when the database is opened: recommended Gibbs energy, entropy, formation enthalpy, scientific status, uncertainty, source ID, and exact source locator |
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

The file stores evidence only. `reported_thermochemistry` holds every reported value with its
source, status and, where it differs from the general locator in `sources`, a value-specific
`source_locator`. The recommended value of each species and property is derived when the
database is opened: the selection policy `src/pourbase/data/selection-policy.toml`, or another
policy the user loads, chooses one eligible reported value. The package presents the result to
every connection as the temporary table `selected_thermochemistry`, with one row per species and, for each
property, the value, status, uncertainty, source, locator and `value_id` of the chosen reported
value. A property without an eligible value has status `terminal_evidence_gap` when a reported row
records the gap and `not_available` otherwise. Schema 7 files, which store a `thermochemistry` table and the
flag `selected_as_recommended`, remain readable.

Reported rows are observations and source records, not an automatically averaged population.

The final MINES R05 import adds 92 observations and 35 species. These include
individual USGS mineral evaluations and original fitted outputs from Gysi et al.
(2018) and Gysi and Harlov (2021). Existing non-empty preferred properties are
preserved. Copied JANAF/CODATA cells, missing original tables, unresolved native
variants and reaction-anchor derivations remain in the external source review.
Entropy-only records retain an empty formation Gibbs energy.

Realgar uses the full As₄S₄ formula unit: source AsS properties and uncertainty
intervals are multiplied by four. Sphalerite and wurtzite have separate ZnS phase
records. For FeS₂, formal Fe oxidation state +2 accompanies a four-electron
reaction coefficient when the two sulfur atoms are represented by free S²⁻.

The `phosphate-po4` ligand uses the explicitly open NBS PDR reference for free
PO₄³⁻, G = −1,018,700 J/mol at 298.15 K and 1 bar. Its activity is specified
directly. Total-phosphate concentrations, phosphate protonation and mineral solid
solutions require their own models. Ideal beta-Ca₃(PO₄)₂ and hydroxyapatite use
their full formula units; natural substituted whitlockite is a separate composition.

The rare-earth phosphate and monohydroxo fit outputs have status
`source_verified_estimate`. Modes I and II use different coupled calibrations;
each output carries its mode, original table locator and reported Monte Carlo
dispersion. The retained 2021 Fit 2 entropies and Fit 3 enthalpies are distinct
constrained estimates. A preferred triplet assembled from these outputs does
not establish a thermodynamically consistent joint model. Warnings describe
these dependencies, and existing aqueous-ion preferences remain in place.

Verified NBS fallback observations and the USGS plattnerite evaluation are retained as
alternatives that the default policy does not recommend. Each has a property-specific source record
containing the exact table or CSV locator, standard state and reuse attribution. The existing
preferred fields supply calculations. Reported USGS uncertainty intervals retain their source
interpretation; they are not assigned an independent one-sigma convention or covariance.

VO₂ retains seven alternative federal evaluations: G/H/S from the open NBS PDR
release and NBS Technical Note 270-5 (1971), Table 54(2), plus the entropy
reevaluation in Bureau of Mines Bulletin 672 (1982), page 459. Every source uses
V₂O₄; all retained properties are divided by two to match the stored VO₂ formula
unit. The PDR values retain 1 bar, and the older evaluations retain 1 atm as
1.01325 bar. Their individual uncertainties are unavailable. Shared NBS ancestry
and the identical Bureau of Mines/NBS 1971 formation enthalpy are documented;
that repeated enthalpy is linked to the NBS observation.

The source α phase maps to the existing monoclinic M1 record through its
340 K transition branch and independently cited structural studies. Each locator
identifies this as a cross-source inference; the original calorimetry specimen's
diffraction record remains a follow-up. Existing preferred properties and the
phase row are preserved. The Bureau of Mines formation G retains a JANAF
elemental-reference hold in the external review. These additions cover the
three previously unresolved VO₂ permission requests as retained alternatives.

`computational_fallbacks` never overwrites `selected_thermochemistry`. The package reads it only under the
explicit `experimental_then_mp` energy policy, and only when the recommended experimental Gibbs
field is empty.

`metal_oxidation_state` describes the metal's formal chemical oxidation state.
`electron_coefficient_per_metal` describes the signed number of electrons on the product side of
the formation reaction used by the Pourbaix calculation. A negative value means that the reaction
consumes electrons. These values differ for metal hydrides. For example, TiH2 stores oxidation state
+2 and electron coefficient -2.

The TiH₂ source review adds structural and provenance warnings. The original
Padurets et al. (1999) X-ray study identifies TiH₁.₉₉ as cubic at 298 K and
tetragonal at 288 K. Its specimen provides structural evidence for the existing
phase assignment; a link to the specimens underlying the preferred thermochemistry
remains unverified. The cubic/tetragonal phase names are cross-referenced explicitly.

Three open NBS PDR candidates remain in the external review ledger because the
generic crystalline row lacks specimen composition and polymorph evidence. The
Bulletin 674 TiH₂ entry explicitly cites JANAF (reference 7), so it remains an
inherited source hold. This review adds two source records and three warnings;
all reported observations, preferred properties and species/phase rows are preserved.

The anhydrous Sr(OH)₂ review adds four source records and four warnings.
The original NBS powder standard identifies orthorhombic Pbnm material and
flags an older pattern labelled anhydrous as the monohydrate. Its diffraction
specimen is separate from the thermochemical evaluations. The original NBS
Table 95:Sr formation enthalpy remains external pending specimen/evaluation
mapping; its Gibbs-energy and entropy cells are empty. Konings et al. (1988)
provides an original formation-enthalpy candidate whose auxiliary numerical
inputs still need review. Konings et al. (1990) provides a low-temperature
calorimetry lead; its numerical entropy table has not been retrieved. This
review adds zero numerical observations. Existing preferred values, statuses,
source IDs and phase/species records are preserved.

The anhydrous Ba(OH)₂ review adds four source records and five warnings. The
existing α-phase assignment retains its structural crosswalk to deuterated
Ba(OD)₂. The open NBS formation enthalpy remains in the external review ledger
pending an α/β polymorph assignment. Djamali's (2009) original α-phase calorimetry
provides a further enthalpy candidate whose extrapolation and auxiliary numerical
inputs still require verification.

The preferred JANAF entropy has an estimated origin: its source describes additive
cation/anion entropy constants. That limitation is now explicit in a warning;
the existing value, status and source ID are preserved. Powers and Blalock's
original ORNL-1653 calorimetry supplies high-temperature heat-content increments
and heat capacities. Those quantities remain distinct from the requested
298.15 K formation properties and absolute entropy. This review admits zero
numerical observations and preserves all earlier observations and preferences.

## Retained aqueous research evaluations

The remaining Shock1997 Table 7/10 batch adds 67 observations and 26 species:
eight fitted Gibbs energies, 51 fitted/correlated entropies and eight explicitly
NBS-derived enthalpies. Seventeen existing original evaluations are linked once.
Original-paper identities establish neutral HGaO₂ and singly negative YO₂⁻,
correcting charge errors in the native release. Original Table 10 entropy source
ambiguities for CdO₂²⁻, ZrO²⁺ and HfO²⁺ remain external. Earlier non-empty preferred
properties and sources are preserved; each available property has one preference.

Twenty-five new species retain entropy only. Strict calculations report these
missing Gibbs energies; `allow_incomplete=True` calculates with the available
Gibbs values and lists exclusions. The available-G-only diagrams for all 74 systems
match the prior database on the checked grid. Existing closed-mass-balance support
continues to require systems without a gas phase.

The Shock et al. (1997) Fe/Ni/Sn/Pb continuation retains 35 observations: 11 original
Gibbs energies, 14 original fitted/correlated entropies and ten newly calculated
NBS-reference enthalpies. Both original Table 7 iron regressions retain their own
G/S pairs and derived H. Hydrated formulas explicitly add open NBS water properties.
Every earlier non-empty preferred property and source is preserved.

Table 7 and Table 10 disagree on NiO(aq) and PbOH⁺ entropy. Their entropy and
dependent enthalpy candidates remain external, with database warnings. Original
correlation estimates retain their calibration dependencies; inherited hydrolysis
formation values and native Cox/Glushko/Wagman-derived enthalpies remain held.
Total uncertainty and covariance are unavailable. The general Table 7 entropy
interval is recorded in locators with its unspecified confidence convention.

New aqueous Fe(OH)₃, Ni(OH)₄²⁻ and Sn(OH)₂ have entropy only. They remain
inspectable in `species_records`. Calculations omit them with
`allow_incomplete=True`; strict mode reports the missing Gibbs energies. The strict
periodic screen calculates 56 systems, or 59 with the six solid MP fallbacks.
Allowing incomplete systems calculates all 74 supported systems.

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

Crystalline EuF₃ has a preferred Gibbs estimate derived from the original Migdisov
(2009) Table 2 solubility extrapolation, `log10 Ksp = -19.28`, and open NBS Eu³⁺/F⁻
reference energies. Its dissolution reaction, `EuF3(cr)=Eu3+(aq)+3F-(aq)`, retains all
three fluoride ions. The extrapolation uses the authors' disclosed solid entropy and
heat-capacity calibration. Total uncertainty and the source-specific condensed-phase
pressure correction are unavailable; the exact polymorph remains unspecified.
EuF₃ also retains two alternatives from Bureau of Mines Bulletin 674 (1984),
page 213: formation H = −1584062.4 J/mol and estimated S = 107.1104 J/(mol K).
Both retain 298.15 K and the source's original 1 atm pressure as 1.01325 bar;
their uncertainties are unavailable. H is the government critical evaluation
citing Kim and Oishi (1979); S is explicitly marked as an estimate. The original
parent's numerical tables and measurement ancestry remain follow-ups. These rows
remain alternatives pending source, phase and standard-state reconciliation with
the existing nominal 1 bar calculation record. Its preferred Gibbs estimate and
unassigned H/S fields are preserved. The source's calculated formation G retains
a JANAF ancestry hold: its elemental fluorine entropy comes through Bulletin 672.
The low-temperature branch label and the separate 920 K EuF₃ transition are
recorded without assigning a crystal structure to the solubility-study sample.

The original 2016 Table 11 omits EuF₃. Native MINES G differs from this reference-anchored
estimate; native S and calculated H retain their original-source follow-ups. The
anhydrous solid and the existing H-only EuF₃·H₂O record have separate identities.
Calculations activate the anhydrous solid when a free-fluoride reservoir is supplied.

La(OH)₃ and Nd(OH)₃ retain nine additional observations alongside their preferred
calorimetric/critical evaluations. These include the open NBS crystalline La(OH)₃
enthalpy, the original 2016 Wood-based Nd(OH)₃ G/S model, Wood's original 2002
formation-enthalpy estimate, and separately labelled estimates using open NBS anchors.
Each derivation records every input and its reference; total derived uncertainty is
unavailable. Wood's published H interval remains ±5000 J/mol. His dissolution-reaction
properties are converted to formation properties with explicit aqueous/water references.
Rounded reaction entropy limits cross-property consistency. The NBS La row specifies
crystalline material without a named polymorph; its source and phase uncertainty remain
explicit. Original 1980 calorimetric entropies round to the existing preferred values and
are linked in the source review. Native MINES enthalpies retain their original-reference
follow-up. The preferred calculation values remain selected.

The `sulfide-s` ligand reference uses the open NBS S²⁻ Gibbs energy, **+85800 J/mol**,
CSV logical record 526, DOI 10.18434/M32124. Monoclinic acanthite Ag₂S enters calculations
when a buffered free S²⁻ activity is supplied. Its balanced reaction is
`2Ag(cr)+S²⁻(aq)=Ag₂S(cr)+2e⁻`; each formula unit contains two active silver atoms.
The metal balance conserves silver. Total sulfide requires H₂S/HS⁻ protonation and a
separate sulfur component balance.

Acanthite retains preferred USGS Bulletin 2131 formation G = −39700 ± 1000 J/mol
and H = −32000 ± 1000 J/mol, with exact property columns and original 1951/1988
electrochemical/calorimetric ancestry. These are the government critical evaluations;
the parent papers' full numerical tables remain source follow-ups. Original Grønvold–Westrum
**1986** calorimetry supplies preferred S = 142.89 ± 0.44 J/(mol K). The MINES year 1985
is corrected to the published year. The original entropy's pressure is unspecified and
remains `NULL` in its reported row; calculations use nominal 1 bar with an unquantified
condensed-phase correction. Source uncertainty intervals retain their reported meaning.
The USGS rounded entropy 142.9 ± 0.3 links externally to the same original evaluation.

A fourth observation retains the separately labelled new estimate
`G=H−298.15*(S−2S(Ag,cr)−S(S,rhombic cr))` = −39748.9185 J/mol, with open NBS elemental
entropies and unavailable total uncertainty/covariance. All three available properties
have one preferred value; earlier records and preferences are preserved. Rights follow
the government evaluation, explicit open NBS licence and individually cited original
research-fact routes. The university deposit supplies access to the copyrighted 1986
paper. Its article licence remains separate from reuse of its individual numerical fact.
The conflicting open NBS alpha phase label “orthorhombic” and distinct beta phase values
retain identity holds outside this monoclinic record. Heat capacity, thermal enthalpy
increments, Gibbs functions and transition properties remain external model candidates.

Galena retains eight observations for anhydrous cubic crystalline PbS: open NBS G/H/S,
Bureau of Mines Bulletin 689 G/H/S, and USGS Bulletin 2131 formation G/H. Preferred
G = −96800 ± 2000 J/mol and H = −98300 ± 2000 J/mol are the USGS critical evaluations;
preferred S = 91.2 J/(mol K) comes from open NBS PDR CSV logical record 3275.
Each property has one preferred value. The warning identifies this mixed evaluation
triplet and overlapping source ancestry; uncertainties retain their published meaning.

The Bureau of Mines alternatives retain their original 1 atm pressure as 1.01325 bar
and exact calorie conversions, with an unquantified condensed-phase pressure correction.
The USGS/native entropy 91.7 J/(mol K) keeps its JANAF ancestry hold in the external
review. Formation properties carry their own property-specific research references.
Galena uses one Pb and one buffered free S²⁻ in `Pb(cr)+S²⁻(aq)=PbS(cr)+2e⁻`.
Total sulfide speciation, additional property models and exact space-group details
retain their separate follow-ups. All earlier observations and preferences are preserved.

Cotunnite retains eight observations for anhydrous orthorhombic PbCl₂. Preferred
G = −314100 J/mol, H = −359410 J/mol and S = 136.0 J/(mol K) come from explicitly
open NBS PDR CSV logical record 3241, at 298.15 K and 1 bar. Their uncertainties
are unavailable. Bureau of Mines Bulletin 674 formation G/H alternatives retain
their original 1 atm pressure as 1.01325 bar. Bulletin 592 supplies three separate
entropy evaluations with their published intervals and unspecified pressure (`NULL`).
Its adopted entropy also appears in Bulletin 674; that source repetition is linked
in the review notes. Shared ancestry and pressure differences are documented.

The USGS/MINES PbCl₂ thermochemical representations keep their JANAF source holds
in the external review. The original USGS phase description corroborates cotunnite;
its uncertainties are kept separate from the open NBS evaluation. Cotunnite uses
one Pb and two buffered free Cl⁻ in `Pb(cr)+2Cl⁻(aq)=PbCl₂(cr)+2e⁻`. The existing
chloride reference is corroborated by open NBS logical record 174. Total chloride
conservation, other property models and exact space-group details remain follow-ups.

Litharge retains five additional source representations alongside its earlier values:
USGS Bulletin 2131 G = −188900 ± 800 J/mol and H = −219000 ± 800 J/mol, and
Bureau of Mines Bulletin 672 G/H/S at the original 1 atm pressure (1.01325 bar).
All five are alternatives; existing preferences, phase identity and earlier observations
are preserved. The USGS formation values cite the NBS evaluation already retained
from the open PDR. Their rounding and published uncertainty intervals remain attached
to the USGS representation. Source overlap is documented; values are kept individually.

The Bureau of Mines formation H and 298.15 K entropy cite the older NBS technical
note. Its low-temperature heat-capacity citation points to King reference 128, while
the bibliography identifies the relevant lead-oxide paper as 129. The database
records this mismatch and the government table's actual G/H/S ancestry. Original
experimental tables, heat-capacity models and pressure corrections remain follow-ups.

Anglesite retains six alternative G/H/S observations from the original NBS Technical
Note 270-2 (1966), Table 27(4), and USGS Bulletin 1259 (1968), pages 22 and 197.
Both sources retain their original 1 atm pressure as 1.01325 bar. The USGS observations
carry their published intervals; the NBS observations have no supplied uncertainty.
Their shared ancestry is recorded: USGS entropy cites Gallagher et al. (1960), and
formation G/H cite the 1966 NBS evaluation. Each source representation is kept with
its own precision and interval. All existing preferred properties and phase records
are preserved. Preferred anglesite G/H/S are corroborated by open NBS PDR logical
record 3277. The later USGS/MINES and Bureau of Mines representations that cite
CODATA retain their source-rights holds in the external review.

Minium retains seven additional federal observations for crystalline Pb₃O₄: G/H/S
from NBS Technical Note 270-2 (1966), Table 27(1), and USGS Bulletin 1259 (1968),
page 18, plus the entropy recalculation in Bureau of Mines Bulletin 592 (1961),
page 58. All retain the original 1 atm pressure as 1.01325 bar. Bulletin 592 states
this entropy convention on page 4. Its S = 211.292 ± 6.6944 J/(mol K) includes
a disclosed low-temperature extrapolation; the later USGS evaluation has the same
rounded entropy with its own interval ±6.276 J/(mol K). Each interval remains
attached to its source. NBS supplies no uncertainty. Shared evaluation ancestry
and the difference between the older formation G representations are documented.

All existing minium observations, preferred values and tetragonal phase identity
are preserved. The later USGS/MINES and Bureau of Mines minium representations
retain their JANAF ancestry holds in the external review. The full formula unit
contains three Pb and four O atoms: `3Pb(cr)+4H₂O(l)=Pb₃O₄(cr)+8H⁺+8e⁻`.
Original experimental tables and additional property models remain follow-ups.
The newly verified Bulletin 592 pressure convention also supplies evidence for the
three earlier cotunnite entropy rows whose pressure is currently `NULL`; a warning
records this evidence and their separate metadata reconciliation follow-up.

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

The Perry–Gysi (2020) carbonate-source review adds independent anhydrous crystalline
NBS evaluations for Y₂(CO₃)₃, Sm₂(CO₃)₃, Nd₂(CO₃)₃ and La₂(CO₃)₃ Gibbs energies,
and Tb₂(CO₃)₃ and Pr₂(CO₃)₃ enthalpies. Each observation cites its exact row and column
in the openly released NIST PDR, DOI 10.18434/M32124, at 298.15 K/1 bar. Values use
the full two-metal/three-carbonate formula unit. NIST is acknowledged; kJ-to-J
conversions date from 6 October 2026. Source uncertainties and polymorph details are
unavailable, with no inferred crystal structure. The two enthalpy-only records retain
unavailable Gibbs energy and entropy and are excluded from equilibrium calculations.
The four Gibbs records enter calculations when buffered free carbonate is selected.

Perry–Gysi Appendix A.2 identifies its carbonate G/H values as inherited compilation
or separately cited calorimetry inputs; those native representations keep their source
holds in the external review. Its new Table 6 Gibbs models describe calcite solid-solution
endmembers at 200 °C/15.5 bar. Its carbonate heat capacities require separate property
and temperature-model support. These source states and model identities are retained
in the external candidate ledger. The independent NBS entries preserve all existing
preferences and do not assign an anhydrous evaluation to a hydrate or solid solution.

Nineteen Akinfiev–Diamond (2003) observations retain independent model evaluations for
aqueous CH₄, CO₂, N₂, NH₃ and H₂S. Six separately cited Table 1 Henry-solubility fits
produce Gibbs energies and absolute entropies through the rounded 298.15 K/1 bar
relations in Appendix A.4, using explicitly open NBS gas references. Six enthalpies
are new estimates from `H=G+298.15*(S-S_elements)` with open NBS elemental entropies.
Both H₂S fit ranges are retained separately, together with the original printed
below-200 °C entropy output, 29.96 cal/(mol K), converted using 4.184 J/cal.

All 19 observations have `source_verified_estimate` status and remain alternatives;
existing preferred values are preserved. Sources identify every fitted coefficient,
gas and elemental reference row, molal standard state, derivation and conversion date.
Entropy includes the gas entropy; the model's mole-fraction-to-molality conversion
is applied once. Published coefficient rounding limits precision, and total uncertainty
and covariance are unavailable. NIST is acknowledged for the open NBS PDR references,
DOI 10.18434/M32124. The original model's Hill/Glushko solvent-calibration dependency
is disclosed; no separate restricted calibration entries or copied Table 2 inputs
are added. These individually cited research facts do not confer an open licence
on the copyrighted paper. Native MINES reference variants remain externally held.

Verified aqueous benzene entropy is retained in the external candidate ledger pending
an eligible Gibbs energy, preserving carbon-screening coverage. Hydrogen, oxygen and
argon model outputs await component support; their values and source decisions are
also retained externally. Preferred calculations and periodic-screen coverage are
unchanged by this batch.

Eleven Wolery–Jové Colón (2017) observations retain new research evaluations for
Al³⁺, gibbsite and corundum, DOI 10.1016/j.gca.2016.09.028. Table 23 supplies two
recomputed mineral formation Gibbs energies. Table 24 supplies separate G/H/S
triplets for corrections to the Pokrovskii–Helgeson (1995) and Tagirov–Schott (2001)
models. These corrections preserve the gibbsite dissolution reaction G and S while
updating water and elemental references. Table 25 supplies a separate calorimetric
reevaluation of Al³⁺ G/H/S. Exact citations identify the public author manuscript's
pages 54–55, tables, rows and columns; G/H use the column-header kJ/mol units.

The calorimetric uncertainties remain the source's reported two-standard-deviation
intervals: 1623 J/mol for G, 862 J/mol for H and 4.610 J/(mol K) for S. Corrected
model rows have unavailable uncertainty. All observations have
`source_verified_estimate` status. The calorimetric H fills the previously missing
preferred Al³⁺ enthalpy; existing preferred properties are preserved. A warning
identifies the mixed preferred Al³⁺ G/S/H evaluations, which must be assessed
separately from each internally related source triplet.

These individually cited original research outputs follow the project's research-fact
route. Public manuscript access establishes access to evidence; article and report
licences require their own assessment. The numerical evaluations retain disclosed
USGS, SUPCRT92, CODATA and calorimetric dependencies. Unchanged inherited comparison
rows and calibration tables remain external, including the corundum H/S inputs.
The recomputed corundum G coincides with CODATA because its H/S inputs coincide.
Original Tagirov–Schott (2001) fluoride tables still await direct source verification;
the new corrected evaluations are attributed to Wolery–Jové Colón (2017).

Four silica models retain the Wolery–Jové Colón (2017) Table 20 reference corrections
to the Rimstidt (1997), Gunnarsson–Arnórsson (2000), Stefánsson (2001) and
Apps–Spycher (2004) evaluations. Eleven new corrected properties are attached to the
existing neutral aqueous H₄SiO₄ record. Their sources identify manuscript page 50,
each model row and property column, and the supporting calculation worksheets.
They use the authors' quartz, water and elemental reference convention at
298.15 K/1 bar, with `source_verified_estimate` status and unavailable total uncertainty.

Rimstidt's original G/H/S solubility-fit outputs are retained separately, verified
against the original publisher abstract, DOI 10.1016/S0016-7037(97)00103-8. Their
reported one-standard-deviation intervals are 610 J/mol for G, 542 J/mol for H and
0.49 J/(mol K) for S. The abstract's numerical content was retrieved through the
indexed publisher page; full original methods remain a source follow-up. Its
nominal 298.15 K/1 bar standard state is corroborated by the later original research
paper. The unchanged Rimstidt entropy in Table 20 links to this original observation.
The corrected G/H evaluations carry their own uncertainty interpretation.

The table's SiO₂(aq) columns represent the same models with two liquid-water formula
units removed. Their 12 property cells remain linked in the external review ledger
to the H₄SiO₄ observations. This preserves their source representation and avoids
adding a duplicate aqueous solute. The correction preserves quartz dissolution G/S
and recalculates final formation H from G/S. Related evaluations share source inputs
and must be assessed as models with dependencies. All 14 admitted observations
remain alternatives; existing preferred values and calculation results are preserved.
They follow the individually cited original research-fact route, with reference
dependencies disclosed and article licences assessed separately. Copied compilation
inputs and tentative silica-dimer corrections retain their external source holds.

KO₂ retains four additional federal evaluations: open NIST PDR formation G/H and
entropy at 298.15 K/1 bar, and the Bureau of Mines Bulletin 672 (1982), page 208,
formation H at 298.15 K/1 atm. Each is per mole of the full KO₂ formula unit.
The Bureau of Mines enthalpy cites D'Orazio–Wood (1965) and Gilles–Margrave (1956)
and equals the existing preferred enthalpy numerically; shared ancestry remains
possible. Its JANAF-derived entropy and formation G remain outside this import.

The historical NBS entropy is 116.7 J/(mol K), compared with the preferred
122.499 J/(mol K). The difference is close to the spin-½ entropy R ln 2.
Todd's original calorimetry began near 50 K; the full low-temperature integration
and magnetic correction remain under review. A warning records this hypothesis
and the convention limitation on the retained historical G/S evaluations.
Their `verified` status establishes the reported source values. Compatibility as
replacements requires a further review of their entropy basis. All preferred
values and the tetragonal I4/mmm phase record are preserved. The room-temperature
bulk-phase mapping is an explicit cross-source inference; historical specimen
identity remains open. A separate warning tracks the legacy formal oxidation
metadata; the balanced reaction retains four electrons and four protons per K.

The α-TiO record retains the original Beyer et al. (1982) entropy evaluation,
34.26 ± 0.07 J/(mol K), as an alternative. The Bureau of Mines study reports
the calorimetric sample's O/Ti ratio as 1.006 ± 0.002 and identifies its monoclinic
structure by powder XRD after one week of vacuum annealing at 1180 K. The authors
use their measured entropy for nominal α-TiO in the discussion on page 965.
The source locator preserves this nominal composition mapping, the sample-based
molar mass, and the published uncertainty interval. A correction to exact O/Ti=1
and a separate composition-mapping uncertainty remain unavailable.

Table 5 reports S(T)−S(0); page 965 explicitly uses the measured value as absolute
entropy. The authors extrapolate heat capacities below 5 K and omit the negligible
superconducting contribution below 1 K. Standard-state pressure is unspecified
and remains NULL; the calorimeter's helium backfill is recorded as apparatus
information. The CDC archive labels the study Public Domain; this import retains
one individually cited original research value. Its formation H/G results inherit
JANAF formation enthalpy and remain outside this import. The NBS TiO G/H/S
alternatives retain their original-specimen and evaluation-ancestry holds.
All preferred values, source IDs, species fields and phase records are preserved.

On 12 October 2026, the database gained 19 USGS Bulletin 2131 observations for
seven pure carbonate minerals: calcite, aragonite, vaterite, siderite,
rhodochrosite, strontianite and witherite. Printed pp. 25–26 give formation
Gibbs energies for all seven and entropies and formation enthalpies for six;
vaterite's missing properties in this table remain explicit. Each observation is at 298.15 K
and 1 bar, per mole of the full MCO₃ formula unit. Energy values and their
uncertainty intervals were converted from kJ/mol to J/mol. Entropies retain
J/(mol K). Source locators preserve the evaluation's numbered numerical parents.

The published uncertainty intervals are stored as reported. The source describes
calorimetric intervals as typically twice the standard deviation of the mean;
these intervals should retain their source-specific interpretation in uncertainty
analyses. Calcite, aragonite and vaterite remain separate phase records.

These minerals use the existing `carbonate-co3` reference and a buffered free
CO₃²⁻ activity. Enable that ligand to include them in calculations. A total
dissolved carbonate concentration requires a separate carbonate speciation model.
The balanced reaction has two electrons, no protons and one carbonate per metal.
Solubility products calculated with the selected aqueous-ion and ligand references
combine those evaluations with the USGS solid values. Native PHREEQC reaction
constants remain subject to their own source and standard-state review.

The default policy selects all 19 new properties. Earlier evidence and selections
are preserved. The resulting snapshot has 792 species and 2,588 observations,
with 700 selected Gibbs energies, 670 entropies and 520 formation enthalpies
before the following derivation batch.

The native carbonate reaction review adds six separately calculated G/H/S
alternatives for aragonite and vaterite from the original Plummer and Busenberg
(1982) solubility-fit equations. For dissolution to the same Ca²⁺ and CO₃²⁻
products, the aqueous reference terms cancel:
`G_phase − G_calcite = RT ln(K_phase/K_calcite)`.
Differentiating the original temperature expressions gives
`S_phase − S_calcite = −d(G_phase − G_calcite)/dT` and
`H_phase − H_calcite = (G_phase − G_calcite) + T(S_phase − S_calcite)`.
The reviewed USGS calcite G/H/S provide the separate formation anchors.

These estimates use a stated local constant-volume model for the 1 atm to
1 bar transfer. Original solid volumes give a relative G/H correction below
0.004 J/mol; the model assumes temperature-independent volumes and zero entropy
transfer. Source locators record the complete equations, coefficients, anchors
and pressure assumption. Fit-coefficient, shared-model and anchor covariance
are unavailable, so total uncertainty remains NULL. The derived aragonite entropy
differs from calorimetry and stays an alternative.

All six observations have `source_verified_estimate` status and class E under
the unchanged default policy. Vaterite gains estimated H and S; its selected
G remains the USGS point evaluation, 233.2 J/mol below the paired derived G.
These selected properties represent distinct evaluations, with a warning that
they do not establish a single fitted thermodynamic triplet. Earlier reported
values and selections are preserved. The current snapshot has 792 species,
2,594 observations, 700 selected Gibbs energies, 671 entropies and 521 formation
enthalpies. Default and carbonate-enabled diagrams and metal balances are
unchanged because the selected Gibbs energies are preserved.

The subsequent Sr/Ba anchor batch adds two verified NBS ion formation enthalpies
and 18 original-fit formation estimates for strontianite, witherite and aqueous
SrCO₃, BaCO₃, SrHCO₃⁺ and BaHCO₃⁺. The two bicarbonate complexes are new species.
NBS CSV logical records 9635/9932 supply Sr²⁺/Ba²⁺ G/H/S; records 1661/1673
supply CO₃²⁻/HCO₃⁻ G/H/S. Each source locator records the original rows,
columns, values, units and reference conventions.

The original 1984/1986 reaction fits use 1 atm. The new estimates explicitly
assume a locally pressure-flat balanced reaction (`ΔV_r(T) = 0`) over the
1.01325-to-1 bar interval. Reaction pressure corrections to G/H/S are zero
in this approximation. The sensitivity of G to an actual constant reaction
volume is −0.001325 J/mol per cm³/mol; the locator's 100 cm³/mol example
is illustrative, with no certified bound on the pressure error. Actual
reaction-volume temperature dependence and total fit/reference covariance
remain unavailable, so uncertainty is NULL. This assumption covers local
298.15 K/1 bar estimates. Exact native pressure transfers stay in the external
review. Original-study metal-ion reevaluations are separate from these NBS anchors.

For each fitted reaction, `ΔG = −RT ln K`, `ΔH = RT² d(ln K)/dT` and
`ΔS = (ΔH − ΔG)/T`. Association formation properties add the reaction
properties to the ion/ligand anchors; mineral dissolution subtracts them.
Balanced charges preserve the conventional aqueous H⁺ reference. Bicarbonate
complexes use one `carbonate-co3` ligand and one core hydrogen, giving two
electrons and −1 proton per metal in the transformed formation reaction.
The original association constants are reproduced with the NBS carbonate
protonation reference under this local approximation.

All earlier evidence is retained. The unchanged default policy selects the
original-fit estimates over correlations for aqueous SrCO₃/BaCO₃, changing
six preferred G/H/S fields. Eight previously absent preferred fields become
available: Sr²⁺/Ba²⁺ H and both bicarbonate-complex G/H/S triplets. Selected
solid mineral values stay unchanged. The 74 default ligand-free diagrams
are unchanged; carbonate-enabled Sr/Ba diagrams incorporate the new complexes
and selected association fits. Their aqueous ratios and closed-metal balances
are checked against the original rounded point constants. Current totals:
794 species, 2,614 observations, and 702/673/525 selected G/S/H fields.

The Fe/Mn original-source checkpoint retains four further observations.
Open NBS CSV logical records 5804/6291, column 7 (zero-based), supply Fe²⁺
and Mn²⁺ formation enthalpies of −89.1 and −220.75 kJ/mol, converted to
−89,100 and −220,750 J/mol. Both apply at 298.15 K/1 bar, with the
conventional aqueous H⁺ reference and unavailable uncertainty. The Fe²⁺
preferred G/S remain the later Parker/Khodakovskii values; its new NBS H
belongs to a separate evaluation. Each property's source stays visible.

Original USGS calorimetry in Robie, Haselton and Hemingway (1984), pp. 353–354,
Tables 5–6, reports pure-endmember entropies of 98.03 ± 0.10 J/(mol K)
for rhodochrosite and 95.47 ± 0.15 J/(mol K) for siderite. The authors
corrected the measured specimens' minor carbonate impurities before integrating
and smoothing their heat capacities. These source-verified observations retain
their published precision and intervals. Their pressure is unspecified (NULL);
the 5 kPa helium calorimeter fill is recorded as apparatus information.
They share an experimental lineage with the stored later critical evaluations,
whose explicit-1-bar entropies remain preferred. The source warning records
that covariance and uncertainty conventions are source-specific.

The accompanying native-source register distinguishes crystalline siderite
(WATEQ species 94) and rhodochrosite (564) from separate synthetic/disordered
evaluations (9 and 190). A blank reaction enthalpy retains its missing-evidence
status. The original Nordstrom1990 abstract specifies 1 bar; its numerical
chapter tables and per-property upstream ancestry remain held outside the
release. Reaction H is kept distinct from formation H in this review.

All previously stored rows and preferred values are preserved; two missing
ion H fields become available. All 74 default diagrams and six carbonate-enabled
Fe/Mn diagrams and metal balances are unchanged. The current snapshot has
794 species, 2,618 observations and 702/673/527 selected G/S/H fields.

The calcium aqueous-association continuation adds seven observations: the
missing Ca²⁺ formation enthalpy (−542,830 J/mol, open NBS CSV logical record
9196) and six original-fit G/H/S alternatives for existing CaCO3(aq) and
CaHCO3+ records. Plummer and Busenberg (1982), original numerical abstract
equations 4–5, supply the association functions. Their exact printed
bicarbonate coefficient is 0.31294. Fit derivatives give reaction H/S;
open NBS ion and ligand properties give the separate formation anchors.
These class E estimates use the documented local pressure-flat approximation
and NULL total uncertainty. Miron formation recommendations remain preferred.

WATEQ4F (1991), printed p. 26, lists the same association functions with
reaction-enthalpy point entries of 5.410 kcal/mol for CaHCO3+ and 4.030 kcal/mol
for CaCO3(aq). The function derivatives at 298.15 K give approximately
2.692 and 3.545 kcal/mol respectively. Their source-specific discrepancy is
recorded; the new estimates consistently use the original fit derivatives.
Current native WATEQ4F/Tipping_Hurley files instead list approximately 2.69
and 3.545 kcal/mol. Native pressure, reference-component and model variants
remain separate from the admitted NBS-anchored formation estimates.

All prior observations and recommendations are preserved. Ca²⁺ H fills one
missing field; all default and checked carbonate diagrams remain unchanged.
Current totals: 794 species, 2,625 observations and 702/673/528 selected G/S/H.

The magnesium carbonate checkpoint adds four pure mineral records with all
12 G/H/S properties from USGS Bulletin 2131, p. 25, at 298.15 K/1 bar:
magnesite MgCO3, nesquehonite MgCO3(H2O)3, hydromagnesite
Mg5(CO3)4(OH)2(H2O)4 and artinite Mg2(CO3)(OH)2(H2O)3. Properties are
per complete formula unit. Their metal/carbonate counts are 1/1, 1/1, 5/4
and 2/1; core oxygen/hydrogen counts are 0/0, 3/6, 6/10 and 5/8.
These produce two electrons per metal and proton coefficients 0, 0, 0.4
and 1 per metal. Hydration water therefore cancels against the water reference
in the transformed potential. Formula units and water terms are checked using
independently balanced dissolution boundaries and closed-metal concentrations.

Three original entropy alternatives retain the published precision, experimental
lineage and unspecified source pressure (NULL): magnesite 65.09 ±0.13 J/(mol K),
nesquehonite (46.76 ±0.14) ×4.184 J/(mol K), and hydromagnesite
(120.38 ±0.37) ×4.184 J/(mol K). The original hydromagnesite authors assumed
zero residual entropy for an ordered compound; this absolute-entropy interpretation
has `source_verified_estimate` status. The later USGS critical entropies remain
preferred. Original and later representations share calorimetric lineage;
their covariance is unavailable.

Open NBS Mg²⁺ H of −466,850 J/mol fills a missing field. Open NBS MgHCO3+ G
of −1,047,200 J/mol becomes preferred under the unchanged policy's class B
family ordering; the earlier Miron G of −1,048,857 J/mol remains stored.
The selected complex G/H/S combine distinct evaluations and carry a source-basis
warning. No policy override or exclusion is introduced.

This checkpoint adds 17 observations and 13 missing selected properties while
preserving every earlier row. The 74 ligand-free diagrams are unchanged.
Carbonate-enabled magnesium mass balances include the four new solids and can
change precipitation substantially; the independently checked formula-unit,
hydration and proton balances remain conserved. Native four-Mg hydromagnesite,
mixed Ca/Mg phases, isotope models, association originals and exact native
pressure/reference transfers remain separate source/model follow-ups.
Current totals: 798 species, 2,642 observations and 706/677/533 selected G/S/H.

The subsequent magnesium mineral-variant checkpoint adds seven observations and
two crystalline compositions. Original artinite absolute entropy is
(55.67 ±0.16) ×4.184 = 232.92328 ±0.66944 J/(mol K), with unspecified pressure.
The authors add a 1.38 cal/(mol K) configurational residual term to the measured
54.29 cal/(mol K) increment and assume that disorder persists to zero temperature.
The absolute value has `source_verified_estimate` status; the calorimetric increment
stays external. The critical artinite entropy remains selected. The two existing
USGS artinite energy locators now correctly identify parent reference 169 as
Hemingway and Robie (1973), USGS Journal of Research 1, 535–541.

Open NBS supplies three magnesite properties and Gibbs energies for nesquehonite,
lansfordite and the crystalline composition Mg4(CO3)3(OH)2(H2O)3. The last two
are new species with G only. Lansfordite has five hydration waters, metal/carbonate
counts 1/1 and core O/H counts 5/10. The four-Mg composition has counts 4/3 and
core O/H 5/8; its crystal structure and mineral name remain unspecified. It is
stored separately from the five-Mg hydromagnesite record. Both use their complete
source formula units and two electrons per metal.

The unchanged class B ordering selects older NBS magnesite G/H/S and nesquehonite
G over the stored USGS values. Magnesite G changes from −1,029,500 to −1,012,100
J/mol, H from −1,113,300 to −1,095,800 J/mol and S from 65.1 to 65.7 J/(mol K).
Nesquehonite G changes from −1,723,800 to −1,726,100 J/mol. All earlier numerical
evidence remains stored. The Mg table was prepared in 1967; source-network
dependencies and missing uncertainties remain explicit. This retention does not
establish that the older values improve the later critical evaluations.

With the same selected ion and carbonate references, the magnesite dissolution
log10 K changes from −8.21477 to −5.16642. The 74 ligand-free diagrams are
unchanged, while carbonate-enabled magnesium precipitation changes substantially.
Independent dissolution-boundary and closed-metal checks verify full hydration,
basic-carbonate proton terms and conservation. Current totals: 800 species,
2,649 observations and 708/677/533 selected G/S/H.
