# NEA iron cyanide and thiocyanate observations

This closing batch retains 27 observations across 11 new species. The policy
selects 26 new species/property combinations. One printed entropy remains
reported with a precise scientific exclusion. Every earlier observation and
preferred value remains unchanged.

The source is Lemire, R. J.; Palmer, D. A.; Taylor, P.; Schlenz, H. (2020),
*Chemical Thermodynamics of Iron, Part 2*, NEA No. 7499, Table III-1,
printed pp. 48–49/PDF pp. 83–84, and Sections X.1.1–X.1.2. The
[official book](https://www.oecd-nea.org/upload/docs/application/pdf/2020-03/7499-vol13b-iron.pdf)
was accessed on 27 October 2026. Its SHA-256 is
`933c3b599997364d7dc1753a79d6457bfa20115826f04180e16153149c5978d1`.
Each observation records its exact source cell, method, phase, standard state,
formula unit, interval and reuse route.

## Main selections

G and H below are kJ/mol; S is J/(mol K), at 298.15 K and 1 bar. Database
G/H use J/mol. A dash means the source did not assign that property or interval.

| Species/phase | Charge | G | H | S |
|---|---:|---:|---:|---:|
| Fe(CN)6, aqueous | −4 | 680.226 ± 21.260 | 434.945 ± 21.255 | 75.035 ± 6.369 |
| Fe(CN)6, aqueous | −3 | 714.921 | 547.185 | 269.783 |
| HFe(CN)6, aqueous | −3 | 655.796 | 437.045 | 164.017 |
| H2Fe(CN)6, aqueous | −2 | 642.097 | — | — |
| FeSCN, aqueous | +2 | 59.007 ± 4.062 | — | — |
| Fe(SCN)2, aqueous | +1 | 138.978 ± 6.376 | — | — |
| KFe(CN)6, aqueous Fe(II) | −3 | 384.302 | 186.405 | 234.300, reported/excluded |
| KFe(CN)6, aqueous Fe(III) | −2 | 424.077 | 297.145 | 405.979 |
| K4Fe(CN)6·3H2O, monoclinic | 0 | −1187.609 | −1486.279 | 593.095 ± 0.973 |
| K4Fe(CN)6, crystalline | 0 | −472.056 | −613.666 | 420.111 ± 1.621 |
| K3Fe(CN)6, crystalline | 0 | −143.194 | −263.616 | 426.494 ± 0.206 |

The cyanide parameters come from NEA's second-cycle weighted experimental
assessment, joining calorimetry, solubility, dehydration, redox and protonation
measurements. The thiocyanate selections use the source's critical speciation
and ionic-strength treatment. FeSCN notation follows the review; its discussion
identifies Fe–N binding. Higher thiocyanate complexes remain a separate source
question. Finite-medium reaction enthalpies do not supply formation enthalpies
for the two G-only thiocyanate records.

## Intervals, covariance and a source discrepancy

Table X-9, printed p. 291, reports small fit errors conditioned on an exact CN−
formation enthalpy. They are stored as qualified `conditional_fit_error` metadata
on the corresponding observations. The primary uncertainty field retains the
main-table total interval or its missing value. The shared CN− anchor causes
strong covariance between fitted species. These are related evaluations;
scalar uncertainty plots do not reconstruct the source's joint covariance.
The selected reaction intervals in Table III-2 remain available as a separate
reaction-property representation task.

For KFe(CN)6(3−), Table III-1 prints S = 234.300. The entropy cycle using the
review's own Table III-2 association reaction differs by 1 J/(mol K). G and H
separately reproduce the same source reaction. The literal S is preserved in
reported evidence and excluded from selection pending a source correction or
an identified evaluation variant. A locally corrected replacement is not added.
Two illustrative body entropy figures on p. 291 also remain in the external
source-variant follow-up.

## Components and calculation scope

The existing CN− and SCN− references remain unchanged. The new `potassium-k`
reference reuses the already reviewed K+(aq) observation, G = −283270 J/mol,
from the explicitly open non-SRD NIST NBS digitization
[M32124](https://doi.org/10.18434/M32124), Table 100:K, logical CSV record
12095, G column index 8. Its original reported value and missing interval
remain. The reference metadata preserves the observation ID, exact digitization
locator, bounded cross-check and completed reuse basis. All 32 earlier fixed
references remain, bringing the total to 33.

Potassium-associated species require both CN− and K+ activities. Their complete
K counts are additional components; each stored formula contains one Fe.
Protonated complexes retain one or two core hydrogens, giving proton coefficients
−1 or −2. The trihydrate retains three waters. Balanced electron coefficients
are 2 for the Fe(II) cyanides and 3 for the Fe(III) cyanides and thiocyanates.
Exact specimen space groups and the anhydrous salt polymorphs remain unassigned.

The open NBS K+ reference differs from the source's internal anchor. Published
formation properties remain literal; exact source reaction checks are separate
from calculations using the project's chosen reservoirs. Free CN−, SCN− and K+
activities are externally buffered. Closed calculations conserve primary Fe;
joint closed ligand/alkali inventories and buffered thermal extensions remain
separate model tasks. The 75 default diagrams remain unchanged.

## Reuse

These are NEA's own selected/evaluated outputs under the
[recorded OECD clarification and terms](nea-tdb-reuse.md), with appropriate
OECD citation. When sharing or licensing work made using these data, include
the same acknowledgment requirement in every sublicense and require further
sublicensees to do the same. Distributed notices carry that requirement.
The K+ reference uses the separate completed NBS/M32124 route: NIST is
acknowledged and the data are distributed without warranty. The book, private
correspondence and directly copied auxiliary compilation data remain external.
Other sources retain their separate permission holds.
