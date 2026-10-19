# R11g: seven palladium source routes

Reviewed 19 October 2026. This review adds **eight local Gibbs observations on
six new aqueous species**: four ammine complexes and two hydroxo complexes.
The hydroxo complexes each retain a historical alternative. Six preferred G
properties become available, alongside one neutral free-ammonia reference.
Every previous database row and preferred value remains.

| Original route | Decision |
| --- | --- |
| PdO2H(−) | Store full Pd(OH)3(−); retain original 2002 and revised 2023 local estimates. |
| PdCl2(OH)2(2−) | Hold: the original −7 is an upper bound, despite its scalar representation in the native dataset. |
| PdCl3OH(2−) | Hold: native 2.5 uses inherited JAEA SIT selections; independent original measurements need a compatible standard-state parent/reference route. |
| Pd(NH3)(2+) | Add qualified local G from original cumulative log beta 9.6. |
| Pd(NH3)2(2+) | Add qualified local G from original cumulative log beta 18.5. |
| Pd(NH3)3(2+) | Add qualified local G from original cumulative log beta 26.0. |
| Pd(NH3)4(2+) | Add qualified local G from original cumulative log beta 32.8. |

The adjacent neutral Pd(OH)2(aq) companion receives both historical and revised
G estimates so that the source's hydrolysis model retains its intermediate.
The old amorphous Pd(OH)2 solubility branch is separately held: the newer review
withdraws that interpretation of the experiments. The crystalline PdO2 gap
remains separate.

## Original sources and limited reuse basis

