# R11c: metal-bearing selenium observations

The 16 October 2026 R11c checkpoint adds **28 observations and 14 species**,
filling 28 properties. Every earlier reported observation and preferred value
ID remains. The unchanged policy selects the new observations for their
previously absent species. Two free-ligand references are added; the existing
selenite reference now follows the preferred NEA observation.

The database contains **1,025 species / 3,247 observations / 74 systems**,
with selected G/S/H counts **902/812/696**. Policy fingerprint:
`d7d53842a14a`; recommendation fingerprint: `5aeea70ce34752d6`.

## Source and reuse decisions

Olin, Å., Noläng, B., Osadchii, E. G., Öhman, L.-O. and Rosén, E. (2005),
*Chemical Thermodynamics of Selenium*, OECD Nuclear Energy Agency,
Chemical Thermodynamics Series, volume 7,
[official publication](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/chemical_thermodynamics_of_selenium_volume_7.pdf),
accessed 16 October 2026. Source SHA-256:
`2179ecdc4d5b16029d67c26f792a72fd055570da16c97e43cd24be68797989e3`.

The admitted observations comprise:

| Route | Observations | Source location and qualification |
| --- | ---: | --- |
| NEA selected formation properties | 21 | Table III-1, pp. 48/50; source phase and estimation qualifications retained |
| NEA additional formation evaluations | 6 | Table E-1, pp. 641/644; auxiliary data did not receive TDB critical review |
| Local FeSeO3+ formation-G estimate | 1 | Table III-2, p. 59, with existing eligible NEA Fe3+ and selenite inputs |

The Appendix E observations are NEA's evaluated results. Its introduction,
p. 639, explicitly distinguishes their scientific review status from the
selected formation set. Their database status is `source_verified_estimate`.
The recorded OECD permission review covers these NEA-authored evaluated data;
no additional reuse restriction was identified for these cells. The six
observations comprise MnSeO3·2H2O G/H/S, MnSeO4(aq) G, and CaSeO3·H2O H/S.
No independent auxiliary table is imported. Original experimental ancestry
and the auxiliary-data limitation remain in every observation's provenance.

The written NEA-TDB clarification and OECD data terms permit use, adaptation
and redistribution, including commercially, with appropriate OECD citation
and source-specific restrictions checks. Every sublicense of work using
these data must include the same OECD acknowledgment requirement and require
further sublicensees to pass it on. The metadata key
`source_permission_NEA_TDB_Se_R11c` preserves the permission evidence hashes
and this batch's scope. Private correspondence, publications, source page
images and independently copied auxiliary tables remain external.
See [the source instructions](nea-tdb-reuse.md) and
[distributed notices](../../THIRD_PARTY_NOTICES.md).

The [November 2005 errata](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/errata_selenium_volume_7_2020-09-02_11-47-23_191.pdf)
were checked, carrying forward the original release review. The CdSeO4(aq)
reaction correction applies to a different species; none of this batch's
cells changes. Other sources retain their existing permission status.

## Identities, conditions and missing properties

The finite inventory covers two nickel selenocyanates; Ca/Mg/Mn/Ni aqueous
selenates; FeSeO3+; Mg/Ni/Ca/Mn selenite hydrates; BaSeO4; and Ba/Sr selenites.
Full formula units, charge and hydration are preserved. Formation G/H use
J/mol and S uses J/(mol K), at 298.15 K / 1 bar and infinite dilution for
aqueous species. Source total uncertainty intervals retain their original
95%-type interpretation and widths. Exact cells and conversions accompany
every observation.

NEA assumes the hydrate identity of several legacy solubility specimens.
Nickel dihydrate calorimetry distinguishes crystalline and amorphous products;
the retained values describe the crystalline phase. Calcium monohydrate H/S
follow a source reassignment of a formerly labelled dihydrate. Strontium's
anhydrous assignment retains its analytical qualification. No space group or
structure match is inferred. MgSeO4(aq) retains the source's provisional
selection of a cited thesis result that the reviewers could not verify.

Selected reaction enthalpies and entropies are separate from formation
properties. The source rejects the proposed Ni/Mn aqueous-selenate reaction
enthalpies and accepts no free SeCN formation H/S. These species therefore
keep G only. The source's uncertain nickel 1:3 selenocyanate remains outside
this finite two-complex admission.

