# NEA iron selenium and tellurium selections

This batch retains 19 observations: 17 newly transcribed main-table cells and
two own enthalpy recalculations. It adds five species and 12 previously missing
species/property combinations. Two unchanged entropy cells link to existing
observations. Every earlier observation remains available.

The source is Lemire, Palmer, Taylor and Schlenz (2020), *Chemical Thermodynamics
of Iron, Part 2*, NEA No. 7499, Table III-1, printed pp. 46–47 (PDF pp. 81–82),
with the method and phase discussions in Sections IX.2–IX.3, pp. 191–217, and
Appendix A. The [official book](https://www.oecd-nea.org/upload/docs/application/pdf/2020-03/7499-vol13b-iron.pdf)
was accessed on 27 October 2026. Its recorded SHA-256 is
`933c3b599997364d7dc1753a79d6457bfa20115826f04180e16153149c5978d1`.

## Values and recommendations

G and H below are kJ/mol; S is J/(mol K), at 298.15 K and 1 bar.
Quoted intervals use the source convention. Database G/H use J/mol.

| Source formula/phase | G | H | S |
|---|---:|---:|---:|
| FeSe1.95, marcasite-type specimen | — | — | 81.4 ± 2.0 |
| Fe1.042Se, beta | −75.233 ± 4.009 | −74.700 ± 4.000 | 72.1 ± 0.8 |
| Fe7Se8, alpha | −547.084 ± 39.038 | −521.000 ± 39.000 | 613.8 ± 5.0, existing link |
| Fe3Se4, gamma | −257.000 ± 20.024 | −248.000 ± 20.000 | 279.8 ± 3.0, existing link |
| FeSe2, ferroselite | −111.722 ± 9.022 | −120.000 ± 9.000 | 83.5 ± 2.0 |
| FeSeO3+, aqueous | −446.544 ± 3.048 | — | — |
| Fe2(SeO3)3·3H2O, rhombohedral | −2083.916 ± 4.463 | — | — |
| Fe1.111Te, beta | −29.014 ± 1.811 | −26.060 ± 1.810 | 89.22 ± 0.15 |
| FeTe2, epsilon/frohbergite | — | — | 100.22 ± 0.20 |

NEA2020 revises the earlier NEA2005 enthalpies of alpha-Fe7Se8, gamma-Fe3Se4
and FeSe2. The earlier R10 observations remain. Phase-specific policy rules
prefer the new alpha-Fe7Se8 H with its expanded interval and the corrected
FeSe2 entropy. The other two revised H selections follow the ordinary policy.
The FeSe2 entropy correction accounts for impurity and nonstoichiometry in the
original calorimetric specimen. The older 86.8 ± 1.0 remains evidence.

The existing `r11c-fe-feseo3-aqueous` is the same charged Fe(III) complex.
Its earlier locally derived G, −442.263 kJ/mol, remains an alternative; the
new directly tabulated NEA evaluation becomes preferred. Exact charge matching
prevents a duplicate species. Five earlier preferred properties change in all.

Own Fe1.042Se H recalculations of −69.8 ± 4.0 and −77.4 with no assigned
interval are retained alongside the final −74.7 ± 4.0. NEA identifies possible
positive and negative biases in the alternatives. A policy rule selects the
final Piacente-based assessment. The −69.8 figure appears with an interval on
p. 194 and without one in the third-law comparison on p. 196; those locations
remain linked to one observation. These alternatives share experimental
ancestry. They do not count as independent replications.

## Formula, phase and calculation scope

Literal Fe1.042Se and Fe1.111Te formula units are retained, including their
noninteger Fe counts. FeSe1.95 remains a separate source specimen. None is
silently replaced by an integer stoichiometric compound. The book retains the
precise Fe1.042 composition to avoid rounding errors. The beta phases have a
tetragonal structure at room temperature. Exact specimen space groups remain
unassigned. Epsilon-FeTe2 retains the source Pnnm/Pnn2 structural ambiguity.

Neutral elemental Se and Te are the buffered reference components. Their
balanced net electron coefficients are zero. Formal ionic bookkeeping is
separate: monoselenide/monotelluride means use chalcogen(−II), while the
marcasite-type diselenides/ditelluride use chalcogen(−I). The nominal FeSe1.95
formal mean of 1.95 is explicitly conditional on that diselenide convention;
it makes no claim about defect-site or atom-resolved charge. Its S-only record
is omitted from Gibbs diagrams. FeTe2 also remains S-only.

The rhombohedral trihydrate is the source's XRD-based reassignment of an older
nominal hexahydrate solubility specimen. It is distinct from mandarinoite and
other hydrates. It uses two Fe, three selenites and three waters per unit.
FeSeO3+ has charge +1 and formal/net Fe(III). NEA warns that its fitted
complexation model is approximate and that the experimental studies disagree;
its equilibrium-constant intervals are estimated. These qualifications remain
attached to the evaluated experimental observations.

All 31 fixed component references remain. Main-table G/H/S cycles are checked
with the source's elemental entropy functions as external validation inputs.
Those checks do not add auxiliary compilation data to the database. Source
intervals are retained without unsupported uncertainty propagation.

## Reuse and remaining scope

These are NEA's own selected/evaluated outputs and recalculations. They use the
[recorded OECD permission and terms](nea-tdb-reuse.md), with appropriate OECD
citation. When sharing or licensing work made using these data, include the
same acknowledgment requirement in every sublicense and require further
sublicensees to do the same. The distributed notices carry that requirement.
The completed email and terms review is preserved. Other sources retain their
separate permission holds, including directly copied auxiliary compilations.

Fe2TeO6 has only a selected Cp, 180.7 ± 4.0 J/(mol K), in this main-table
inventory. Its thermal-function representation remains under R18. The body
quotes a Ball1992 FeTe2 enthalpy and explicitly calls it incompletely
TDB-consistent; that upstream value remains a separate source/consistency
review. Neither creates a missing G/H/S value in this batch.
