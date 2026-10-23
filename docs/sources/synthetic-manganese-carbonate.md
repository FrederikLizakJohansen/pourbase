# R11m: synthetic manganese carbonate

Reviewed 20 October 2026. This follow-up adds **two observations and one
precipitated MnCO3 record**, making G and H available for that material category.
The database now retains **1,056 species and 3,373 observations**, with
**933/827/712 preferred G/S/H properties** across 75 systems. All earlier
observations, preferred IDs, component references and selection rules remain.

## Completed review

- [x] Verify the original precipitated-material identity and numerical G cell.
- [x] Resolve the original G pressure basis using an explicit standard-state conversion.
- [x] Verify the openly released NBS precipitated-material H cell.
- [x] Preserve the original values, source conditions and independent source identities.
- [x] Validate formula/charge, reference conversion, diagrams and supported balances.
- [x] Apply the eligible observations and preserve the later native-variant follow-up.

## Original material and Gibbs estimate

[Garrels, Thompson and Siever (1960), *Stability of some carbonates at 25 degrees C and one atmosphere total pressure*](https://doi.org/10.2475/ajs.258.6.402),
American Journal of Science 258, 402–418, reports **−194.7 kcal/mol** for
“Rhodochrosite, synthetic pptd.” in the opening table, printed p. 402 / PDF p. 1,
**This work** column. Printed p. 409 / PDF p. 8 identifies reagent-grade
precipitated MnCO3 with broad XRD reflections matching rhodochrosite.
It distinguishes this material from natural samples containing about 5 mol%
other cations and from better-crystallized material grown in a salt bridge.
The latter receives its own specimen discussion; its value is not substituted.

The experiments approach equilibrium from undersaturation. Source pH/time
extrapolation and incomplete equilibration limit the result. The admitted G
therefore retains **`source_verified_estimate`**, class E, with NULL numerical
uncertainty. The printed 0.1 kcal/mol precision remains explicit. Computed
digits from conversion do not add experimental precision.

Source p. 402 and the formation-G calculation on p. 413 / PDF p. 13 establish
the 25 °C, 1-atmosphere basis and kcal convention. The downloaded publisher PDF
places printed pp. 413 and 414 out of order; locators identify printed and PDF
pages separately. The complete PDF SHA256 is
`53b228b0a48a9a26d5f159505911b27a65613b1b4be288efa53ed57a6cff8b83`.

Reuse follows the project's established **individual original numerical-facts
policy**, carried from R11g/R11l. The article itself has no asserted open
licence. The release contains the individually cited original number, its local
adaptation and scientific limitations. Full article, tables, prose, figures
and OCR remain external. This source route is distinct from the explicit open
licence covering the NBS digitization below.

## Standard-state pressure conversion

[Grenthe et al. (1992), *Chemical Thermodynamics of Uranium*](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/uranium.pdf),
section II.3.2, pp. 24–27 / PDF pp. 42–45, gives the pressure prescription.
Equation **II.38**, p. 26 / PDF p. 44, applies the gas-reference correction to
formation Gibbs energy:

`Gf(1 bar) − Gf(1 atm) = −δgas RT ln(1.01325)`.

For `Mn(cr) + C(graphite) + 1.5 O2(g) = MnCO3(precipitated)`,
`δgas = −1.5`. Using 298.15 K and runtime R = 8.31446261815324 J/(mol K):

- Original G: `−194.7 × 4184 = −814624.8 J/mol`.
- Reference-pressure correction: **+48.9457169698 J/mol**.
- Adapted G: **−814575.8542830301 J/mol**, stored at 1 bar.

The conversion uses the cited ideal-gas reference approximation and neglects
condensed-phase pressure effects. The source's experimental and equilibration
limitations remain. The raw value, kcal conversion, original pressure,
formation reaction and correction are retained in the observation locator and
metadata. These are two representations of one evaluation; they do not count
as independent measurements. No new numerical interval is invented.

OECD and the OECD Nuclear Energy Agency are acknowledged through the pressure
method citation. The carried written clarification **NEA-TDB-OECD-2026-10-14**
and [OECD data terms](https://www.oecd.org/en/about/terms-conditions.html)
remain recorded. Every sublicense of work using these data must include the
same acknowledgment requirement and require further sublicensees to do the same.
Complete publications and permission correspondence stay external.

## Open NBS enthalpy and phase scope

The carried, explicitly open non-SRD
[NIST PDR M32124 release](https://doi.org/10.18434/M32124),
`NBS_Tables_with_ErratumValues.csv`, SHA256
`cb8a8b8b94a287e6e8c82eed8bad2cf9b611d574d1cfd95c8528d318dfef4b44`,
has **−883.2 kJ/mol** formation H for MnCO3, material **precipitated**, state
**cr2**, in one-based logical record **6408**, including both headers,
column **8**. Its G and S cells are missing. The value becomes **−883200 J/mol**
at the release's 298.15 K / 0.1 MPa = 1 bar conditions, class B, with NULL
numerical uncertainty. NIST is acknowledged under its
[open licence](https://www.nist.gov/open/license); the data are provided without
warranty. Completed release/licence review carries forward; the new row was
checked directly.

The record `r11m-mn-mnco3-precipitated` represents nominal precipitated MnCO3,
separate from `r07-mn-mnco3-rhodochrosite`. The two source observations describe
independently evaluated preparations. Their exact grain sizes, surface state
and specimen equivalence are unreported. The phase record retains
`phase_identity_incomplete`, the reported rhodochrosite structure of the
Garrels sample and source-specific crystallinity. It assigns no space group.

Preferred G and H form a mixed-source set. The batch supplies no coherent
joint thermal fit, S, Cp, or zero dissolution enthalpy. The existing temperature
model continues to exclude explicit ligand species away from 298.15 K.

## Scientific checks

All previous SQL rows and preferred observation IDs are preserved. Repeated
application is idempotent. Schema 9, selection policy **b2ad235bba62**, its
46 overrides and 10 exclusions, 75 systems and 29 component references remain.
The recommendation fingerprint becomes **416612a99dc16a8d**.

The new phase has one Mn atom, one carbonate component, charge zero,
electron coefficient 2 and proton coefficient zero. Explicit free-carbonate
activity is required. Its transformed G remains **4524.14571697 J/mol** above
the existing crystalline phase at every checked pH, potential and carbonate
activity. Thus it supplies a metastable competitor while leaving the selected
stable-phase maps unchanged.

Checks compare all **75 default maps and uncertainty masks** on 81 × 91 grids.
Three carbonate-enabled manganese scenarios at log free activity −6/−3/−1
preserve stable maps and 1σ masks. At 3σ, the −3/−1 scenarios gain
**4172/4738** uncertain cells. The source has no assigned G interval; these
bands use the calculation's explicitly identified **assumed 2000 J/mol**
uncertainty. That plotting assumption is separate from the stored NULL
source uncertainty.

**18** supported balance scenarios pass: full versus prior inventories and
restricted precipitate/ion balances, at three carbonate activities with ideal
and Davies activity models. Restricted metal/precipitate boundaries and
solubility agree with independent thermodynamic calculations. On current NBS
ion/component references, the admitted estimate gives dissolution
**log Ksp = −10.2778130024**. This is a reconstructed value on that reference
basis; it is distinct from the later native evaluation.

## Remaining native variant

- [ ] **R11m1 — strict specimen requirement:**
  [R11s](native-synthetic-manganese.md) resolves the original selected logK,
  source reference and native carbonate/bicarbonate re-expression, and adds
  one qualified nominal synthetic-material G alternative. Original1990
  Table2III,p406 and the retrieved USGS1991Table2p30,row190 agree.
  Exact specimen/surface matching remains R11s1; original full-resolution
  chapter retrieval remains the separate R11s2 evidence upgrade.
- [x] Original numerical-table and native reaction-reference reconciliation.
- [x] Preserve both earlier observations and add the supported G alternative.

The original-source identity and pressure parts of R11l2 are now resolved.
The later native reaction re-expression is reconciled in R11s. Exact specimen
mapping remains an open scientific follow-up.
The broader R11 task and other sources' permission/scientific holds remain
open. Historical requested-property coverage stays **116/131 = 88.5%**,
including all **28/28 NEA** targets. The main checklist retains **5/18 = 27.8%**
checked headline reviews; these tasks have unequal sizes and separately
tracked holds. This batch does not close one of the six historical crystalline-G
gaps.
