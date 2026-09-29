# Third-party data and attribution

pourbase combines individual thermochemical values traced to scientific sources with selected
Materials Project records. The GPL-3.0 license covers the code and the compilation. Source-specific
terms and scientific citation obligations remain in force.

## NIST and NBS

Many values are traced to NIST Chemistry WebBook SRD 69, NIST-JANAF, and the NBS Tables of Chemical
Thermodynamic Properties. Cite the exact source attached to each field. Consult NIST's current terms
when redistributing derived data:

- <https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications>
- <https://webbook.nist.gov/chemistry/>
- <https://janaf.nist.gov/>

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
confidence, and source URL. The `paper` folder contains comparison figures derived from these
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

## Software dependencies

Optional dependencies are installed from their own distributions and are not vendored:
`mp-api` (BSD 3-Clause) and pymatgen (MIT) for the live comparison; PySide6 (LGPL-3.0),
pyqtgraph (MIT) and keyring (MIT) for the desktop application.
