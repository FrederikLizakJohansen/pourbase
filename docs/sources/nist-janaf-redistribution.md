# JANAF redistribution review and conditional replacement plan

Reviewed 28 October 2026 against database SHA-256
`a204d6aaf706372cd1e76953d8dcff6c7121a89d84e453c19d2fdf441bfad0b2`,
repository revision `897d28cccfb9427dcd6652270565ac673e8eaa2e`, and default
selection policy `4b21643c5aa9`.

This is a separately scoped follow-up to the closed
[database expansion round](../database-expansion-closure.md). The identifiers
above describe the research baseline. The independent-source release decision
and its implementation are recorded below.

## Finding and decision

JANAF's redistribution status needs resolution. The research has established
no explicit open redistribution grant for our use. It has also not established
that every individual number requires permission as a matter of law. The
earlier family-check statement that NIST requires permission describes NIST's
published policy; it is insufficient by itself to decide the legal treatment
of this particular extraction.

The user subsequently confirmed that the original NIST request had already
been sent long ago without a response and instructed proceeding. The chosen
release route uses independently reviewed sources and archives direct JANAF
values privately. This is a release-policy decision; the legal question about
individual numerical-fact reuse remains unresolved. No new message was sent
and no NIST grant is inferred. NEA's written OECD clarification and all other
sources' separate conditions remain in force.

## Evidence checked

