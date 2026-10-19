# R11f: seven tin source routes

Reviewed 19 October 2026. Seven PSI/Nagra reaction routes lead to seven new
observations: four historical formation-G alternatives on existing species and
one crystalline burtite G/H/S triplet. All previous rows and preferred values
remain. Three preferred properties become available for the new phase.

| Route | Result |
| --- | --- |
| SnO3(2−) | Original historical logK −18.4 ± 0.3 gives a local G alternative on existing full-formula Sn(OH)6(2−). |
| HSnO3(−) | Original historical logK −8.0 ± 0.3 gives a local G alternative on existing Sn(OH)5(−). |
| Sn3(OH)4(2+) | Original historical logK −5.6 ± 1.6 gives a local G alternative; large SIT-extrapolation qualification retained. |
| SnO2(am) | Original historical dissolution logK −7.3 ± 0.3 gives a local G alternative. |
| CaSn(OH)6(s) | New original crystalline burtite G/H/S admitted; historical fresh-precipitate branch remains separately held. |
| Sn(OH)Cl(aq) | Scientific hold: later NEA evaluation finds the available data insufficient for a reliable standard constant. |
| SnS | Scientific hold: native label conceals an inadequately characterized precipitate; no assignment to crystalline herzenbergite. |

The finite seven-route review is complete. The wider R11 queue remains open,
with 40 other-original-source reaction routes. Seven palladium routes form the
next bounded source review. The six ammonia source holds, two R11e nickel
holds, 28 prior solid holds and earlier zirconium thermal/scientific follow-ups
retain their individual histories.

## Sources and reuse basis

