# Materials Project cobalt and hafnium source check

MP17 checked the sources on 19 October 2026 against revision `b052de2`.
MP17a applies the validated corrected cobalt observation on the same date,
preserving every earlier observation. The proposed hafnium upgrade retains its
source/reuse hold. The original manuscript text and paper follow-up list remain
with their authors; generated dataset counts are refreshed for this admission.

| Species | Preferred G before MP17a, kJ/mol | Source-check outcome |
| --- | ---: | --- |
| HCoO2−(aq) | −348.9456, Shock et al. (1997), class E | Original TN270 value found; later official correction gives **−345.5**, eligible as class B. |
| Hf4+(aq) | −554.7984, Shock et al. (1997), class E | Brookins page found; inherited Latimer calculation remains held under the project's source criteria. |

## HCoO2−: original page and the subsequent correction

[Wagman et al. (1969), NBS Technical Note 270-4](https://nvlpubs.nist.gov/nistpubs/Legacy/TN/nbstechnicalnote270-4.pdf),
Table 40(1), printed **p. 54 / PDF p. 70**, gives HCoO2− in the aqueous
standard state, m = 1, with formation G **−97.4 kcal/mol** at 298.15 K.
The scanned row, charge, state and G column were inspected visually.
Using the report's thermochemical calorie, 1 cal = 4.1840 J, this is
**−407.5216 kJ/mol**. The displayed original value does not reproduce every
digit of the Materials Project's **−407.57 kJ/mol**. Original one-atmosphere
conventions are retained in the external ledger; no precise conversion to
1 bar is inferred from this numerical proximity.

The NBS 1982 edition, Table 40:Co, printed p. 2-170 / PDF p. 178, displays
−407.5 kJ/mol. This original page was inspected for comparison. Its value
has a subsequent correction.

The explicitly open [NIST digitization, DOI 10.18434/M32124](https://doi.org/10.18434/M32124),
`NBS_Tables_with_ErratumValues.csv`, logical record **5482**, including the
two header records, column **9** (G), gives **`-345.5*`** for
`HCoO2<sup>-</sup>`, state `ao`. The CSV SHA-256 is
`cb8a8b8b94a287e6e8c82eed8bad2cf9b611d574d1cfd95c8528d318dfef4b44`.
The normalized observation is −345500 J/mol at 298.15 K and 1 bar, per full
HCoO2− formula unit, under the conventional aqueous H+ reference.
No numerical uncertainty is supplied.

[Reed (2020), section 3, p. 2](https://nvlpubs.nist.gov/nistpubs/jres/125/jres.125.007.pdf)
explains that an asterisk identifies values corrected using the 1989 erratum,
DOI 10.1063/1.555845. Thus this marker records a correction; it does not turn
the cell into an unreadable number or an estimated uncertainty. The corrected
open release and Reed's explanation verify this candidate. A page in the
original six-page 1989 erratum was not retrieved during this check.

Reuse of the corrected cell follows the completed review of the explicit
non-SRD NIST PDR release and its [NIST open licence](https://www.nist.gov/open/license),
with NIST acknowledgment and warranty qualifications. The original 1969
Technical Note has its separate [NIST Technical Series reuse basis](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications).
No new observation is copied from an NIST SRD product, and no blanket licence
for Materials Project's upstream compilation is inferred.

In the applied database, the unchanged policy classifies the corrected observation
as **NBS Tables, class B**. It is the preferred cobalt G while retaining
the Shock observation. Its difference from the earlier Shock value is +3.4456 kJ/mol.
The old value near −407.5 should remain documented as historical, corrected
source evidence. It should not become the preferred cobalt value.

## Hf4+: page verified, original evidence still needed

[Brookins (1988), *Hafnium*, pp. 118–119](https://doi.org/10.1007/978-3-642-73093-1_48),
Table **48 on p. 118** (PDF p. 126 in the consulted original publication),
gives Hf4+(aq) formation G **−156.80 kcal/gfw**. Exact unit conversion gives
**−656.0512 kJ/mol**, close to the Materials Project reference file's
−656.04 kJ/mol. Brookins attributes it to **Latimer (1952)**. Footnote a
identifies a calculation from the Hf → Hf4+ + 4e− electrode potential,
E° = +1.70 V in the oxidation direction. This establishes a bibliographic
and arithmetic trail, with a compiled potential as its input.

The publisher identifies Springer copyright and subscription content.
Brookins and Latimer are commercial compilations; independently reusable
original numerical evidence remains necessary under the current project
instructions. A public mirror or the MP reference does not supply that evidence
or establish an open reuse grant. No hafnium observation is proposed for import
from these compilations. The original source of the potential, its experimental
or estimated basis, and its conventions are specific follow-up targets.

The present policy also has **no Brookins family pattern**. A hypothetical
`source_verified_estimate` observation with that citation maps to `estimates`
(class E); an accepted observation without a matching pattern falls back to
`experimental papers` (class D). A page citation alone does not establish
class B, experimental status or permission. This review changes no policy rule.
Original NBS TN270-5, Table 59(1), p. 22 / PDF p. 38, was also checked; it
contains gaseous Hf4+ enthalpy data, providing no aqueous Hf4+ G alternative.

## Completed checks and handoff

- [x] Verify both original source locations, species, units and ancestry.
- [x] Identify the corrected, explicitly open cobalt observation and its marker.
- [x] Validate the complete cobalt candidate in a database copy, retaining all earlier rows.
- [x] Verify the actual source-family classifications and record the hafnium hold.

MP17a changes one preferred G and no coverage counts. On an 81 × 91 grid,
59 of 7371 cobalt phase points and 112 uncertainty-mask points change.
The other 73 default systems, including hafnium, retain their maps and masks.
Two supported ideal/Davies primary-cobalt balances conserve metal. Integrity,
foreign keys, unchanged policy and repeated-import checks pass.

The reviewed package, source hashes, images, decisions and validation are in
`pourbase-work/reaktoro-dataset-review/mp17-cobalt-hafnium-source-check/`.
The running tracker records the corrected cobalt admission separately from
hafnium original-source retrieval. R11j's seven silicate routes and every
completed source review remain carried forward.

## MP17a admission and thermal scope

The database now retains 3286 observations across 1038 species. One G alternative
is added; no species or newly available property is added. The selected G/S/H
counts remain 915/816/700. The policy remains `b2ad235bba62` with 46 overrides
and 10 exclusions; the recommendation fingerprint becomes `63d0abf8e2e5654b`.
The old Shock G remains eligible and is not marked superseded by this separate
evaluation. The absence of a numerical interval remains explicit.

HCoO2- has one Co, two core O, one core H, charge -1, two electrons and three
protons per formula unit. The corresponding hydrolysis reaction is
`Co2+ + 2H2O = HCoO2- + 3H+`. No new formation H or standard S is inferred.
The existing constant formation-entropy approximation uses the retained Shock
entropy through its mixed-source fallback. Its slope is unchanged; G shifts
by +3445.6 J/mol at 323.15 and 373.15 K as well as at the reference temperature.
The checked thermal cobalt maps change 69 and 79 of 7371 points, respectively;
those changes belong to the updated G. Shared source ancestry and covariance
remain unknown. Package notices retain NIST attribution and the open-release
warranty qualifications; the OECD downstream acknowledgment for other data
remains applicable.
