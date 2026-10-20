# R11k: two pyrophosphate source routes

Reviewed 20 October 2026. Both PSI/Nagra routes are reconciled with their
original NEA evaluations and the explicitly open NBS digitization. The batch
adds **12 observations and two aqueous phosphorus species**, fills six
properties, and aligns the existing free-pyrophosphate reference with its
policy-selected ion value. All earlier observations and preferred IDs remain.

| Native route | Full reaction | Source combination |
| --- | --- | --- |
| 121, P2O7(4−), log K −3.39 | 2 HPO4(2−) = P2O7(4−) + H2O | −3.386, rounded to −3.39 |
| 247, HP2O7(3−), log K 6.01 | 2 HPO4(2−) + H+ = HP2O7(3−) + H2O | 6.014, rounded to 6.01 |

Each ion retains four G observations: NEA1992, its retained NEA2003 evaluation,
the open NBS evaluation, and a local NEA-reaction adaptation using current
NBS monomer/water references. NBS also supplies H and S. The NEA editions
share one evaluation; native rounding and the later PSI representation are
identified as the same reaction route.

## Original sources and reuse

[Grenthe et al. (1992), *Chemical Thermodynamics of Uranium*, OECD2004 reprint](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/uranium.pdf)
provides exact formation G in Table IV.1, printed pp. 69–70 / PDF pp. 87–88.
Its original evaluation is explained in section VI.3.2, pp. 386–389 /
PDF pp. 404–407. NEA calculates composite formation values from its selected
phosphoric-acid basis, dimerization reaction and averaged dissociation constants.
NBS and Perrin are scientific ancestry. The retained numbers are NEA's own
composite evaluations, with explicit uncertainty assignments.

