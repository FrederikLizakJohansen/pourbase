# Zirconium compounds with elemental buffers

The 15 October 2026 NEA02g2 checkpoint resolves six zirconium reference/model
holds. It adds **16 observations and six species**, filling 16 properties
without changing any earlier preferred value. Production contains **975
species and 3,109 observations across 74 systems**, with selected G/S/H
**860/781/660**. Eleven of the original 27 zirconium holds are now resolved;
16 remain with the disputed-source and mixed-metal reviews.

## Selected source observations

The values below come from Brown, Curti and Grambow, with Ekberg (2005),
*Chemical Thermodynamics of Zirconium*, OECD Nuclear Energy Agency volume 8,
Table III-1, printed p. 52/PDF p. 82. G/H are J/mol of the complete formula;
S is J/(mol K), at 298.15 K and 1 bar. Exact locators retain source units,
conversion, uncertainty and evaluation method.

| Species | G | H | S |
| --- | ---: | ---: | ---: |
| ZrTe1.843(cr) | −291,328 ± 7,000 | −295,000 ± 7,000 | 117.48 ± 0.12 |
| ZrTe2(cr) | −290,037 ± 7,000 | −294,000 ± 7,000 | 124.23 ± 0.10 |
| Zr5Te4(cr) | −810,430 ± 44,000 | −829,000 ± 44,000 | 330.0 ± 0.4 |
| ZrTe3O8(cr) | — | −2,119,200 ± 9,600 | — |
| ZrN(cr) | −341,852 ± 1,952 | −370,500 ± 1,389 | 38.8 ± 4.6 |
| ZrC(cr) | −203,476 ± 2,585 | −207,000 ± 2,500 | 33.0 ± 2.2 |

The NEA total intervals correspond in principle to 95% confidence. The
published widths are retained without conversion to one standard deviation
or an inferred covariance model.

The telluride selections use measured thermochemistry reviewed in section
V.5.3.1, pp. 194–195, Table V-29; NEA calculates G from selected H/S.
ZrTe1.843 keeps its exact composition, and Zr5Te4 keeps five Zr atoms per
formula. The engine divides its formula energy by five exactly once.
The tellurite enthalpy is the selected direct solution-calorimetric evaluation
in section V.5.3.2, p. 195. Its G/S remain absent.

ZrN is the stoichiometric reference endmember from section V.6.1.1.1,
pp. 195–197. Its real homogeneity range is recorded as a source qualification.
NEA combines a weighted combustion enthalpy evaluation with re-evaluated
thermal data and a low-temperature extrapolation.

ZrC retains the stronger qualification from section V.7.1.1.1, pp. 208–210:
H is a fitted endmember from combustion data on ZrCx. S and the resulting G
use NEA's approximation that the thermal properties of an impure ZrC0.96
sample also represent stoichiometric ZrC. All three observations are marked
`source_verified_estimate`, with the separate derivations explained in their
locators. The NEA source family retains class A under the existing policy.
These records define fixed reference compositions; a variable-composition
solid solution requires a separate model.

## Elemental reference components

