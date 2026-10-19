# Nickel carbonate, silicate and arsenate follow-up: R11e

The ten-route review adds **11 observations and three species**, filling
**nine properties**. Two local Gibbs values remain alternatives to the
preferred NEA evaluations. The release now contains **1,029 species and
3,260 observations**, with **906/815/699 selected G/S/H properties**.
Every earlier SQL row and preferred observation ID is preserved.

| Reviewed route | Outcome |
|---|---|
| NiCO3·5.5H2O, NiCO3(cr), beta-Ni(OH)2, NiO | Link existing NEA observations; no duplicates |
| NiHCO3+ | Add qualified local G from PSI's approximate supplemental constant |
| NiHSiO3+ native notation | Add full-formula NiSiO(OH)3+ local G from PSI's original SIT reanalysis |
| Ni3(AsO4)2·8H2O | Add the selected NEA G/H/S triplet for annabergite |
| HNiP2O7- | Add a complete local G/H/S variant; retain preferred NEA G |
| Ni(CO3)2(2-) | Keep the upper bound outside the scalar-property import |
| Ni3(AsO3)2·xH2O | Keep unknown hydration and arsenite-reference requirements explicit |

The companion NiP2O7(2-) receives the same complete local G/H/S treatment
as HNiP2O7-. This adjacent extension uses the paired selected reaction in
the same source table. The two variants fill four H/S properties and
retain two alternative G observations.

## Sources and reuse

