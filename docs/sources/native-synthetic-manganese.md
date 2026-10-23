# Native synthetic manganese carbonate: R11s / R11m1

- [x] Locate the original numerical rows and reference convention.
- [x] Crosscheck the synthetic-material selection in the primary USGS report.
- [x] Reconstruct the native bicarbonate reaction and add one local G alternative.
- [ ] Match the exact original specimen/surface state beyond its material category.

Nordstrom et al. (1990), *Revised Chemical Equilibrium Data for Major
Water–Mineral Reactions and Their Limitations*, ACS Symposium Series 416,
398–413, [DOI10.1021/bk-1990-0416.ch031](https://doi.org/10.1021/bk-1990-0416.ch031),
Table2 III, p.406, lists separate crystalline and synthetic rhodochrosite
dissolution constants. The synthetic value is **log Ksp = −10.39**, with
reaction H missing. The carbonate note (e), p.407, and reference82, p.412,
trace the selected K values to Garrels, Thompson and Siever (1960).
Page403 specifies the infinite-dilution aqueous convention and 1 bar.

The original chapter was checked through indexed book text. Its original
full-resolution PDF remains unavailable through the checked routes.
The retrieved primary [Ball and Nordstrom (1991), USGS OFR91-183](https://doi.org/10.3133/ofr91183),
Table2, printed p.30 / PDF p.36, row190, was inspected directly. It labels
MnCO₃(synthetic), repeats −10.39, cites Nordstrom1990 as reference47,
and gives no reaction H. These releases share an evaluation; one observation
retains both citations.

## Native reaction and reference conversion

The later native reaction is:

```text
Mn2+ + HCO3− = H+ + MnCO3(synthetic), log K = 0.06115
```

Combining carbonate precipitation with bicarbonate dissociation gives
`log Knative = log Ka2 − log Ksp`.
The original acid-reference polynomial at 298.15 K gives
**log Ka2 = −10.328854378506376**, hence
**log Knative = 0.06114562149362435**, which rounds to **0.06115**.
The reverse association polynomial is independently printed in USGS1991,
Table2, p.25 / PDF p.31, row68.

The production G conversion uses current open NBS Mn²⁺ and carbonate
references (logical records6291 and1661):

```text
Gsynthetic = −228100 −527810 + R × 298.15 × ln(10) × (−10.39)
           = −815216.218731 J/mol
```

This enters as a local class E `source_verified_estimate` on the existing
nominal synthetic/precipitated MnCO₃ record. The source evaluation already
uses 1 bar; the older Garrels pressure correction is retained with its own
observation. Total G uncertainty remains NULL.

The source-equivalent bicarbonate reference is −586767.198943 J/mol.
The independently rounded open NBS bicarbonate value is −586770 J/mol,
a **−2.801057 J/mol** difference. Observation metadata preserves this
residual and native rounding explicitly. The carbonate and bicarbonate
representations are algebraically reconciled on consistent references.
They form one observation, with no component-reference change.

## Selection, material scope and checks

The default policy selects the new G, a shift of **−640.364448 J/mol**.
The older pressure-adapted Garrels G and NBS precipitated-material H remain.
No species or previously unavailable property is added. The new synthetic
G remains **3883.781269 J/mol** above preferred crystalline rhodochrosite.

The original labels support the nominal synthetic/precipitated category.
Exact original grain size, surface state and specimen equivalence remain
unverified. The phase record keeps its incomplete identity and unspecified
space group. Missing synthetic reaction H stays explicit; the crystalline
row's H is not assigned to the synthetic material. No S, Cp, zero reaction H
or source-consistent joint thermal fit is added.

Staging preserves every earlier SQL row and all other preferred IDs.
All75 sampled default maps/masks and three carbonate-buffered Mn maps/masks
remain. Eighteen supported full/restricted balance scenarios conserve Mn;
full inventories stay unchanged. Restricted ideal solubilities, metal
boundaries and carbonate/bicarbonate chemical potentials agree analytically.
The source NULL interval and assumed plotting interval remain distinct.

## Reuse and remaining requirements

The batch carries the individually attributed USGS numerical-fact/federal
evaluation route already reviewed for this report, plus the explicitly open
non-SRD NBS ionic references. USGS and NIST are acknowledged. One selected
result is adapted with its original ancestry and local changes documented.
The complete ACS chapter is not asserted open licensed. Publications, tables,
prose, figures and database exports remain external. Existing OECD attribution
and downstream acknowledgment requirements remain applicable to NEA material.

- [ ] **R11s1 / strict R11m1 specimen requirement:** exact specimen/surface
  mapping beyond the supported nominal material category.
- [ ] **R11s2:** retrieve the original full-resolution chapter for an evidence
  archive upgrade; current indexed-original/USGS checks retain their exact basis.

R11m1's numerical and reaction-reference questions are resolved. Its strict
specimen requirement remains open. Completed reviews, the fixed100-value
audit and all independent permission/scientific holds carry forward.
Historical request coverage remains116/131 (NEA28/28,NIST88/103), with the
same six original crystalline-G gaps.