[Hummel et al. (2002), Nagra NTB02-16](https://media.nagra.ch/uploads/2022/08/e_ntb02-016.pdf)
provides the original critical evaluations on printed pp. 407, 409 and 415
(PDF pp. 431, 433 and 439). Four isolated original reaction results are used
under the project's established individual-original-numerical-facts policy.
Nagra reserves copyright in the report and its reproduction. The source PDF,
text, tables, figures, table arrangements and inherited absolute master-species
values remain external. This is a limited numerical-fact use, with attribution;
it does not assert a general open licence for Nagra's publication or database.

[Haase et al. (2021), Chemical Thermodynamics and Thermal Analysis 1–2,
100005](https://doi.org/10.1016/j.ctta.2021.100005) supplies three original
numerical results for one characterized mineral, Table 7, printed p. 8
(PDF p. 9 in the university-deposited version). **The article is CC BY-NC-ND
4.0.** The three factual results use the established isolated-original-facts
route; the article itself stays external under its own terms. No protected
article expression, table arrangement, bulk table extraction or separately
licensed auxiliary dataset is included. The
[Creative Commons FAQ](https://creativecommons.org/faq/) explains the
separate treatment of purely factual data and unprotected excerpts; the
[US Copyright Office facts guidance](https://www.copyright.gov/help/faq/faq-protect.html)
also explains that facts themselves receive no copyright protection. Source
hashes, rights snapshots and the scoped decision are recorded outside the
repository and summarized in `source_reuse_R11f_tin_original_results` metadata.
The article's licence is not presented as a GPL-compatible publication licence.

Existing NEA12 tin anchors use the carried written OECD permission and
source-specific reviews. OECD and NEA receive appropriate credit. Every
sublicense of work using the NEA data must include the same OECD acknowledgment
requirement and require further sublicensees to pass it on. The existing open
non-SRD NBS water and free-calcium reference reviews are carried forward with
NIST attribution. Other sources' permission holds remain separate. The NEA
permission does not license the Nagra or Haase publications.

## Arithmetic, identity and evidence status

At 298.15 K, local G estimates use R = 8.31446261815324 J/(mol K), the
retained project water G = −237129 J/mol, NEA Sn2+ G = −27390 J/mol and NEA
Sn(OH)4(aq) G = −944914 J/mol. Each full reaction, input observation ID,
original width, source page and resulting local G is retained in
`R11f_tin_derivations`. These four G observations are
`source_verified_estimate`; their total uncertainties remain NULL because
shared ancestry, covariance and width conventions do not justify combining
intervals. All four existing direct NEA G choices remain preferred.

Native SnO2(aq), HSnO3(−) and SnO3(2−) remove respectively two, two and three
waters from the physical full hydroxo formulas. Reaction normalization agrees
with the existing Sn(OH)4, Sn(OH)5 and Sn(OH)6 records. No duplicate oxyanion
record or inherited native master G is created. The trimer retains three Sn
atoms and the existing supported solver scope.

Burtite (`r11f-sn-casn-oh-6-burtite`) has nominal formula CaSn(OH)6, cubic
Pn-3, space-group number 201; source Table 1 gives a = 8.1508(1) Å. Table 6
corrects 0.59 excess adsorbed waters before calculating nominal phase properties.
These are not structural hydration waters. Stored values are:

| Property | Result | Evidence status |
| --- | --- | --- |
| Formation G | −1885800 ± 7600 J/mol | Source-derived estimate |
| Formation H | −2149900 ± 6900 J/mol | Original calorimetric evaluation, verified |
| Absolute S | 215.7 J/(mol K), total interval unspecified | Source estimate |

The published G/H widths retain their original meaning; no uniform standard
error convention is imposed. The published formation entropy is used only as
a rounded diagnostic, giving a G/H closure residual below 100 J/mol. Standard
properties are stored at 298.15 K and nominal standard pressure 1 bar. Complete
G/H/S does not enable a new thermal model: calcium reference scope still
excludes this ligand-bearing phase at 323.15 and 373.15 K.

The full formula has one calcium component, six core O, six core H, four
electrons and six protons per Sn. Free Ca2+ is an external reservoir. Runtime
acid-dissolution logK values are approximately 15.233 and 7.681 for the source's
reactions 23 and 24, consistent with its rounded 15.2 and 7.7. Precipitation
from retained Sn(OH)6 gives logK approximately 3.43. The historical fresh
precipitate's 9.7 differs by over six log units; kinetic treatment, drying and
phase identity remain a separate branch hold. These values are not averaged.
Phase boundaries depend on free calcium, primary-metal concentration and the
reference set; source qualitative environmental statements are conditional.

The Sn(OH)Cl hold follows NEA12 (2012), pp. 116–117, superseding confidence
in the older −3.1 estimate. The SnS precipitate hold follows Nagra p. 343:
possible hydroxide contamination, sulfide oxidation and incomplete phase
characterization prevent mapping its acid-dissolution result to the existing
crystalline herzenbergite G/H/S record.

## Verification and progress

- [x] Trace and decide all seven routes; retain three precise branch/source holds.
- [x] Stage and validate seven observations before applying them.
- [x] Preserve every prior SQL row, preferred value and selection policy.
- [x] Check four reaction reconstructions, two native-water identities and nine full-formula energies.
- [x] Preserve all 74 default diagrams and uncertainty masks.
- [x] Check nine buffered Ca/Cl/sulfide scenarios and 20 closed primary-tin balances.

Closed balances use explicit gas-free systems and the existing polynuclear
aqueous exclusion. They cover ideal and supported Davies models; calcium is
buffered externally. Two high-tin stress checks demonstrate precipitation at
0.05 M total Sn, free-Ca log activity −1, pH 13–14 and Eh 0.4–0.6 V.

The applied dataset contains **1,030 species, 3,267 observations, 1,730 source
records, 1,397 warnings and 577 phase records**. Selected G/S/H counts are
**907/816/700**. Policy `d7d53842a14a` retains 44 overrides and 10 exclusions;
recommendation fingerprint is `a5723f490434e69d`. Original-request coverage
remains 116/131 (NEA 28/28, NIST 88/103). The six original crystalline G gaps
remain separate. Tests, generated statistics, manuscript assets, packaged
notices and installed-distribution checks accompany this checkpoint.
