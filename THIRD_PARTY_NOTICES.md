# Third-party data and attribution

## R08 NASA thermochemistry and open atomic references

NASA CEA data use pinned revision
`2f79a647e85737742fb08a127da00d1ea1d069da` of
https://github.com/nasa/cea. Copyright (c) 2025, United States Government as
represented by the Administrator of the National Aeronautics and Space
Administration. Licensed under the Apache License, Version 2.0. NASA's
NOTICE explicitly identifies its thermodynamic data files. Unmodified
[licence](src/pourbase/data/nasa-cea-LICENSE.txt) and
[NOTICE](src/pourbase/data/nasa-cea-NOTICE.txt) files accompany the database
and wheel. Pourbase selects atomic entropy evaluations and adapts one
nominal wustite fit, adding its own formation-G calculations, qualifications
and record mappings. These are modifications and selections by pourbase.

Scientific attribution: McBride, B. J., Zehe, M. J. and Gordon, S. (2002),
*NASA Glenn Coefficients for Calculating Thermodynamic Properties of Individual
Species*, NASA TP-2002-211556, https://ntrs.nasa.gov/citations/20020085330;
Gordon, S. and McBride, B. J. (1999), *Thermodynamic Data to 20 000 K for
Monatomic Gases*, NASA TP-1999-208523,
https://ntrs.nasa.gov/citations/19990063361.

