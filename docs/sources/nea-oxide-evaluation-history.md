# Original NEA SrO/BaO evaluation history

R11j3f adds six original NEA G/H/S observations on the existing SrO and BaO
records. It adds no species or previously missing property. All earlier NBS and
2020 NEA observations remain. R11j3f2 now selects the independently revised 2020 G/S values and retains
the two original 1992 H values. Ten reviewed observation lineages distinguish
independent revisions from actual reprints.

## Original values, conventions and reprint links

Grenthe et al. (1992), *Chemical Thermodynamics of Uranium*, Chemical
Thermodynamics 1, OECD Nuclear Energy Agency,
[Table IV.1, p. 77](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/uranium.pdf)
(PDF p. 95), gives the original selected values. Chapter VI.5, pp. 400–401
(PDF pp. 418–419), describes the evaluation, source research and 1-bar Gibbs
calculation. The 2003 update Table 8-1, p. 146 (PDF p. 186), repeats these six
cells. The 2020 Table 8-1, p. 161 (PDF p. 225), retains the same two H cells.
These eight reprint cells link to the original observations and create no duplicates.

| Species | Original G, kJ/mol | Original H, kJ/mol | Original S, J/(mol K) |
| --- | ---: | ---: | ---: |
| SrO(cr) | −559.939 ±0.914 | −590.600 ±0.900 | 55.440 ±0.500 |
| BaO(cr) | −520.394 ±2.515 | −548.100 ±2.500 | 72.070 ±0.380 |

Values refer to 298.15 K and 1 bar, per full MO formula unit. G/H are stored in
J/mol and S in J/(mol K). Quoted source total uncertainty widths retain their
approximately 95% meaning. These are original NEA selected evaluations with
shared experimental ancestry; the reprints are not independent measurements.

Chapter VI.5 explicitly states that the CODATA review supplies no Sr/Ba values.
NEA selects the strontium assessment of Busenberg, Plummer and Parker and the
barium research of Cordfunke, Konings and Ouweltjes, combines the selected H/S
and assigns source uncertainties. Its original G calculations use the 1-bar
reference state. All six cells are nonbold own NEA selections.

## Selection history and the explicit-lineage correction

Two H preferences change from original NBS to the class-A NEA values:
SrO −592.0 to −590.6 kJ/mol and BaO −553.5 to −548.1 kJ/mol. The 5.4 kJ/mol
BaO H spread remains explicit in the retained alternatives.

At the R11j3f checkpoint, the import also changed four G/S preferences from the 2020 revision to
the earlier values above. The earlier policy's `original_publication` tie-break treated
two NEA citations sharing first author Grenthe as an original and a reprint,
and therefore chose 1992. The 2020 review independently revised the G/S
selections using newer calorimetry. Its values remain eligible and stored:
SrO G −559.400, S 53.630; BaO G −519.780, S 70.010 in the units above.

R11j3f1 quantified the heuristic and verified the bounded four-choice proposal.
R11j3f2 implements it with explicit evaluation and derivation identities in
observation provenance. Current defaults select 2020 G/S: SrO −559400 J/mol
and 53.63 J/(mol K); BaO −519780 J/mol and 70.01 J/(mol K).
Original 1992 H remains selected. No numerical observation, uncertainty,
status, citation, fixed reference or phase identity changes. The source-linked
1992/2003 and 2020 H reprint cells remain linked without duplicate observations.

Within a reviewed evaluation and derivation, `original_publication` prefers
the original; independent revisions compete in later tie-breaks. Explicit
reprint links work across author changes. The compatibility stage retains the
legacy heuristic for unannotated groups, carrying the separate broader review
forward. Selector version `2-explicit-evaluation-lineage` is included in policy
fingerprints; at the R11j3f2 checkpoint the default fingerprint was `f8ee0083e857`.
Its recommendation fingerprint was `ae3314cf312519c9`. Optional lineage is visible through reported
evidence, candidate selection and record export. These changes add no source
or observation and carry the existing OECD attribution and downstream terms.

## Reuse, validation and continuing work

OECD and NEA are acknowledged. The supplied written NEA clarification and
[OECD data terms](https://www.oecd.org/en/about/terms-conditions.html) cover
these own selected/evaluated observations, including commercial adaptation and
redistribution, with citation and applicable additional restrictions checked.
When sharing or licensing work using these data, include the same OECD
acknowledgment requirement in sublicences and require further sublicensees
to do the same. Sources were accessed on 25 October 2026. The data permission
covers selected numerical results; complete publications and private correspondence
remain outside the distribution. Other sources' permission holds remain separate.

Staging preserves every previous SQL row, all phase metadata and all 31 fixed
references. It checks source units/widths, repeat-import behaviour, both source
reference cycles, six energies, four thermal calculations and eight supported
primary balances. All six preference changes are reviewed. All 75 default maps
and 1σ/3σ masks remain unchanged at 81×91 resolution. The original checkpoint used the 1992 H/G triplets. After R11j3f2, the
thermal model uses the 2020 S from the selected Gibbs source: formation
entropies are −104.646 J/(mol K) for SrO and −94.986 J/(mol K) for BaO.
The original H alternatives remain stored and selected as enthalpies.

Exact SrO/BaO structures retain their earlier unresolved status. Broader auxiliary
source work, further explicit-lineage reviews, R06/R07 and the original six crystalline
Gibbs gaps continue separately. Concurrent GUI implementation remains untouched.
