# Third-party data and attribution

pourbase combines individual thermochemical values traced to scientific sources with selected
Materials Project records. The GPL-3.0 license covers the code and the compilation. Source-specific
terms and scientific citation obligations remain in force.

## NIST and NBS

Most NBS values come from the NIST Public Data Repository dataset *The NBS Tables of Chemical
Thermodynamic Properties* (Wagman et al. 1982, with errata; doi:10.18434/M32124), published under
the NIST open licence. NIST is acknowledged as the source of these data; the dataset is
distributed without warranty. <https://www.nist.gov/open/license>

On 5 October 2026, 86 additional evaluated NBS properties were retained as source-linked
alternatives. Values in kJ/mol were converted to J/mol; entropy units were retained. Each
observation cites its digitized CSV logical record, formula, state and property column.
The existing preferred properties remain selected for calculations.

## USGS plattnerite evaluation

The database retains the plattnerite PbO2 Gibbs energy, formation enthalpy and absolute entropy
from Robie and Hemingway (1995), USGS Bulletin 2131, printed pp. 18 and 209, at 298.15 K and
1 bar. Source-specific uncertainty intervals and the government evaluation's lineage are
documented in each source locator and the species warning. The values are retained as
alternatives alongside the existing preferred evaluation. USGS-authored data are public domain;
USGS is acknowledged as the source.

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