## Free references and the iron calculation

The new free references are SeO4²−, G = **−439,485 J/mol**, from the retained
preferred NEA7 observation, and SeCN−, G = **136,051 ± 3,800 J/mol**, from
Table III-1 p. 44. The reference table has no uncertainty column; the SeCN
interval and exact locator are retained in
`metadata.R11c_selenium_reference_history` and the external import ledger.

The existing `selenite-seo3` reference changes from **−369,800** to
**−362,392 J/mol**, matching the policy-selected NEA7 SeO3²− observation.
The earlier NBS observation, source and complete former reference row remain
stored. This is the single documented reference-row update. All earlier
reported observations, species, sources and warnings are preserved.
The existing zirconium selenite remains H-only, and its Gibbs-calculation
exclusion is preserved. Unrelated ligand references retain their values.

The FeSeO3+ estimate uses the selected reaction
`Fe3+ + SeO3(2-) = FeSeO3+`, with ΔrG = −63,645 J/mol:

`Gf(FeSeO3+) = −16,226 − 362,392 − 63,645 = −442,263 J/mol`.

The Fe3+ input is the retained Lemire et al. (2013) NEA13a observation; the
selenite input is the retained Olin et al. (2005) observation. All input IDs,
source intervals and the equation are recorded in
`metadata.source_reuse_R11c_FeSeO3_derived`. NEA p. 330 assumes the original
296 K equilibrium valid at standard conditions; the local estimate retains
that approximation. Total uncertainty remains NULL because shared covariance
is unavailable. No formation H/S or new thermal conversion is inferred.

## Calculation checks and limits

Ligand atoms are removed once from core O/H, leaving exactly the hydrate
waters. The balanced electron coefficient is 2 per divalent metal and 3 for
Fe(III), with no residual proton coefficient. Source formation observations
are preserved even where independently selected runtime cation/water
references differ from NEA's auxiliary set. The 14 reaction checks quantify
these differences; the largest is about **0.765 log10K**, for SrSeO3.
This mixed-reference limitation is exposed in the species warnings.

Six complete triplets reconstruct within 0.51 J/mol using the source's
elemental entropy choices. Using the current older Sr entropy instead gives
about a 1.014 kJ/mol difference. The Appendix E manganese triplet retains a
140.8 J/mol mixed-reference/precision residual, within its 6,700 J/mol G
interval. These are external consistency diagnostics; source observations
retain their reported values and no auxiliary table is copied into release.

All **74 default maps and uncertainty masks** and **118 existing zirconium
buffered scenarios** remain unchanged. **42 new buffered scenarios** and
**84 ideal/Davies primary-metal inventories** pass. Full-formula reaction
and ligand-activity responses are checked. Existing selenium gas/temperature
scopes and all earlier preferred IDs are preserved. The current temperature
extension excludes buffered species away from 298.15 K.

These calculations prescribe free selenium-ligand activities. Closed balances
conserve the primary metal; total Se inventories and coupled protonation need
their own model. Concurrent GUI implementation is untouched.

## Checklist and next work

- [x] Verify all 14 source routes, complete formulas and source qualifications.
- [x] Retain 21 selected observations, six qualified NEA additional evaluations
  and one documented local estimate through validated staging.
- [x] Add two free references and preserve the old selenite reference/evidence.
- [x] Check all previous selections, default maps and buffered calculations.
- [x] **R11d:** Review eight independent PSI nickel routes; retain two
  hydrosulfide formation-G estimates with verified inputs and keep six
  ammonia routes on original-source holds. See [the review](psi-nickel-hydrosulfides.md).
- [ ] Continue the carried Zr, other-original-source and unsupported-system
  routes. Wider R11 remains open.

The original 28 NEA requests remain covered. Historical coverage stays
**116/131: NEA 28/28 and NIST 88/103**; the six original crystalline Gibbs
gaps remain. Zirconium hydride, calcium identity, gas-accuracy and the three
temperature-conversion holds retain their separate reviews. The 20 routed
PSI selenium products now have original-source formation coverage, including
the qualified additions and local adaptation described here. Native PSI
versions and extrapolation functions retain their own review decisions.

The full candidate/import package, source images, reference history, derivation,
reaction diagnostics, 42 scenarios and validation reports are saved in the
external `reaktoro-dataset-review/r11c-metal-selenium` checkpoint.
