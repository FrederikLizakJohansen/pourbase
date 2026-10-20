# R11l: final 13 original-source routes

Reviewed 20 October 2026. The finite source review adds **46 observations and
10 species**, fills **26 properties**, and introduces radium as the **75th
supported elemental system**. The database now retains **1,055 species and
3,371 observations**, with **932/827/711 preferred G/S/H properties**.
All earlier observations remain. The unchanged selection policy selects new
NEA Gibbs energies for sulfide and iodic acid; all other existing preferred
observation IDs remain.

The 13 routes have decisions. Eleven yield eligible additions; two retain
specific scientific holds. These decisions complete this review queue. Wider
R11 follow-ups and earlier permission, thermal and phase holds remain open.

## Route checklist

A checked entry means its source decision is documented and eligible additions
are applied. Each unresolved scientific requirement remains unchecked below.

- [x] **4, RaSO4** — Open NBS G/H/S and original Langmuir–Riese solubility-based G estimate.
- [x] **23, RaCO3** — Original crystalline-endmember solubility estimate, G only; structure unspecified.
- [x] **69, S(2−)** — Own NEA1992/2003 G evaluations and local reaction/reference alternative; NBS observations retained.
- [x] **79, pyrochroite** — Existing Bricker G linked; local H/S from Nagra's own supplemental thermal estimate.
- [x] **157, HIO3(aq)** — Own NEA1992/2003 G evaluations and local reaction/reference alternative; existing H/S retained.
- [x] **257, NbO2(+)** — Existing finite-I ancestry linked; standard-state conversion held.
- [x] **325, Nb2O5(cr)** — Open NBS high-temperature-form G/H/S; native reaction remains qualified by its I = 1 aqueous basis.
- [x] **363, AlF6(3−)** — Local G from authors' own SIT/trend estimates, with explicit fluoride activity.
- [x] **371, RaOH(+)** — Both original Langmuir–Riese and later Nagra trend models retained as local G/H/S estimates.
- [x] **377, AlF5(2−)** — Local G from authors' own SIT/trend estimates, with explicit fluoride activity.
- [x] **383, witherite** — Existing USGS triplet linked; local G/H/S alternatives from Nagra's own refit.
- [x] **386, Rds-Syn** — Less-stable synthetic MnCO3 phase requires original specimen evidence; separate crystalline SIT alternative added.
- [x] **413, CN(−)** — Own NEA2005 CN/HCN G/H/S and open NBS alternatives; explicit N2 reservoir.

## Sources and reuse

