# Sodium zirconosilicates: source temperature and original intervals

NEA02g4b retains **three original-study Gibbs-energy observations** alongside
the NEA evaluations for existing sodium catapleiite, vlasovite and elpidite
records. All six observations keep their **323.15 K** temperature and remain
excluded from 298.15 K selection. This checkpoint adds **zero species and
zero newly available 298.15 K properties**. The database now contains
**989 species and 3,148 observations**; all earlier preferred IDs are preserved.

## Original observations and NEA alternatives

Aja, Wood and Williams-Jones, *The Solubility of Some Alkali-Bearing Zr
Minerals in Hydrothermal Solutions*, MRS Proceedings 432, 69–74,
[DOI 10.1557/PROC-432-69](https://doi.org/10.1557/PROC-432-69), explicitly
reports these formation Gibbs energies at 50 °C in its original author
abstract. The volume is dated 1996; copyright and the NEA bibliography use
1997. The citation preserves both dates.

| Existing record | Formula | Original G, J/mol | Original interval, J/mol | NEA interval, J/mol |
|---|---|---:|---:|---:|
| Sodium catapleiite | Na2ZrSi3O9(H2O)2 | −4654200 | 5600 | 20000 |
| Vlasovite | Na2ZrSi4O11 | −5181000 | 7300 | 20000 |
| Elpidite | Na2ZrSi6O15(H2O)3 | −7391000 | 11600 | 30000 |

Values and widths are multiplied by 1000 from kJ/mol. Each formula contains
one Zr; the two and three hydration waters are preserved. Formula mapping
follows NEA volume 8, p. 223, which cites the same study. The original
abstract supplies mineral names and numerical results; it establishes no
additional polymorph assignment. Source pressure and statistical confidence
convention are unspecified. New rows retain `pressure_bar = NULL` and the
reported widths without interpreting them as standard deviations.

The original results were checked against the publisher page and its
Crossref deposit. Full article methods were unavailable: the PDF endpoints
returned abstract HTML. The new rows have `source_verified_estimate` status
for the solubility-derived values and their experimental qualifications.
The original and NEA representations share experimental ancestry. Their
separate intervals document an evaluation change; they are not independent
measurements. NEA p. 223 explicitly widened the intervals to reflect the
experimental procedure. Its original values and locators remain unchanged.

## What a temperature conversion requires

At fixed standard pressure, `d(ΔfG)/dT = −ΔfS`. A one-temperature G value
therefore supplies no thermal slope. For constant formation heat capacity,
with no phase transition, a conversion from T1 to T0 would use

`G(T0) = G(T1) + (T1 − T0) ΔfS(T1)`

`         + ΔfCp [(T0 − T1) − T0 ln(T0/T1)]`.

Here T1 = 323.15 K and T0 = 298.15 K. The needed entropy is **formation
entropy**, including the elemental reference contributions. A justified
constant-entropy approximation still needs that slope and a bounded thermal
error. Three hypothetical slopes of −100, −500 and −1000 J/(mol K) would
produce corrections of −2.5, −12.5 and −25 kJ/mol. These examples show the
underdetermination; none is imported as a mineral property.

The available original Aja evidence supplies no phase-specific H/S/Cp set
for this conversion. The 1995 study
([DOI 10.1016/0883-2927(95)00026-7](https://doi.org/10.1016/0883-2927(95)00026-7))
also concerns 50 °C dissolution. Marr and Wood's
[1992 petrogenetic grid](https://msaweb.org/AmMin/AM77/AM77_810.pdf) supplies
qualitative phase constraints and explicitly unresolved entropy ordering on
p. 818. It provides no absolute thermal anchor for these values. The
[1992 polyhedral estimation study](https://doi.org/10.1127/ejm/4/6/1251)
is a further qualified-estimate lead; its numerical tables were unavailable
and no predicted entropy is introduced here.

Thoenen and Curti's [2014 PSI review](https://www.psi.ch/sites/default/files/import/les/DatabaseEN/TM-44-14-04.pdf),
section 8.2, p. 27, reports that the underlying dissolution experiments were
not reversed. New warnings attribute that criticism to its own source.
Their database's low-temperature scope also motivates exclusions there;
that scope decision supplies no proof that these minerals are
thermodynamically impossible. No numerical PSI database table is imported.

## Selection, calculations and reuse

Three additional source-specific exclusions keep the original observations
outside 298.15 K recommendations, alongside the three existing NEA exclusions.
The same physical three-species temperature hold now covers six observations.
An explicit source preference still respects these exclusions. Selecting
323.15 K in the existing extrapolation API supplies neither a conversion
nor missing buffered-component thermal data.

All 74 default phase maps and uncertainty masks, 118 buffered scenarios and
18 tested temperature/gas scenarios retain their previous results. Default
closed zirconium balances conserve metal. Selected G/S/H counts remain
869/790/671; the policy changes to record the three exclusions while the
recommendation fingerprint stays unchanged.

The new observations use the established **individual original numerical
facts** route, separately from NEA/OECD permission. Independently transcribed
facts, citations and our provenance are distributed; article and abstract
expression retain their copyright. Neither the publisher's generic terms
nor its Crossref deposit is represented as an open article licence. The
[U.S. Copyright Office guidance](https://www.copyright.gov/help/faq/faq-protect.html)
and completed project reuse review provide the recorded basis. The metadata
key `source_reuse_AjaWoodWilliamsJones1997_NEA02g4b_original` identifies this
scope. The PSI criticism is cited in our own words.

Earlier NEA evaluations retain their OECD attribution and the same
acknowledgment requirement in sublicenses, including onward propagation by
further sublicensees. Source documents, permission evidence and retrieval
responses remain external. See [the notices](../../THIRD_PARTY_NOTICES.md).

The original-evidence checkpoint is complete. NEA02g4b1 remains open for
phase-specific thermal data or reversible multi-temperature equilibrium
constraints, consistent aqueous references, pressure conventions and
uncertainty propagation. No justified 298.15 K conversion was found in this
review. The two original admission holds, gas reassessment and other sources'
permission holds remain separately tracked.

## Original-source retrieval follow-up, 16 October 2026

The publisher landing page for Aja, Wood and Williams-Jones (1992),
*On estimating the thermodynamic properties of silicate minerals*,
[DOI 10.1127/ejm/4/6/1251](https://doi.org/10.1127/ejm/4/6/1251),
provides an original one-page preview. It describes polyhedral estimates and
their limitations, and contains no mineral-specific numerical thermal table.
The complete 1992 tables and 1995/1997 experimental methods remain retrieval
targets. A bibliographic lead to a multi-temperature conference abstract
supplies no verified measurements for conversion.

The preview and retrieval record are preserved in the external R11 checkpoint;
no source prose or page image is distributed. No observation is added from
this preview. All six stored 323.15 K observations retain their three physical
298 K conversion holds. The bounded search checkpoint is complete; NEA02g4b1
remains open. R11 continues independently with [the selenium batch](nea-selenium.md).