[Hummel et al. (2002), Nagra NTB02-16](https://media.nagra.ch/uploads/2022/08/e_ntb02-016.pdf),
printed pp. 244–245 (PDF 268–269), provides two original in-house hydrolysis
estimates: cumulative log beta −4 ± 1 for Pd(OH)2 and −15.5 ± 1 for Pd(OH)3.
These are qualified model estimates from a critical reappraisal of solubility
measurements. They are retained as historical observations.

[Hummel and Thoenen (2023), Nagra NTB21-03](https://media.nagra.ch/uploads/2023/05/NTB-21-03.pdf),
printed pp. 755 and 757 (PDF 813 and 815), provides substantively revised
original supplemental estimates −4.6 and −16.6. The later fit assumes metallic
Pd controls solubility and uses specified hydrogen fugacity. Printed p. 758
(PDF 816) concludes that the available experiments do not establish an
amorphous-hydroxide solubility constant. Source uncertainty in controlling
phase, redox conditions, colloids and fitted species remains explicit.
The equation on p. 757 and its figure establish the negative sign of −16.6;
the following prose drops that sign once. The equation is the numerical basis.

[Rasmussen and Jørgensen (1968), Acta Chemica Scandinavica 22, 2313–2323](https://doi.org/10.3891/acta.chem.scand.22-2313)
provides the four original spectrophotometric stepwise ammine results.
The [university-hosted original scan](https://actachemscand.ki.ku.dk/pdf/acta_vol_22_p2313-2323.pdf)
was checked visually at printed pp. 2313 and 2317 (PDF 1 and 5). Equation 3
gives log K = 9.6, 8.9, 7.5 and 6.8, each approximately ±0.1. Adding the
steps gives cumulative 9.6, 18.5, 26.0 and 32.8. The original approximate
step widths are retained separately; the later JAEA-assigned cumulative ±0.2
interval is outside this import.

These eight isolated original reaction facts use the project's established
**individual-original-numerical-facts route**. Nagra reserves copyright in both
reports, including reproduction and electronic storage of protected publication
material; Acta Chemica Scandinavica retains its archive copyright. Their
publications, expression, figures, table layouts, bulk tables and databases
remain external. This route does not assert a blanket open publication licence.
The carried [Creative Commons factual-data guidance](https://creativecommons.org/faq/)
and [US Copyright Office facts guidance](https://www.copyright.gov/help/faq/faq-protect.html)
support the distinction. New source hashes, publication rights, scope and
scientific qualifications are recorded in
`source_reuse_R11g_original_palladium` and the external checkpoint.

Open non-SRD NIST PDR [M32124](https://doi.org/10.18434/M32124) supplies the
existing Pd2+, water and NH3 anchors. NH3(aq), logical CSV record 861, has
G = −26.50 kJ/mol; Pd2+(aq), record 6050, has G = 176.5 kJ/mol. Values are
multiplied by 1000 and match the retained selected observations. The new neutral
`ammonia-nh3` ligand reference uses −26500 J/mol and cites that open release.
The [NIST open licence](https://www.nist.gov/open/license), attribution and
warranty qualification are carried forward. Existing OECD attribution and
requirements for further sublicensees remain in the distributed notices.
No new NEA or JAEA licence is inferred for these original-source routes.

## Local estimates, medium assumptions and selection

All eight G observations are `source_verified_estimate` at 298.15 K and nominal
standard pressure 1 bar, with NULL total uncertainty. The complete equations,
original reaction widths, source pages and input observation IDs are in
`R11g_palladium_derivations`. No H/S/Cp or new temperature model is inferred.

Hydrolysis uses G(complex) = G(Pd2+) + n G(water) − RT ln(10) log beta.
Native PdO2H(−) removes one water from physical Pd(OH)3(−); transforming the
native two-water reaction gives the same energy as the full three-water
reaction. The full trihydroxo species has charge −1, three O, three H, two
electrons and three protons per Pd. The neutral dihydroxo species has two of
each O/H, two electrons and two protons per Pd.

Ammine formation uses G(complex) = G(Pd2+) + n G(NH3) − RT ln(10) log beta.
The original experiments used ionic strength 1 M, mainly NaClO4, with the first
step determined in 1 M HClO4. Local adaptation assumes cancellation of a
charge-only correction between successive +2 complexes with neutral NH3.
Specific ion interactions remain unknown. These are qualified standard-reference
approximations; they are not measured zero-ionic-strength constants. Original
step covariance and reference-input intervals do not support a total G interval.
Solvent coordination waters are omitted; the diamine record represents the
measured solution ensemble with a possible cis preference. NH3 hydrogens belong
to the neutral ligand, leaving core O/H and proton coefficients zero, with two
electrons per Pd.

The 2023 hydrolysis changes are substantive revisions of the same authors'
earlier fit. The policy's original-publication tie-break otherwise prefers the
older publication as a repeat. **Two documented overrides** choose the 2023
local variants while preserving the 2002 alternatives. The Pd(OH)3 G difference
exceeds 5 kJ/mol and remains flagged for review. The policy has 46 overrides and
10 exclusions, fingerprint `b2ad235bba62`; recommendation fingerprint is
`49645568fbf6d060`. Every pre-existing policy entry and preferred observation ID
remains intact.

## Precise remaining holds

The mixed dihydroxochloride's native scalar −7 corresponds to an original
upper bound. It is retained externally as a bound. The trichlorohydroxide
point 2.5 combines JAEA-derived standard-state selections. Independent original
leads are [Elding (1972)](https://doi.org/10.1016/S0020-1693(00)91874-7)
(1 M perchloric acid) and [Byrne and Yao (2000)](https://doi.org/10.1016/S0016-7037(00)00501-9)
(0.5 M NaCl). Their original reported finite-medium constants cannot simply be
combined across these media. A separately verified compatible parent chloride
reference and original zero-ionic-strength evaluation are required. The newer
Nagra chloride re-evaluation is recorded as an independent future lead; its
additional constants and reaction enthalpies require their own complete package.

The historical amorphous solid branch remains a third, adjacent scientific
hold following the newer report's phase reinterpretation. Original NIST
request coverage stays **116/131 (NEA 28/28, NIST 88/103)**; the six original
crystalline G gaps and other sources' permission holds remain separate.

## Verification and next work

- [x] Decide all seven routes and document two primary holds plus the adjacent solid hold.
- [x] Stage and validate eight observations, six species and the open NH3 reference.
- [x] Preserve previous SQL rows and preferred IDs; review two new policy overrides.
- [x] Reconstruct eight reactions, native water normalization and 54 formula-energy checks.
- [x] Check all 74 default diagrams and uncertainty masks: each remains unchanged.
- [x] Check eight buffered scenarios and 16 ideal/Davies closed primary-Pd balances.
- [x] Preserve temperature scope and the crystalline PdO2 gap.

Balances use dilute total Pd = 10−7 M with externally buffered free NH3, and
chloride where specified. Closed systems use the supported gas-free subset.
They do not introduce a total nitrogen inventory or automatic ammonium
speciation. The reported free-ammonia activity is an independent input.

The database now contains **1,036 species and 3,275 observations**, with
**913/816/700 preferred G/S/H properties**, 1,737 source records, 1,403 warnings,
577 phase records and 28 ligand references. Statistics, manuscript numbers and
references, tests and packaged notices accompany this checkpoint. Concurrent
GUI implementation remains untouched.

The finite R11g review is complete. The wider queue contains **33 other-original-
source routes**. **R11h: six europium routes** is the next bounded review;
R11g chloride/solid follow-ups and prior tin, nickel, ammonia, solid and
zirconium holds retain separate entries in the running tracker.
