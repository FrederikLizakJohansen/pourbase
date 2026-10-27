# NEA phosphorus auxiliary observations

R11j3j reconciles all 14 phosphorus cells in the remaining NEA auxiliary inventory.
Five cells link to already retained evaluations: three phosphate properties in R14e2
and the P2O7⁴−/HP2O7³− Gibbs energies in R11k. Nine eligible missing NEA
observations and ten independent open NBS alternatives are added. Four new records
gain ten properties: aqueous H2P2O7²−, H3P2O7− and H4P2O7 gain G/H/S,
and amorphous red phosphorus gains H. Earlier preferred values are preserved.

## Sources and identity

The NEA source is Grenthe et al. (1992), *Chemical Thermodynamics of Uranium*,
Chemical Thermodynamics 1, OECD Nuclear Energy Agency, Table IV.1, pp.69–70
(PDF pp.87–88); Chapter VI.3.2, pp.386–389
([official reprint](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/uranium.pdf),
accessed 25 October 2026). The original phosphoric-acid evaluation is distinct from
the later 2024 evaluation, which remains preferred. The pyrophosphate evaluation
combines an NBS dimerization anchor with selected acid dissociation constants.
Shared ancestry and source confidence conventions remain explicit.

Independent alternatives come from Wagman et al. (1982), *The NBS Tables of
Chemical Thermodynamic Properties*, digitized with errata, the explicitly open
non-SRD [NIST release M32124](https://doi.org/10.18434/M32124).
Logical CSV records 1358, 1359 and 1363 supply the three aqueous G/H/S triplets
(columns 9/8/11, one-based); record 1262 supplies amorphous red P H (column 8).
Missing NBS uncertainties remain missing. The NEA red-P selection cites the same
NBS ancestry and supplies its own quoted width of 2 kJ/mol.

Amorphous red P remains distinct from crystalline white reference P and red
triclinic P. Its Gibbs energy and entropy are missing, so it is omitted from current
Gibbs calculations. An amorphous material receives no inferred crystal space group.
Other NBS elemental phases and crystalline/supercooled-liquid pyrophosphoric-acid
H-only rows remain separately recorded candidates for later expansion.

## Formula units and source cycles

The diphosphate records contain two P atoms and seven O atoms. Their H counts
are 2, 3 and 4, with charges −2, −1 and 0. Each balanced reaction has five electrons
per P. Molar G/H/S values are stored for the complete formula; the engine divides
by two for a per-P diagram. Existing closed-primary calculations explicitly exclude
polynuclear aqueous species. Fixed-activity and temperature views retain them.

All NEA values refer to 298.15 K, 1 bar, infinite dilution and the conventional
zero proton reference, using crystalline white P as the elemental reference.
G/H are converted from kJ/mol to J/mol; S uses J/(mol K). Quoted NEA widths
correspond in principle to 95% confidence and remain unconverted.
The two complete original NEA triplets agree with their reference cycles within
2 J/mol. The source dimerization constant is log K ≈−2.790, and its four
stepwise dissociation constants are −1, −2.25, −6.65 and −9.40. With our later
preferred phosphoric acid the dimerization constant is approximately −2.817.
The source evaluations and all earlier derived anchors retain their original values.

The NBS H2P2O7²− and H3P2O7− triplets have formation-cycle residuals of
approximately −503 and −310 J/mol, using their own elemental references and
conventional proton entropy. Their printed values are preserved with explicit
warnings. These residuals are separate from uncertainty. The preferred G values
come from NEA; the current thermal model uses its existing mixed-source H/G route
for these two species. NBS H4P2O7 has a residual of approximately −9 J/mol.

## Validation and reuse

Validation covers 21 balanced energy checks, eight thermal scenarios and 12
supported primary-element mass balances, including chloride/fluoride scenarios.
The closed-primary solver explicitly excludes all three new aqueous diphosphates.
All 75 default maps and uncertainty masks remain unchanged. Every previous SQL
row, preferred value, phase identity and all 31 fixed free references are preserved.
The production policy remains unchanged. The H-only red phosphorus record makes
the strict P inventory incomplete. The strict periodic count is now 54 experimental
systems, or 57 with computational fallbacks (previously 55/58). The available-data
screen continues to calculate all 75 systems.

The supplied NEA clarification and OECD data terms cover these selected/evaluated
outputs. Credit OECD/NEA and the exact evaluation; include the same acknowledgment
requirement in sublicences and require further sublicensees to do the same.
NIST credit, the open NBS release licence and its warranty notice also apply.
See [NEA reuse](nea-tdb-reuse.md) and [distributed notices](https://github.com/FrederikLizakJohansen/pourbase/blob/main/THIRD_PARTY_NOTICES.md).
Copied CODATA/Glushko, the H2SO3 identity question, policy follow-up R11j3f1
and other independent source/model holds remain separate.

Metadata keys are `R11j3j_NEA_phosphorus_review`,
`R11j3j_phosphorus_observations` and `R11j3j_source_and_model_holds`.
