# R16: Thermoddem rights and independent original sources

This checkpoint adds **64 observations on 24 original NBS chloride/hydrate
rows**, including **15 new species** and **44 missing properties**: 14 G,
14 S and 16 H. All earlier SQL rows and preferred values remain. Totals:
**1,326 species /4,090 observations /75 systems**, selected G/S/H
**1107/1084/901**. The policy, runtime and existing ligand references are unchanged.

## Thermoddem rights remain held

The reviewed file is Thermoddem v1.10 MAJ2020, dated 15 December 2020,
pinned in Reaktoro commit `f587235e692b7168faa272c8892a4c079a1f7dd9`.
SHA256: `a2fddf9c966b90d9408b39cea1f6a3fd1a0278c6a218cb4261082e4184f8f6df`.
All **1,790 native reaction blocks** retain explicit rights/source dispositions.
No Thermoddem logK, reaction enthalpy, analytical function or native formation
number enters this batch.

The initial completed audit records that the
[BRGM Thermoddem terms](https://thermoddem.brgm.fr/page/terms-and-conditions-use)
require permission for reproduction/dissemination, with no compatible separate
grant verified. The audit's wording and hash are preserved externally. A full
primary terms snapshot from that audit was not found, and current HTTPS/HTTP
retrieval failed on **25 October 2026**. This checkpoint supplies no invented
verbatim terms quotation. The accessible
[official product page](https://www.brgm.fr/en/software/thermoddem-brgm-reference-thermodynamic-database-geochemical-modelling)
provides no verified Thermoddem-specific compatible redistribution grant.
BRGM's ADES and HubEau open-data statements cover other services. The Reaktoro
software licence and OECD NEA clarification remain separate source routes.
No permission outreach was authorized or performed.

Bulk permission and primary-terms retrieval remain **R16a**. Other original
numerical, structural, hydration and model questions remain separately tracked.
This finite source review resolves no bulk Thermoddem permission hold.

## Independent open NBS observations

Every admitted number is verified against the explicitly open non-SRD NIST
Public Data Repository release of Wagman et al. (1982), *The NBS Tables of
Chemical Thermodynamic Properties*, digitized with errata,
[doi:10.18434/M32124](https://doi.org/10.18434/M32124).
CSV SHA256: `cb8a8b8b94a287e6e8c82eed8bad2cf9b611d574d1cfd95c8528d318dfef4b44`.
NIST is acknowledged under its [open licence](https://www.nist.gov/open/license);
data are supplied without warranty. Existing OECD acknowledgment and downstream
requirements continue for NEA material independently.

The original CSV's condition row specifies **298.15 K and 0.1 MPa (1 bar)**.
Only solvent-free crystalline rows are used. G/H use zero-based columns **8/7**
(kJ/mol, multiplied by 1000), and S uses column **10** (J/(mol K)). Zero-K H,
liquid and aqueous ion-pair rows are excluded. Each observation carries the exact
logical CSV record, formula, state, column, original value and conversion.
No uncertainty is stated for these cells; precision supplies no confidence interval.

| System | Original crystalline source rows and logical CSV records |
| --- | --- |
| Zn | ZnCl₂ (4043) |
| Cd | CdCl₂ (4326), monohydrate (4341), 2.5-hydrate (4342) |
| Cu | CuCl (4786), CuCl₂ (4789), dihydrate (4816) |
| Ni | NiCl₂ (5306), dihydrate (5329), tetrahydrate (5330), hexahydrate (5331) |
| Co | CoCl₂ (5492), monohydrate (5513), dihydrate (5514), hexahydrate (5515) |
| Fe | FeCl₂ (5832), dihydrate (5844), tetrahydrate (5845), FeCl₃ (5846), hexahydrate (5870) |
| Mn | MnCl₂ (6313), monohydrate (6325), dihydrate (6326), tetrahydrate (6327) |

Nine rows match existing Fe/Ni records; their new NBS alternatives retain the
NEA and other earlier evaluations. FeCl₂ dihydrate gains its missing H,
**−953100 J/mol**. Fifteen source compositions add records. New exact crystal
structures remain unresolved; a generic NBS `cr` row supplies no space group
or verified correspondence to a native mineral alias.

CoCl₂ monohydrate has **H only**, −615000 J/mol; G/S stay missing. NBS FeCl₂
dihydrate/tetrahydrate and FeCl₃ hexahydrate also supply H only, preserving
other available evaluations. FeCl₃ hexahydrate retains its earlier G gap.
No missing G or S is reconstructed from a reaction or an entropy estimate.

The full-source G/H/S cycle screen records residuals up to **0.660 kJ/mol**
for NiCl₂ tetrahydrate against the pinned NBS elemental references. Reported
facts remain unchanged, and the diagnostic supplies no new uncertainty or
locally corrected property. Earlier preferred NEA values remain selected.
These observations establish no additional thermal or concentrated-brine model.

## Formula, calculation and identity scope

All values retain one complete original formula unit. A hydrate MClₙ·wH₂O
has one primary metal, n external free chloride components, residual O=w
and H=2w. The reduction has n electrons and zero protons per primary.
CuCl keeps Cu(I); CuCl₂ keeps Cu(II). The CdCl₂·2.5H₂O formula retains
O=2.5 and H=5, with water included exactly once. Buffered calculations use
the existing `chloride-cl` reference. Closed balances conserve primary metal;
chloride activity and water reference remain externally prescribed.

Source-name matching is a composition screen. For example, the pinned
Thermoddem file labels a CuCl₂ equation “Melanothallite”; this native
name/formula relationship remains unverified and is not transferred to the
NBS crystal. Native FeCl₃ reaction rearrangements through other chlorine
oxidation states supply no new formation-property observations.

Validation covers **180 energies**, **21 buffered diagrams** and **70 primary
balances**. Davies checks use background ionic strength 0.01 at the lower
chloride activities; unit chloride activity is checked with the ideal model.
All 75 default maps and uncertainty masks remain unchanged. Source-derived
alternatives, original-source holds, structural identity, closed chloride and
brine-water/thermal models retain their own dispositions. Historical requests
remain **116/131**; the six original crystalline G gaps remain open.
