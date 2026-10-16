# NEA calcium-silicate formula review

NEA02g4a checks the held `NEA02d-086` row. **The formula and original molar
basis remain unresolved. No observations or species are added.** The database
retains 989 species and 3,142 observations, with 869/790/671 selected G/S/H
properties. All previous numerical observations and preferred values are preserved.

## Printed formula and numerical consequence

Brown, Curti and Grambow, with Ekberg (2005), *Chemical Thermodynamics of
Zirconium*, NEA volume 8, Table III-1 p.53 and section V.7.2.2 p.220,
prints `Ca2ZrSi3O12`. With Ca(II), Si(IV) and O(−II), neutrality requires
Zr(VIII). The accompanying discussion identifies a CaO–SiO2–ZrO2 system.
Both the selected table and the chapter repeat the same formula.

The held selected values are G = −5,951,457 ±15,076 J/mol,
H = −6,283,000 ±15,000 J/mol and S = 297.6 ±5.0 J/(mol K),
at 298.15 K and 1 bar, per the printed formula unit. Published uncertainty
intervals retain their source interpretation. Heat capacity remains in the
external thermal-property review. [NEA source](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/chemical_thermodynamics_of_zirconium_volume_8.pdf).

Table III-1 marks G as internally calculated from H and entropy. Using the
review's elemental entropies gives, for the printed formula:

`G = H − T [S − Σ n(element) S(element)] = −5,951,456.6037 J/mol`.

This reproduces the selected G within 0.4 J/mol rounding. The calculation
therefore supplies evidence that the inconsistent stoichiometry entered the
Gibbs evaluation. It supports keeping the numerical assignment under review.

A hypothetical change to `Ca2ZrSi4O12`, holding H/S fixed solely for the
sensitivity check, shifts G by **+5,608.2015 J/mol**. This calculation
illustrates why changing the formula requires rechecking the numerical
properties. It supplies no justified replacement observation. Other
charge-balanced edits are also possible; charge balance alone cannot choose
the measured identity or establish its molar basis.

## Original-source retrieval

NEA cites three Shibanov–Chukhlantsev studies:

| NEA code | Publication as cited by NEA | Retrieval status |
|---|---|---|
| 69SHI/CHU | Russian Journal of Inorganic Chemistry 14 (1969), 337–338; approximate thermodynamic calculations for zirconates | Article pages unretrieved. |
| 71SHI/CHU | Zhurnal Fizicheskoi Khimii 45 (1971), 1635–1637; solid-state reactions in CaO–ZrSiO4 | Original article pages unretrieved; issue 7 and its page range confirmed in the university holdings catalogue. |
| 78SHI/CHU | Zhurnal Fizicheskoi Khimii 52 (1978), 1832–1833; high-temperature specific heats and enthalpies of calcium zirconosilicates | Original article pages and original title unverified; issue 7 page range confirmed. |

Bibliographic details come from NEA volume 8 pp.451, 453 and 462.
The [1971](https://www.chem.msu.ru/rus/jlib/cyr/20/41.html) and
[1978](https://www.chem.msu.ru/rus/jlib/cyr/20/48.html) MSU catalogue pages
provide holdings. They do not provide the original measurements.
The exact formula, sample identity, original amount basis, calorimetric units
and thermal evaluation must be established from those articles or an
authoritative correction before assigning their values to a revised formula.

## Separate primary-study leads

Jacob and Waseda (1994), [DOI 10.1111/j.1151-2916.1994.tb04543.x](https://ceramics.onlinelibrary.wiley.com/doi/abs/10.1111/j.1151-2916.1994.tb04543.x),
report oxide-reaction measurements for `Ca2ZrSi4O12` at 973–1273 K.
Róg et al. (2005), [DOI 10.1016/j.ssi.2004.11.020](https://badap.agh.edu.pl/publikacja/22459),
report measurements for that formula and Ca3ZrSi2O9 at 923–1273 K.
These primary abstracts identify useful independent candidates. Their full
numerical data and a link to the held NEA H/S basis have not been verified.
The AGH record marks its article as outside open access. Source-specific
numerical reuse and temperature-conversion reviews remain necessary before
any import. Access to an abstract establishes no open-data licence.

The later studies' formulas establish no reassignment of the NEA values.
Phase identity also needs checking: the 1994 abstract's orthorhombic wording
is retained as source wording. No structure or Materials Project match is
assigned during this review.

## Admission and permission status

The active hold is **scientific identity and molar basis**. Schema 9 already
supports independent calcium and silica reservoirs. The existing NEA reuse
review and `NEA-TDB-OECD-2026-10-14` permission continue to apply to NEA's
selected/evaluated numerical data, with the distributed OECD attribution and
downstream acknowledgment requirement. Other sources retain their own reuse
status. Private correspondence and source publications remain external.

The finite search and arithmetic checkpoint is recorded. Original-source
verification (`NEA02g4a1`) and the calcium admission hold remain open.
The original zirconium inventory remains **25/27 rows admitted**, with ZrH
and this calcium row held. Three admitted 323.15 K observations have separate
298.15 K calculation holds. The next independent task is the oxide-gas
source upgrade (`NEA02g3b`).