- [JANAF's own credits](https://janaf.nist.gov/janbanr.html) identify SRD 13
  and carry a Department of Commerce copyright reservation. That page names
  the 1985 edition; the website's main page identifies the 1998 content.
- [NIST's SRD policy](https://www.nist.gov/srd/public-law) states a prior
  permission requirement. The [general licensing page](https://www.nist.gov/open/license)
  treats SRD separately from the broad grant for other NIST data.
- [15 USC 290e](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title15-section290e&num=0&edition=prelim)
  authorizes SRD copyright despite the usual federal-work limitation. Federal
  authorship alone therefore does not settle JANAF's status.
- The [official JANAF repository metadata](https://data.nist.gov/rmm/records/mds00xmwqs)
  has `accessLevel: public`, identifies the resource as `nrd:SRD`, and links
  its `license` field to the general NIST licensing page. The open NBS
  digitization links to the same page but lacks the SRD type. This generic
  link does not establish a JANAF-specific waiver of the SRD reservation.
- The [U.S. Copyright Office's compilation guidance](https://www.copyright.gov/circs/circ14.pdf)
  distinguishes copyright in a compilation's selection and arrangement from
  the underlying data. This is a substantive reason to investigate our use of
  individually selected numerical facts. Applying that principle to evaluated
  JANAF outputs and international redistribution needs a specific assessment.
- The [Copyright Office's fair-use FAQ](https://www.copyright.gov/help/faq/faq-fairuse.html)
  explains that there is no automatic permitted percentage. Our limited
  extraction is relevant context, not a numerical safe harbour.
- The [NIST store agreement](https://shop.nist.gov/ccrz__CCPage?pageKey=SRDTC)
  reserves redistribution and discusses separate developer/distributor
  agreements. It concerns licensed store products; this review does not
  assume its purchase-contract provisions bind use of JANAF's public website.

No JANAF-specific small-extraction permission or applicable open licence was
found in the checked website, metadata and NIST policies. Free access and the
age of the tables do not themselves resolve the question. The preserved
correspondence contains the NIST request and the independent NEA clarification;
no NIST grant was found there. NEA's OECD permission and the NBS digitization's
reuse basis remain separate and available.

## Measured scope

The reviewed baseline retained **100 direct JANAF observations on 49 species**:
26 formation Gibbs energies, 26 formation enthalpies and 48 absolute entropies.
Its default policy chose **17 properties on six species** from JANAF.
Unselected alternatives are also part of the distributed database.

A read-only simulation excludes all 100 observations from selection, preserving
the other policy rules. It finds existing policy-eligible non-JANAF candidates
for **87 properties**: 69 NBS, 14 NEA, three USGS and one Bureau of Mines.
These routes carry their completed source reviews. Candidate availability
does not itself perform a new scientific or rights review.

Four preferred properties would move to existing candidates: the G/H/S triplet
of plattnerite PbO₂ and the entropy of alpha-TiO. Thirteen properties would
become unavailable:

| Existing species identity | Properties needing another eligible observation | Carried review condition |
| --- | --- | --- |
| Ba(OH)₂, anhydrous | G, H, S | Polymorph/specimen match, calorimetric inputs and entropy origin |
| Sr(OH)₂, anhydrous | G, H, S | Specimen match, original enthalpy inputs and entropy table |
| Delta-TiH₂ | G, H, S | Composition/phase match and independent numerical ancestry |
| Alpha-TiO | G, H | Vacancy ordering, original formation measurements and compatible references |
| Stoichiometric FeO endmember | G, S | Exact composition and an independent evaluation; existing NBS H remains available |

Without additional observations, selected G/S/H counts would change from
**1327/1296/1352 to 1322/1292/1348**. The simulation measures selection only;
diagram and temperature effects have not yet been validated.

There were also **three JANAF heat-capacity inputs** for liquid water, hydrogen
gas and oxygen gas in `src/pourbase/temperature.py`. They sit outside the
100-observation inventory and enter the temperature correction for water.
Fixtures, published comparisons and any numerical derivatives need a bounded
dependency check if replacement proceeds.

The open NBS digitization already supplies candidate heat capacities for all
three inputs: CSV logical records 41, 27 and 15, respectively, zero-based
column 11, at 298.15 K and 1 bar. Formulas, states, units and the CSV checksum
were checked against the official release metadata. The numerical entries
differ slightly from the old constants. The release now uses these three NBS
inputs. Their formation-heat-capacity combination is 31.7895 J/(mol K), and
its effect on the water Gibbs correction is about 0.3273 J/mol at 373.15 K.

The historical **88/103 NIST-request coverage** includes three nitrogen
properties formerly sourced through WebBook. The current **87/100** count
measures the direct JANAF subset under today's selection policy. These counts
answer different questions.

## Checklist and stopping conditions

- [x] J01 — Check JANAF-specific notices, official metadata, NIST policies,
  the SRD statute, and the distinction between compilation rights and facts.
- [x] J02 — Reconcile the current 100 observations and 17 preferred properties;
  simulate exclusion; identify the 13 gaps and three code constants. Preserve
  the inventory and simulation privately before implementation.
- [x] J03 — Record the forward-path decision. The original email remains
  unanswered. The user chooses independently sourced distribution and
  instructs proceeding; a new permission request is unnecessary for that
  route. A future NIST grant or particular-use assessment can reopen admission.
- [x] J03a — Prepare the private clarification email and a checked attachment
  containing all 100 current observations and the three heat-capacity inputs.
  Prepared 28 October 2026 as `nist-clarification-email.md` and
  `nist-janaf-scope.csv` in the private review directory. The attachment has
  103 rows with values, units, conditions and source-table locations. Its
  numerical inventory remains outside the distributed repository.
- [x] J03b — Record that a fresh clarification is superseded by the user's
  independent-source release instruction. The prepared draft stays private
  and unsent. This completion records a release choice, not permission.
- [x] J04 — Retention branch is inapplicable: no new grant was received.
  Follow the independently sourced release branch J05–J08.
- [x] J05 — Stage the release outside the production database. Carry
  the 87 existing alternatives forward. Reuse completed reviews of the five
  gap species and examine only the specific missing evidence listed above.
  Preserve exact compositions, phases, reference states, uncertainties and
  distinctions between measurements and estimates. Keep every eligible
  alternative and let the policy select one preferred value per property.
  The five earlier source/specimen reviews remain unresolved; all 13 gaps are
  explicit. No new observation is admitted from an unverified lead.
- [x] J06 — Check the three heat-capacity inputs against independently reusable
  original releases; carry forward the NBS candidate check above. Trace actual
  numerical dependencies in code, fixtures,
  derived observations and distributed comparisons. Same-number agreement,
  a new citation or a mirror's licence alone supplies no independent route.
  Record an unresolved dependency explicitly if no compatible route is ready.
- [x] J07 — Assemble the candidate distribution with a disposition for every
  direct observation and identified dependency. Where permission remains
  absent under the chosen release policy, retain the original evidence in the
  private archive and omit the affected values from distributed artifacts.
  A preference change alone leaves archived observations in the package.
  Do not rewrite repository history. Preserve source citations and all
  independently eligible alternatives; document any remaining coverage gaps.
- [x] J08 — Compare selections, source/phase integrity, affected diagrams and
  temperature calculations against the baseline. Check all 75 default systems
  for effects and test changed behavior. Update relevant fixtures, notices,
  statistics, paper assets/numbers and historical request coverage. Verify
  wheel and source-distribution contents. Preserve concurrent GUI work.
  Release validation is complete; commit and push are recorded in the private
  release checkpoint.

## Independent-source release result

The release removes 100 direct JANAF observations plus **54 superseded,
source-less rounded representations** whose links lead to those observations.
Those representations have no independent source route. Their full records,
the 49 unused JANAF source records and three obsolete source-linked warnings
are preserved in a private, hashed archive. Five new warnings identify the
remaining property gaps. Supersession references remain valid. SQLite is
compacted so deleted records are not left in free pages.

Every other observation and all species, phase identities, component references,
Materials Project records and NEA permission evidence are preserved. No new
experimental value or estimated replacement is invented. The default policy
chooses the existing plattnerite G/H/S evaluation and alpha-TiO entropy; its
JANAF family and citation pattern are removed. The 62 overrides and 18
exclusions remain, with policy fingerprint **4c1df55bbeff** and recommendation
fingerprint **c3bf0c97a0fd5151**.

The database has **1,771 species, 5,143 observations, 1,790 source records
(265 distinct citations), and 2,757 warnings**. Selected G/S/H coverage is
**1322/1292/1348**. Historical request coverage remains **116/131**, including
**NEA 28/28 and NIST 88/103**; that measure already counted independently
eligible alternatives. Missing G/H/S for Ba(OH)₂, Sr(OH)₂ and TiH₂, G/H for
TiO, and G/S for FeO remain visible. TiO retains its original entropy and FeO
retains its NBS formation enthalpy. Related wustite compositions stay distinct.

All 75 supported default systems still calculate with incomplete data allowed.
Of their default 84,581-point maps, **73 are unchanged**. Lead changes 386
points after the plattnerite replacement. Titanium changes 14,720 points after
TiO/TiH₂ are excluded for missing Gibbs energies. Strict coverage exposes the
new gaps: 50 systems calculate with `allow_incomplete=False`, compared with
53 previously. Five affected systems were also compared at 323.15 and 373.15 K.
The complete suite passes **596 tests**, including open-source policy examples,
temperature derivatives, source-distribution guards and the GUI suite. GUI
runtime code remains unchanged; its policy tests use existing open evaluations.

Thirty mass-balance scenarios for the five affected systems conserve metal
at three temperatures and two concentrations. The representation audit reports
zero errors. The paper's 200-sample sensitivity runs cover all 75 systems in
both scopes. Its regenerated assets and statistics feed a 56-page private proof
with three successful LuaLaTeX passes, no unresolved references and no overfull
boxes. The live manuscript and PDF are preserved; a private patch supplies the
updated source-family table, policy example and heat-capacity wording. Wheel,
source-distribution and installed-wheel checks retain the current data and
notices and exclude private correspondence and archived observations.

## Subsequent manuscript alignment

At the user's request, the live manuscript was then aligned with the release:
JANAF was removed from the included-source description and introductory policy
table, the temperature section now cites the open NBS inputs, and the example
policy explanation matches its existing USGS-first configuration. The SI
exclusions table gives JANAF SRD 13 and WebBook SRD 69 separate entries.

This pass also found four copies of the excluded JANAF observations in the
published manual-audit CSVs. Their original sample records and completed
reviews were preserved privately. The other 96 sample and review rows remain
exact. Public audit summaries now report those 96 retained reviews: 95 source
matches, one inherited source mismatch and zero identified agent transcription
errors. The paper explains the original 100-value draw, the four exclusions
and the retained subset. Sampling provenance preserves the original population;
no new sampling or source verification was performed. This correction changes
the audit artifacts and manuscript, with no further database or policy change.

This follow-up ends with a documented retention decision or a validated
distribution in which every scoped JANAF item has a disposition. A finite
replacement pass may end with clearly reported missing properties. Additional
species, database families and unbounded literature searches require a new
scope. Completed source reviews and unrelated permission holds carry forward.

Private evidence and the reproducible audit are stored in
`pourbase-work/janaf-redistribution-review-2026-10-28/`. Successful local
downloads include both official metadata records. Several direct downloads
returned HTTP 403; their primary pages were inspected through the web tool,
and the acquisition manifest records those download limits.
