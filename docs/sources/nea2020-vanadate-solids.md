# Selected NEA vanadates and independent open NBS alternatives

R11j3c adds crystalline NaVO3 and Ca(VO3)2 with ten observations and six
available G/H/S properties. Four own selected/recalculated NEA G/H outputs
coexist with six independent original open NBS G/H/S observations. The existing
policy selects NEA G/H and NBS S, preserving every earlier observation and
preferred candidate.

## Original evaluations and complete formula units

Grenthe et al. (2020), *Second Update on the Chemical Thermodynamics of U, Np,
Pu, Am and Tc*, Chemical Thermodynamics 14, OECD Nuclear Energy Agency,
NEA No. 7500,
[Table 14-1, p. 605](https://www.oecd-nea.org/upload/docs/application/pdf/2020-10/7500_second_update_of_u_np_pu_am_and_tc_web.pdf)
(PDF p. 669), gives the own selected G/H outputs. Chapter 14.1, p. 606 and
Appendix A, pp. 1203–1205 document the calorimetric reanalysis.

| Species | Own NEA G, kJ/mol | Own NEA H, kJ/mol | NBS G, kJ/mol | NBS H, kJ/mol | NBS S, J/(mol K) |
| --- | ---: | ---: | ---: | ---: | ---: |
| NaVO3(cr) | −1067.480 ±1.520 | −1149.140 ±1.500 | −1064.07 | −1145.79 | 113.68 |
| Ca(VO3)2(cr) | −2174.750 ±3.280 | −2334.350 ±3.230 | −2169.60 | −2329.27 | 179.1 |

Values refer to 298.15 K and 1 bar, per full original source formula unit.
Ca(VO3)2 contains two V atoms; the reported molar values retain that complete
unit. The engine divides by two when calculating energy per mole of V. The
open NBS notation CaO·V2O5 has the same CaV2O6 composition. G/H are stored
in J/mol. NEA quoted total uncertainty widths retain their approximately 95%
source meaning; missing NBS uncertainty remains NULL.

NEA recalculates the two NaVO3 calorimetric evaluations and selects their
weighted result, enlarging its uncertainty to 1.5 kJ/mol. For the calcium salt,
Appendix A, p. 1204 explicitly recalculates H from the measured reaction heat
and selected reference inputs:
−634.92 −1556.00 −143.43 = −2334.35 kJ/mol. The NEA outputs retain their
original reference conventions and numerical ancestry. No copied anchor is
introduced as a new independent observation.

Original NBS rows are logical CSV records 11964 (NaVO3) and 9604 (CaO·V2O5),
columns 9/8/11 for G/H/S in the corrected
[non-SRD Public Data Repository release M32124](https://doi.org/10.18434/M32124).
Both source crystal identities remain unresolved at the specimen/structure level;
no named polymorph or space group is inferred.

## Bibliographic qualifications and reuse

Table 14-1 and the sodium discussion give different informational-entropy
citations; the bibliography identifies the cited 1961 entry as a clay-mineral
paper and the 1962 entry as calcium vanadates. The table's calcium entropy
citation identifies a magnesium paper, while Appendix A, p. 1204 supplies the
calcium reference. These discrepancies remain explicit. This batch retains the
four own selected G/H outputs and the independently located original open NBS
entropy observations. Informational NEA S/Cp cells retain separate source work.

OECD and NEA are acknowledged. The supplied written NEA clarification and
[OECD data terms](https://www.oecd.org/en/about/terms-conditions.html) cover these
own selected/recalculated outputs, including commercial adaptation and
redistribution, with citation and applicable additional restrictions checked.
When sharing or licensing work using these data, include the same OECD
acknowledgment requirement in sublicences and require further sublicensees
to do the same. NIST is acknowledged for the six independent original NBS cells
under its [open licence](https://www.nist.gov/open/license); data are distributed
without warranty. Sources were accessed on 25 October 2026. Earlier copied
Glushko/CODATA and other independent source holds remain separate.

## Supported calculations and validation

The salts use the existing free sodium and calcium references, with one buffered
cation per complete formula unit. Both reduce by five electrons per V atom.
Their buffers have independently prescribed free activities. Closed sodium or
calcium inventories and ligand thermal functions remain separate model work.
The current thermal model excludes both ligand-bearing salts.

Staging preserves every earlier SQL row and preferred candidate, verifies units,
source widths and repeat-import behaviour, and checks 36 original-alternative
energies, four thermal exclusions, six buffered diagrams and 24 primary-V
balances. All 75 default diagrams and 1σ/3σ masks remain unchanged at 81×91
resolution. The six buffered test diagrams also retain their earlier stable-phase
labels. Magnesium vanadate and remaining own ancillary/borate observations
continue separately; R06/R07, the original six crystalline Gibbs gaps and earlier
source/model holds retain their status.
