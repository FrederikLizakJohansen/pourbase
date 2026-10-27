# NEA2020 iron sulfide selections

The source is Lemire, Palmer, Taylor and Schlenz (2020),
[Chemical Thermodynamics of Iron, Part2, NEA No7499](https://www.oecd-nea.org/upload/docs/application/pdf/2020-03/7499-vol13b-iron.pdf),
main TableIII-1, printed p.45/PDF p.80, and the phase-specific discussions
on pp.162–183. R16d6 adds21 observations across seven records, including
four new phases and ten newly available properties. Every earlier observation
remains. Seven earlier choices move to the new class-A NEA evaluation.

| Phase | Stored unit | Source-unit factor | G, kJ/mol stored | H, kJ/mol stored | S, J/(mol K) stored |
| --- | --- | ---: | ---: | ---: | ---: |
| Troilite | FeS | 1 | −101.259 ±2.002 | −100.910 ±2.000 | 60.310 ±0.220 |
| 6C pyrrhotite | Fe11S12 | 12 | absent | −1169.760 ±47.160 | absent |
| 5C pyrrhotite | Fe9S10 | 10 | −978.930 ±22.320 | −958.900 ±22.300 | 631.500 ±2.500 |
| 4C pyrrhotite | Fe7S8 | 8 | −776.040 ±16.024 | −764.240 ±16.000 | 485.600 ±2.720 |
| Pyrite | FeS2 | 1 | −162.219 ±2.361 | −173.630 ±2.360 | 52.920 ±0.140 |
| Marcasite | FeS2 | 1 | −158.317 ±2.442 | −169.430 ±2.380 | 53.920 ±0.410 |
| Greigite | Fe3S4 | 1 | −309.000 ±10.000 | absent | absent |

G/H and their intervals convert to J/mol in the database. The original source
units Fe11/12S, Fe9/10S and Fe0.875S scale by12,10 and8 respectively.
The quoted intervals are NEA total uncertainties, approximately95percent;
covariance and a universal one-sigma conversion are unassigned. These are
critically evaluated experimental calorimetric/equilibrium/electrochemical
results. Published G values calculated from selected H/S remain source
evaluations, with their input ancestry recorded.

## Phase identity and full formula units

Ordered4C,5C and6C pyrrhotites have separate stable IDs. The legacy NBS Fe7S8
record has unspecified ordering and retains its existing observations and choice.
Composition alone does not establish correspondence with4C, metastable3C or
other near-Fe7S8 structures. Six USGS pyrrhotite cells retain a separate
scientific crosswalk. Named NEA phases are resolved; exact thermochemical
specimen space groups remain unassigned. Structural exemplars from different
specimens do not supply those missing assignments. NEA includes calorimetry of
a metastable3C specimen in its4C enthalpy evaluation, assuming a very small
3C-to-4C transformation enthalpy (p171). This evaluated approximation is
explicit in the observation provenance; it is not a direct4C measurement.

Complete metal/sulfur counts and buffered S2− electron coefficients are11/12
and24/11 for6C,9/10 and20/9 for5C,7/8 and16/7 for4C, and3/4 and8/3
for greigite. Formal valences of the mixed-valence phases are conventional
formula averages. Pyrite and marcasite retain formal Fe(II), separately from
net four reaction electrons per Fe. H-only6C remains outside room-temperature
G diagrams. Closed sulfur, solid solutions and new thermal models remain
separate.

## Alternatives and source discrepancies

Three own intermediate combinations remain alongside the final recommendation:
troilite H−100.91±1.59kJ perFeS (p164),4C H−95.53±1.77kJ perFe0.875S
(p172), and greigite G−308.7±7.9kJ perFe3S4 (p181). The final NEA
recommendations deliberately broaden these uncertainties. Exact policy rules
prefer those final recommendations, while shared evaluation identities document
that the alternatives share experimental ancestry.

Marcasite's table gives H uncertainty2.438kJ/mol; the explicit recommendation
on p183 gives2.38. Both were visually verified and retained. The preferred body
interval agrees with quadrature of the quoted pyrite2.36 and transition0.30
inputs (about2.379). The table G uncertainty2.442 remains literal and carries
the discrepancy; no inferred corrected G interval is introduced. The prior
USGS-specific H override is retired because this new own NEA evaluation now
supplies the phase-matched triplet. All other earlier overrides/exclusions stay.
Policy `118f85cc935a` has56 overrides/13 exclusions; recommendation
`86b894f121b636b2`.

Greigite G comes from NEA's own re-evaluation of Berner1967 solubility, with
selected Fe2+/HS− anchors. Sulfur control, fine grains and possible mackinawite
impurity motivate the final uncertainty expansion. It is a qualified experimental
reaction-derived value. The same NEA selections give about−57.826kJ perFe3S4
for disproportionation to4C pyrrhotite plus pyrite. The source describes greigite
as metastable; this observation is retained without forcing stability. No H/S
is fabricated. Quoted raw third-party alternatives and further own per-study
adjustments have separate source follow-ups.

The unchanged mackinawite cell links to the already retained original2013
selection; the2020 reprint adds no duplicate observation. Other main iron rows
and individual-study adjustments remain continuation work.

## Reuse and attribution

These own NEA selected/evaluated data are available under the supplied written
OECD clarification and recorded [reuse conditions](nea-tdb-reuse.md).
Credit OECD (2020), Chemical Thermodynamics of Iron, Part2, NEA No7499,
the authors above and the official source URL (accessed27October2026).
When sharing or licensing work made using these data, include the same
acknowledgment requirement in every sublicense and require further sublicensees
to do the same. Source-specific additional restrictions remain applicable.
The email and applicable terms evidence are preserved.

Main TableIII-1 bold type marks newly tabulated reviewed material. Auxiliary
TableIV-1 bold CODATA cells have a separate inherited-data route. Raw quoted
third-party data and other sources' permission holds remain separate. Full
reviews and correspondence stay outside distributions. Metadata keys:
`R16d6_NEA_iron_sulfides`, `R16d6_NEA_iron_observations`,
`source_permission_NEA_TDB_Fe2020_main`, and
`R16d6_NEA_marcasite_width_discrepancy`.
