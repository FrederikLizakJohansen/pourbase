# NEA halogen and sulfur auxiliary evaluations

R11j3i retains 21 observations on seven existing aqueous records: HF, HF2−,
ClO3−, BrO3−, IO3−, SO3²− and HSO3−. These are alternatives to existing
properties; this batch creates no species or property fills. The unchanged policy
selects one value per property and changes 17 earlier preferred IDs.

## Exact source versions

Seventeen original selections come from Grenthe et al. (1992), *Chemical
Thermodynamics of Uranium*, Chemical Thermodynamics 1, OECD Nuclear Energy
Agency, Table IV.1, pp.65–68 (PDF pp.83–86), and Chapter VI, pp.366–380
([official reprint](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/uranium.pdf)).
The review evaluates HF equilibria at infinite dilution and selects calorimetry,
adopts original oxyhalogen research with its own Gibbs calculations and uncertainty
assessment, and calculates sulfite Gibbs energies from selected redox and protonation
data. The underlying references remain scientific ancestry of these own NEA outputs.

Four distinct internal-calculation or uncertainty revisions come from Guillaumont
et al. (2003), *Update on the Chemical Thermodynamics of Uranium, Neptunium,
Plutonium, Americium and Technetium*, Chemical Thermodynamics 5, Table 8-1,
pp.136,138, with its conventions on p.135
([official volume](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/update_on_the_chemical_thermodynamics_of_uranium_neptunium_plutonium_americium_and_technetium_volume_5.pdf)).
HF entropy remains 88 J/(mol K), while its quoted width changes from 1.341 to
3.362. HF2− entropy changes from 92.685 ±7.260 to 92.683 ±8.469 J/(mol K).
The two sulfite Gibbs energies differ by 1 J/mol between these versions.
Both versions are retained, with no claim of independent new measurements.
All source URLs were accessed 25 October 2026.

The current 2020 inventory cells link to their exact matching source version.
Nineteen of the 20 cells are reconciled, including two HIO3/S²− Gibbs cells
already retained through R11l. Those existing observations and their completed
reviews carry forward. No extra reprint observations are added.

## Conventions and calculation effects

G/H use J/mol and S uses J/(mol K), per complete formula at 298.15 K and 1 bar.
Source confidence widths are retained; they correspond in principle to 95% and
are not converted to standard deviations. Conventional aqueous proton G/H/S are zero.
HF2− has two F atoms: its original molar value is stored in full, and the engine
normalizes by two for a per-F diagram. The closed-primary model retains its
explicit exclusion of polynuclear aqueous species.

Source-specific cycles for all five complete original triplets agree within 1 J/mol.
The original NEA HF and HF2− formation constants are log K ≈3.18 and 0.44.
With our selected fluoride ion they become approximately 3.659 and 0.919.
These mixed-source choices remain explicit; all 31 fixed free-component references
are preserved. The sulfite protonation pair gives log K ≈7.220.
G-only sulfite alternatives retain the current mixed-source H/G thermal route.

Validation covers 27 balanced energies, 14 thermal scenarios, 28 supported primary
mass balances, four ligand-enabled reference comparisons and all 75 default maps.
On an 81 ×91 grid, F/Br/I change at 182/7/52 points. The other 72 default maps
and uncertainty masks are unchanged. Independent free fluoride, chloride and sulfide
reservoir scenarios for Al/Zr/Ni/Zn remain unchanged.

## Scientific identity follow-up and reuse

The remaining cell is formal H2SO3(aq). The current neutral sulfur(IV) record is
SO2(aq). Goldberg and Parker (1985), pp.342–343, discuss aqueous SO2 and
stoichiometric sulfurous-acid notation
([original NBS article](https://nvlpubs.nist.gov/nistpubs/jres/090/jresv90n5p341_a1b.pdf)).
A source-specific water-reference transformation and matching activity convention
are needed before mapping the NEA acid value. R11j3i1 tracks that scientific
identity question. The unconverted acid value remains external; adding it as an
independently counted molecular population would require additional evidence.
No numerical values from the 1985 article enter this batch.

The supplied NEA clarification and OECD data terms cover these own evaluated
selections and internal recalculations. Credit OECD/NEA and the exact source.
Include the same acknowledgment requirement in sublicences and require further
sublicensees to do the same. Copied CODATA/Glushko cells and other sources’
permission holds remain separate. See [NEA reuse](nea-tdb-reuse.md) and
[distributed notices](../../THIRD_PARTY_NOTICES.md).

Metadata keys are `R11j3i_NEA_halogen_sulfur_review`,
`R11j3i_halogen_sulfur_observations` and `R11j3i_source_and_model_holds`.
All prior observations, species identities, phase metadata and production policy remain.
