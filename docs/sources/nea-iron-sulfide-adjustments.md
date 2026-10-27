# NEA review-adjusted iron sulfide alternatives

R16d6b adds 15 formation-enthalpy observations from NEA's own reassessment of
experimental thermochemistry. It adds two H-only records and preserves every
earlier observation and preferred choice. The source is Lemire, Palmer, Taylor
and Schlenz (2020), [Chemical Thermodynamics of Iron, Part 2, NEA No. 7499](https://www.oecd-nea.org/upload/docs/application/pdf/2020-03/7499-vol13b-iron.pdf).
Exact pages, methods, formula conversions and uncertainties remain in each
observation locator.

| Source phase or specimen | Original experimental route | Printed page | Source formula unit | H, kJ/mol source unit |
| --- | --- | ---: | --- | ---: |
| Troilite | 1951 gas/solid equilibrium, NEA third-law analysis | 343 | FeS | −100.05 ±2.11 |
| Quenched FeS, ordering unresolved | 1964 acid dissolution, NEA partition correction | 391 | FeS | −98.91 ±2.28 |
| Troilite | 1988 direct reaction, NEA uncertainty reassessment | 523 | FeS | −102.59 ±2.94 |
| Troilite | 2010 oxide melt, NEA cycle recalculation | 617 | FeS | −100.89 ±4.20 |
| 5C pyrrhotite | Equilibrium/third-law evaluation | 166 | Fe0.9S | −95.82 ±2.63 |
| 5C pyrrhotite | 2010 oxide melt, NEA cycle recalculation | 616 | Fe0.9S | −96.05 ±4.20 |
| 3C pyrrhotite | 2010 oxide melt, NEA cycle recalculation | 616 | Fe0.875S | −94.61 ±3.19 |
| 4C pyrrhotite | Updated 1992 third-law evaluation | 171 | Fe0.875S | −95.98 ±3.00 |
| 4C pyrrhotite | NEA third-law treatment of 2005 electrochemistry | 586–587 | Fe0.875S | −95.90 ±3.00 |
| 4C pyrrhotite, comparison only | NEA standardization of 2014 electrochemistry | 172 | Fe0.875S | −93.16 ±3.01 |
| Pyrite | 1988 direct reaction, NEA uncertainty reassessment | 523 | FeS2 | −171.64 ±5.88 |
| Pyrite | 2010 oxide melt, NEA cycle recalculation | 617 | FeS2 | −175.85 ±6.18 |
| Pyrite | Updated equilibrium/third-law evaluation | 174 | FeS2 | −173.63 ±2.83 |
| Wurtzite | 1964 acid dissolution, NEA partition correction | 391 | ZnS | −191.17 ±2.01 |
| 4C pyrrhotite | NEA solid-sulfur reference conversion of 2005 result | 586 | Fe0.875S | −102.20 ±3.00 |

## Units, methods and shared ancestry

The stored integer units are Fe9S10 for 5C and Fe7S8 for 3C/4C. All source
values and intervals scale by 10 or 8 respectively, then by 1,000 to J/mol.
Other rows use factor one before SI conversion. Quoted intervals retain their
source meaning, including NEA's own uncertainty reassessments. No universal
one-sigma conversion or new local propagation is applied.

The 1988 reassessment widens the original study's reported scatter to account
for possible incomplete reaction and rounding. The 2010 recalculations change
auxiliary anchors and use nominal batch compositions. Those are own NEA
reviewed results with their numerical ancestry recorded. The individual-study
adjustments and final combined recommendations share experimental inputs;
they represent related alternatives.

The 2005 sulfur-reference conversion is explicitly published by the reviewer:
`−166.5 + 0.5 ×128.6 = −102.2 kJ/mol` per Fe0.875S. The original method's
details are incomplete and the reviewer considers a second-law treatment
likely. This experimental thermochemical route is recorded alongside NEA's
separate third-law result and final combination. The printed uncertainty stays
literal. The original nonstandard gas-reference figure stays outside this
standard formation-enthalpy import.

## Physical specimens and selection

XRD identifies the 2010 Fe0.875S calorimetric specimen as metastable 3C
pyrrhotite. Its adjusted H is stored on a separate 3C record. The source's
4C evaluation uses that input under an explicit small-transformation-enthalpy
approximation, documented in [the main-selection review](nea-iron-sulfides-2020.md).
Exact specimen space groups remain unassigned. The legacy NBS Fe7S8 record
keeps its ordering qualification and all observations.

The 1964 FeS specimen was quenched. Its nearly stoichiometric composition
supports nominal FeS, while attainment of fully ordered troilite remains
uncertain. NEA leaves it outside the final troilite combination. It is retained
as a separate specimen-qualified record with unresolved ordering and H only.
Both new records retain missing G and S and remain outside room-temperature
Gibbs-energy diagrams.

NEA presents the standardized 2014 result for comparison only and explicitly
omits it from the assessment because its Ag2S thermochemical anchor had not
been evaluated by TDB. The numerical observation is preserved with an exact
selection exclusion. This is a scientific qualification with its own follow-up;
its reuse permission is recorded separately.

Two new property rules prefer the final combined 5C and pyrite H evaluations
over their retained individual-study adjustments. The existing final troilite
and 4C rules continue to apply. The coherent USGS wurtzite triplet remains
preferred: the new NEA adjustment differs from its H by 12.63 kJ/mol, so its
source history and G/H/S consistency need a bounded follow-up. The existing
rule now states that qualification. Every alternative remains available.
Policy `4ffe2d63a073` has 58 overrides and 14 exclusions; recommendation
fingerprint `3344748823f9fcb1`.

## Finite inventory and remaining work

All 19 scoped cells have a disposition: 15 new observations, one link to the
already retained adjusted 6C H, and three phase/mixture holds. The latter are
Fe0.94S, Fe0.96S and Fe0.98S, whose anomalous 2C structures and expected
low-temperature partitioning prevent a confirmed pure-phase assignment.
Their own adjusted H values and locations stay in the external source ledger.
The existing 6C datum is linked without duplication. Other main iron rows,
USGS phase crosswalks and further numerical variants remain separate work.

## Reuse and attribution

These own NEA selected/evaluated data use the supplied written OECD
clarification and the recorded [NEA reuse conditions](nea-tdb-reuse.md).
Credit OECD (2020), Chemical Thermodynamics of Iron, Part 2, NEA No. 7499;
Lemire, Palmer, Taylor and Schlenz; and the official source URL (accessed
27 October 2026). When sharing or licensing work created using these data,
include the same acknowledgment requirement in every sublicense and require
further sublicensees to do the same. Source-specific additional restrictions
remain applicable. The preserved email and terms evidence carry forward.

Raw quoted third-party figures have their own source routes. Auxiliary copied
CODATA cells and other sources' permission holds remain separate. Full books
and private correspondence stay outside distributions. Metadata keys:
`R16d6b_NEA_adjusted_sulfides`, `R16d6b_NEA_adjusted_observations`,
`source_permission_NEA_TDB_Fe2020_adjusted` and
`R16d6b_NEA_scientific_followups`.