The open non-SRD NIST PDR M32124 release supplies separately cited atomic
and wustite observations and reference inputs, https://doi.org/10.18434/M32124.
NIST is acknowledged under its [open licence](https://www.nist.gov/open/license);
data are distributed without warranty. Pankratz, L. B. (1982), *Thermodynamic
Properties of Elements and Oxides*, Bulletin 672, pp. 155–156,
https://stacks.cdc.gov/view/cdc/219421, supplies public-domain federal
composition and metastability evidence.

The current NASA licence supplies no blanket permission for the distinct
legacy snapshot or separately copied restricted tables. No copied
JANAF/Chase/TRC or unverified commercial-compilation thermochemistry is
imported here. Existing OECD credit and the requirement for further
sublicensees to pass on the acknowledgment requirement continue for NEA
inputs separately. See [the source review](docs/sources/nasa-thermochemistry.md).

pourbase combines individual thermochemical values traced to scientific sources with selected
Materials Project records. The GPL-3.0 license covers the code and the compilation. Source-specific
terms and scientific citation obligations remain in force.

## NEA selenium selected observations

OECD and the Nuclear Energy Agency are acknowledged for selected numerical
data from Olin, Å., Noläng, B., Osadchii, E. G., Öhman, L.-O. and Rosén, E.
(2005), *Chemical Thermodynamics of Selenium*, Chemical Thermodynamics
Series, volume 7, Table III-1 pp. 40–42
([official publication](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/chemical_thermodynamics_of_selenium_volume_7.pdf),
accessed 16 October 2026). The official November 2005 errata were checked;
source conventions, estimates and the selenite entropy discrepancy accompany
the observations. See [the source review](docs/sources/nea-selenium.md).

The written NEA-TDB clarification and
[OECD data terms](https://www.oecd.org/en/about/terms-conditions.html) permit
use, adaptation and redistribution, including commercially, subject to
source-specific additional restrictions. Every sublicense of work using
these data must include the same OECD acknowledgment requirement and require
further sublicensees to pass it on. These requirements accompany the
package's GPL-3.0-only licence. Complete publications, third-party figures,
independent auxiliary tables and private correspondence retain their existing
rights and stay outside this import.

## OECD Nuclear Energy Agency Thermochemical Database (NEA-TDB)

The R11c metal-selenium continuation acknowledges Olin et al. (2005),
*Chemical Thermodynamics of Selenium*, volume 7, Table III-1 pp. 44/48/50,
Table III-2 pp. 58–60 and Table E-1 pp. 641/644. Six Appendix E observations
retain NEA's explicit unreviewed-auxiliary qualification and are recorded as
estimates. One local FeSeO3+ formation-G estimate adapts the selected NEA7
reaction using retained NEA7 selenite and Lemire et al. (2013), *Chemical
Thermodynamics of Iron, Part 1*, volume 13a, Fe3+ data. OECD and NEA are
acknowledged for all these inputs. Independent auxiliary tables, source
publications and private correspondence remain external.

The written clarification and OECD data terms cover these NEA-authored
evaluations and their adaptation, subject to additional restrictions checks.
Every sublicense of work using these data must carry the same OECD
acknowledgment requirement and require further sublicensees to pass it on.
The prior open NBS selenite observation and source attribution remain in the
database when its free-reference pin changes to the preferred NEA value.
See [the R11c source review](docs/sources/nea-metal-selenium.md).

OECD and the Nuclear Energy Agency are acknowledged as the source of the NEA-TDB
selected thermochemical data retained in pourbase. Cite the review associated
with each observation, including its table and page. Written clarification
supplied by Frederik on 14 October 2026 confirms that the OECD data terms apply
to these data. They permit extraction, copying, adaptation and redistribution
for any purpose, including commercial use, subject to additional restrictions
identified for a particular source.

**Required downstream acknowledgment:** When sharing or licensing work created
using these data, include the same requirement to give appropriate credit to
the OECD in every sublicense you grant. Require each further sublicensee to
include and pass on that acknowledgment requirement in their own sublicenses.
Use the citation associated with the data. Where none is provided, cite
OECD (year), dataset name, data source, DOI or URL, and access date.

Applicable terms, section 3, Data:
<https://www.oecd.org/en/about/terms-conditions.html> (accessed 14 October 2026).
This source-specific acknowledgment obligation accompanies the project's
GPL-3.0 software and compilation licence. See
`docs/sources/nea-tdb-reuse.md` for scope and source-admission instructions.

The 14 October 2026 expansion uses Table III-1 of these reviews (accessed
14 October 2026). Individual database locators identify the exact rows,
published uncertainty intervals and conversions from kJ/mol to J/mol.

- Lemire, R. J., Berner, U., Musikas, C., Palmer, D. A., Taylor, P. and
  Tochiyama, O. (2013), *Chemical Thermodynamics of Iron, Part 1*,
  Chemical Thermodynamics 13a, OECD Nuclear Energy Agency, NEA No. 6355,
  printed p. 44.
  <https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/6355-vol13a-iron.pdf>
- Gamsjäger, H., Bugajski, J., Gajda, T., Lemire, R. J. and Preis, W. (2005),
  *Chemical Thermodynamics of Nickel*, Chemical Thermodynamics 6,
  OECD Nuclear Energy Agency, printed p. 44.
  <https://www.oecd-nea.org/dbtdb/pubs/vol6-nickel.pdf>
- Gamsjäger, H., Gajda, T., Sangster, J., Saxena, S. K. and Voigt, W. (2012),
  *Chemical Thermodynamics of Tin*, Chemical Thermodynamics 12,
  OECD Nuclear Energy Agency, ISBN 978-92-64-99206-1, printed pp. 44–45.
  <https://www.oecd.org/content/dam/oecd/en/publications/reports/2012/12/chemical-thermodynamics-of-tin-volume-12_g1g39522/9789264992061-en.pdf>

The NEA02a solid-phase continuation uses the same reviews, Table III-1,
printed pp. 44–47 in each volume. It retains 158 further G/H/S observations
and 48 distinct solid species. OECD and the Nuclear Energy Agency are
acknowledged. Full hydrated formula units, source phase labels, uncertainty
intervals and unit conversions remain attached to every observation. The same
OECD attribution and downstream acknowledgment requirement above applies.
The selected numerical data use the existing permission route; other sources
retain their separate terms. Complete publication pages remain external.

The NEA02b continuation adds the selected Fe0.932O formation G/H and entropy
from iron volume13a, Table III-1, printed p.44, with the composition and
qualifications in sectionVII.2.8, printed pp.205–212. OECD and the Nuclear
Energy Agency are acknowledged. These are retained as source-reviewed
estimates for a fixed-composition metastable solid. The entropy follows the
published convention that omits an unknown residual configurational term.
The same OECD attribution and downstream acknowledgment requirements apply.

The earlier NEA observations retain their own associated review citations in
the database. Pourbase retains alternative evaluations and normalizes units
and formula encodings for calculation. Complete publications, page images,
independent third-party tables and electronic database software retain their
own terms; their redistribution requires a separate applicable reuse basis.

The NEA02d zirconium continuation retains 148 selected observations from
Brown, P. L., Curti, E. and Grambow, B., with Ekberg, C. (2005),
*Chemical Thermodynamics of Zirconium*, OECD Nuclear Energy Agency,
Chemical Thermodynamics Series, volume 8, Table III-1, printed pp. 48–53.
OECD and NEA are acknowledged. Source URL:
<https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/chemical_thermodynamics_of_zirconium_volume_8.pdf>
(accessed 14 October 2026). Complete formula units, source phases, intervals,
internal-calculation and estimation qualifications accompany these values.
The same OECD acknowledgment requirement applies in every sublicense and must
be passed on by further sublicensees. The source publication is retained in
the external review workspace; independent third-party tables are outside this
selected-data import.

The NEA02c ligand continuation retains 86 further selected observations from
the same iron, nickel and tin reviews, Table III-1, printed pp. 44–47.
These comprise 42 aqueous rows, seven tin molecular gas rows and one liquid
row. OECD and the Nuclear Energy Agency are acknowledged. Complete formula
units, charges, phases, source intervals and conversions accompany the data.
The same OECD acknowledgment requirement must be included in sublicenses and
passed on by further sublicensees. Runtime ligand reference evaluations remain
explicit; they can give reaction constants different from the NEA auxiliary set.

## R11e nickel carbonate, silicate, arsenate and pyrophosphate evaluations

The R11e nickel follow-up acknowledges Gamsjäger et al. (2005),
*Chemical Thermodynamics of Nickel*, NEA volume 6, Table III-1 p. 46
(annabergite G/H/S), Table III-2 p. 50 (pyrophosphate reaction evaluations),
and sections V.6.2.2.2/V.6.3.2.1. OECD and NEA are acknowledged for these
selected values and the retained Ni2+ inputs. Their OECD data terms and
written clarification apply: every sublicense of work using these data
must include the same OECD acknowledgment requirement and require further
sublicensees to pass it on. Additional source-specific restrictions remain
applicable. Independent auxiliary tables remain outside the import.

Original PSI numerical evaluations are cited separately: Hummel and Thoenen
(2014), PSI TM-44-14-05, pp. 25–26 (approximate supplemental bicarbonate),
and Hummel (2014), PSI TM-44-12-05, pp. 10–11/Fig. 8.6 (nickel-silicate
SIT reanalysis). Their isolated original numerical results use the established
individual-fact route with attribution. Complete reports and bulk PSI
database files retain their own rights. Miron et al. (2017),
doi:10.2475/07.2017.01, supplies the retained original silicate anchor.

NIST is acknowledged for the explicitly open non-SRD NBS PDR M32124 input
cells, CSV logical records 1281/1357/1673, under the NIST open licence,
without warranty. Source qualifications, complete calculations and
cross-reference differences accompany the local estimates. See
[the R11e source review](docs/sources/psi-nickel-carbonate-silicate.md).

## PSI nickel hydrosulfide evaluations

The R11d nickel hydrosulfide continuation cites Hummel, W. and Thoenen, T.
(2014), *Data Selection for Nickel*, PSI TM-44-14-05, pp. 11/13 and
Table 5.5 p. 30, [official report](https://www.psi.ch/en/media/47948/download)
(accessed 16 October 2026). Two individual original PSI regression results
support local formation-G estimates; the established numerical-fact route
covers this isolated use. Complete reports and PSI database files retain
their own rights and remain outside the distribution.

The local estimates use retained Gamsjäger et al. (2005), NEA volume 6,
Ni2+ and openly released NBS HS- inputs. OECD, NEA and NIST are acknowledged.
The HS- formation G independently matches NIST open non-SRD PDR M32124,
CSV logical record 584, under the NIST open licence, without warranty.
The NEA input retains its OECD terms: every sublicense of work using these
data must include the same OECD acknowledgment requirement and require
further sublicensees to pass it on. PSI's original evaluations have their
own numerical-fact basis. See [the source review](docs/sources/psi-nickel-hydrosulfides.md).

## NIST and NBS

Most NBS values come from the NIST Public Data Repository dataset *The NBS Tables of Chemical
Thermodynamic Properties* (Wagman et al. 1982, with errata; doi:10.18434/M32124), published under
the NIST open licence. NIST is acknowledged as the source of these data; the dataset is
distributed without warranty. <https://www.nist.gov/open/license>

The NEA02c continuation adds free-ion Gibbs references for SCN⁻, P2O7⁴⁻ and
AsO4³⁻ from that open NBS PDR release. The CSV logical records are 2096, 1281
and 1473, respectively, including the two header records. Formation Gibbs
energies are converted from kJ/mol to J/mol; the exact row, state, source-file
hash and open licence are recorded in each reference's source locator.

The NEA02d free-sulfite reference uses logical record 573 of the same open
NBS PDR CSV, including its two header records. SO3²⁻ formation G at 298.15 K
and 1 bar is converted from −486.5 kJ/mol to −486,500 J/mol. Its source
locator records the exact aqueous-ion row, column, file hash and open licence.
NIST is acknowledged; the data are supplied without warranty.

On 5 October 2026, 86 additional evaluated NBS properties were retained as source-linked
alternatives. Values in kJ/mol were converted to J/mol; entropy units were retained. Each
observation cites its digitized CSV logical record, formula, state and property column.
The existing preferred properties remain selected for calculations.

On 12 October 2026, the open NBS digitization also supplied the missing Sr²⁺
and Ba²⁺ formation enthalpies. Their locators identify logical CSV records
9635 and 9932, the aqueous state, property column and conversion to J/mol.
Open NBS ion, carbonate and bicarbonate G/H/S anchor the separately calculated
strontium/barium carbonate-fit estimates described below. NIST is acknowledged.

The Fe/Mn carbonate source review adds the missing Fe²⁺ and Mn²⁺ formation
enthalpies from the same open NBS digitization, logical records 5804 and 6291,
zero-based column 7, at 298.15 K/1 bar. NIST is acknowledged. Their locators
retain the published values, conversion and unavailable uncertainty.

## USGS mineral evaluations

One local magnesite Gibbs estimate uses Robie (1965), USGS Professional Paper
525-D, printed D69, Eq. 21, as an individually attributed federal equilibrium
evaluation. Exact Mg²⁺, HCO3−, CO2(g) and water Gibbs anchors come from the
explicitly licensed NIST PDR digitization, DOI 10.18434/M32124. The source's
aqueous-complexing caveat and local pressure model are retained. USGS, NIST and
UNT are acknowledged. Original report pages and the held JANAF-dependent
decomposition calculations remain external. Complete original report:
<https://digital.library.unt.edu/ark:/67531/metadc872685/m2/1/high_res_d/report.pdf>.

Four local formation estimates for nesquehonite and five-Mg hydromagnesite combine
the original USGS-authored 1973 calorimetric reaction heats and 1972 entropy facts
with constituent enthalpies and elemental entropies from the explicitly licensed
NIST PDR release, DOI 10.18434/M32124. The established individual-source fact route
and explicit data licence apply; USGS and NIST are acknowledged. These are local
estimates with an explicit pressure model and unavailable total uncertainty.
The original 1968 auxiliary absolute-property values are replaced completely.
Original journal text, pages and held formation outputs remain external.
Original source: <https://pubs.usgs.gov/journal/1973/vol1issue5/report.pdf>, pp. 543–547.

The same original paper, pp. 544/546, identifies the older four-Mg hydromagnesite
formula as incorrect. Its NBS observation remains historical evidence with an
explicit scientific exclusion; it supplies no active calculation value.

The original artinite entropy alternative comes from Hemingway and Robie (1972),
American Mineralogist 57, 1754–1767, printed p. 1765. The authors add a modelled
configurational residual entropy to the calorimetric increment. Its assumption,
conversion and shared experimental lineage are retained under the existing
individually attributed USGS numerical-fact route; journal material stays external.
USGS is acknowledged. Original source: <http://www.minsocam.org/ammin/AM57/AM57_1754.pdf>.

Six further Mg mineral properties use the explicitly licensed NIST PDR digitization,
Table 93:Mg, logical records 9085, 9086, 9087 and 9098. Exact formula units and
crystalline labels were corroborated against original NBS printed p. 2-264.
The existing data licence applies; NIST is acknowledged. Source age and competing
evaluations remain explicit. Original NBS pages are external corroboration; the
distributed numerical observations come from the licensed digitization.

The magnesium continuation adds 12 Bulletin 2131 properties for magnesite,
nesquehonite, hydromagnesite and artinite, printed p. 25. The existing federal
public-domain evaluation review covers these individually cited observations;
USGS is acknowledged. Formula units, hydration and published intervals are
retained. Three original entropy observations use the established individually
attributed USGS numerical-fact route: Hemingway, Robie, Fisher and Wilson (1977),
USGS Journal of Research 5, 797–806, and Robie and Hemingway (1972), American
Mineralogist 57, 1768–1781. Original journal material stays in the external review.
The original hydromagnesite absolute-entropy interpretation is labelled an
estimate because the authors explicitly assumed zero residual entropy.

- Original magnesite calorimetry: <https://pubs.usgs.gov/journal/1977/vol5issue6/report.pdf>
- Original hydrated-carbonate calorimetry: <http://www.minsocam.org/ammin/AM57/AM57_1768.pdf>

Open NBS digitization also supplies Mg²⁺ formation enthalpy and MgHCO3+ formation
Gibbs energy, logical CSV records 8864 and 9092, zero-based columns 7 and 8.
The explicit NIST PDR data licence and previous review apply; NIST is acknowledged.
These source-linked values are retained alongside the earlier aqueous evaluations.

The calcium aqueous-association continuation retains six G/H/S estimates from
the original Plummer and Busenberg (1982) numerical abstract, equations 4–5,
at <https://pubs.usgs.gov/publication/70011789>. These individually attributed
USGS-authored numerical fits use the carried-forward federal fact reuse route
and open NBS Ca²⁺/carbonate/bicarbonate anchors. USGS and NIST are acknowledged.
The estimates explicitly assume a locally pressure-flat reaction between 1 atm
and 1 bar; total uncertainty remains unavailable. Original equation images
remain in the external review. The missing Ca²⁺ formation enthalpy comes from
open NBS CSV logical record 9196, zero-based column 7, converted to J/mol.

The database retains the plattnerite PbO2 Gibbs energy, formation enthalpy and absolute entropy
from Robie and Hemingway (1995), USGS Bulletin 2131, printed pp. 18 and 209, at 298.15 K and
1 bar. Source-specific uncertainty intervals and the government evaluation's lineage are
documented in each source locator and the species warning. The values are retained as
alternatives alongside the existing preferred evaluation. USGS-authored data are public domain;
USGS is acknowledged as the source.

On 12 October 2026, 19 properties for calcite, aragonite, vaterite, siderite,
rhodochrosite, strontianite and witherite were added from the same USGS evaluation,
printed pp. 25–26. These are seven distinct pure mineral phases at 298.15 K and
1 bar. Each property records the original table location, unit conversion,
published uncertainty interval and numbered references used by the USGS evaluation.
The existing public-domain source review covers this addition; USGS is acknowledged.
This table supplies vaterite's Gibbs energy; its entropy and enthalpy are absent.

Two original entropy observations from Robie, Haselton and Hemingway (1984)
retain their exact published precision and intervals after the authors corrected
the specimens to pure FeCO₃/MnCO₃ endmembers. These original USGS-authored
calorimetry facts use the established federal public-domain source route, with
USGS attribution. They share an experimental lineage with the later critical
evaluations already stored. The original entropy pressure is unspecified and
remains NULL; the source's helium-fill pressure is apparatus information.
Journal text, figures and complete tables remain in the external review.

- Robie, R. A., Haselton, H. T., Jr. and Hemingway, B. S. (1984),
  *American Mineralogist* 69, 349–357, pp. 353–354, Tables 5–6.
  Original journal archive: <http://www.minsocam.org/ammin/AM69/AM69_349.pdf>

Six additional calculated G/H/S alternatives for aragonite and vaterite use
the original USGS-authored calcium carbonate solubility fits of Plummer and
Busenberg (1982), DOI 10.1016/0016-7037(82)90056-4. The equations and point
constants were checked against the author abstract in the USGS Publications
Warehouse and its original equation images. Relative polymorph differences
cancel the aqueous reference terms and use the reviewed Bulletin 2131 calcite
G/H/S as anchors. A stated constant-solid-volume model transfers the differences
from 1 atm to 1 bar. These are separately labelled estimates with unavailable
total uncertainty; vaterite's H/S estimates fill two property gaps. The reuse
basis is individually attributed USGS-authored numerical facts and the reviewed
federal evaluation. USGS is acknowledged. Original article images remain in
the external source review.

- Plummer and Busenberg (1982), original study and numerical abstract:
  <https://pubs.usgs.gov/publication/70011789>
- Ball and Nordstrom (1991), WATEQ4F manual, Table 2, printed pp. 23–24,
  independently corroborates the calcite and aragonite constants and source:
  <https://doi.org/10.3133/ofr91183>

Eighteen additional G/H/S estimates use the original USGS-authored dissolution
and association fits of Busenberg, Plummer and Parker (1984) and Busenberg and
Plummer (1986). They cover strontianite/witherite and aqueous SrCO₃, BaCO₃,
SrHCO₃⁺ and BaHCO₃⁺. Each locator states the original 1 atm convention,
open NBS formation anchors and a local pressure-flat reaction approximation
at 298.15 K/1 bar. Actual reaction volumes and total covariance are unavailable;
these entries are labelled estimates with NULL uncertainty. The source-specific
reuse route covers individually attributed original federal numerical facts
and licensed NBS inputs. USGS and NIST are acknowledged. Original-study ion
reevaluations and native database evaluations retain separate ancestry reviews.

- Busenberg, Plummer and Parker (1984), original strontium study and numerical abstract:
  <https://pubs.usgs.gov/publication/70014019>
- Busenberg and Plummer (1986), original barium study and numerical abstract:
  <https://pubs.usgs.gov/publication/70015035>

- Robie, R. A. and Hemingway, B. S. (1995), *Thermodynamic Properties of Minerals and Related
  Substances at 298.15 K and 1 Bar (10^5 Pascals) Pressure and at Higher Temperatures*.
  <https://doi.org/10.3133/b2131>
- USGS reuse policy:
  <https://www.usgs.gov/faqs/are-usgs-reportspublications-copyrighted>
- Pankratz, L. B. (1982), *Thermodynamic Properties of Elements and Oxides*, Bureau of Mines
  Bulletin 672, p. 300; source lineage for enthalpy and low-temperature entropy.
  <https://stacks.cdc.gov/view/cdc/219421>

## NIST Standard Reference Data

Values from the NIST-JANAF Thermochemical Tables (SRD 13) and the NIST Chemistry WebBook (SRD 69)
are NIST Standard Reference Data, © U.S. Secretary of Commerce on behalf of the United States of
America. Cite the exact source attached to each field.

- <https://janaf.nist.gov/>
- <https://webbook.nist.gov/chemistry/>

## Other scientific sources

The `sources` table identifies the evaluated databases, books, assessments, and journal articles
behind each value. The database contains citations, locators, brief factual summaries, and
individual reported or derived numerical values. Cite the sources attached to the values used in
your work.

## Materials Project

The database includes 299 method-specific Materials Project thermochemistry rows for 105
phase-matched records from database version 2026.04.13, and six 300 K Gibbs estimates generated
through pymatgen's Materials Project SISSO descriptor for explicit use as gap fallbacks. These
records keep the MP identifier, calculation type, model, database version, retrieval date, mapping
confidence, and source URL. `STATISTICS.md` and `docs/statistics` contain comparison figures derived from these
records, with their plotted rows. Materials Project core data are provided under CC BY 4.0.

The optional live comparison retrieves the current Materials Project database through the official
API with the user's own API key. The package contains no API key. Results record the MP database
version and the client-library versions; keep this metadata, the MP identifiers, and a statement
that the analysis was made with pourbase from MP data when sharing a comparison.

- <https://materialsproject.org/>
- <https://docs.materialsproject.org/frequently-asked-questions>
- Horton, M. K. et al. *Nature Materials* (2025). <https://doi.org/10.1038/s41563-025-02272-0>
- Jain, A. et al. *APL Materials* 1, 011002 (2013). <https://doi.org/10.1063/1.4812323>
- Persson, K. A. et al. *Physical Review B* 85, 235438 (2012). <https://doi.org/10.1103/PhysRevB.85.235438>
- Singh, A. K. et al. *Chemistry of Materials* 29, 10159-10167 (2017). <https://doi.org/10.1021/acs.chemmater.7b03980>
- Bartel, C. J. et al. *Nature Communications* 9, 4168 (2018). <https://doi.org/10.1038/s41467-018-06682-4>

## Original solubility fits and nitrogen estimates

The database retains individually verified nickel solubility and hydrolysis fits from
González-Siso et al. (2018), and derived iron formation energies from the original reaction
fits of Fürst et al. (2025, 2026). The Fürst articles carry CC BY 3.0. Nickel uses individually
cited original numerical facts; its article retains its copyright. Gibbs energies were
calculated by pourbase using the documented parent-ion and water references, with model,
temperature, pressure and specimen assumptions retained as estimate warnings. The iron parent
uses the existing Parker/Khodakovskii (1995) evaluation, independently verified at its exact
1-bar locator; that article retains its copyright. Original-paper numerical facts follow the
project's individual-source policy. No article-wide open licence is asserted for these papers.

The nitrogen estimates use Sander's CC BY 4.0 publisher supplement, traced to Rettich et al.
(1984), and open NBS water molar mass and gas entropy. The original 1984 table was unavailable
for independent verification; the immediate source is Sander's licensed transcription.
Pourbase fitted the source points and converted to a molal basis on 5 October 2026. Source
locators and warnings retain the nominal-pressure treatment and entropy convention.

- González-Siso, M. R. et al. (2018), *Radiochimica Acta* 106, 31–45, section 4.3, pp. 38–39.
  <https://doi.org/10.1515/ract-2017-2762>
- Fürst, P. Q. et al. (2025), *RSC Advances* 15, 46308–46319, model-development fit and Table 2.
  <https://doi.org/10.1039/D5RA07073B>
- Fürst, P. Q. et al. (2026), *RSC Advances* 16, 36843–36849, Tables 1–2.
  <https://doi.org/10.1039/D6RA02690G>
- Parker, V. B. and Khodakovskii, I. L. (1995), *Journal of Physical and Chemical Reference
  Data* 24, 1699–1745, section 6.1 and Table 8, p. 1719.
  <https://doi.org/10.1063/1.555964>
- Sander, R. (2023), *Atmospheric Chemistry and Physics* 23, 10901–12440, supplement ref2434.
  <https://doi.org/10.5194/acp-23-10901-2023>
- Rettich, T. R., Battino, R. and Wilhelm, E. (1984), *Journal of Solution Chemistry* 13, 335–348.
  <https://doi.org/10.1007/BF00645706>

## Software dependencies

Optional dependencies are installed from their own distributions and are not vendored:
`mp-api` (BSD 3-Clause) and pymatgen (MIT) for the live comparison; PySide6 (LGPL-3.0),
pyqtgraph (MIT) and keyring (MIT) for the desktop application.

## GEOPIG SLOP aqueous-complex evaluations

The remaining Shock1997 Table 7/10 continuation retains 59 further original
fitted/correlated G/S outputs from the GEOPIG CC BY 4.0 release, independently
checked against the original paper, and eight separately calculated NBS-reference
enthalpies. Seventeen already stored evaluations retain their original identity.
Conversions use the exact calorie factor and explicitly cited open NBS water and
elemental entropy references. The original paper establishes the corrected neutral
HGaO₂ and singly negative YO₂⁻ species identities. Unresolved original entropy
ancestry and inherited hydrolysis/native-enthalpy inputs remain in the external
review. These numerical portions retain CC BY 4.0 attribution; pourbase's code
and compilation retain GPL-3.0.

The Fe/Ni/Sn/Pb continuation retains 25 individually checked original outputs from
Shock et al. (1997), Tables 7 and 10, printed pp. 934 and 942–943, and ten separately
labelled NBS-reference enthalpy calculations. Nineteen outputs match the CC BY 4.0
GEOPIG numerical release. Six numerical facts from the alternative iron regression
in Table 7, footnote d, are individually transcribed from the original paper and carry
that exact citation. Four previously stored evaluations are linked to the same original
source without adding duplicate observations.

Hydration conversions add explicitly cited open NBS liquid-water properties. The new
enthalpies use same-fit G/S pairs and open NBS elemental entropies. Correlation outputs
identify inherited cation properties as calibration dependencies. Inherited simple-ion
values, hydrolysis-compilation formation values and native enthalpies with
Cox/Glushko/Wagman reference ancestry remain in the external review. NiO and PbOH⁺
entropies disagree between the original tables; those entropy representations and
dependent enthalpies remain held. Each available property retains one preferred value.

- Shock, E. L., Sassani, D. C., Willis, M. and Sverjensky, D. A. (1997),
  *Geochimica et Cosmochimica Acta* 61, 907–950.
  <https://doi.org/10.1016/S0016-7037(96)00339-0>

On 8 October 2026, pourbase retained 151 additional original Gibbs-energy and entropy
evaluations from Sverjensky, Shock and Helgeson (1997), Tables 2, 3 and 12, printed
pp. 1391–1392 and 1400. The numerical values were checked against the original paper
and GEOPIG's author release, *GEOPIG slop files* (Arizona State University, 2019),
distributed under CC BY 4.0. These portions retain that licence and attribution.
The GPL-3.0 licence covers pourbase's code and compilation.

Pourbase converted calorie units with the exact factor 4.184 and normalized identified
HSiO3 species to their stored H3SiO4 formula by adding open NBS water. It also calculated
52 separately labelled formation-enthalpy estimates from verified G/S pairs and open
NBS elemental entropies. Each retained observation identifies its numerical row,
property, conversion and source. Estimates have unknown total uncertainty. Existing
preferred values remain selected; distinct original evaluations are retained as alternatives.

The original article retains its publisher's copyright. Inherited properties with unresolved
source ancestry remain in the external review. The author-release licence applies to
the selected original outputs; it supplies no new permission for restricted third-party inputs.

- GEOPIG (2019), *GEOPIG slop files*, Arizona State University.
  <https://doi.org/10.5281/zenodo.2630820>
- CC BY 4.0: <https://creativecommons.org/licenses/by/4.0/>
- Sverjensky, D. A., Shock, E. L. and Helgeson, H. C. (1997), *Geochimica et Cosmochimica
  Acta* 61, 1359–1412. <https://doi.org/10.1016/S0016-7037(97)00009-4>
- NBS reference data: <https://doi.org/10.18434/M32124>

Bromide complexes require an explicitly supplied free Br⁻ activity. The bromide reference
G is −103960 J/mol from the existing open NBS record. A total bromide concentration
requires a component balance. Entropy-only additions remain inspectable and are skipped
by calculations that require a formation Gibbs energy.

## MINES and aq17 research evaluations

The database retains individually verified aqueous Gibbs-energy and entropy evaluations from
Miron et al. (2016, 2017), including alternate evaluations and identified differences between
published and downloadable representations. Each observation has its own source locator.
Existing preferred Gibbs energies are preserved; newly selected model values carry the
`source_verified_estimate` status. These are derived research evaluations with mineral calibration
dependencies described by the authors. Per-record warnings document compatibility and uncertainty.

MINES23.1 permits use, sharing and modification: “This database is free to use, share, and modify.”
The ThermoHub data mirror is distributed under GPL-3.0. Individual facts verified in the original
papers retain their original citations. These terms apply to the selected data and retain the
original publications' attribution; the journal articles themselves are not relicensed.

Carbonate complexes require an explicit buffered free CO₃²⁻ activity. The reference value comes
from the existing openly licensed NBS carbonate record. A total carbonate concentration requires
an acid/base and mass balance treatment. Inherited properties awaiting original-source
verification remain outside the Miron addition.

- MINES23.1: <https://geoinfo.nmt.edu/mines-tdb/index.html>, <https://doi.org/10.58799/mines-tdb>
- ThermoHub pinned data: <https://github.com/thermohub/thermohub/tree/c3e4acf4531204e4c2974c2d4ac5a1b96f37d5ba>
- ThermoHub licence: <https://github.com/thermohub/thermohub/blob/c3e4acf4531204e4c2974c2d4ac5a1b96f37d5ba/LICENSE>
- Miron, G. D. et al. (2016), *Geochimica et Cosmochimica Acta* 187, 41–78.
  <https://doi.org/10.1016/j.gca.2016.04.026>
- Miron, G. D. et al. (2017), *American Journal of Science* 317, 755–806, Tables 2, 4, 5 and Appendix A1.
  <https://doi.org/10.2475/07.2017.01>

The remaining-Miron continuation adds 14 individually verified Gibbs evaluations, three original
conductance-fit entropies republished in Appendix A1, and 18 explicitly labelled enthalpy
calculations from verified Miron G/S and open NBS elemental reference entropies. Hydrated
formula conversions use the open NBS H2O(l) Gibbs value. Each calculated or normalized
observation cites its original numerical inputs and NBS PDR DOI 10.18434/M32124 under the
NIST open licence. Article text, images and complete tables remain outside the distribution.
Inherited mineral calibration data and source-unresolved native H/S values remain in the
external review inventory. Two new buffered ligand references carry their selected species'
source attribution: H₃SiO₄⁻ from the normalized Miron evaluation and Al(OH)₄⁻ from the existing NBS record.

The metal-complex continuation retains individually sourced Gibbs energies, entropies and
published derived formation enthalpies from the original research below. Each value carries
`source_verified_estimate`, an exact property locator and a warning describing its model basis.
Existing preferred values are preserved. Source-inherited properties are admitted only after
their original numerical ancestry is verified; unresolved native variants remain in the review
inventory. Journal articles themselves retain their original rights.

The 2014 dehydrated aqueous zinc formulas are normalized to the existing hydroxide formulas by
adding one H2O(l) unit. On 5 October 2026, these properties were transformed using the openly
licensed NBS digitization's liquid-water G, H and S (Table 1:O, CSV logical record 41).
Property locators retain the original facts, conversion and NBS attribution.

- Akinfiev, N. N. and Zotov, A. V. (2001), *Geochemistry International* 39(10), 990–1006,
  Table 2, p. 993; derivations pp. 995–999.
- Liu, W. and McPhail, D. C. (2005), *Chemical Geology* 221, 21–39, Table 1, p. 25.
  <https://doi.org/10.1016/j.chemgeo.2005.04.009>
- Akinfiev, N. N. and Tagirov, B. R. (2014), *Geochemistry International* 52(3), 197–214,
  Table 1, p. 199, original research rows.
  <https://doi.org/10.1134/S0016702914030021>
- Sverjensky, D. A., Shock, E. L. and Helgeson, H. C. (1997), *Geochimica et Cosmochimica
  Acta* 61(7), 1359–1412, Table 12, p. 1400, AuCl row and footnote h.
  <https://doi.org/10.1016/S0016-7037(97)00009-4>

## Rare-earth MINES continuation

The database retains 98 individually verified original model outputs from Migdisov,
Williams-Jones and Wagner (2009): 42 Gibbs energies and 56 fitted entropies for 14 rare-earth
monochloride, dichloride and monofluoride complexes. The alternative monochloride entropy
fits are both retained; the preferred fit follows the authors' 2016 selection. Each numerical
fact cites its original table, page, species, charge, unit and conversion. Shared evaluations
republished in 2016 retain their original 2009 identity.

An additional 56 enthalpies are explicitly calculated from these fits and the openly licensed
NBS elemental entropies, with the conventional aqueous proton-reference correction. They are
labelled estimates with unavailable total uncertainty and covariance. The new fluoride ligand
reference cites NBS PDR logical record 119, F⁻(aq). NIST is acknowledged.

The continuation also retains 41 property-specific USGS Bulletin 2131 evaluations, including
the separate boehmite and diaspore phases. Their original research and government reference
lineages and reported uncertainty intervals are cited. New JANAF-derived values and unresolved
CODATA compilation candidates remain in the external source review. USGS is acknowledged.

Scientific article text, images and complete tables are outside the distributed package.
The retained entries consist of individually referenced numerical facts and labelled calculations.

- Migdisov, A. A., Williams-Jones, A. E. and Wagner, T. (2009), *Geochimica et Cosmochimica
  Acta* 73, 7087–7109, Tables 4–7. <https://doi.org/10.1016/j.gca.2009.08.023>
- Migdisov, A. A. et al. (2016), *Chemical Geology* 439, 13–42, Tables 3 and 5.
  <https://doi.org/10.1016/j.chemgeo.2016.06.005>
- Original accepted manuscript: <https://www.osti.gov/biblio/1351190>
- Robie and Hemingway (1995), USGS Bulletin 2131, pp. 15–20.
  <https://doi.org/10.3133/b2131>
- USGS data policy: <https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits>
- NBS Tables with errata: <https://doi.org/10.18434/M32124>

## NEA02e nickel water-component normalization

The selected Ni(OH)3(-) Gibbs evaluation is from Gamsjäger et al.(2005),
*Chemical Thermodynamics of Nickel*, OECD Nuclear Energy Agency volume6,
TableIII-1 p.44, with the hydrolysis discussion on pp.101–102. OECD and NEA
are acknowledged. G=-590519 +/-9735J/mol is represented in the existing
HNiO2(-) water-component basis as -353390J/mol after subtracting the pinned
project-water reference -237129J/mol at298.15K and unit water activity.
The original source value, conversion and uncertainty convention are retained
in the observation locator. Existing numerical alternatives remain stored.

The clarified OECD data terms cover use, adaptation and redistribution,
including commercial use, subject to source-specific additional restrictions.
Every sublicense of work using these data must include the same OECD
acknowledgment requirement and require further sublicensees to pass it on.
The [source crosswalk](docs/sources/nea-derived-crosswalk.md) documents the
admission and remaining routes. The private permission correspondence and
complete source publications are retained outside the distribution.

## NEA02g3 qualified zirconium gas and sulfide estimates

OECD and the Nuclear Energy Agency are acknowledged for the selected
ZrO(g), ZrO2(g) and ZrS1.5 observations from Brown, Curti and Grambow,
with Ekberg (2005), *Chemical Thermodynamics of Zirconium*, NEA volume 8,
Table III-1 pp. 48/51 and sections V.3.3/V.5.1.1. The historical gas estimates
retain the scientific critique in Rand, Fuger, Grenthe, Neck and Rai (2008),
*Chemical Thermodynamics of Thorium*, NEA volume 11, Appendix F pp. 781–782.
The later review has its own bibliographic source record. Independent copied
JANAF/Glushko comparison data are outside this import. The sulfide record
documents the source's selected-table/discussion discrepancy. See
[the source review](docs/sources/nea-zirconium-disputed-evaluations.md).

The written NEA-TDB clarification and OECD data terms permit use, adaptation
and redistribution, including commercially, subject to source-specific
additional restrictions. Every sublicense of work using these data must
include the same OECD acknowledgment requirement and require further
sublicensees to pass it on. Source-data requirements apply alongside the
package's GPL-3.0-only licence. Complete source publications and private
correspondence retain their existing rights and stay outside the distribution.

## NEA02g2 zirconium compounds with elemental buffers

OECD and the Nuclear Energy Agency are acknowledged for selected ZrTe1.843,
ZrTe2, Zr5Te4, ZrTe3O8, ZrN and ZrC observations from Brown, Curti and
Grambow, with Ekberg (2005), *Chemical Thermodynamics of Zirconium*,
NEA volume 8, Table III-1 p. 52, sections V.5.3, V.6.1.1.1 and V.7.1.1.1.
The source's fitted endmember and ZrC0.96 thermal approximation remain explicit.
See [the source review](docs/sources/nea-zirconium-element-reservoirs.md).

The clarified OECD data terms permit use, adaptation and redistribution,
including commercially, subject to source-specific additional restrictions.
Every sublicense of work using these data must include the same OECD
acknowledgment requirement and require further sublicensees to pass it on.
Source-data requirements apply alongside the package's GPL-3.0-only licence.

NIST is acknowledged for the defined elemental formation-energy references
Te(cr), N2(g) and graphite from Wagman et al. (1982), *NBS Tables with errata*,
explicitly open non-SRD NIST Public Data Repository
[M32124](https://doi.org/10.18434/M32124), logical records 788, 835 and 1639,
under the [NIST open licence](https://www.nist.gov/open/license).
The reference zeros retain their thermodynamic definition. Auxiliary absolute
entropy tables and complete publications are outside this import; private
correspondence stays outside the distribution.

## NEA02g1 zirconium hydrolysis, gas, selenite and zircon

OECD and the Nuclear Energy Agency are acknowledged for selected values from
Brown, P. L., Curti, E. and Grambow, B., with Ekberg, C. (2005), *Chemical
Thermodynamics of Zirconium*, NEA volume 8, Table III-1 and sections V.1,
V.2.2, V.3.1.1, V.5.2.2 and V.7.2.1. Source formulas, water-component
conversions, uncertainty conventions and exact locators accompany the values.
See [the source review](docs/sources/nea-zirconium-hydrolysis.md).

Under the NEA-TDB-OECD-2026-10-14 clarification and OECD data terms, these
selected data may be used, adapted and redistributed, including commercially,
subject to source-specific additional restrictions. Every sublicense of work
using these data must include the same OECD acknowledgment requirement and
require further sublicensees to pass it on. This requirement applies to
these source data alongside the package's GPL-3.0-only licence.

NIST is acknowledged for the independently sourced free SeO3²⁻ and H4SiO4
reference values: Wagman et al. (1982), *NBS Tables with errata*, NIST Public
Data Repository [M32124](https://doi.org/10.18434/M32124), logical records
759 and 2941, under the [NIST open licence](https://www.nist.gov/open/license).
This is the explicitly open non-SRD release. H4SiO4 is converted to a neutral
SiO2 component using the project water reference. The convention follows
Shock et al. (1997), p. 932, Eq. 50 and adjoining discussion,
[DOI 10.1016/S0016-7037(96)00339-0](https://doi.org/10.1016/S0016-7037(96)00339-0).
Complete publications and private correspondence retain their existing rights
and stay outside the distribution.

## NEA02f nickel gas/liquid and stannane

OECD and the Nuclear Energy Agency are acknowledged for selected Ni(g),
Ni(l) and SnH4(g) data from Gamsjäger et al.(2005), *Chemical Thermodynamics
of Nickel*, NEA volume6, TableIII-1 p.44 and sectionsV.1.1/V.1.3; and
Gamsjäger et al.(2012), *Chemical Thermodynamics of Tin*, NEA volume12,
TableIII-1 p.44 and sectionVII.3.1. The source table and exact property
locators are described in [the phase review](docs/sources/nea-adjacent-phases.md).
All nine observations are admitted. The two new gases have an explicit
phase-selection scope; their G/H/S remain available as thermochemical evidence.

The NEA-TDB-OECD-2026-10-14 clarification permits use, adaptation and
redistribution, including commercially, subject to source-specific additional
restrictions. Every sublicense of work using these data must include the
same OECD acknowledgment requirement and require further sublicensees to
pass it on. Complete publications and private correspondence retain their
existing rights and stay outside the distributed package.

## NEA02g4 mixed-metal zirconium observations and free-cation references

OECD and the Nuclear Energy Agency are acknowledged for selected/evaluated
values from Brown, Curti and Grambow, with Ekberg (2005), *Chemical
Thermodynamics of Zirconium*, volume 8, Table III-1 p. 53, sections V.7.2.2,
V.7.2.3, V.7.2.5 and V.7.2.7, and Table V-39 p. 224. Both NASICON phosphate
Gibbs representations retain their own locators; source temperatures and
scientific qualifications remain explicit. See [the review](docs/sources/nea-zirconium-mixed-components.md).

The written NEA-TDB clarification and OECD data terms permit use, adaptation
and redistribution, including commercially, subject to source-specific
additional restrictions. Every sublicense of work using these data must
include the same OECD acknowledgment requirement and require further
sublicensees to pass it on. Source-data requirements apply alongside the
package's GPL-3.0-only licence. Private correspondence and complete source
publications retain their existing rights and stay outside the distribution.

NIST is acknowledged for the Ca²⁺, Sr²⁺, Na⁺ and Cs⁺ free-ion references from
Wagman et al. (1982), *NBS Tables with errata*, explicitly open non-SRD Public
Data Repository [M32124](https://doi.org/10.18434/M32124), CSV logical records
9196, 9635, 10732 and 13936, under the [NIST open licence](https://www.nist.gov/open/license).

## Original zirconium oxide-gas enthalpies

Murad, E. and Hildenbrand, D. L. (1975), *Thermochemical properties of gaseous
ZrO and ZrO2*, Journal of Chemical Physics 63(3), 1133–1139,
[DOI 10.1063/1.431439](https://doi.org/10.1063/1.431439), and Ackermann, R. J.
and Rauh, E. G. (1974), *Thermodynamic properties of ZrO(g) and HfO(g); a
critical examination of isomolecular oxygen-exchange reactions*, Journal of
Chemical Physics 60(6), 2266–2271,
[DOI 10.1063/1.1681357](https://doi.org/10.1063/1.1681357), are acknowledged
for three individually cited formation-enthalpy facts verified in their
original publisher-deposited abstracts. The 1974 value retains its 0 K condition
and exclusion from 298.15 K selection. Source uncertainty and verification scope
are recorded with each observation.

These entries use the established individual numerical-facts route, with
[U.S. Copyright Office factual-material guidance](https://www.copyright.gov/help/faq/faq-protect.html)
and the separately reviewed [AIP permissions policy](https://publishing.aip.org/resources/researchers/rights-and-permissions/permissions/).
The original articles and abstract prose retain their copyright. Distributed
material consists of numerical facts, citations and pourbase provenance notes.
No open article licence or blanket publisher permission is asserted; complete
articles, protected text, figures and table arrangements remain outside the
distribution. These independent original observations have their own reuse
records; the earlier NEA evaluations continue under OECD terms with the same
acknowledgment requirement carried into sublicenses and further sublicensees.
See [the source review](docs/sources/nea-zirconium-gas-upgrade.md).


## Zirconium hydride source review

Douglas, T. B. and Victor, A. C. (1958), *Heat Content of Zirconium and of
Five Compositions of Zirconium Hydride from 0° to 900°C*, Journal of Research
of the NBS 61, 13–23, [DOI 10.6028/jres.061.002](https://doi.org/10.6028/jres.061.002),
and Douglas, T. B. (1963), *High-Temperature Thermodynamic Functions for
Zirconium and Unsaturated Zirconium Hydrides*, Journal of Research of the
NBS 67A, 403–426, [DOI 10.6028/jres.067A.043](https://doi.org/10.6028/jres.067A.043),
are acknowledged for the original bulk-sample and assemblage review.
The [article-specific notice](https://pmc.ncbi.nlm.nih.gov/articles/PMC5319804/)
states that the Journal of Research papers are public domain in the United
States; third-party illustrations may retain separate rights. No source
figure is reproduced. [NIST's terms](https://www.nist.gov/open/license)
were recorded separately from any NIST SRD licensing route.

This checkpoint adds no observations to the release database. The held
NEA bulk values retain the existing OECD/NEA acknowledgment and downstream
acknowledgment requirement, including onward propagation by further
sublicensees. No independent publisher permission is inferred for the
unretrieved JACS 1958 or Turnbull 1964 articles. See
[the review](docs/sources/nea-zirconium-hydride-assemblage.md).


## Original sodium-zirconosilicate Gibbs observations

Aja, S. U., Wood, S. A. and Williams-Jones, A. E. (1997; proceedings volume
dated 1996), *The Solubility of Some Alkali-Bearing Zr Minerals in
Hydrothermal Solutions*, MRS Proceedings 432, 69–74,
[DOI 10.1557/PROC-432-69](https://doi.org/10.1557/PROC-432-69), is acknowledged
for three individually cited formation-G facts and reported intervals at
323.15 K, verified in the original publisher-deposited abstract.

These observations use the established individual original numerical-facts
route, with the [U.S. Copyright Office factual-material guidance](https://www.copyright.gov/help/faq/faq-protect.html)
and the completed project reuse review carried forward. The distributed
material contains independently transcribed numerical facts, citations and
our provenance. The article and abstract expression retain their copyright;
no open article licence or blanket publisher permission is asserted. Complete
abstracts, article text, figures and source table arrangements remain external.

Thoenen, T. and Curti, E. (2014), *The PSI/Nagra Chemical Thermodynamic
Database 12/07: Data Selection for Zirconium*, PSI Technical Memorandum
TM-44-14-04, section 8.2, p. 27
([report](https://www.psi.ch/sites/default/files/import/les/DatabaseEN/TM-44-14-04.pdf)),
is acknowledged for the cited experimental critique, paraphrased in our
provenance. No numerical PSI database table is imported.

These independent references are separate from NEA/OECD permission.
Earlier NEA observations retain OECD/NEA attribution and the same
acknowledgment requirement in sublicenses, including onward propagation by
further sublicensees. See [the source review](docs/sources/nea-zirconium-temperature-review.md).

## R11f original tin evaluations and crystalline burtite

Hummel, Berner, Curti, Pearson and Thoenen (2002), *Nagra/PSI Chemical
Thermodynamic Data Base 01/01*, Nagra NTB02-16, pp. 407, 409 and 415:
four isolated original reaction evaluations support attributed local historical
G alternatives. Source: https://media.nagra.ch/uploads/2022/08/e_ntb02-016.pdf.
Nagra's publication remains copyrighted. No report, source table arrangement,
inherited database or publication expression is redistributed. The limited
original numerical facts follow the project's individual-facts reuse policy.

Haase, Christensen, Nielsen, Koch, Galazka and Majzlan (2021), *Stability and
solubility of members of tin perovskites in the schoenfliesite subgroup*,
Chemical Thermodynamics and Thermal Analysis 1–2, 100005,
https://doi.org/10.1016/j.ctta.2021.100005, Table 7, burtite CaSn(OH)6:
three original numerical G/H/S results are included as isolated factual results.
The article is CC BY-NC-ND 4.0; its expression, figures and table arrangements
remain external under those terms. This numerical-facts use does not claim a
GPL-compatible licence to redistribute or adapt that article. No bulk source
table or separately licensed auxiliary dataset is included. See
https://creativecommons.org/faq/ and
https://www.copyright.gov/help/faq/faq-protect.html.

The historical local estimates retain NEA12 inputs. OECD and the OECD Nuclear
Energy Agency are acknowledged, with the relevant NEA tin-volume citations and
written clarification NEA-TDB-OECD-2026-10-14. The OECD data terms permit use,
adaptation and redistribution, including commercially, subject to applicable
source-specific additional restrictions. Every sublicense of work using these
data must include the same OECD acknowledgment requirement and require further
sublicensees to pass it on. NIST is acknowledged for retained open non-SRD NBS
reference inputs under https://www.nist.gov/open/license, without warranty.
Separate publication/source rights remain applicable. The full evidence and
scientific scope appear in docs/sources/tin-original-routes.md and database
metadata; private correspondence and complete source publications remain external.

## R11g original palladium hydrolysis and ammine results

Hummel et al. (2002), Nagra NTB02-16, pp. 244–245,
https://media.nagra.ch/uploads/2022/08/e_ntb02-016.pdf, and Hummel and Thoenen
(2023), Nagra NTB21-03, pp. 755/757,
https://media.nagra.ch/uploads/2023/05/NTB-21-03.pdf: four isolated original
hydrolysis-model results support attributed local G estimates, retaining both
historical and revised variants. Nagra's publication copyright and reproduction
rights remain applicable. Complete reports, expression, figures, table layouts
and bulk source databases stay external.

Rasmussen, L. and Jørgensen, Chr. K. (1968), *Palladium(II) Complexes. I.
Spectra and Formation Constants of Ammonia and Ethylenediamine Complexes*,
Acta Chemica Scandinavica 22, 2313–2323,
https://doi.org/10.3891/acta.chem.scand.22-2313: four isolated original
stepwise formation constants support local ammine G estimates. The archive
retains Acta Chemica Scandinavica copyright; publication expression remains
external. Numerical use follows the established individual-original-facts route,
with source media and original approximate step widths preserved. No blanket
open publication licence or JAEA data grant is asserted. Supporting factual-data
guidance: https://creativecommons.org/faq/ and
https://www.copyright.gov/help/faq/faq-protect.html.

NIST is acknowledged for the explicitly open non-SRD NBS digitization,
PDR M32124, https://doi.org/10.18434/M32124, under
https://www.nist.gov/open/license, without warranty. Retained Pd2+, NH3(aq)
and liquid-water anchors support these estimates; the new neutral NH3 reservoir
matches the already selected open NBS observation. Existing OECD credit and
the same acknowledgment requirement for further sublicensees continue to apply
to NEA-derived material elsewhere in this distribution. See
`docs/sources/palladium-original-routes.md` for source-specific scope and holds.

## R11h original europium evaluations

Hummel et al. (2002), Nagra NTB02-16, pp. 150/155/160,
https://media.nagra.ch/uploads/2022/08/e_ntb02-016.pdf, and Hummel and Thoenen
(2023), Nagra NTB21-03, pp. 900/1003,
https://media.nagra.ch/uploads/2023/05/NTB-21-03.pdf: six isolated original
numerical reaction evaluations support local europium G estimates, preserving
original source intervals, variants and phase/model qualifications. Their use
follows the established individual-original-numerical-facts route. Nagra's
publication copyright and reproduction/storage rights remain applicable;
complete publications, protected expression, figures, table layouts and bulk
source databases remain external. Supporting factual-data guidance:
https://creativecommons.org/faq/ and
https://www.copyright.gov/help/faq/faq-protect.html.

NIST is acknowledged for explicitly open non-SRD NBS PDR M32124 reference
inputs, https://doi.org/10.18434/M32124, under
https://www.nist.gov/open/license, without warranty. The existing Miron 2017
silicate reference carries its original-result/open-water review and attribution.
Existing OECD credit and the same acknowledgment requirement for further
sublicensees continue for NEA-derived material elsewhere; they do not license
Nagra publications. Original amorphous-source, unknown carbonate hydration and
superseded strong-silicate-model issues remain separately documented in
`docs/sources/europium-original-routes.md` and database reuse metadata.

## R11i NEA nominal ferrihydrite models

Lemire, R. J. et al. (2013), *Chemical Thermodynamics of Iron, Part 1*,
OECD Nuclear Energy Agency, NEA No. 6355, pp. 227–228; selected Fe3+
reference p. 44 and evaluated auxiliary OH− reference p. 55:
https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/6355-vol13a-iron.pdf.
OECD and NEA are acknowledged for two adjusted nominal ferrihydrite enthalpies,
a six-line entropy estimate and the calculated solubility used in an attributed
local formation-G adaptation. These are qualified model suggestions, outside
the normal NEA selected set; original calorimetric alternatives remain.

Reuse follows the OECD data terms and written clarification
NEA-TDB-OECD-2026-10-14, subject to applicable source-specific restrictions:
https://www.oecd.org/en/about/terms-conditions.html. Every sublicense of work
using these data must include the same OECD acknowledgment requirement and
require further sublicensees to do the same. No separate additional restriction
was identified on these NEA-authored evaluations. Source-specific rights remain
applicable. Private permission correspondence and complete publications stay
external. See `docs/sources/iron-hydrolysis-carbonate-routes.md` for the model,
phase, uncertainty and native-source holds.

## MP17a corrected NBS cobalt Gibbs energy

NIST is acknowledged for the corrected HCoO2− aqueous formation Gibbs energy
in the explicitly open non-SRD NBS digitization, DOI 10.18434/M32124,
https://doi.org/10.18434/M32124. Source file
`NBS_Tables_with_ErratumValues.csv`, logical record 5482, column 9, gives
−345.5 kJ/mol with an asterisk indicating the 1989 erratum correction.
Reed (2020), section 3, p. 2, explains that marker:
https://nvlpubs.nist.gov/nistpubs/jres/125/jres.125.007.pdf.

Reuse follows https://www.nist.gov/open/license and the NIST non-SRD data
acknowledgment and warranty qualifications reproduced above. Conversion on
19 October 2026 multiplies kJ/mol by 1000; the stored value is −345500 J/mol.
The source provides no numerical uncertainty. The older Shock et al. (1997)
G and entropy observations remain available. Historical corrected NBS values
and the Brookins/Latimer hafnium source hold are documented separately in
`docs/sources/mp-cobalt-hafnium-check.md`. No new Brookins, Latimer or NIST
SRD observation is imported in this batch. Existing OECD attribution and
the same acknowledgment requirement for further sublicensees remain in force
for the NEA-derived material elsewhere in the distribution.

### R11j original silicate evaluations

Grenthe et al. (1992), *Chemical Thermodynamics of Uranium*, OECD2004 reprint,
Table IV.1 p.72 and silicon discussion pp.394–399, and Guillaumont et al.(2003),
*Update on the Chemical Thermodynamics of Uranium, Neptunium, Plutonium,
Americium and Technetium*, Table8-1 pp.141–142, supply NEA-authored evaluated
H2SiO4(2−) G/H/S and H4Si4O12(4−) G. OECD and the OECD Nuclear Energy Agency
are acknowledged through these citations. Reuse follows written clarification
NEA-TDB-OECD-2026-10-14 and the
[OECD data terms](https://www.oecd.org/en/about/terms-conditions.html), including
commercial adaptation and redistribution. Every sublicense of work using these
data must include the same acknowledgment requirement and require further
sublicensees to do the same. No separate third-party restriction was identified
on these NEA-authored evaluations. Historical editions and reference discrepancies
are identified in the observation locators.

Hummel et al.(2002), Nagra NTB02-16 pp.315–317; Hummel(2014), PSI TM-44-12-05
pp.9–10/13; and Hummel and Thoenen(2023), Nagra NTB21-03 pp.966/969/972/994,
provide original reaction evaluations. Isolated numerical facts and locally
derived formation-G estimates follow the carried original-result reuse review.
Publication copyright and reproduction/storage rights remain applicable; full
reports, table expression and bulk database files stay outside the distribution.
NEA permission does not extend to these reports. Open non-SRD NBS reference
inputs acknowledge NIST under its open licence and are distributed without warranty;
the retained Miron2017 input carries its completed original-result review.
Shared experimental ancestry, uncertain stoichiometry and missing total-G
covariance are explicit. The 20°C/1.2M alkaline-Al constant remains on hold.
See [the silicate source review](docs/sources/silicate-original-routes.md).

### R11k pyrophosphate evaluations and reference alignment

Grenthe etal.(1992), *Chemical Thermodynamics of Uranium*, OECD2004 reprint,
TableIV.1 pp.69–70 and sectionVI.3.2 pp.386–389, and Guillaumont etal.(2003),
*Update on the Chemical Thermodynamics of Uranium, Neptunium, Plutonium,
Americium and Technetium*, Table8-1 pp.139–140 and Table8-2 pp.151–152,
supply NEA-authored composite formation-G evaluations and selected reactions
for P2O7(4−)/HP2O7(3−). OECD and the OECD Nuclear Energy Agency are acknowledged
through those citations. Under written clarification NEA-TDB-OECD-2026-10-14
and the [OECD data terms](https://www.oecd.org/en/about/terms-conditions.html),
these data may be used, adapted and redistributed, including commercially,
with appropriate attribution. Every sublicense of work using these data must
include the same acknowledgment requirement and require further sublicensees
to do the same. No additional restriction was identified on these NEA-authored
composite numerical evaluations. The official November2005 errata were checked.
Separately restricted tables and complete publications remain outside this import.

Six additional G/H/S cells use the explicitly open non-SRD NBS PDR M32124
CSV, logical records1281/1357. NIST is acknowledged under its open licence;
the data are distributed without warranty. Two local NEA-reaction/NBS-reference
G estimates preserve inputs and shared ancestry. The former NBS free-pyrophosphate
pin remains in metadata and as a retained G observation; the current reference
matches policy-selected NEA G. Complete reports and private permission evidence
stay external. See [the pyrophosphate review](docs/sources/pyrophosphate-original-routes.md).

### R11l final original-source routes

Grenthe et al. (1992), *Chemical Thermodynamics of Uranium*, Table IV.1 p.67;
Guillaumont et al. (2003), *Update on the Chemical Thermodynamics of Uranium,
Neptunium, Plutonium, Americium and Technetium*, Table8-1 pp.137–138; and Olin
et al. (2005), *Chemical Thermodynamics of Selenium*, TableIV-1 p.75 and
pp.433–436: OECD and the OECD Nuclear Energy Agency are acknowledged for
own composite sulfide, iodic-acid and aqueous CN/HCN evaluations. Written
clarification NEA-TDB-OECD-2026-10-14 and the
[OECD data terms](https://www.oecd.org/en/about/terms-conditions.html) apply.
Every sublicense of work using these data must include the same acknowledgment
requirement and require further sublicensees to do the same. Source-specific
restrictions remain applicable. Scientific ancestry does not extend this
permission to independently copied third-party tables.

Wagman et al. (1982), *The NBS Tables of Chemical Thermodynamic Properties*,
explicitly open non-SRD [NIST PDR M32124](https://doi.org/10.18434/M32124),
with errata: NIST acknowledged for Ra(cr), Ra(2+), RaSO4(cr), high-temperature
Nb2O5(cr), CN(−), HCN(aq), and reference inputs. The
[NIST open licence](https://www.nist.gov/open/license) applies; data are
provided without warranty. Existing release/licence reviews carry forward.

Hummel and Thoenen (2023), *The PSI/Nagra Chemical Thermodynamic Database
2020*, NTB21-03, pp.217/232–233/262–263/558–559/568–569,
https://media.nagra.ch/uploads/2023/05/NTB-21-03.pdf: authors' own regression,
SIT and analogy results support separately cited local estimates. The existing
isolated-original-numerical-facts review is carried forward. Nagra retains
copyright and reproduction/storage restrictions; this is separate from an
open licence for its report or exports. Source Cp and supporting model outputs
are retained as numerical metadata. Whole tables, figures and prose remain
external. Independently inherited commercial selections remain held.

Langmuir and Riese (1985), *The thermodynamic properties of radium*, GCA49,
1593–1601, https://doi.org/10.1016/0016-7037(85)90264-9: original isolated
numerical facts verified in the publisher abstract support local Ra solubility
and RaOH association estimates on open reference inputs. The complete article
has no open-licence claim. Original solid-enthalpy sign issues remain held.
See [all source and scientific decisions](docs/sources/final-original-routes.md).

### R11m precipitated manganese carbonate

Garrels, R. M., Thompson, M. E. and Siever, R. (1960), *Stability of some
carbonates at 25 degrees C and one atmosphere total pressure*, American
Journal of Science 258, 402–418, https://doi.org/10.2475/ajs.258.6.402:
one individually attributed original precipitated-MnCO3 formation-G estimate
from the p.402 opening table, with material limitations on p.409. Reuse follows
the carried individual-original-numerical-facts policy. The article itself has
no asserted open licence; complete text, tables, figures and OCR remain
external. The original value and standard pressure remain in its locator.

Grenthe et al. (1992), *Chemical Thermodynamics of Uranium*, sectionII.3.2,
pp.24–27, Eq.II.38 p.26: OECD and the OECD Nuclear Energy Agency are
acknowledged for the standard-state pressure method used in the local
1-atm to 1-bar adaptation. The carried NEA-TDB-OECD-2026-10-14 clarification
and [OECD data terms](https://www.oecd.org/en/about/terms-conditions.html)
remain applicable. Every sublicense of work using these data must include
the same acknowledgment requirement and require further sublicensees to do
the same. Source-specific restrictions remain applicable.

Wagman et al. (1982), *The NBS Tables of Chemical Thermodynamic Properties*,
explicitly open non-SRD [NIST PDR M32124](https://doi.org/10.18434/M32124)
with errata: NIST acknowledged for precipitated MnCO3 H, logical record6408,
column8. The [NIST open licence](https://www.nist.gov/open/license) applies;
data are provided without warranty. Existing source/licence review carries
forward. Separate source preparations and missing uncertainty remain explicit.
See [the source and pressure review](docs/sources/synthetic-manganese-carbonate.md).

### R11n niobium aqueous fitted models

Peiffert, C., Nguyen-Trung, C., Palmer, D. A., Laval, J. P. and Giffaut, E.
(2010), *Solubility of B-Nb2O5 and the Hydrolysis of Niobium(V) in Aqueous
Solution as a Function of Temperature and Ionic Strength*, Journal of
Solution Chemistry 39, 197–218, https://doi.org/10.1007/s10953-010-9495-z:
twelve individually attributed original G/H/S fitted-model results from
Table 7 p. 216, including a local neutral water-equivalent normalization.
Reuse follows the carried individual-original-numerical-facts policy.
No open licence for the article is asserted; complete source, table layout,
prose, figures and OCR remain external. Source intervals and the authors'
oxide-reference assumption remain explicit.

NIST is acknowledged for explicitly open non-SRD PDR M32124 reference data,
https://doi.org/10.18434/M32124, including water logical record 41 and the
previously reviewed high-temperature-labelled oxide. The NIST open licence,
https://www.nist.gov/open/license, applies; data are distributed without
warranty. No restricted source table or new whole-publication licence is
inferred. Earlier OECD acknowledgments and the requirement for every further
sublicensee to pass on the acknowledgment requirement remain in force for
NEA inputs elsewhere in this database.
See [the niobium source and standard-state review](docs/sources/niobium-standard-state.md).

R11t adds an attributed comparison with the original federal research of
J. L. Waring, R. S. Roth and H. S. Parker (1973), *Temperature-Pressure Phase
Relationships in Niobium Pentoxide*, Journal of Research of the National
Bureau of Standards A77A(6), 705–711,
https://doi.org/10.6028/jres.077A.042, Table 2, p. 708. NIST is acknowledged
under its [open licence](https://www.nist.gov/open/license), without warranty.
The comparison qualifies phase identity; it adds no absolute thermochemistry.

Computational context is attributed to Benjamin Grimm, Moritz Nitzsche and
Thomas Bredow, *Energetic Order of Nb2O5 and Ta2O5 Polymorphs* (2022),
Physica Status Solidi B, 2200052, https://doi.org/10.1002/pssb.202200052.
Copyright 2022 The Authors; published by Wiley-VCH GmbH under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Pourbase supplies its own brief interpretation; no calculated energies or
article tables are imported. Existing Peiffert numerical-fact reuse and NEA
OECD acknowledgment obligations continue separately.

### R11u supplemental alkaline-niobium adaptations

Hummel, W. and Thoenen, T. (2023), *The PSI Chemical Thermodynamic Database
2020*, Nagra Technical Report 21-03, section 17.4.2.2, p. 667,
https://media.nagra.ch/uploads/2023/05/NTB-21-03.pdf, supplies four original
author SIT/regression results adapted into local hexaniobate formation-G
estimates. Copyright 2023 Nagra, Wettingen, Switzerland. The established
individual original numerical-facts route covers these narrowly cited model
outputs; no open licence is asserted for the report, tables or database
export. Complete publication, tables, prose, figures and OCR remain external.

The pinned original Peiffert2010 neutral observation and open non-SRD NBS
water retain their existing reuse reviews, NIST acknowledgment and warranty
statement. Filella–May2020 CC BY-NC-ND article/supplement data, conditional
sodium-salt constants and restricted compilations supply no new observations
in this batch. Existing OECD credit and the requirement for further
sublicensees to pass on the acknowledgment requirement remain in force
independently. See [the source and model review](docs/sources/niobium-alkaline-models.md).

### R11o open modern radium solubility evaluations

Copyright 2022 Paul L. Brown, Artem V. Matyskin and Christian Ekberg.
*The aqueous chemistry of radium*, Radiochimica Acta 110(6–9),505–513,
https://doi.org/10.1515/ract-2021-1141, published by De Gruyter, is licensed
under [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). The original
licence footer is verified in the Chalmers advance-online PDF, article p.1 / PDF p.2.
Two evaluated solid-solubility entries in Table 1, article p.4 / PDF p.5, are adapted.
Changes made by pourbase: convert the evaluated logK values into local
formation-G estimates with independently verified open ionic references;
record pressure/model assumptions, partial intervals and unavailable total
uncertainty. No endorsement by the source authors or publisher is implied.
The source attribution and CC BY4.0 notice remain applicable to this material.

NIST is acknowledged for explicitly open non-SRD PDR M32124 ionic reference
inputs, https://doi.org/10.18434/M32124. Its open licence,
https://www.nist.gov/open/license, applies; data are distributed without
warranty. No new restricted SRD/JAEA or commercial compilation table is
imported. The original 2019 thermal table remains outside this batch.
Earlier OECD attribution and downstream acknowledgment requirements remain
applicable to the database's NEA material.
See [the source and model review](docs/sources/modern-radium-fits.md).

## R11p experimental radium carbonate adaptation

© 2023 Artem V. Matyskin, Burçak Ebin, Stefan Allard, Natallia Torapava,
Lars Eriksson, Ingmar Persson, Paul L. Brown and Christian Ekberg.
*Disordered Crystal Structure and Anomalously High Solubility of Radium
Carbonate*, Inorganic Chemistry 62(30), 12038–12049,
[DOI 10.1021/acs.inorgchem.3c01513](https://doi.org/10.1021/acs.inorgchem.3c01513).
The main article is licensed under
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

Pourbase adapts the authors' own Table6 solubility result to one local
nominal-endmember formation-G estimate using the open non-SRD NBS ionic
references acknowledged elsewhere in these notices. Changes include that
conversion and qualified endmember, nominal-temperature and ambient-pressure
assumptions; the source fit and adjusted intervals remain documented.
Attribution, the licence link and identification of these changes must be
retained when sharing this adaptation. No author endorsement is implied.
The separately deposited CC BY-NC4.0 supporting information is excluded
from the database and distributions. See
[the source review](docs/sources/experimental-radium-carbonate.md).

## R11q sign-corrected historical radium-solid estimates

Langmuir, D. and Riese, A. C. (1985), *The thermodynamic properties of radium*,
Geochimica et Cosmochimica Acta49(7),1593–1601,
[DOI10.1016/0016-7037(85)90264-9](https://doi.org/10.1016/0016-7037(85)90264-9).
Hummel, W.; Berner, U.; Curti, E.; Pearson, F. J.; Thoenen, T. (2002),
*Nagra/PSI Chemical Thermodynamic Data Base01/01*, NTB02-16, section5.16,
pp300–301, provides the explicit correction of the original solid
dissolution-enthalpy signs.

Pourbase retains four locally derived historical H/S estimates from the
individual original reaction facts, the cited sign correction and the
explicitly open non-SRD NBS references acknowledged above. This carries
the documented scoped numerical-facts route. Complete publications,
tables, prose, figures and database exports are excluded. Neither publication
is asserted open licensed. The conversion and historical evaluation scope
are identified in the database; modern carbonate G remains independent.
The NIST open release is acknowledged and distributed without warranty.
Existing OECD attribution and downstream acknowledgment obligations remain
applicable to NEA material. See [the source review](docs/sources/radium-solid-enthalpies.md).

## R11r higher aluminium-fluoride thermal adaptations

Latimer, W. M. and Jolly, W. L. (1953), *Heats and Entropies of Successive
Steps in the Formation of AlF6---*, Journal of the American Chemical Society
75(7),1548–1550, [DOI10.1021/ja01103a008](https://doi.org/10.1021/ja01103a008),
TableVI,p1549. The original numerical/convention checks use indexed original
journal text, crosschecked against retrieved primary PSI/Nagra evaluations:
Hummel etal.(2002),NTB02-16,p98, and Hummel and Thoenen(2023),NTB21-03,
pp263–264. The latter records the assumed finite-medium applicability at I=0.

Pourbase adapts a narrow selection of original calorimetric facts into four
local H/S estimates using independently reviewed G models and open ionic
references. This carries the documented isolated-original-numerical-facts
route. Neither complete publication is asserted open licensed. Publications,
whole tables, prose, figures and database exports are excluded. The local
cumulative conversion, finite-medium approximation and excluded original
mixed-medium entropy are documented. Full-resolution original-PDF access
is a separately recorded evidence follow-up.

One Al3+ H observation and recipe reference cells come from the openly
released, non-SRD NBS digitization, DOI10.18434/M32124, logical3571 and119.
NIST is acknowledged; those data retain the open-release attribution and
warranty statement above. Existing OECD attribution and downstream
acknowledgment obligations remain applicable to NEA material. See
[the source and model review](docs/sources/aluminium-fluoride-thermal.md).

## R11s native synthetic manganese-carbonate adaptation

USGS is acknowledged through Ball, J. W. and Nordstrom, D. K. (1991),
*User's manual for WATEQ4F, with revised thermodynamic data base and test cases
for calculating speciation of major, trace, and redox elements in natural waters*,
USGS Open-File Report91-183,Table2,p30,record190,
[DOI10.3133/ofr91183](https://doi.org/10.3133/ofr91183).
The selected synthetic-material result is attributed to Nordstrom etal.(1990),
*Revised Chemical Equilibrium Data for Major Water–Mineral Reactions and Their
Limitations*,ACS416,398–413,Table2III,p406,
[DOI10.1021/bk-1990-0416.ch031](https://doi.org/10.1021/bk-1990-0416.ch031),
with original numerical ancestry in Garrels, Thompson and Siever(1960).

Pourbase adapts one selected result into a local G estimate with separately
open, non-SRD NBS ionic references. USGS/NIST attribution and the carried
federal numerical-fact/evaluation route remain applicable; no blanket licence
for other source rows or restricted upstream tables is inferred. NIST data
are distributed without warranty under the open-release notice above.
The local conversion, nominal material category and bicarbonate-reference
reconciliation are identified. The complete ACS chapter is not asserted
open licensed. Complete publications, tables, prose, figures and database
exports are excluded. Existing OECD attribution and downstream acknowledgment
obligations remain applicable to NEA material. See
[the source review](docs/sources/native-synthetic-manganese.md).
