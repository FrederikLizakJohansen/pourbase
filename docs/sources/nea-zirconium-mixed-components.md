# NEA zirconium mixed-metal compounds

NEA02g4 reviews the twelve mixed-metal rows 086–097 of Brown, Curti and
Grambow, with Ekberg (2005), *Chemical Thermodynamics of Zirconium*, NEA
volume 8, Table III-1, printed p. 53. The batch retains **24 observations
and 11 species**, making **20 additional 298.15 K properties** available.
All earlier observations and preferred selections are preserved.

| Source formula | Retained properties | Conditions and decision |
|---|---|---|
| Ca2ZrSi3O12 | Held | Formula in table and section V.7.2.2 requires Zr(VIII) with Ca(II), Si(IV), O(−II); original composition/molar basis needs checking. |
| Ca3ZrSi2O9 | G/H/S | Exact formula; mineral name and space group unassigned. |
| SrZrSi2O7 | G/H/S | Solution-calorimetric H and corrected low-temperature S. |
| Sr6ZrSi5O18 | H | G/S remain unavailable. |
| Na2ZrSiO5 | G/H/S | NEA's enlarged entropy interval retained. |
| Na2ZrSi2O7 | G/H/S | Selected thermal evaluation retained. |
| Na2ZrSi3O9(H2O)2 | G | 323.15 K observation retained; excluded from 298.15 K selection. |
| Na2ZrSi4O11 | G | 323.15 K observation retained; excluded from 298.15 K selection. |
| Na2ZrSi6O15(H2O)3 | G | 323.15 K observation retained; excluded from 298.15 K selection. |
| Na4Zr2Si3O12 | G/H/S | Fixed NASICON endmember; high-temperature evaluation extrapolated to 298.15 K. |
| NaZr2P3O12 | G/H/S and alternative G | Fixed NASICON endmember; two representations of the same source evaluation retained. |
| Cs2ZrSi2O7 | H | G/S remain unavailable. |

The source discussions are sections V.7.2.2 (pp. 220–221), V.7.2.3 (p. 221),
V.7.2.5 (pp. 222–224) and V.7.2.7 (p. 225). Exact per-observation locators
retain source conditions, precision, units and uncertainty intervals. NEA's
intervals are retained as published, generally total intervals corresponding
in principle to 95% confidence; no one-sigma conversion is inferred.

## Temperature and source alternatives

The explicit 323.15 K condition in the chapter takes precedence over the
generic 298.15 K selected-table heading for catapleiite, vlasovite and
elpidite. The original Aja, Wood and Williams-Jones study's publisher
abstract also identifies 50 °C. Their missing H/S prevents a justified
conversion to 298.15 K. Three reasoned default-policy exclusions retain the
observations as evidence. `ReportedValue.temperature_K` and `.pressure_bar`
expose the stored conditions through the species-record API.

For NaZr2P3O12, Table III-1 gives G = −4,556,968 ±20,222 J/mol, while
Table V-39 gives −4,565,000 ±20,000 J/mol for x = 0. Both are retained with
their own table locators. The 8,032 J/mol difference triggers the spread
review. An explicit policy override selects Table III-1, whose value
reproduces the source H/S calculation within reported rounding. These are
two representations of one evaluation, not independent experiments.

Both NASICON endmembers retain `source_verified_estimate` status and the
source's high-temperature extrapolation caveat. NEA notes intrinsic NASICON
stability above 600 K. The records describe fixed compositions; equilibrium
stability at low temperature and a variable-composition solution model
remain separate questions. Complete-formula energies are divided by the
two Zr atoms once during calculation.

## Independent buffered components

Schema 9 adds `additional_components(record_id, ligand_id, component_count)`.
The existing species ligand columns hold the first reference; this table
holds each further reference. Each row uses its own reference energy, charge,
stoichiometry and explicitly prescribed free activity. `BufferedComponent`
and `ThermodynamicSpecies.components` expose the complete component tuple.
The reader continues to support schema 7 and 8 files.

These solids use Zr as the conserved primary metal, a free Ca²⁺, Sr²⁺, Na⁺
or Cs⁺ reservoir, and either neutral silica or free PO4³⁻. A record enters
calculations only when every required reference is selected and has a Gibbs
energy. Neutral silica retains the existing H4SiO4 − 2 H2O convention and
direct free-H4SiO4 activity at unit water activity. All eleven formulas and
reaction coefficients balance with Zr(IV). The resulting chemical potentials
support conditional diagrams and closed **Zr** inventories with externally
buffered secondary elements. Closed inventories of all elements and solid
solutions require further model work. Temperature extrapolation excludes
these buffered species because component entropy data are unavailable.

Four independent free-cation references come from Wagman et al. (1982),
*NBS Tables with errata*, explicitly open non-SRD NIST Public Data Repository
[M32124](https://doi.org/10.18434/M32124):

| Reference | CSV logical record¹ | G, J/mol |
|---|---:|---:|
| Ca²⁺ | 9196 | −553580 |
| Sr²⁺ | 9635 | −559480 |
| Na⁺ | 10732 | −261905 |
| Cs⁺ | 13936 | −292020 |

¹ One-based CSV records including the two header records; state `ao`, column 9.
Source kJ/mol values are converted to J/mol. Unreported H/S and uncertainties
remain unassigned. These references retain their own NIST citation and reuse
basis; they are distinct from restricted NIST SRD sources.

## Reuse and remaining work

OECD and NEA are acknowledged for their selected/evaluated data under
`NEA-TDB-OECD-2026-10-14` and the OECD data terms, including source-specific
additional restrictions. Every sublicense of work using the data must carry
the same OECD acknowledgment requirement and require further sublicensees
to pass it on. The [distributed notices](../../THIRD_PARTY_NOTICES.md)
also acknowledge NIST under its open licence. Completed source reviews and
private permission evidence are carried forward. Complete publications and
Restricted Use correspondence remain outside the distribution.

Of the original 27 zirconium source/model holds, **25 rows are admitted**.
The two admission holds are ZrH's bulk/assemblage model and the inconsistent
calcium formula above. The three admitted 323.15 K observations have separate
298.15 K calculation holds. The historical oxide-gas source upgrade remains
open. Earlier source permission holds, heat-capacity routes and wider
exploration tasks retain their independent status.