The existing `ligands` table can represent a prescribed external component
chemical potential. Three new neutral references use the explicitly open
non-SRD NIST Public Data Repository release *NBS Tables with errata*,
[DOI 10.18434/M32124](https://doi.org/10.18434/M32124).

| Reference ID | NBS logical record | Reference state | Formation G |
| --- | ---: | --- | ---: |
| `elemental-te-cr` | 788 | Crystalline Te | 0 J/mol |
| `nitrogen-n2-gas` | 835 | N2 gas | 0 J/mol |
| `carbon-graphite` | 1639 | Graphite, Acheson spectroscopic | 0 J/mol |

Logical numbers include the two header records; column 9 supplies G.
These zeros define formation energies relative to the elements in their
reference states. They do not assert zero uncertainty in an absolute
chemical potential. Consistent elemental reference pressure preserves the
defined zero. No NBS or NEA auxiliary absolute entropy is imported here.

Pure crystalline Te and graphite use **unit activity**, supplied as
`log10_free_activity=0`. For N2, this field supplies **log10(f_N2/1 bar)**.
It represents the chemical potential of an external gas buffer. It is
separate from `GasFugacityModel`, which controls included gas species.
Use direct activities for these references: aqueous total-molarity and
acid/pKa assignments do not describe these phases. Other effective solid
activities would require a separately justified alloy or reservoir model.

## Balanced reactions and scope

| Compound | Formation reaction against the elemental buffer | Formal Zr state | Electrons per Zr |
| --- | --- | ---: | ---: |
| ZrTe1.843 | Zr + 1.843 Te → ZrTe1.843 | 3.686 | 0 |
| ZrTe2 | Zr + 2 Te → ZrTe2 | 4 | 0 |
| Zr5Te4 | 5 Zr + 4 Te → Zr5Te4 | 1.6 | 0 |
| ZrN | Zr + 0.5 N2 → ZrN | 3 | 0 |
| ZrC | Zr + C(graphite) → ZrC | 4 | 0 |
| ZrTe3O8 | Zr + 3 Te + 8 H2O → ZrTe3O8 + 16 H+ + 16 e− | 4 | 16 |

Formal telluride oxidation states use Te(−II) bookkeeping; the average
fractional values describe formula balance in metallic compounds. They do
not establish uniquely localized ionic charges. Tellurite uses Te(IV).
The neutral-element reactions have their own signed electron coefficients.
Replacing those coefficients with formal zirconium oxidation states would
introduce an incorrect potential dependence.

For the five G-bearing phases, the transformed energy per Zr is
`[G_formula − n_buffer RT ln(a_buffer)] / n_Zr`, independent of pH and
potential. Lowering N2 fugacity raises the nitride formation energy by
`−0.5 RT ln(f_N2/1 bar)`. Source H/S reconstructions reproduce the selected
G values within 0.51 J/mol using NEA's own auxiliary values solely for
arithmetic verification.

These calculations describe zirconium in contact with prescribed external
elemental buffers. Selecting a buffer can substantially change the predicted
phase map. Te/N/C inventories and their aqueous redox speciation are outside
this conditional model. Closed zirconium mass balance remains available
with an external N2 buffer; it conserves zirconium while that buffer is open.
A finite closed nitrogen inventory needs a headspace model. All ligand and
component species retain the existing exclusion away from 298.15 K.

For example:

```python
import pourbase as pb

database = pb.ThermodynamicDatabase.bundled()
conditions = pb.PourbaixConditions(
    ligand_activities=pb.LigandActivityModel((
        pb.LigandActivity("nitrogen-n2-gas", log10_free_activity=-6),
        pb.LigandActivity("carbon-graphite", log10_free_activity=0),
    )))
diagram = pb.PourbaixEngine(database).calculate("Zr", conditions)
```

## Validation, reuse and next work

All 74 default phase maps and uncertainty masks are preserved, as are the
55 tested plain/existing-buffer scenarios. Seventy total buffered scenarios
run and 140 explicitly gas-free zirconium inventories conserve metal under
ideal and Davies models. Full-formula balances and transformed energies
agree, and the aligned default pymatgen check passes. Calculations include these compounds when their named reference is explicitly
selected;
the evidence API exposes all observations independently of that scope.

OECD and NEA are acknowledged for the selected zirconium evaluations.
Completed volume-8 reuse checks are carried forward under the written
NEA-TDB clarification and [OECD data terms](https://www.oecd.org/en/about/terms-conditions.html),
subject to source-specific additional restrictions. Every sublicense of
work using these data must include the same OECD acknowledgment requirement
and require further sublicensees to pass it on. NIST is acknowledged for the
defined elemental references under its [open licence](https://www.nist.gov/open/license).
See [distributed notices](https://github.com/FrederikLizakJohansen/pourbase/blob/main/THIRD_PARTY_NOTICES.md). Private correspondence
and complete source publications stay outside the package.

The remaining 16 zirconium holds comprise four disputed source evaluations
and twelve mixed-metal records. The next task is the four disputed entries:
ZrO(g), ZrO2(g), the mixed-phase ZrH correlation and the ZrS1.5 discrepancy.
Two Cp-only rows remain with R18; earlier solid/model holds, broader source
reviews and other sources' permission states retain their own histories.
Historical request coverage remains **116/131 (NEA 28/28; NIST 88/103)**;
the six original crystalline Gibbs gaps remain open.

Source: [NEA volume 8](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/chemical_thermodynamics_of_zirconium_volume_8.pdf).