[Guillaumont et al. (2003), *Update on the Chemical Thermodynamics of Uranium, Neptunium, Plutonium, Americium and Technetium*](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/update_on_the_chemical_thermodynamics_of_uranium_neptunium_plutonium_americium_and_technetium_volume_5.pdf)
retains both G values in Table 8-1, pp. 139–140 / PDF pp. 179–180.
Table 8-2, pp. 151–152 / PDF pp. 191–192 retains the reaction constants.
The [official November2005 errata](https://www.oecd-nea.org/dbtdb/pubs/Errata_Update.pdf)
contain no correction to these cells or reactions. The later 2020 auxiliary
review remains the separately tracked R11j3 follow-up. Editions are explicit;
this batch makes no claim of complete coverage of every later NEA volume.

NEA data reuse follows **NEA-TDB-OECD-2026-10-14** and the
[OECD data terms](https://www.oecd.org/en/about/terms-conditions.html).
OECD and NEA are acknowledged through the volume citations. Every sublicense
of work using these data must include the same acknowledgment requirement
and require further sublicensees to do the same. No additional third-party
restriction was identified on these NEA-authored composite evaluations.
Separate restrictions on independently copied tables remain applicable.
Complete publications and private permission correspondence stay external.

The NBS observations use the previously reviewed, explicitly open non-SRD
[NIST PDR M32124 release](https://doi.org/10.18434/M32124),
`NBS_Tables_with_ErratumValues.csv`, SHA256
`cb8a8b8b94a287e6e8c82eed8bad2cf9b611d574d1cfd95c8528d318dfef4b44`.
Logical records **1281 and 1357**, including both header records, identify
P2O7(4−) and HP2O7(3−), state `ao`. G/H/S occupy one-based columns 9/8/11.
G and H are multiplied by 1000; S retains J/(mol K). The header specifies
298.15 K and 0.1 MPa = 1 bar. These cells supply no numerical intervals.
NIST is acknowledged under its [open licence](https://www.nist.gov/open/license),
and the data are distributed without warranty. This release's completed
source/licence review is carried forward; each new cell was checked directly.

## Values, selections and reaction bases

| Ion | Preferred NEA2003 G, kJ/mol | NBS G, kJ/mol | NBS H, kJ/mol | NBS S, J/(mol K) |
| --- | ---: | ---: | ---: | ---: |
| P2O7(4−) | −1935.503 ± 4.563 | −1919.0 | −2271.1 | −117 |
| HP2O7(3−) | −1989.158 ± 4.482 | −1972.2 | −2274.8 | 46 |

The unchanged policy selects class-A NEA2003 G and class-B NBS H/S. The
published NEA intervals retain their source convention. These preferred
properties form a mixed-source set; NEA supplies no charged-ion H/S here.
No observation is adjusted to force thermodynamic closure.

The local G alternatives use

`G(pyrophosphate) = 2 G(HPO4) − G(water) − RT ln(10) log K`.

The monomer G is the retained NBS −1089150 J/mol, and water G is −237129 J/mol.
The source combination uses dimerization log K −2.79, twice the monomer
protonation constants 7.212 and 2.14, and pyrophosphate dissociation constants
−1.0, −2.25 and −6.65; the P2O7 route also adds −9.40. Component intervals
and exact inputs are retained. Shared inputs/covariance prevent a supported
total G interval for the local alternatives, which remain estimates with NULL
uncertainty. The PSI2014 update Table12, printed/PDF p. 34, reports native
rounded values with widths 0.97/0.96. That inherited re-expression is recorded
in the crosswalk, with its original NEA ancestry.

For ionic formation-entropy diagnostics, the conventional H+ reference requires

`ΔfS = S(ion) − nP SP − nO SO2/2 − (nH − charge) SH2/2`.

The retained NBS triplets give cycle residuals about −709 and +193 J/mol.
Combining preferred NEA G with NBS H/S gives residuals about +15794 and
+17151 J/mol. Source covariance is unavailable; these residuals are documented
without a rounding-only explanation. The existing temperature model uses
its explicitly labelled H/G fallback from two sources. Checks at 323.15 and
373.15 K verify that behavior without introducing a new thermal model or Cp.

## Free reference and scientific effects

The free P2O7(4−) reference changes from NBS **−1919000** to preferred NEA
**−1935503 J/mol**. Metadata `R11k_pyrophosphate_reference_history` preserves
the complete previous reference, source and new preferred observation ID.
The old NBS G becomes an explicit species observation alongside the new
alternatives. The preferred ion's ±4563 J/mol interval is preserved there;
the ligand table has no uncertainty column.

Three existing species use this reference: NiP2O7(2−), HNiP2O7(−), and
ZrP2O7(cr). Their formation observations are unchanged. The preferred nickel
association constants now reconstruct as **8.7300135** and **14.5399197**,
matching NEA's 8.73 and 5.14 + 9.40 within tabulated precision. Earlier
warnings about a 2.891-unit reference offset remain as historical evidence;
new warnings identify the current aligned reference.

At fixed numerical free activity, each affected complex's transformed energy
increases by **16503 J/mol**. Adding **2.8912005** to log10 free activity restores
the old chemical potential and the previous diagrams, uncertainty masks and
checked metal inventories. A prescribed free activity is an external reservoir;
no total-phosphorus inventory or automatic acid-base equilibration is implied.

Both new ions contain two P atoms. Energies normalize per P, with five
electrons per P and proton coefficients 7/6.5. Full-formula atoms and charges
balance in the condensation reactions. The existing closed-balance filter
excludes both polynuclear aqueous ions. All 74 default maps/masks remain.
Six buffered scenarios cover Ni/Zr; optional nickel maps change at fixed
activity, while the sampled zirconium maps remain. Thirteen supported metal
balances conserve the primary inventory.

The dataset contains **1045 species / 3325 observations**, with selected
G/S/H **922/819/703**, 29 ligand references and 74 systems. The policy retains
46 overrides/10 exclusions; fingerprint `b2ad235bba62`, recommendation
`f8245c4acb14f88a`. Historical request coverage stays **116/131**
(NEA28/28, NIST88/103), and six original crystalline G gaps remain.
Thirteen further R11 original routes and all earlier source/chemistry holds
stay open. The next finite batch is the three radium routes.
