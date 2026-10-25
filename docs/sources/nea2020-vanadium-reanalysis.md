# Own NEA 2020 aqueous vanadium reanalysis

R11j3a adds four own selected observations: G/H/S for VO2+ and G for VO4(3−).
They fill the missing VO2+ formation enthalpy and replace three preferred values
under the existing selection policy. Every earlier observation remains.

## Original selected observations

Grenthe, Gaona, Plyasunov, Rao, Runde, Grambow, Konings, Smith and Moore (2020),
*Second Update on the Chemical Thermodynamics of U, Np, Pu, Am and Tc*,
Chemical Thermodynamics 14, OECD Nuclear Energy Agency, NEA No. 7500,
[Chapter 14.1.2 and Table 14-1, pp. 603–605](https://www.oecd-nea.org/upload/docs/application/pdf/2020-10/7500_second_update_of_u_np_pu_am_and_tc_web.pdf)
(PDF pp. 667–669), explicitly assigns these outputs to “This review”.

| Species | Property | New own selected value | Quoted total uncertainty | Earlier preferred value |
| --- | --- | ---: | ---: | ---: |
| VO2+ | G, kJ/mol | −590.280 | 1.530 | −587.000 |
| VO2+ | H, kJ/mol | −651.840 | 1.580 | Missing |
| VO2+ | S, J/(mol K) | −38.000 | 7.400 | −42.300 |
| VO4(3−) | G, kJ/mol | −892.750 | 1.910 | −899.000 |

All quantities refer to 298.15 K and 1 bar, per complete one-V formula unit.
The aqueous standard state is infinite dilution. The stored entropy is the
absolute conventional ionic entropy, with S(H+)=0. The separate printed VO2+
formation entropy of −206.5 J/(mol K) is a different quantity. G/H are stored
in J/mol. Quoted source uncertainty widths retain the NEA total-uncertainty
convention, corresponding in principle to 95% confidence.

The review reanalyses LaSalle and Cobble's 1955 solubilities, selects reaction
calorimetry from the 1966 study and combines these with its selected reference
properties. VO4(3−) uses its own selected VO2+ value and zero-ionic-strength
hydrolysis from the reviewed literature. IVTAN/Glushko reference inputs and
Baes/Mesmer hydrolysis are explicit numerical ancestry for these own outputs.
The four observations preserve the published NEA evaluation and its citation.

Using the source water G of −237.14 kJ/mol, the selected formation values imply
171.81 kJ/mol for reaction 14.6. The separately printed reaction value is
171.3 ±1.1 kJ/mol. The 0.51 kJ/mol difference is retained as a source qualification;
the formation values and quoted widths stay as printed. No correlated reaction
uncertainty or missing VO4 H/S is inferred. Its earlier estimated H/S remain
available under the existing thermal model and source qualifications.

## Source-specific reuse and holds

OECD and NEA are acknowledged. The supplied written NEA clarification and
[OECD data terms](https://www.oecd.org/en/about/terms-conditions.html) cover these
own selected/evaluated outputs, including commercial adaptation and redistribution,
with citation and applicable additional restrictions checked. When sharing or
licensing work using these data, include the same OECD acknowledgment requirement
in sublicences and require further sublicensees to do the same. The source was
accessed on 25 October 2026.

Six proposed CsCl/CsBr G/H/S cells from 2020 Table 8-1 remain held separately.
The original [2001 review](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/vol4-neptunium-plutonium.pdf),
Table 5.1, pp. 76–77 and Chapter 18.1.3.8–9, traces adopted values to
[82GLU/GUR]. Nonbold typography in a later reprint supplies insufficient evidence
for reuse of those copied compilation cells under this task. Existing independent
open NBS CsCl observations remain. Informational and directly copied Glushko
entries, bold CODATA cells and every earlier independent source hold retain
separate decisions. Additional V2O5 and vanadate-solid cells continue in R11j3b
with per-cell source, phase and component checks.

## Numerical validation

All earlier SQL rows remain, repeated application is idempotent and the policy
fingerprint stays 53505340b507. Six energies, two thermal calculations and four
supported vanadium mass balances pass. Across all 75 default system diagrams,
only V changes: 429 of 7,371 grid labels change at 81×91 resolution, with 513
and 494 uncertainty-mask changes at 1σ and 3σ. These are source-selection effects
of the new G values and quoted uncertainties. Model implementations, references,
GUI work and the six original crystalline Gibbs gaps retain their earlier status.
