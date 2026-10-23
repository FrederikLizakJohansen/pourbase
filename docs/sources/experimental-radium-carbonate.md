# Experimental radium carbonate: R11p / R11l4

- [x] Check original composition, temperature and uncertainty evidence.
- [x] Separate the main article and supporting-information reuse terms.
- [x] Add one qualified nominal-endmember G estimate, preserving all alternatives.
- [x] Check source arithmetic, preferred-value selection and calculation effects.

Matyskin, Ebin, Allard, Torapava, Eriksson, Persson, Brown and Ekberg (2023),
*Disordered Crystal Structure and Anomalously High Solubility of Radium
Carbonate*, Inorganic Chemistry 62(30), 12038–12049,
[DOI 10.1021/acs.inorgchem.3c01513](https://doi.org/10.1021/acs.inorgchem.3c01513),
is available as the [original Chalmers PDF](https://research.chalmers.se/publication/536924/file/536924_Fulltext.pdf)
and [PMC article](https://pmc.ncbi.nlm.nih.gov/articles/PMC10394661/).
The article carries CC BY 4.0; its numerical Table 6 is the source used here.
The separately deposited [supporting information](https://acs.figshare.com/articles/journal_contribution/23725805)
has CC BY-NC 4.0 terms in its publisher metadata. It remains external,
read-only context. No supplementary content enters the database or packages.

## Admitted observation

Table 6, journal p.12045 / Chalmers PDF p.9, reports log₁₀Ksp = **−7.52 ± 0.02**
for both Davies and ESIT analyses at nominal 25°C and zero ionic strength.
These fits share experimental data and give the same value. One observation
retains both method labels. Section 2.6, p.12041 / PDF p.5, increases the
one-sigma logK interval to **0.04** for possible Ba-related systematic effects.
Both intervals remain distinct from the abstract's rounded −7.5(1), 2σ.

The local conversion uses the existing explicitly open, non-SRD NBS references
Ra²⁺ = −561500 J/mol and CO₃²⁻ = −527810 J/mol (logical records 10248 and 1661):

```text
G(RaCO3) = G(Ra2+) + G(CO3(2-)) + R × 298.15 × ln(10) × log10Ksp
         = −1132234.231459 J/mol
```

The database stores this as `source_verified_estimate`, evidence class E,
on the existing nominal RaCO₃ record. The unchanged selection policy prefers
it over the 2022 and historical estimates. Both previous observations remain.
No property gap is filled. Source-derived partial intervals are approximately
114.16 and 228.32 J/mol; the total G uncertainty remains NULL because the
reference, composition, temperature and pressure contributions are unavailable.
The plotting default of 2 kJ/mol is a separate assumed interval.

## Scientific qualifications

Section 3.1, p.12042, describes fractional crystallization into Ra-rich and
Ba-rich phases. The reported bulk Ra/Ba composition describes that mixture.
The major phase is estimated to have Ba/Ra ≤ 0.1; its exact composition and
endmember activity remain unknown. Section 4, p.12046, explicitly supports
applying its solubility to pure RaCO₃ from structural and solubility arguments.
The local estimate adopts that published hypothesis. The record keeps its
nominal endmember identity, with no exact mixed-solid composition, mixing
correction or resolved F23 space-group assignment.

Methods 2.4, p.12040, reports a **25.1 ± 0.1°C** bath and **25°C** centrifugation.
The adaptation adopts Table 6's nominal 25°C convention as a qualified
298.15 K estimate. A rigorous 0.1 K correction needs reaction thermal data.
The source does not separately specify measurement pressure; the local 1 bar
estimate uses the recorded ambient condensed-phase pressure-flat approximation.
No H, S, Cp or temperature model is added.

The published high-ionic-strength free-carbonate cells in Table 5 require
clarification before an independent refit. This batch uses the authored
Table 6 result and preserves that limitation explicitly.

## Verification and remaining work

All prior SQL rows and observations remain. One preferred G changes by
−171.240285 J/mol; all other preferred IDs and policy settings remain.
All 75 default maps and nominal uncertainty masks are unchanged. Eleven
buffered Ra scenarios retain their stable phase maps. Some nominal masks
change because the energy separation crosses thresholds under the assumed
plotting interval. Eighteen supported metal-balance scenarios conserve Ra;
restricted solubilities and metal/precipitate boundaries agree analytically.

- [ ] **R11p1:** independent exact major-phase composition, endmember activity
  and pure/disordered phase validation for an unqualified endmember value.
- [ ] **R11p2:** thermal evidence for a rigorous 25.1-to-25.0°C correction.
- [ ] **R11p3:** clarify Table 5 concentrations and fit covariance before an
  independent refit; keep the separate supplementary-material licence hold.

The finite R11l4 source-and-eligibility review is complete with this qualified
adaptation. These stricter follow-ups remain open. R11l3 (original 2019 full
thermal fit), R11l5 (historical signed solid enthalpies), and all other
scientific and permission holds retain their own status. Completed numerical
and reuse reviews carry forward, including the fixed 100-value transcription
audit. Historical request coverage stays 116/131 (NEA 28/28, NIST 88/103),
with six original crystalline-G gaps.
