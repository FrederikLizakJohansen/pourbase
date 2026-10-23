# R11o: modern radium solubility evaluations

Reviewed 20 October 2026. This batch adds **two G alternatives**, with **no new
species or property fills**. The unchanged policy selects the newer carbonate
estimate and retains NBS sulfate G. All earlier SQL rows and observations remain.

## Completed open-source batch

- [x] Check original 2019 publisher, Crossref, Chalmers and repository routes.
- [x] Obtain the original open 2022 article and verify its CC BY4.0 footer.
- [x] Verify two solid-solubility cells, source conditions and reference ancestry.
- [x] Match existing records and independently verify open NBS ionic inputs.
- [x] Stage/apply two qualified G estimates; preserve alternatives and missing H/S.
- [x] Validate policy effects, default/buffered diagrams, boundaries and balances.
- [x] Record the separate original 2019 thermal/source follow-up.

## Open release and exact cells

Brown, P. L., Matyskin, A. V. and Ekberg, C. (2022),
[*The aqueous chemistry of radium*](https://doi.org/10.1515/ract-2021-1141),
Radiochimica Acta 110(6–9),505–513, is available through the
[Chalmers full PDF](https://research.chalmers.se/publication/530326/file/530326_Fulltext.pdf).
The retrieved PDF is the advance-online version, preceded by a repository
cover page. Article pages1–9 correspond to PDF pages2–10. Its first article-page
footer, **PDF p.2**, states copyright 2022 Paul L. Brown et al. and **CC BY4.0**.
The complete source hash and saved licence evidence are recorded in metadata
`source_reuse_R11o_modern_radium`.

**Table 1, AOP article p.4 / PDF p.5**, **Ra column**, provides:

| Source row | log10 Ksp | Quoted width |
|---|---:|---:|
| MSO4(s) | −10.24 | ±0.05 |
| MCO3(s) | −7.49 | ±0.10 |

The table specifies **25°C and zero ionic strength**. Section2.2, AOP article
p.2 / PDF p.3, discusses the source evaluations. The sulfate value is the
authors' aggregate of accepted Matyskin2018, Brown2019, Langmuir–Riese1985
and Paige1998 values; they reject an inconsistent Kitamura/Yoshida-derived
solubility. The carbonate entry is the 2022 selected endmember evaluation,
with discussion of their team's earlier solubility and structural work.
These entries are verified directly in the 2022 publication. They are separate
from the inaccessible original 2019 numerical fit table.

Reuse follows the article's [CC BY4.0 licence](https://creativecommons.org/licenses/by/4.0/),
with author/title/citation credit, licence link and the local change described
below. No source-specific third-party exception was identified for these two
selected evaluations. Other table rows, including those with restricted JAEA
ancestry, remain outside this batch. The article's licence supplies no blanket
clearance for separately restricted upstream tables.

## Local Gibbs-energy adaptations

For `RaXO_n(cr) = Ra2+ + XO_n(2−)`, the local calculation is:

`Gsolid = G(Ra2+) + G(anion) + R T ln(10) log10 Ksp`.

Inputs independently match the explicitly open, non-SRD
[NIST PDR M32124 release](https://doi.org/10.18434/M32124),
`NBS_Tables_with_ErratumValues.csv`, SHA256
`cb8a8b8b94a287e6e8c82eed8bad2cf9b611d574d1cfd95c8528d318dfef4b44`:

- Ra2+ G **−561500 J/mol**, logical record 10248, column9.
- Sulfate G **−744530 J/mol**, logical record 574, column9.
- Carbonate G **−527810 J/mol**, logical record 1661, column9.

Logical numbering includes both headers. NIST is acknowledged under its
[open licence](https://www.nist.gov/open/license), without warranty.
The sulfate component's historical `NIST_WebBook` ID and legacy status remain;
this batch verifies its numerical input independently against the open PDR
cell and imports no WebBook data.

At 298.15 K with R=8.31446261815324 J/(mol K), the adaptations yield:

- RaSO4 G **−1364480.017305961 J/mol**.
- RaCO3 G **−1132062.9911739891 J/mol**.

Both retain **`source_verified_estimate`, class E**. Calculated digits express
conversion output and do not improve source precision. The new sulfate
alternative remains below the preferred class B NBS observation in the ranking.
The carbonate alternative replaces the selected older Langmuir-based
**−1136686.4788710426 J/mol**, which remains as evidence. No values are averaged
locally and no selection override is added.

The source table does not separately report pressure. The local 1 bar estimate
uses an explicit **ambient condensed-phase pressure-flat approximation**.
No measured 1 bar source value or numerical pressure-correction uncertainty is
claimed. The source's dimensionless I=0 equilibrium evaluation is used on the
project's unit-activity reference convention; no density-based molarity/molality
conversion is inferred. These qualifications remain in each locator.

The published logK widths remain attached to their original values. The source
describes 95% intervals for multiple-data averages. Their G contributions,
`RT ln(10) × width`, are **partial intervals only**. Ionic-anchor, pressure,
phase and covariance contributions are unavailable, so stored **total
uncertainty remains NULL**. Calculation bands retain the existing explicit
assumed 2000 J/mol interval; it is separate from the source's partial interval.

## Identity and thermal scope

The observations belong to the existing nominal pure-endmember RaSO4 and
RaCO3 records. The 2022 source describes sulfate as orthorhombic and carbonate
as cubic with disordered oxygen. Existing phase records and labels remain;
no exact sample equivalence, space group or Materials Project match is inferred.
The Ba-containing 2023 carbonate specimen is a separate scientific follow-up.

Only two G observations are added. The original 2019 H/Cp values remain
unverified and no H, S, zero reactionH or full 0–300 °C model is inferred.
RaCO3 remains G-only. Its explicit ligand species continues to be excluded
from the current temperature approximation away from 298.15 K.

## Scientific effects and release

The policy remains **8c4739134347**, with 46 overrides/13 exclusions. One
preferred G changes; every other previous preferred ID remains. Recommendation
fingerprint: **d9282c8b53ae36fa**. The database contains **1059 species /
3387 observations /75 systems**, with **933/830/715** preferred G/S/H values.

All **75 default maps and their 1σ/3σ masks** are unchanged on 81×91 grids.
Eleven buffered radium scenarios cover carbonate, sulfate and combined
reservoirs. At log carbonate activity−2, **7283/7371** stable cells change;
the same count changes with sulfate activity10^-6 present. Uncertainty masks
also change in other buffered cases, using the explicitly assumed intervals.
Sulfate-only maps and masks remain. The detailed scenario ledger is retained
in the external validation checkpoint.

The carbonate logK change from−8.3 to−7.49 gives a solubility-product ratio
**10^0.81≈6.46**. In a restricted Ra2+/RaCO3 calculation with 10^-2 free carbonate
activity, the older estimate permits about 5.01×10^-7 mol/L dissolved Ra;
the modern estimate permits about 3.24×10^-6 mol/L. Thus a 1 µM total inventory
is fully dissolved under the new estimate, while the older one would partly
precipitate. This example uses a fixed free ligand activity and the evaluated
endmember model; it is not a closed carbonate inventory or solid solution.

**18** full supported metal balances pass with ideal and Davies I=0.001/0.01
activity models. Three independently calculated restricted solubilities and
metal/precipitate potential boundaries pass. Thermal checks at 323.15/373.15 K
preserve the existing explicit-ligand exclusion. Earlier observations are
preserved, SQLite checks pass and repeated import is idempotent.

Historical request coverage stays **116/131 (88.5%)**, including all **28/28 NEA**
targets. Six original crystalline-G gaps remain. The main tracker retains
**5/18 checked headline reviews (27.8%)** with separately recorded holds.

## Remaining original-source requirements

- [ ] **R11l3:** obtain the original 2019 full numerical fit/thermal table for
  [Brown, Ekberg and Matyskin](https://doi.org/10.1016/j.gca.2019.04.009).
  Chalmers511208 has metadata without a full-text file. Publisher PDF routes
  returned403; the API supplied metadata and a FULL request returned429.
  No original 2019 H/Cp, uncertainty reconstruction or complete thermal
  parameterization is imported. The 2022 additions are separately sourced.
- [ ] **R11l4:** resolve the Ba-containing 2023 carbonate material and 25.1 °C
  measurement conditions before a pure-RaCO3/298.15K reinterpretation.
- [x] **R11l5:** [R11q](radium-solid-enthalpies.md) verifies the authoritative
  correction and adds separately qualified historical H/S alternatives.

The finite 2022 open-source admission batch is complete. R11l3's original 2019
requirement and the wider R11 task remain open. Completed reviews and other
sources' permission/scientific holds carry forward.
