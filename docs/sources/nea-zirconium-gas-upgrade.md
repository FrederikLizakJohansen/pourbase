# Original zirconium oxide-gas enthalpies

The NEA02g3b checkpoint retains **three original-study observations** for
the existing ZrO(g) and ZrO2(g) records. Two are formation enthalpies explicitly
reported at 298.15 K; the third is a ZrO formation enthalpy at 0 K, retained
as evidence with an explicit exclusion from 298.15 K selection.

The database now contains **989 species and 3,145 observations**. The default
policy retains all earlier preferred observations: selected G/S/H counts stay
**869/790/671**. No species or newly available 298.15 K property is added.

## Primary evidence and source conditions

| Source | Species | Reported property | Stored value, J/mol | Stored uncertainty, J/mol |
|---|---|---|---:|---:|
| Murad and Hildenbrand (1975) | ZrO(g) | Formation H at 298.15 K | 83000 | 12000 |
| Murad and Hildenbrand (1975) | ZrO2(g) | Formation H at 298.15 K | −298000 | 30000 |
| Ackermann and Rauh (1974) | ZrO(g) | Formation H at 0 K | 89537.6 | Unassigned; source gives a collective range |

The first study is Murad, E. and Hildenbrand, D. L. (1975), *Thermochemical
properties of gaseous ZrO and ZrO2*, Journal of Chemical Physics 63(3),
1133–1139, [DOI 10.1063/1.431439](https://doi.org/10.1063/1.431439).
Its original author abstract, deposited by AIP Publishing in Crossref,
explicitly gives the two 298.15 K results in kJ/mol; values and widths are
multiplied by 1000. The abstract describes mass-spectrometric equilibrium
measurements and sensitivity to spectral data. Confidence conventions and
covariances are unspecified. Retain the reported widths and
`source_verified_estimate` status; no one-sigma or 95% interpretation is inferred.

The second study is Ackermann, R. J. and Rauh, E. G. (1974), *Thermodynamic
properties of ZrO(g) and HfO(g); a critical examination of isomolecular
oxygen-exchange reactions*, Journal of Chemical Physics 60(6), 2266–2271,
[DOI 10.1063/1.1681357](https://doi.org/10.1063/1.1681357). Its original
publisher-deposited abstract gives H0(ZrO) = 21.4 kcal/mol. Conversion uses
1 thermochemical kcal = 4184 J. The decimal J/mol representation preserves
the converted number; source precision remains one decimal kcal/mol.
The authors give 1–2 kcal/mol collectively for the 0 K enthalpies and
bond-dissociation energies. An individual ZrO width is unassigned and the
range stays in the locator. A policy exclusion keeps the actual 0 K
observation outside 298.15 K recommendations.

Neither abstract specifies a standard pressure. The observations retain
`pressure_bar = NULL`. Ideal-gas enthalpy is pressure independent; no
numerical 1-atm/1-bar correction or invented source-pressure statement is
applied. These are qualified original reported alternatives. Their source
conditions remain visible through `ReportedValue.temperature_K` and
`.pressure_bar`.

The primary verification route is each publisher's Crossref deposit:
[1975 record](https://api.crossref.org/works/10.1063/1.431439) and
[1974 DOI](https://doi.org/10.1063/1.1681357). Exact retrieved deposits and
hashes remain in the external review workspace. Full article methods and
numerical tables were not recovered. The import scope is the explicitly
reported abstract results. Older estimates and the NEA critique remain intact.

## Selection and calculations

The unchanged class ordering places the qualified original-study estimates
in family `estimates`, class E. The NEA review remains class A, so the new
298.15 K alternatives are retained without changing the preferred H values
56,200 and −289,600 J/mol. A user can explicitly select either 1975
observation with a source-specific policy override. The 0 K exclusion remains
in effect until a justified thermal conversion is available.

No G or S is inferred by combining incompatible thermal/spectral evaluations.
The 1974 abstract's G fit covers 2000–2800 K and stays in the external
thermal-function ledger. Bond-dissociation and ionization results likewise
remain external evidence outside the current G/H/S property interface.
The two sources' reported results and their thermal assumptions warrant
further review before a consistent replacement G/H/S set is selected.

All default phase maps and uncertainty masks, 118 existing buffered
scenarios and default temperature calculations retain their previous results.
Optional gas selection, prescribed fugacity and gas-free default closed
balances retain their scope. This checkpoint improves the retained evidence;
it does not resolve the scientific disagreement about a complete gas set.

## Reuse and attribution

These three observations follow the project's established **individual
original numerical facts** route. The distributed records contain separately
transcribed facts, scientific citations and our provenance descriptions.
The articles and their abstract prose retain their copyright; no open article
licence or blanket publisher permission is asserted. The
[U.S. Copyright Office](https://www.copyright.gov/help/faq/faq-protect.html)
distinguishes facts from protected expression. The
[AIP content permissions policy](https://publishing.aip.org/resources/researchers/rights-and-permissions/permissions/)
was reviewed separately. Article text, figures, table arrangements and bulk
source compilations remain outside this import.

The metadata keys `source_reuse_MuradHildenbrand1975_NEA02g3b_original`
and `source_reuse_AckermannRauh1974_NEA02g3b_original` document this limited
reuse basis, source-deposit hash and attribution. The existing OECD terms
continue to govern the earlier NEA evaluations, with the same acknowledgment
requirement passed to further sublicensees. NEA permission supplies no
licence for these independent articles. See the
[distributed notices](https://github.com/FrederikLizakJohansen/pourbase/blob/main/THIRD_PARTY_NOTICES.md).

## Remaining work

The finite original-enthalpy checkpoint is complete. A consistent G/S and
thermal reassessment remains open as NEA02g3b1. It needs the original full
methods, calibration/spectral inputs, uncertainty interpretation and a
compatible standard-state evaluation. The original 27 zirconium rows still
have 25 admissions and two admission holds: ZrH and the calcium formula.
The three sodium-silicate temperature calculation holds remain separate;
this batch adds one distinct 0 K enthalpy exclusion. Earlier requests,
permission holds and wider source reviews retain their histories.