Selected NEA observations and reaction evaluations use Gamsjäger et al.
(2005), *Chemical Thermodynamics of Nickel*, volume 6, Table III-1 p. 46,
Table III-2 p. 50, and sections V.6.2.2.2/V.6.3.2.1.
The [original NEA publication](https://www.oecd-nea.org/dbtdb/pubs/vol6-nickel.pdf)
and November 2005 errata retain the completed permission and source review.
The relevant errata do not change these admitted cells.

OECD and NEA are acknowledged. The written NEA clarification and OECD data
terms permit use, adaptation and redistribution, including commercially,
subject to source-specific additional restrictions. Every sublicense of work
using these data must include the same OECD acknowledgment requirement and
require further sublicensees to pass it on. Independent auxiliary tables
remain outside this import. See [the source instructions](nea-tdb-reuse.md)
and [distributed notices](../../THIRD_PARTY_NOTICES.md).

The independent PSI numerical results have their own established
**individual original numerical facts** reuse basis:

- Hummel and Thoenen (2014), *Data Selection for Nickel*, PSI TM-44-14-05,
  pp. 25–26/Table 5.5 p. 30: approximate supplemental NiHCO3+ log-beta of
  approximately 1. [Original report](https://www.psi.ch/en/media/47948/download).
- Hummel (2014), *Data Selection for Silicon*, PSI TM-44-12-05,
  pp. 10–11/Fig. 8.6: original SIT reanalysis, log-beta 6.34 ± 0.10.
  Its rounded supplemental configuration uses 6.3.
  [Original report](https://www.psi.ch/fr/media/47930/download).

This route preserves isolated original numerical evaluations and their
scientific qualifications with attribution. It grants no open licence for
complete reports or bulk PSI database files. The silicon report was checked
for additional restrictions; the completed PSI imprint and numerical-facts
review is carried forward. Publications, source images, native files and
private correspondence remain in the external workspace.

The silicate anchor carries the completed R04 review of Miron et al. (2017),
[DOI 10.2475/07.2017.01](https://doi.org/10.2475/07.2017.01), original optimized
aqueous G and its documented open NBS water normalization. No calibration
mineral or restricted compilation value is added.

NIST is acknowledged for explicitly open non-SRD NBS PDR
[M32124](https://doi.org/10.18434/M32124) under the
[NIST open licence](https://www.nist.gov/open/license), without warranty.
Newly used input cells are aqueous-ion CSV logical records **1281** (P2O7),
**1357** (HP2O7) and **1673** (HCO3), with zero-based columns 7/8/10 for H/G/S.
G and H are converted from kJ/mol to J/mol; S remains J/(mol K).
The HCO3 G already exists and is reused. Free-ion H/S inputs are retained
in the derivation metadata; no duplicate free-ion species are created.

## Derivations and source qualifications

Annabergite retains the full formula Ni3(AsO4)2(H2O)8:
G = −3,491,557 ± 8,823 J/mol, H = −4,179,000 ± 20,000 J/mol,
S = 540.771 ± 73.331 J/(mol K). The source's selected H has a widened
interval because the experimental auxiliary inputs were unavailable;
S is source-internally calculated. Source total 95%-type intervals remain
as published. The three-Ni formula, two arsenate ions and eight waters
resolve historical hold **NEA02a-073** using the existing `arsenate-aso4`
reference. The original 29-row hold history is preserved; 28 rows remain.

The bicarbonate and silicate estimates use
`Gf(complex) = Gf(Ni2+) + Gf(free ligand) - RT ln(10) log10(beta)`.
Inputs are the retained NEA Ni2+ G, open NBS HCO3 G and retained eligible
Miron H3SiO4 G. Each observation stores its exact input IDs and calculation.
Both are `source_verified_estimate` values at 298.15 K. Their total
uncertainties remain NULL because supported input intervals are missing.
PSI pressure conditions use an explicit local 1 bar pressure-flat assumption.

The bicarbonate constant is an approximate supplemental model choice.
It is scientifically distinct from the rejected experimental interpretation
and from the NEA upper-bound discussion. Its effect depends on the imposed
free carbonate activity and pH. It supplies no new H/S or thermal model.

The nickel silicate remains independently unconfirmed, as stated by PSI.
Its original reanalysis value 6.34 ± 0.10 is retained; the rounded 6.3
configuration is recorded in metadata as the same evaluation. Native
NiHSiO3+ notation differs from full NiH3SiO4+ by one water component.
The full original formula and matching free H3SiO4 reference remove that
water-basis ambiguity. No native mirror formation G is copied.

For each pyrophosphate property X, the local variant uses
`X(complex) = X(Ni2+) + X(free pyrophosphate ion) + reaction X`.
The NEA reaction G/H/S values are −49,831/30,600/269.768 for NiP2O7
and −29,339/47,900/259.062 for HNiP2O7, in J/mol and J/(mol K).
Their reaction cycles close within 1 J/mol. The source accepts reaction H
from a 5–35 °C study at 0.1 M KNO3 as an infinite-dilution approximation
and warns that alkali-metal concentrations above 0.01 M require explicit
alkali-pyrophosphate associations. Those limitations accompany the values.

The new local G alternatives differ from preferred direct NEA formation G
by **16,503 and 16,958 J/mol**, respectively, because the free-ion
evaluations differ. H/S fill gaps using the same local input variants.
Independently tabulated NBS ion G/H/S are not algebraically exact: the
formation-cycle residuals are approximately **−708 and +193 J/mol** using
the documented elemental-entropy convention. These residuals remain
explicit diagnostics; source rounding alone is not asserted to explain them.
All six local observations are qualified estimates with NULL total intervals.
The selected properties therefore combine evaluations; the complete local
alternatives remain available for review or a user-supplied policy.

## Reaction scope and verification

Annabergite uses three Ni atoms, two free arsenates and eight waters per
stored formula unit. Its energy is divided by three for per-metal diagrams.
NiHCO3+ uses existing `carbonate-co3` with one residual hydrogen:
`log10 a(CO3) = log10 a(HCO3) + pH - pKa`, with pKa calculated from the
retained free-ion G values. NiH3SiO4+ uses `silicate-h3sio4` with zero
residual core O/H. All three have electron coefficient 2 per Ni.

All previous selections, 74 default phase maps and uncertainty masks remain.
Twelve imposed-free-ligand scenarios check the carbonate, silicate and
arsenate systems separately and together; 24 ideal/Davies nickel balances
conserve primary metal. These are external free-component reservoirs.
Total C/Si/As inventories and protonation are separate model tasks;
the imposed activities alone do not establish a physically attainable
total-ligand concentration. The current temperature model continues to
exclude ligand species away from 298.15 K, including complete triplets.

## Checklist and follow-ups

- [x] Review all ten routes and retain source/reuse history.
- [x] Add eleven eligible observations through validated staging.
- [x] Link four existing routes without duplicates and preserve prior preferences.
- [x] Resolve annabergite hold NEA02a-073; retain the other 28 historical solid holds.
- [x] Record the dicarbonate upper bound and unknown-hydration arsenite hold.
- [x] Update tests, notices, statistics, manuscript assets and running reconciliation.
- [ ] **R11e1:** Resolve the arsenite hydration/reference requirements or a
  separately justified water-component model. No anhydrous phase is inferred.
- [ ] **R11e2:** Seek an eligible measured dicarbonate point value. A value
  below an upper bound requires evidence; the bound itself stays external.
- [ ] **R11f:** Review the seven remaining tin reaction routes within the
  other-original-source PSI inventory; wider R11 stays open.

Six original-Bjerrum ammonia holds, zirconium scientific/thermal work and
other sources' permission holds remain separate. Historical requested
coverage stays **116/131: NEA 28/28 and NIST 88/103**. The six original
crystalline Gibbs gaps remain. The external checkpoint is
`r11e-nickel-carbonate-silicate`, with complete candidates, import package,
derivations, reconciliation, source hashes and release evidence.