**Open NBS release.** The previously reviewed, explicitly open non-SRD
[NIST PDR M32124 digitization with errata](https://doi.org/10.18434/M32124),
`NBS_Tables_with_ErratumValues.csv`, SHA256
`cb8a8b8b94a287e6e8c82eed8bad2cf9b611d574d1cfd95c8528d318dfef4b44`,
supplies G/H/S for Ra(cr), Ra(2+), RaSO4(cr), high-temperature Nb2O5(cr), CN(−)
and HCN(aq). One-based logical records, including both headers, are
**10244, 10248, 10254, 6881, 1949 and 1957**. Columns 9/8/11 contain G/H/S;
G/H in kJ/mol are multiplied by 1000. All six new cells' formula, physical state
and source form were checked directly. OH(−) record **35** and liquid water
record **41** anchor local cycles. Water S is **69.91 J/(mol K)**.
The release specifies 298.15 K and 0.1 MPa = 1 bar and supplies no numerical
interval for these cells. NIST is acknowledged under its
[open licence](https://www.nist.gov/open/license); data are distributed without
warranty. The completed release review carries forward.

**NEA's own composite evaluations.**
[Grenthe et al. (1992), *Chemical Thermodynamics of Uranium*](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/uranium.pdf),
Table IV.1, printed p. 67 / PDF p. 85, gives S(2−) G = **120.695 ± 11.610 kJ/mol**
and HIO3(aq) G = **−130.836 ± 0.797 kJ/mol**. Sections VI.1.4.1 and VI.2.1.2,
pp. 373/375, explain the own composite evaluations: averaged iodate protonation
log K **0.788 ± 0.029**, and best-estimate HS(−) dissociation log K **−19 ± 2**.
NEA explicitly declines to select iodic-acid reaction enthalpy.
[Guillaumont et al. (2003)](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/update_on_the_chemical_thermodynamics_of_uranium_neptunium_plutonium_americium_and_technetium_volume_5.pdf),
Table 8-1, pp. 137–138 / PDF pp. 177–178, retains these evaluations.
The editions share one evaluation. The carried official 2005 errata contain
no correction to these cells.

[Olin et al. (2005), *Chemical Thermodynamics of Selenium*](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/chemical_thermodynamics_of_selenium_volume_7.pdf),
Table IV-1 p. 75 / PDF p. 116, explicitly marks CN/HCN results as “This review”.
Its own gas/aqueous partition evaluation and cyanide protonation selection are
explained on pp. 433–436 / PDF pp. 474–477. The selected values are:

| Ion | G, kJ/mol | H, kJ/mol | S, J/(mol K) |
| --- | ---: | ---: | ---: |
| CN(−) | 166.939 ± 2.519 | 147.350 ± 3.541 | 101.182 ± 8.475 |
| HCN(aq) | 114.368 ± 2.517 | 103.750 ± 3.536 | 131.271 ± 8.440 |

The exact table values take precedence over rounded discussion values.
The source reaction gives protonation log K **9.21 ± 0.02** and
H **−43.60 ± 0.20 kJ/mol**. Open NBS G/H/S alternatives are respectively
**172.4/150.6/94.1** and **119.7/107.1/124.7**, with G/H in kJ/mol.
The carried official selenium errata contain no correction to these cells.
These are own NEA composite results; separately copied underlying tables are
outside this reuse decision.

OECD and the OECD Nuclear Energy Agency are acknowledged through those
volume citations. Reuse follows written clarification
**NEA-TDB-OECD-2026-10-14** and the
[OECD data terms](https://www.oecd.org/en/about/terms-conditions.html).
Every sublicense of work using these data must include the same acknowledgment
requirement and require further sublicensees to do the same. Source-specific
restrictions were checked for these numerical evaluations. Full publications,
permission correspondence and applicable-terms evidence remain external, with
the established permission hashes preserved in database metadata.

**Original numerical facts and local estimates.**
[Hummel and Thoenen (2023), Nagra NTB21-03](https://media.nagra.ch/uploads/2023/05/NTB-21-03.pdf)
retains copyright and reproduction/storage restrictions. The carried
R11g/R11h/R11j isolated-original-numerical-facts review applies to this batch's
newly verified authors' own regression and analogy outputs. This route is
separate from an open licence for the report. Local estimates retain source
ancestry, equations and exact reference observations. Complete tables,
figures, prose and database exports are excluded from the release.

The admitted own outputs are:

- Witherite, p. 217 / PDF p. 275: own refit of Busenberg–Plummer measurements,
  dissolution log K **−8.57 ± 0.03**, H **3.3 ± 0.4 kJ/mol**. Reaction Cp
  **−508 ± 10 J/(mol K)** remains metadata; the calculation model is unchanged.
- RaOH(+), pp. 232–233 / PDF pp. 290–291: own unweighted hydrolysis trend,
  log K **−13.7 ± 0.4**, H **62 ± 14 kJ/mol**. The source's unrounded and weighted
  model outputs remain in observation metadata.
- AlF5/AlF6, pp. 262–263 / PDF pp. 320–321: own SIT analysis with stepwise log K
  **7.08, 5.65, 4.05, 2.51, 1.0, 0**, giving cumulative **20.29** for both.
  The fifth/sixth steps use two/one points and a trend estimate. G alternatives
  use retained Al(3+) and F(−) references. Reaction widths remain separately
  documented; H/S require an original thermal-source follow-up.
- Pyrochroite, pp. 558–559 / PDF pp. 616–617: own analogy-model thermal mean
  **−123 ± 17 kJ/mol** for acid dissolution. Supporting H outputs
  **−122.5, −111.5, −137 and −121.4 kJ/mol** and their assigned intervals remain
  in metadata. Local formation H uses retained Mn(2+)/water anchors; local S
  additionally uses existing Bricker G. S is a derived estimate. The reported
  dissolution/formation sign distinction is explicit.
- Crystalline rhodochrosite, pp. 568–569 / PDF pp. 626–627: own SIT extrapolation
  of Néher-Neumann's finite-I result to dissolution log K **−10.80 ± 0.17**.
  This adds a local G alternative to the crystalline record. The native
  less-stable synthetic solid retains its separate phase hold.

[Langmuir and Riese (1985), pp. 1593–1601](https://doi.org/10.1016/0016-7037(85)90264-9)
has an original publisher abstract that directly supplies the 25 °C / 1 bar
RaSO4/RaCO3 solubility constants **−10.26/−8.3**, and RaOH association
log K **0.5**, H **1.1 kcal/mol**. These original isolated numerical facts
support local estimates on checked open reference values. The complete article
has no open-licence claim. Original solid-dissociation H sign issues remain
held; the RaOH association estimate is retained separately.

Local formation intervals remain NULL because anchor uncertainty/covariance is
unavailable. Source reaction intervals are retained without invented independent
quadrature. Model alternatives and original source editions share ancestry.

## Reference alignment and scientific effects

The unchanged policy remains **b2ad235bba62**, with 46 overrides and 10 exclusions.
Its recommendation fingerprint becomes **f7f7744cf2d903c3**.
Own NEA class-A G replaces the selected NBS G for S(2−) and HIO3. Earlier
observations and their H/S values remain, so mixed-source thermal routes are
explicitly qualified. Every other existing preferred observation ID is preserved.

Free sulfide G changes **85800 → 120695 J/mol**; free cyanide G changes
**172400 → 166939 J/mol**, aligning each fixed component with its selected ion.
`R11l_reference_history` preserves complete old pins, source information,
affected species and the activity offsets that restore their previous chemical
potentials. Complex formation observations stay intact. Source-specific sulfide
Ksp/dissociation conventions remain explicit; their raw constants are not
silently reinterpreted. The fixed free-component model is separate from a
closed total-ligand or protonation calculation.

CN/HCN are stored per full physical formula with carbon as the primary element
and **0.5 N2(g)** as an explicitly enabled reservoir. Their electron coefficient
is **−1**; proton coefficients are **0/−1**. The formal carbon oxidation state
+2 is distinct from this electron balance relative to C(cr) + 0.5 N2(g).
Their default carbon diagram is unchanged. Nitrogen fugacity is a specified
external condition; this representation does not introduce total-N conservation.

RaCO3/RaSO4 require their carbonate/sulfate buffers. RaOH is an empirical
estimate. NBS high-temperature Nb2O5 retains its full two-Nb formula,
normalization and physical phase label; it is distinct from B-Nb2O5.
New crystalline phases have unresolved structure records, with no guessed
space group or Materials Project phase assignment.

Staging checks preserve every previous SQL row except two documented reference
pins and the documented Ra coverage update. Reapplying the package is
idempotent. Formula/charge/electron checks pass. All 74 previous default maps
were compared on an 81 × 91 grid: iodine changes 24 cells and sulfur 183;
uncertainty masks change 48/164 cells. The other 72 maps/masks remain.
Equivalent free chemical potentials restore all checked sulfide/cyanide
buffered maps, masks and inventories. **36** supported metal-balance scenarios
pass, including ideal and Davies activity models. Thermal checks at
323.15/373.15 K use the existing qualified approximation.

## Separate unfinished requirements

- [ ] **R11l1 — NbO2(+):** resolve I = 1 mol/kg versus infinite dilution and
  hydration before a standard-state formation value is added. Nagra p. 654
  confirms the native constants inherit the finite-I NBS basis. Modern
  Peiffert2010 DOI10.1007/s10953-010-9495-z uses B-Nb2O5; its phase cannot be
  replaced by NBS's high-temperature form.
- [ ] **R11l2 — Rds-Syn:** reconcile the native Nordstrom1990
  re-expression with the original Garrels1960 specimen and pressure basis.
  The [original paper](https://doi.org/10.2475/ajs.258.6.402), retrieved privately,
  distinguishes a broad-XRD fine precipitate, better-crystallized salt-bridge
  material, and natural samples containing about 5 mol% other cations
  (p. 409 / PDF p. 8). Its experiment and formation-G calculation use 1 atm.
  The native value needs a supported specimen mapping and 1 bar reconciliation.
  Nagra2002 p. 188 distinguishes it from the crystalline route.
- [ ] **R11l3 — modern Ra fits:** obtain the original numerical basis and finish
  source-specific review of Brown/Ekberg/Matyskin2019,
  DOI10.1016/j.gca.2019.04.009. The Chalmers record provides metadata.
- [ ] **R11l4 — experimental Ra carbonate:**
  [Matyskin et al. (2023)](https://doi.org/10.1021/acs.inorgchem.3c01513) has a
  verified CC-BY4.0 licence. Its Ra(Ba)CO3/Ba(Ra)CO3 sample and 25.1 °C
  measurement conditions need a supported pure-RaCO3, 298.15 K interpretation.
  This is a scientific hold.
- [ ] **R11l5 — Ra solid H:** verify the original signed dissociation enthalpies
  or an authoritative correction before adding thermal values. Original G
  estimates remain eligible.
- [ ] **R11l6 — higher AlF thermal values:** verify original Latimer–Jolly1953
  calorimetric cells, cumulative versus stepwise convention, finite-I treatment
  and reuse route before deriving H/S.

Historical requests remain **116/131** covered: NEA **28/28**, NIST **88/103**.
The six original crystalline-G gaps remain. All earlier source reviews and
separate holds carry forward. The wider R11 parent remains open.
