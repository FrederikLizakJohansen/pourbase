# Further original open NBS crystalline chlorides

This batch adds **210 observations and 111 species**, filling **201 properties**:
45 G, 46 S and 110 H. It reconciles **157 original crystalline chloride/hydrate
rows across 66 supported systems**. Ninety-five cells already retained from the
same original NBS evaluation are linked to their earlier observations.

Totals are **1,453 species / 4,423 observations**, selected G/S/H
**1166/1139/1023**. Every earlier SQL row and alternative remains. The unchanged
policy changes one earlier preferred observation: halite S becomes **72.13
J/(mol K)** from NBS; the earlier USGS 72.1 remains stored. Halite gains missing
G/H. All other earlier preferred values remain selected.

## Original source and reuse

The source is Wagman et al. (1982), *The NBS Tables of Chemical Thermodynamic
Properties*, digitized with errata in the explicitly open, non-SRD NIST Public
Data Repository release, [doi:10.18434/M32124](https://doi.org/10.18434/M32124).
The corrected CSV has SHA256
`cb8a8b8b94a287e6e8c82eed8bad2cf9b611d574d1cfd95c8528d318dfef4b44`,
matching the original official PDR metadata and its linked
[NIST open licence](https://www.nist.gov/open/license). NIST is acknowledged;
the data are distributed without warranty. This route remains separate from
NIST SRD/JANAF/WebBook material, the NEA/OECD clarification and Thermoddem
bulk-data permission. All earlier independent source holds continue.

Only solvent-free `cr` rows are used. The source header specifies **298.15 K
and 0.1 MPa (1 bar)**. G/H use zero-based columns **8/7**, converted from
kJ/mol to J/mol; S uses column **10**, J/(mol K). Zero-K H, aqueous/ion-pair,
liquid and gas rows are separate source states. No uncertainty is supplied for
these cells. Printed precision supplies no confidence interval. These are
critically evaluated source-table observations; the digitized row alone does
not distinguish each underlying measurement from an estimate.

| Source-cell disposition | G/H/S slots |
| --- | ---: |
| New original observations retained | 210 |
| Already retained original NBS evaluation linked | 95 |
| No source numerical value | 166 |
| Total across 157 rows | 471 |

Four source rows contain no numerical G/H/S and add no species. Earlier NBS
representations are deduplicated using original evaluation identity, exact
formula/state and numerical basis, with exact CSV locator matches recorded
where already present. Independent NEA, USGS and other evaluations remain
separate alternatives even where their numbers agree.

## Formula, identity and missing properties

All values retain **one full original formula unit**. A chloride MClₙ·wH₂O
has one primary atom, n externally buffered chloride components, residual
O=w and H=2w. Water is counted once, the reduction has n electrons per
primary atom and its proton coefficient is zero.

The new records comprise **44 with G/H/S, 65 with H only and two with S only**.
For example, LaCl₃ retains H = −1071100 J/mol; RaCl₂ retains S = 134 J/(mol K).
Missing G is not reconstructed from those properties. Existing independent G
remains available where a newly added source row lacks it.

All **111 new exact structures remain unresolved**. Original phase/color
labels remain visible: InCl II, black RuCl₃, light-green/pale-blue/dark-blue
CrCl₂ hydrates, α-WCl₆, β-DyCl₃, α-BeCl₂ and α-SrCl₂. The source's label
supplies no inferred crystal space group or native mineral alias. Existing
phase reviews carry forward on matching records.

## Source consistency and calculation scope

The source G/H/S screen covers 75 complete triplets. Two have residuals above
1 kJ/mol against the original elemental entropy references:

| Source row | Original printed table | Cycle residual |
| --- | --- | ---: |
| ReCl₃, logical CSV 6471 | Table 50, p. 2-196, original PDF p. 204 | −2.160 kJ/mol |
| RaCl₂·2H₂O, logical CSV 10252 | Table 97, p. 2-289, original PDF p. 297 | +2.059 kJ/mol |

The original printed cells were visually checked and match the corrected CSV.
The reported numbers remain unchanged, with explicit warnings and a source
consistency follow-up. No local correction or uncertainty is inferred. Other
triplets retain their own diagnostic results; the earlier NiCl₂ tetrahydrate
qualification carries forward. These records enable no additional ligand
thermal model.

Validation covers **414 energies, 198 buffered diagrams and 660 primary-metal
balances**. Ideal calculations cover free chloride activities 10⁻⁶, 10⁻³ and 1;
Davies checks use background ionic strength 0.01 at the lower two activities.
The existing chloride reference remains pinned. Closed balances conserve the
primary element; chloride activity and the water reference remain externally
prescribed. Concentrated-brine water activity, Pitzer interactions, closed
chloride inventories and component thermal functions retain separate model work.

All **75 default diagrams and uncertainty masks remain unchanged**, as do
strict periodic completeness results. These species require the chloride buffer;
G-bearing chloride species remain excluded from non-298.15 K calculations by
the existing ligand thermal limitation. The policy, runtime, ligand references
and GUI implementation remain unchanged.

Historical requested coverage remains **116/131**: NEA 28/28 and NIST 88/103.
The six original crystalline G gaps remain open. Further independently eligible
source properties, precise structures and the two cycle discrepancies remain
explicit follow-ups.
