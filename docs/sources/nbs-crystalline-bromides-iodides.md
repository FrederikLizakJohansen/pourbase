# Original open NBS crystalline bromides and iodides

R16d2a reconciles all 64 Gibbs-bearing rows in the queued 154-row source
inventory. It adds 175 reported observations across 57 new crystalline records,
filling 169 properties. Fifteen existing original-evaluation cells are linked
without duplication: PbI2, CuI, AgI, KBr and KI G/H/S triplets.
Every earlier preferred value and reported observation remains. The unchanged
policy selects one value per property.

## Source and reuse

The source is Wagman et al. (1982), *The NBS Tables of Chemical Thermodynamic
Properties*, digitized with errata in the explicitly open non-SRD
[NIST Public Data Repository M32124](https://doi.org/10.18434/M32124).
The carried release review records the applicable [NIST open licence](https://www.nist.gov/open/license),
attribution and warranty statement. This batch uses original NBS cells.
Other sources' permission holds remain separate, including the bulk Thermoddem
redistribution hold. NIST is acknowledged; data are distributed without warranty.
Accessed 26 October 2026.

Each observation locates the logical CSV record, column, source formula,
crystalline phase, original value string, units and release hash. One-based
G/H/S columns are 9/8/11; G and H convert from kJ/mol to J/mol.
Source conditions are 298.15 K and 1 bar. Missing uncertainty remains NULL.
The compilation's individual measurement/estimate distinctions are unavailable
in these digitized rows; this qualification remains in each locator.

## Formula, hydrate and phase identity

Original molar masses were checked for all 154 preview rows. One digitization
error required the printed source: logical CSV record 11029 says NaI·H2O,
while its molar mass is 185.9250 g/mol. Original Table 99:Na, printed p.2-305
(PDF p.313), explicitly identifies NaI·2H2O with the same values:
G = −771.10 kJ/mol, H = −883.096 kJ/mol and S =196.2 J/(mol K).
The stored dihydrate follows that printed identity. Every observation preserves
the original CSV label and correction evidence; the display and phase label
use NaI·2H2O. Water counts are two O and four H per NaI unit.

The anhydrous NaI values, record 10987, are separately verified on printed
p.2-304 (PDF p.312). The publisher explicitly relaxes its G/H/S constraint.
Source-cycle residuals are approximately +1.484 kJ/mol for anhydrous NaI
and +1.177 kJ/mol for its dihydrate. Both triplets remain unchanged with
source-consistency warnings. Previously retained KI's +1.741 kJ/mol residual
and publisher qualification carry forward. These residuals are arithmetic
checks against source elemental references; they supply no uncertainty estimate.

Full hydrate formulas retain every water once. New crystalline identities remain
unresolved at the structure level; source modifications are preserved, including
monoclinic CBr4 and red HgI2. Existing resolved identities remain unchanged.

The buffered reaction uses one primary atom and the complete number of free
Br− or I− components. Hydrate water cancels explicitly, giving zero proton
coefficient and a net electron coefficient equal to the halogen count.
For Rb/Cs polyhalides, formal alkali oxidation state remains +1. Their net
electron coefficient also accounts for oxidation of the polyhalide anion
against free halide. All 31 existing free-component references remain unchanged.

## Scientific and release checks

Validation covers all 192 source-property slots, 531 balanced energies, complete
formula/charge checks, the existing ligand temperature exclusions and 63 source
G/H/S cycles. Eighty-four buffered-halide diagrams and 280 primary-element
mass balances are checked across 28 systems. Seventeen buffered diagrams
change on the 19 ×21 grid at free-halide log activities −6, −3 and 0.
New phases occupy 1,520 points across those scenarios. These are prescribed
external component activities; primary-element mass balance conserves the
primary inventory. Concentrated-brine, Pitzer and closed-halide models remain
separate development items.

All 75 default phase maps and uncertainty masks remain unchanged. Strict
periodic coverage remains 53 experimental systems or 56 with fallbacks;
available-data calculations cover 75 systems. The six original crystalline
Gibbs gaps and historical request coverage remain unchanged. BiI3 has G only;
its missing H/S stays explicit.

Metadata keys are `R16d2a_NBS_halide_source_review`,
`R16d2a_NBS_halide_observations` and `R16d2a_source_and_model_holds`.
The remaining 90 source rows are tracked separately for the next batch,
including two rows with no numerical G/H/S value. Completed source reviews,
NEA permission and downstream acknowledgment requirements carry forward.
See [distributed notices](../../THIRD_PARTY_NOTICES.md).

## Remaining enthalpy rows: R16d2b

The final 90 source rows contain 88 enthalpy cells and two rows with no
numerical G/H/S value. R16d2b retains all 88 enthalpies, adding 80 crystalline
records with H only. Eight observations are alternatives on existing NEA
records: SnBr2, SnI2, NiBr2, NiI2, FeBr3, FeI2, ZrBr4 and ZrI4.
All earlier preferred values and observations remain. BiBr3 and SnI4 supply
no numerical G/H/S in these original rows; their source-empty dispositions
are retained without adding empty records. Existing SnI4 evidence remains.

Every new observation uses the same explicitly open NBS release, exact source
record, original value, crystalline phase, units and conditions as the first
batch. Missing uncertainty remains NULL. Complete hydrate formulas retain
all water, including BaI2·2.5H2O with fractional stoichiometry. NaI3, KI3
and RbBr3 retain formal alkali oxidation state +1 separately from the net
three-electron reaction against free halide.

The H-only records have explicit missing G and S. They are excluded from
Gibbs calculations and reported as missing-G records when the corresponding
halide component is enabled. Default component scope and strict periodic
counts remain unchanged at 53 experimental systems or 56 with fallbacks.
Available-data calculations continue to cover 75 systems. No Gibbs energy
or entropy is inferred from enthalpy alone.

Validation covers all 270 remaining source-property slots, full formulas and
reaction charge, 150 buffered-halide diagrams and 500 primary-element balances
across 50 systems. Earlier preferred values, default maps and uncertainty masks
remain unchanged. Buffered phase maps also remain unchanged when incomplete
systems are calculated using their available Gibbs energies.

Metadata keys are `R16d2b_NBS_halide_source_review`,
`R16d2b_NBS_halide_observations` and `R16d2b_source_and_model_holds`.
Together the two batches reconcile all 154 rows and 462 G/H/S slots:
263 newly retained observations, 15 linked original cells and 184 source blanks.
They add 137 species and fill 249 properties. All source rows now have an
explicit disposition. Structure identity, missing thermochemistry, independent
source permissions and model extensions remain separately tracked.
