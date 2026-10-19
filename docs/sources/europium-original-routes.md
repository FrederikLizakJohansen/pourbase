# R11h: six europium source routes

Reviewed 19 October 2026. Six new local G observations retain four original
source-route decisions and two precise holds. They add two species and two
preferred G properties, with four additional alternatives. Every previous
observation and preferred value remains; the selection policy is unchanged.

| Route | Result |
| --- | --- |
| Eu(OH)3(am) | Hold: the native 17.6 comes from Diakonov et al. (1998); its original numerical table has not been obtained. |
| EuF3(cr) | Add original Nagra 2002 and 2023 local G alternatives, alongside the existing Migdisov-based preferred value. |
| EuOHCO3(cr) | Add a nominal crystalline hydroxycarbonate G estimate from Nagra's original SIT evaluation. |
| Eu2(CO3)3 | Hold: the original phase is Eu2(CO3)3·nH2O with unspecified n; the native label suppresses hydration. |
| EuHSiO3(2+) | Hold the older strong-association representation externally; add two newer original Nagra evaluations on full EuH3SiO4(2+). |
| Eu(OH)3(cr) | Add the original Nagra SIT G alternative; retain the existing preferred Jordan 2024 G/H/S triplet. |

## Sources and reuse

[Hummel et al. (2002), Nagra NTB02-16](https://media.nagra.ch/uploads/2022/08/e_ntb02-016.pdf)
provides original recalculations on printed pp. 150, 155 and 160 (PDF 174,
179 and 184). The crystalline hydroxide acid-dissolution result is log K =
14.9 ± 0.3; hydroxycarbonate dissolution is −21.7 ± 0.1; fluoride dissolution
is −17.4 ± 0.5. These are Nagra's own evaluations, with upstream experimental
ancestry and phase limitations retained.

[Hummel and Thoenen (2023), Nagra NTB21-03](https://media.nagra.ch/uploads/2023/05/NTB-21-03.pdf)
provides its original fluoride mean evaluation −18.7 ± 0.4 on printed p. 900
(PDF 958), and two original silicate evaluations on p. 1003 (PDF 1061).
Table 25-11 gives the Eu-specific SIT result 7.31 ± 0.20, with its interval
labelled 95%. The source converts the original finite-medium Soli and Byrne
2017 result (6.18 at 0.7 M NaClO4) through a molal value of 6.165 and ionic
strength 0.725 mol/kg. Its separately selected pooled Eu/Am/Cm mean is
7.8 ± 0.5. Both are retained as distinct model variants. The pooled result
includes a cross-element analogy; it is not another independent Eu measurement.

These six isolated original numerical evaluations use the project's established
**individual-original-numerical-facts route**. The carried review of Nagra's
copyright, reproduction and storage terms remains applicable. Complete reports,
protected prose, figures, table layouts, bulk tables and source databases stay
external. This decision asserts limited factual reuse with attribution;
it does not assert a blanket open publication licence. The
[Creative Commons factual-data guidance](https://creativecommons.org/faq/) and
[US Copyright Office facts guidance](https://www.copyright.gov/help/faq/faq-protect.html)
are carried supporting evidence. Source hashes, scope and the original-source
holds are recorded in `source_reuse_R11h_original_europium` and the external
checkpoint.

The retained Eu3+, fluoride, carbonate, hydroxide and liquid-water inputs use
explicitly open non-SRD NIST PDR [M32124](https://doi.org/10.18434/M32124),
under the [NIST open licence](https://www.nist.gov/open/license), with NIST
attribution and warranty qualification. Eu3+ G = −574100 J/mol independently
matches logical CSV record 7774. The existing full-formula silicate reference
G = −1252304 J/mol carries its completed Miron 2017 original-result and open
water normalization review. Existing OECD credit and the acknowledgment
requirement for further sublicensees remain in the distributed notices for
NEA-derived material elsewhere. NEA permission does not license Nagra reports.

## Arithmetic, identity and model scope

All six additions are `source_verified_estimate`, at 298.15 K and nominal
standard pressure 1 bar, with NULL total uncertainties. Original reaction
intervals remain separate; unknown input intervals, shared ancestry and
covariance prevent a supported total G interval. No H/S/Cp or new temperature
model is inferred. Complete equations, inputs, source pages and individual
variants are retained in `R11h_europium_derivations`.

For dissolution, G(solid) = G(Eu3+) + sum of the dissolved-component G values
+ RT ln(10) log K. The crystalline hydroxide uses three waters. Fluoride uses
three F− ions. The source's nominal hydroxycarbonate uses one CO3(2−) and one
OH−, with G(OH−) = −157244 J/mol. Its physical formula is EuOHCO3, with seven
atoms, one Eu, one carbonate ligand, core O/H counts 1/1, three electrons and
one proton per Eu. The source distinguishes this characterized nominal phase
from the hydrated simple carbonate. Its polymorph and space group remain
unspecified.

Silicate formation uses G(complex) = G(Eu3+) + G(H3SiO4−) − RT ln(10) log beta.
The physical EuH3SiO4 formula has nine atoms. The H3SiO4 ligand carries its
three H and four O, leaving zero core O/H, with three electrons and zero protons
per Eu. Native EuHSiO3 and native HSiO3 each remove one water from their full
formulas; those transformations cancel in the association reaction. No duplicate
native oxyanion record or structural hydration is introduced.

The unchanged policy selects the Eu-specific silicate variant in its final
stable-observation-ID tie-break; the source's pooled selected value remains an
alternative. Both have the same estimate class, year and unspecified total G
interval. This outcome is recorded explicitly. The existing direct Jordan
hydroxide triplet and Migdisov fluoride G retain their preferred IDs. The older
and newer fluoride estimates preserve the authors' phase/crystallinity caveats:
the 2023 evaluation labels a nominal crystalline EuF3 result while noting
incomplete characterization of the underlying precipitates. The existing
anhydrous record retains its unspecified-polymorph scope; these are qualified
reaction-derived alternatives.

## Holds and completed review history

The amorphous 17.6 value is inherited from Diakonov et al. (1998), Table 5.
The earlier download attempts are empty files, and the original numerical table
remains unavailable. This is an original-source verification hold. It grants
no permission by elapsed time and is kept separate from other licence holds.

The simple carbonate source explicitly uses Eu2(CO3)3·nH2O. A missing hydration
number prevents assignment to an anhydrous physical formula. Resolve n and the
phase, or separately justify a water-component model, before importing its G.

The older silicate route derives from a strong-association interpretation.
The 2023 review, pp. 1002–1003, rejects the relevant earlier absolute constants
after examining polymerization and interpretation problems. Its independent
new Eu-specific and pooled evaluations supply the eligible replacements here.
Original old-source observations are not fabricated to reproduce a native scalar.

All prior source reviews, the three palladium and three tin follow-ups, nickel
and ammonia holds, 28 prior solid holds and zirconium scientific/thermal work
retain separate tracker entries. Original-request coverage remains
**116/131 (NEA 28/28, NIST 88/103)**. The six original crystalline G gaps remain.

## Verification and next work

- [x] Trace all six routes and document original-source, hydration and old-model decisions.
- [x] Stage six observations, preserving four alternatives and two new species.
- [x] Verify all previous SQL rows and preferred values, unchanged policy and idempotent import.
- [x] Reconstruct six reactions, native-water normalization and 18 full-formula energies.
- [x] Preserve all 74 default diagrams and uncertainty masks.
- [x] Check 12 buffered carbonate/silicate/fluoride scenarios and 24 ideal/Davies primary-Eu balances.
- [x] Preserve temperature scope and keep total ligand inventories external.

The database now contains **1,038 species and 3,281 observations**, with
**915/816/700 preferred G/S/H properties**, 1,743 source records, 1,407 warnings,
578 phase records and 28 ligand references. Policy `b2ad235bba62` retains
46 overrides and 10 exclusions; recommendation fingerprint is
`c002ce744f9753dc`. Balances use total Eu = 10−6 M and supported gas-free systems,
with externally buffered free ligand activities.

The finite R11h review is complete. The wider queue contains **27 other-original-
source routes**. **R11i: five iron hydrolysis/carbonate routes** is the next bounded review. Concurrent
calculation, GUI and test edits are preserved; the release commit includes only
this batch's data, documentation, statistics and test/count changes.
