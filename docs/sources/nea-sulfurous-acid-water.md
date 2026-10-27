# Formal sulfurous acid and the SO2 water reference

R11j3i1 resolves the scientific water-representation hold on the remaining
H2SO3 auxiliary Gibbs cell. Two local derived alternatives enter the existing
neutral SO2(aq) record. The source versions and their confidence intervals
remain visible; the existing preferred value stays selected. Species counts
and preferred-property counts are unchanged.

## Original evaluation and versions

Grenthe et al. (1992), *Chemical Thermodynamics of Uranium*, vol.1,
Table IV.1 p.68 (PDF p.86), gives formal H2SO3 G = −539.188 ±4.072 kJ/mol
([official volume](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/uranium.pdf)).
Chapter VI.2.1.5 pp.376–378 evaluates the protonation of HSO3−, selecting
log10 K =1.84 ±0.08 and calculating this formation property.
Guillaumont et al. (2003), *Update*, vol.5, Table 8-1 p.138
(PDF p.178), prints −539.187 ±4.072 kJ/mol
([official volume](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/update_on_the_chemical_thermodynamics_of_uranium_neptunium_plutonium_americium_and_technetium_volume_5.pdf)).
Both 1 J/mol internal-calculation versions are preserved. The 2020 inventory
cites the 1992 review while printing the later −539.187 variant; its exact
numerical link therefore uses the 2003 version.

## Explicit local standard-state conversion

Goldberg and Parker (1985), *Thermodynamics of Solution of SO2(g) in Water
and of Aqueous Sulfur Dioxide Solutions*, J. Res. NBS 90, pp.342–343,
identifies neutral aqueous SO2 separately from analytical sulfur concentration.
Its acid-ionization equation includes one liquid-water term, and its use of
stoichiometric sulfurous-acid notation supplies no separate molecular population
([original paper](https://nvlpubs.nist.gov/nistpubs/jres/090/jresv90n5p341_A1b.pdf)).

The local component convention defines the formal acid chemical potential as
the neutral SO2 chemical potential plus liquid water. At unit water activity,
the canonical property is G(SO2) = G(formal H2SO3) − G(H2O(l)).
This preserves the NEA protonation reaction on one neutral aqueous population.
It assigns no separate hydration equilibrium or molecular H2SO3 concentration.
Neutral species activity and total analytical sulfur concentration remain distinct.

The unchanged water anchor is −237129 J/mol from original open
[NIST M32124](https://doi.org/10.18434/M32124), logical CSV record 41,
column 9. The resulting alternatives are −302059 J/mol from 1992 and
−302058 J/mol from 2003. Both are local `source_verified_estimate` observations
in class E. The raw 4072 J/mol source intervals remain in their locators.
The water input supplies no uncertainty or covariance, so combined intervals
stay NULL. No uncertainty is inferred from printed precision.

## Validation and reuse

Fifty energy checks verify equivalence of formal and canonical representations
over pH and potential. Both versions reproduce the source protonation constant
within numerical rounding using their matching HSO3− evaluation. Twelve
supported sulfur balances, two unchanged thermal cases and all 75 default maps
and uncertainty masks pass. Every earlier preferred value, all alternatives,
phase identities and 31 fixed references remain. Strict periodic coverage
stays 53 experimental systems or 56 with fallbacks; available-data calculations
cover 75. Historical request coverage and the six original crystalline Gibbs
gaps are unchanged.

The conversion is verified at 298.15 K, 1 bar and unit water activity.
Nonunit-water and new thermal component models remain separate work.
The original-paper reference is used for scientific definitions; its numerical
property tables are outside this import.

The source NEA selected/evaluated properties and adaptation use the supplied
clarification and OECD data terms. Credit OECD/NEA and the original sources;
pass the same acknowledgment requirement into sublicences and require further
sublicensees to do the same. The water input carries NIST credit, its open
licence and warranty statement. Source URLs were accessed on 26 October 2026.
See [reuse instructions](nea-tdb-reuse.md) and
[distributed notices](https://github.com/FrederikLizakJohansen/pourbase/blob/main/THIRD_PARTY_NOTICES.md).

Metadata keys are `R11j3i1_sulfurous_acid_review`,
`R11j3i1_water_converted_observations` and `R11j3i1_SO2_water_convention`.
The complete 729-cell auxiliary inventory now has 203 direct observation links,
four water-representation links, one reference-context cell, 358 copied CODATA
holds, 12 direct Glushko holds, 87 defined references and 64 source blanks.
All cells have an explicit disposition. Independent permission, structure and
model holds remain separately tracked.
