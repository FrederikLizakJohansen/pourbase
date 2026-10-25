# NEA 2020 auxiliary oxide selections and open NBS alternatives

R11j3b adds crystalline SrO and BaO with ten reported observations and six
available G/H/S properties. Four own NEA revised G/S selections coexist with
six independent original open NBS G/H/S observations. Every earlier observation
and preferred value remains. The existing policy chooses NEA G/S and NBS H for
the two new records.

## Own selected NEA evaluation

Grenthe, Gaona, Plyasunov, Rao, Runde, Grambow, Konings, Smith and Moore (2020),
*Second Update on the Chemical Thermodynamics of U, Np, Pu, Am and Tc*,
Chemical Thermodynamics 14, OECD Nuclear Energy Agency, NEA No. 7500,
[Chapter 14.3.2, pp. 607–608](https://www.oecd-nea.org/upload/docs/application/pdf/2020-10/7500_second_update_of_u_np_pu_am_and_tc_web.pdf)
(PDF pp. 671–672), compares low-temperature calorimetric evaluations, selects
Cordfunke et al. (1994) entropy values and recalculates formation Gibbs energies.

| Species | NEA G, kJ/mol | NEA S, J/(mol K) | Original NBS G, kJ/mol | NBS H, kJ/mol | NBS S, J/(mol K) |
| --- | ---: | ---: | ---: | ---: | ---: |
| SrO(cr) | −559.400 ±0.903 | 53.630 ±0.100 | −561.9 | −592.0 | 54.4 |
| BaO(cr) | −519.780 ±2.513 | 70.010 ±0.100 | −525.1 | −553.5 | 70.42 |

All values refer to 298.15 K and 1 bar, per full MO formula unit. G/H are stored
in J/mol and S in J/(mol K). NEA quoted total uncertainty widths retain the
source convention, corresponding in principle to 95% confidence. The NBS release
supplies no uncertainty for these cells; their uncertainty stays NULL. Source
evaluations retain their own reference conventions. Their values are stored
as separate observations without forcing a common G/H/S cycle.

The original NBS rows are logical CSV records 9636 (SrO) and 9933 (BaO),
columns 9/8/11 for G/H/S in the corrected
[non-SRD Public Data Repository release M32124](https://doi.org/10.18434/M32124).
The reviewed CSV SHA-256 is
`cb8a8b8b94a287e6e8c82eed8bad2cf9b611d574d1cfd95c8528d318dfef4b44`.
Both sources identify the crystalline oxide. Exact specimen, structure and
space-group assignments remain unresolved, with the source state preserved.

## Reuse conditions

OECD and NEA are acknowledged. The supplied written NEA clarification and
[OECD data terms](https://www.oecd.org/en/about/terms-conditions.html) cover the
four own selected/recalculated outputs, including commercial adaptation and
redistribution, with appropriate citation and applicable additional restrictions
checked. When sharing or licensing work using these data, include the same OECD
acknowledgment requirement in sublicences and require further sublicensees to
do the same.

NIST is acknowledged for the independent original NBS observations under its
[open licence](https://www.nist.gov/open/license); the data are distributed
without warranty. These are the explicitly open non-SRD release's cells.
Sources were accessed on 25 October 2026. Earlier source holds, including
copied CsCl/CsBr compilation cells, remain separate.

## Validation and remaining scope

Staging verifies SQLite integrity, foreign keys, duplicate prevention, unchanged
prior SQL rows and preferred candidates, and exact units/uncertainty conversions.
Six energy calculations, four thermal derivatives and eight supported Sr/Ba
mass balances pass. All 75 default diagrams and their 1σ/3σ uncertainty masks
remain unchanged at 81×91 resolution. Thermal derivatives use S from the same
source as G before H from a different evaluation, as specified by the existing
model. No Cp or additional thermal function is activated.

These two generic crystalline identities retain unresolved structure follow-ups.
Other selected vanadate/borate solids and auxiliary data continue separately.
The original six crystalline Gibbs gaps, R06/R07 and all prior independent
permission/model holds retain their status. Concurrent GUI implementation and
the selection policy remain untouched.
