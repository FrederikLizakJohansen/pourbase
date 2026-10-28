# CHNOSZ: first bounded source review

The 28 October 2026 review covers exactly **47 candidate records**, drawn
from CHNOSZ 2.3.0: 45 under Huston & Bastrakov (2024), plus two under
Laskar et al. (2025). It adds **63 observations and 17 species**, supplying
**54 previously unavailable preferred properties**: 18 G, 18 S, 18 H.
Every earlier observation, species, source, phase, warning and component
row is preserved. The source-expansion round closed before this follow-up
remains closed.

The database now contains **1,788 species, 5,206 observations, 1,795 source
records and 2,778 warnings**, across 75 systems. Selected G/S/H counts are
**1340/1310/1366**. The policy fingerprint remains `4c1df55bbeff`;
the recommendation fingerprint becomes `37bbab091e86908b`.

## Sources, permissions and attribution

- [CHNOSZ 2.3.0](https://cran.r-project.org/package=CHNOSZ), released
  31 August 2026, declares GPL-3. Jeffrey Dick and contributors are credited
  for the compilation, provenance notes and published corrections.
  CRAN archive SHA256:
  `5c1adb74cabde3fe53ac69da9600ab462dd43d11df08600b4a117893219781b3`.
- Huston, D. L. and Bastrakov, E. (2024), *Germanium, indium, gallium and
  cadmium in zinc ores: a mineral system approach*, Australian Journal of
  Earth Sciences 71, 1125–1155,
  [doi:10.1080/08120099.2024.2423772](https://doi.org/10.1080/08120099.2024.2423772).
  Electronic Appendix E2 is independently available in the Geoscience
  Australia [CC BY 4.0 dataset](https://doi.org/10.26186/148619).
  The publisher notice and deposited Crossref metadata also specify
  CC BY 4.0. The exact E2 CSV/workbook cells were checked. Their original
  reference keys remain in each observation locator.
- Laskar, C., Bazarkina, E. F. and Pokrovski, G. S. (2025), *The role of sulfur
  in palladium transport and fractionation from platinum by hydrothermal
  fluids*, Geochimica et Cosmochimica Acta 406, 134–147,
  [doi:10.1016/j.gca.2024.12.019](https://doi.org/10.1016/j.gca.2024.12.019).
  Author-deposited [data DOI 10.17632/v52mgp7mmm.1](https://doi.org/10.17632/v52mgp7mmm.1)
  explicitly use CC BY 4.0. `Data_Laskar_et_al.xlsx`, sheet **Table 4**,
  cells B2/C2 and B3/C3 independently verify the two G/S pairs. Workbook
  SHA256: `097922147df8fe754157cc39d1c754d7bf481b626aa1d3f01a6ed05410717e97`.
- Robie, R. A. and Hemingway, B. S. (1995),
  [USGS Bulletin 2131](https://doi.org/10.3133/b2131), Table 2, supplies
  independently checked original public-domain cells for Cd entropy
  (printed p. 4/PDF p. 10) and greenockite G/H/S (printed p. 11/PDF p. 17).

CC BY attribution, licence links and adaptations accompany the release
in `THIRD_PARTY_NOTICES.md`. CHNOSZ source release, original appendices,
author workbook, licence/metadata responses and hashes are preserved in
the external review workspace. Individual locators also identify exact
upstream evaluations. Original-article tables were not independently
reverified for the Ge reprints: these are explicitly attributed selected
observations from the open author Appendix E2, with their original
Pokrovski–Schott 1998, O’Hare–Curtiss 1995 and Málek et al. 2011 ancestry.
No blanket open licence is asserted for those whole upstream articles.

Identified Thermoddem, Barin/commercial and handbook holds remain separate.
No JANAF or WebBook values are added. The existing NEA permission remains
independent; OECD acknowledgment and downstream requirements continue for
the existing sulfur component reference.

## Numerical and chemical decisions

G/H use J/mol, S uses J/(mol K); cal converts with **4.184**. Values retain
one full formula unit, 298.15 K and 1 bar. Missing uncertainties remain NULL.
Published fits and predictions retain `source_verified_estimate`, class E;
critical USGS and direct selected GeS/alpha-GeS2 evaluations retain their
appropriate evidence status. No Cp or HKF parameters are added.

The author E2 appendix and CHNOSZ differ in **11 In enthalpies**: the latter
applies the documented OBIGT 2025 correction **−7335 cal/mol = −30689.64 J/mol**.
All 11 corrected cells were checked against the package and formation-cycle
consistency using the conventional-ion charge term. Their residuals against
current open reference entropies are below 0.2 kJ/mol. The original erroneous
H cells stay in the external source ledger. G/S retain the author values;
two rounded entropies already represented by the same correlation are linked
in the ledger without extra observations.

The native otavite H differs by a factor of 10 from E2. That row remains
under its Thermoddem source hold; neither representation is imported.
The CdCl4²⁻ entropy is an author correlation estimate in Bazarkina et al.
(2010), Table 4, p. 175, footnote 2. Its **50.61 cal/(mol K) = 211.75224 J/(mol K)**
becomes preferred over the retained1997 estimate 0.96232. The other Cd
chloride G and first-three S cells explicitly reprint Archer 1998; their
original-source reuse review remains held, separate from this newly
estimated entropy. E2 cites a different 2010 Bazarkina paper, which is
recorded as a bibliography discrepancy.

Source GeO(OH)3⁻ contains one more water than the existing HGeO3⁻ record.
Normalize each property by subtracting one H2O(l): G = −237129 J/mol,
H = −285830 J/mol, S = 69.91 J/(mol K), from open NBS M32124. Existing G remains
preferred; new H/S become available. Other named phases remain distinct:
hexagonal GeO2 and tetragonal argutite; generic NBS GeS2 and alpha-GeS2;
generic NBS CdS and named greenockite. No space group is inferred solely
from a formula. Alpha-GeS2 adds H/S and keeps its missing G explicit.

Metal complexes use existing free chloride, fluoride, sulfate or sulfide
references. Pd/Pt(HS)4²⁻ retain four S and four H, formal metal oxidation
state +II and electron coefficient 2. Sulfur is represented by the buffered
S²⁻ component with residual H4. In–HS complexes retain formal In(III).
A fixed-HS⁻/equivalent-S²⁻ activity check verifies proton/ligand cancellation.
The new ligand species do not imply a closed ligand inventory or additional
thermal capability: the current temperature model excludes ligand species.

## Scientific effects and checks

- 75 default281 × 301 diagrams compared: 74 identical; Ge changes 11475/84581
  grid points through newly available Ge(OH)4 and distinct argutite.
- 20 ligand-enabled diagrams checked across 10 element/component scopes
  at log free activities −8 and −4. Changes occur for In fluoride/sulfide,
  Pd/Pt sulfide and Ge sulfide; unchanged scenarios remain recorded.
- 40 closed-metal balances:10 scopes × 2 concentrations × ideal/Davies models.
  Worst relative conservation residual 2.12 × 10⁻16.
- 12 temperature scenarios at 323.15 and 373.15 K; only Ge phase maps change.
- Representation audit: 1788 species and 5206 observations,zero errors.
- SQLite integrity and foreign keys pass; all prior rows are preserved.

The complete [47-record decision table](chnosz-first-batch.csv) records
24 candidates supplying additions, one duplicate-only candidate and 22
fully held candidates. Some retained candidates have individual held or
already represented properties. A held disposition closes this bounded
review; it supplies no missing permission or numerical verification.

Runtime, GUI, existing component references and default policy are unchanged.
The larger Cu/Au/carbonate/REE source lists remain a separate backlog.

Final release checks: **603 tests pass**, strict documentation builds pass,
and the wheel and source archive contain the current database and attribution
notices. An isolated installed-wheel import and Ge phase load pass. The full
policy-sensitivity analysis uses 200 samples per scope across all 75 systems.
The local paper remains 50 pages after three clean LaTeX passes, with a current
Overleaf archive and no unresolved references or overfull boxes. All 63 newly
reported observations have stable IDs; repeat insertion changes zero rows.
