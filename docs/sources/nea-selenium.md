# NEA selenium: R11a inventory and R11b core species

The 16 October 2026 continuation adds **71 observations across 29 species**,
including **22 new species**, from the original NEA selenium review. It fills
**52 missing properties** and changes **19 existing preferred observations**
under the unchanged selection policy. Every earlier SQL row is preserved.
Production contains **1,011 species and 3,219 observations across 74 systems**,
with selected G/S/H counts **888/805/689**. Policy fingerprint:
`d7d53842a14a`; recommendation fingerprint: `e724c7e0c4a6aefb`.

## Source and reuse

Olin, Å., Noläng, B., Osadchii, E. G., Öhman, L.-O. and Rosén, E. (2005),
*Chemical Thermodynamics of Selenium*, OECD Nuclear Energy Agency, Chemical
Thermodynamics Series, volume 7, [official publication](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/chemical_thermodynamics_of_selenium_volume_7.pdf),
Table III-1, printed pp. 40–42 / PDF pp. 81–83. Accessed 16 October 2026.
Source SHA-256: `2179ecdc4d5b16029d67c26f792a72fd055570da16c97e43cd24be68797989e3`.

The written NEA-TDB clarification and OECD data terms cover these selected
numerical evaluations, including commercial adaptation and redistribution.
OECD and NEA are acknowledged. Every sublicense of work using these data must
carry the same OECD acknowledgment requirement and require further sublicensees
to pass it on. No additional restriction was identified for the admitted
selected cells. Credited third-party figures, independent auxiliary tables,
complete publications and private correspondence remain outside distribution.
This batch adds no independently copied NIST SRD or PSI numerical values.
The volume-specific reuse record carries the existing private evidence hashes;
other sources' permission holds and completed reviews remain intact.

The [official November 2005 errata](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/errata_selenium_volume_7_2020-09-02_11-47-23_191.pdf)
were checked. They correct the CdSeO4(aq) reaction Gibbs energy on printed
p. 57 to −12.957 ± 0.342 kJ/mol and several SIT medium labels. These changes
apply to later routes; they change no admitted core cell. Errata SHA-256:
`a6e5366b3f24ff4a14438bdc270eb2d0b83cb8ced16e18f2bbe9facb4bb9cc17`.

## Finite inventory and conditions

Thirty core Se/H/O rows were reviewed. Twenty-nine supply selected G/H/S;
Se(l) has a heat-capacity route only and remains with R18. The admitted rows
cover stable trigonal and metastable monoclinic selenium, Se1–8 gases,
selenide and three polyselenide ions, oxides, hydrogen selenide, and
selenous/selenic acid species. Halides, other ligands and metal compounds
remain separate batches.

All admitted observations refer to **298.15 K and 0.1 MPa = 1 bar**; aqueous
species use infinite dilution and the conventional H+ reference. G/H are
converted from kJ/mol to J/mol; S remains J/(mol K). Source total uncertainty
intervals correspond in principle to 95% confidence and retain their widths.
Reference G/H zeros have no reported interval. Source-internal calculations
retain the selected table's precision. Each observation has its exact row,
property, page, units, conditions, source and reuse obligations.

The existing `hexagonal-black` elemental record is the trigonal reference:
section V.1, p. 87, explains the naming. Its old labels and observations remain,
with a source-backed phase identity. Monoclinic selenium is a separate
metastable phase. No unreported space group or structure match is inferred.
Se2O5 has alternating Se(IV)/Se(VI) units; its stored coefficient 5 is the
mean per Se. Its source heat cycle neglects the 293–298 K correction, as does
the H2SeO4(cr) evaluation. These retain the source-reviewed estimate status.
Se2O5(cr), H2SeO3(cr) and H2SeO4(cr) supply H only; G/S stay unavailable.

## Selenite discrepancy and thermal scope

Selected Table III-1, p. 41, gives **S(SeO3²−) = −5.055 ± 7.011 J/(mol K)**.
Discussion p. 143 prints **+5.1 ± 7.0**. Both signs were visually checked.
The selected negative sign reconstructs the selected G from H within
0.4 J/mol using the review's elemental and ionic conventions; the positive
discussion sign differs by about 3.03 kJ/mol. The official errata contain
no sign correction. Retain the selected-table observation with an explicit
warning; preserve the positive discussion variant in the external discrepancy
ledger pending authoritative clarification. Relative ionic entropy can be
negative under the H+ convention.

The source warns against mixing thermal evaluations, especially for Se cluster
gases. Se3–8 gas triplets retain the estimated thermal-function qualification.
HSe− supplies NEA G only; its earlier independent H/S remain selected.
Runtime temperature estimates therefore have the documented mixed-source
limitation. Project water and buffered ligand references retain their own
provenance; core selenium additions do not replace those references automatically.

Eleven gases require `include_optional_gases=True` and prescribed external
fugacity. Full cluster formula units are divided by the Se count once in
per-Se calculations. Closed gas/headspace inventories remain unsupported.
The three polynuclear aqueous ions participate in fixed-activity diagrams;
closed mononuclear balances exclude and report them.

The three H-only crystals make the selenium Gibbs inventory incomplete.
Strict periodic screening therefore reports selenium as incomplete: 56
systems calculate with experimental data, or 59 with the existing opt-in MP
fallbacks. The default relaxed screen still calculates all 74 systems and
reports the excluded species.

## Verification and remaining plan

Staging verified integrity, foreign keys, idempotence and preservation of every
earlier SQL row. All 21 complete triplets reconstruct within 0.49 J/mol;
five selected reaction comparisons agree within table rounding, and the sixth
core PSI reaction agrees within its two-decimal logK precision. Aligned
pymatgen checks at activities 10−6 and 10−2 agree at every point. Selenium
changes 430 phase points and 428 uncertainty-mask points on an 81 × 91 grid;
the other 73 default maps/masks and 118 Zr buffered scenarios are preserved.
Eighteen selenium temperature/gas scenarios pass, as do ideal and Davies
closed selenium inventories with their stated species exclusions.

- [x] **R11a:** Reconcile all 2,070 substance-property slots and 1,760
  reaction-property slots, covering 690 substances and 440 reactions. Carry
  forward every original decision and earlier crosswalk link. Composition
  comparison links remain distinct from verified phase identity and ancestry.
- [x] **R11b:** Review and add this finite core selenium batch through staging.
  Six of the 20 selenium reaction routes now have direct original-NEA coverage.
- [ ] **R11c:** Review the remaining 14 metal-bearing selenium routes: two
  nickel selenocyanates; Ca/Mg/Mn/Ni aqueous selenates; FeSeO3+; Mg/Ni/Ca/Mn
  selenite hydrates; Ba selenate; and Ba/Sr selenites. Verify full formulas,
  source exceptions, free-ion references, molar basis and errata individually.
- [ ] Continue the carried 29 Zr reaction routes, eight independent PSI nickel
  routes, 57 other-source routes and unsupported-system decisions, resolving
  the applicable outstanding evidence or model needs.
- [ ] Keep Se(l)/Cp functions with R18 and the positive discussion entropy
  variant on its scientific hold. Wider R11 remains open.

The three sodium-zirconosilicate 298 K conversion holds still cover six
323.15 K observations. The Aja publisher preview provides no thermal table;
see [the temperature review](nea-zirconium-temperature-review.md). Hydride,
calcium formula, gas-accuracy and other-source holds carry forward. Historical
request coverage remains **116/131: NEA 28/28, NIST 88/103**. The six original
crystalline Gibbs gaps remain. Concurrent GUI implementation is untouched.

The complete import package, candidate ledger, 3,830-slot reconciliation,
440-route crosswalk, primary evidence and validation outputs are saved in the
external `reaktoro-dataset-review/r11-psinagra-selenium` checkpoint.
