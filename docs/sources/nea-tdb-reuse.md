# Adding NEA-TDB observations

NEA-TDB selected and evaluated thermochemical data are available to pourbase
under the OECD data terms. Written clarification from Alexia, supplied by
Frederik on 14 October 2026, confirms use, adaptation and redistribution,
including commercial use, with appropriate OECD attribution and a downstream
acknowledgment obligation. Check additional restrictions for the particular
source before admission. Permission record: `NEA-TDB-OECD-2026-10-14`.

The applicable terms are [OECD Terms and Conditions, section 3, Data](https://www.oecd.org/en/about/terms-conditions.html)
(accessed 14 October 2026). Credit the associated data citation; where there is
none, use OECD (year), dataset name, data source, DOI or URL and access date.
Every sublicense of work created using the data must carry the same OECD
acknowledgment requirement and require further sublicensees to pass it on.
[THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) contains the distributed
acknowledgment and the review citations. These source terms accompany the
project's GPL-3.0 software and compilation licence.

## Permission evidence

The supplied email body and subsequent full thread are retained with the private
permission correspondence and external source-review checkpoint, together with
a captured copy of the applicable OECD data terms. The full thread supplies the
project mailbox, signatory's role, initial referral and displayed reply times.
The record distinguishes displayed dates and contextual date interpretations
from raw email headers, which were not supplied. The correspondence retains
its “Restricted Use” marking and stays private. SHA-256 of the initially
preserved email body:
`c41a49b246e2db3eb4b4693a14f8ddfe1d85394be7772ce3c3af54a9abfad6d4`.
SHA-256 of the subsequently supplied full thread:
`eb69c8661d760b6b4941f53a359446dbb66ddc4f748da5f52f1b955addbe6b4d`.
The database metadata key `source_permission_NEA_TDB` records the permission
ID, terms URL, evidence hash, applicable source IDs and obligations.

The clarification resolves the NEA-TDB permission request. NIST SRD, JAEA,
commercial compilations and other independently restricted sources keep their
separate permission status. Carry forward completed source reviews. Reopen a
specific decision when new evidence, an erratum or an identified discrepancy
warrants it.

## Admission procedure

1. Identify the exact NEA review, release, table, page and species. Preserve
   the associated citation, access date, source-file hash and any errata check.
   Check stated additional restrictions and identified third-party ownership.
   The current grant covers NEA's own selected/evaluated data. An upstream
   scientific citation alone does not establish an additional restriction on
   that evaluation. Independently copied third-party tables and separately
   licensed software need their own reuse basis. Keep complete publications
   and page images in the external review workspace.
2. Match the existing species by formula unit, charge, hydration, phase and
   conventions. Retain scientific gaps and identity holds until resolved.
   Add a complete species record only for a distinct supported identity.
3. Record every eligible observation in `reported_thermochemistry`.
   Preserve alternatives; a permission change updates reuse metadata without
   duplicating numerical observations. Put the exact property/table/row
   location in `source_locator` and confirm that API reads retain it.
4. Normalize formation G/H to J/mol and S to J/(mol K), per full stored formula
   unit. Preserve the source's uncertainty interval and its interpretation.
   A total interval described as corresponding in principle to 95% confidence
   remains that interval; a one-sigma conversion requires separate justification.
   Identify source-internal calculations and retain the reported precision.
   For ligand species, name the buffered free ion and check residual O/H,
   charge, ligand count and electron balance. Review new free-ion references
   under their own source terms. Compare the assembled reaction constants
   with source reaction data: different auxiliary evaluations can produce
   substantial differences even when all quantities use the same standard
   state. Preserve source formation values and document the difference.
   The uncertainty screen uses retained widths directly, so mixed interval
   conventions do not support a uniform confidence-level interpretation.
5. Validate a staged copy against the current database. Check old-row
   preservation, integrity, foreign keys, duplicate prevention, idempotence,
   stoichiometry and the default policy's selections. The policy chooses one
   eligible value per property. Review changed selections, Gibbs spreads,
   diagrams and relevant ligand-enabled or mass-balance calculations.
6. Apply the authorized batch. Update source notices, regression expectations,
   statistics, manuscript assets and numbers, and the running checklist.
   Build the distributions and verify that they contain the acknowledgment.
   Preserve concurrent work when committing the owned changes.

## Completed checkpoint: 14 October 2026

- All **28 originally requested NEA observations already existed** with matching
  numerical values. Their reuse status is now available under the clarified
  terms. All 28 selected observation IDs are preserved; no duplicate rows were
  added for the permission change. Six legacy source locators and 34 observation
  locators carry the updated conditions, including six scientific-gap records
  whose numerical eligibility remains unchanged.
- Table III-1 of the iron (2013, volume 13a), nickel (2005, volume 6) and tin
  (2012, volume 12) reviews supplies **25 further observations and six aqueous
  species**. They fill **15 missing properties** and change **ten existing
  selections** under the unchanged policy. The nickel errata were checked;
  they do not change the imported 298.15 K G/H/S rows.
- The first checkpoint contained **806 species and 2,679 observations across 74 systems**,
  with selected G/S/H counts **714/679/539**. All earlier numerical evidence
  remains stored. New polynuclear ions retain their full formula units; the
  current closed metal-balance model excludes and reports polynuclear aqueous
  species. Fixed-activity diagrams can include them.
- Historical request coverage is **116/131**: **28/28 NEA** and **88/103 NIST**
  have an available compatible value. The increase of 15 is permission
  clearance for existing observations. The 25 extension observations are
  separate additions. NIST permission holds remain independent.

## Completed NEA02a solid-phase continuation

The remaining solid rows of Table III-1, printed pp. 44–47, in the retained
iron (13a), nickel (6) and tin (12) reviews have explicit dispositions:
**103 rows**, comprising 66 with additions, four already retained phase
triplets, 30 chemistry/identity holds and three heat-capacity-only rows.
The batch adds **158 observations and 48 species**, fills **115 properties**
and changes **42 earlier selections** under the unchanged policy. The added
beta-Sn entropy remains an alternative to the higher-ranked CODATA selection.
All earlier numerical evidence and all 28 historical NEA request selections
are preserved.

Totals after NEA02a are **854 species /2,837 observations /74 systems**, with
selected G/S/H counts **753/713/581**. The existing source-specific OECD
permission review covers these additional selected numerical data; the same
attribution and downstream acknowledgment requirements apply. New observations
reuse their associated volume citations and carry exact per-property locators.
The published total uncertainty intervals retain their original interpretation.

Distinct identities include amorphous SnO2 and cassiterite, alpha/beta tin,
maghemite/hematite, lepidocrocite/goethite, mackinawite/troilite and alpha/beta
NiS. Complete hydrate amounts and large formula units are retained. NiS2's
formal Ni(II) and four-electron reaction coefficient reflect its disulfide
composition and the free-sulfide calculation reference.

At that checkpoint, held rows included nonstoichiometric compositions, mixed-metal compounds,
unrepresented iodate/arsenic chemistry and dehydrated silicates whose present
H3SiO4- reference would require negative residual core atom counts. Their
source facts remain in the external review ledger. Source permission and
scientific/model holds stay separate. Heat-capacity-only rows are routed to
R18. NIST request coverage and the six original crystalline Gibbs gaps are
unchanged.

## Completed NEA02b fixed-composition wüstite review

Fe0.932O is retained as a separate nominal composition with three
`source_verified_estimate` observations: G −244.593 ±1.906 kJ/mol,
H −265.800 ±1.900 kJ/mol and S 56.690 ±0.490 J/(mol K), per mole of
Fe0.932O. The source is iron volume13a Table III-1, printed p.44, with
sectionVII.2.8, printed pp.205–212, establishing the molar basis, ambient
average structure, metastability and estimation conventions.

The model stores0.932 Fe and one O per formula and uses2/0.932 electrons
and protons per Fe for the water/metal reaction. Fractional metal-count
normalization and precipitation were independently checked by rescaling to
Fe233O250. This is one fixed source composition. The chapter's composition
uncertainty and defect/solid-solution qualifications remain in provenance.

The enthalpy is a third-law estimate; the entropy excludes an unknown
zero-point configurational term. The source-calculated G retains that entropy
convention. All three observations keep source intervals and explicit
warnings, with the established OECD permission and downstream acknowledgment.
The new record preserves the stoichiometric FeO record and every existing
selection. It resolves this one earlier solid hold, leaving29 of the NEA02a
scientific/model holds open.

Totals after NEA02b are **855 species /2,840 observations /74 systems**, with
selected G/S/H counts **754/714/582**. Historical request coverage remains
**116/131**; the stoichiometric FeO requests retain their separate status.
The74 sampled default diagrams are unchanged. The new phase lies above the
balanced Fe/magnetite combination at298.15K under the retained G convention,
consistent with the source's metastability assessment.

## Completed NEA02c ligand continuation

All **50 remaining ligand-bearing aqueous, gas and liquid rows** in the
three retained Table III-1 sets, printed pp. 44–47, have been reviewed:
42 aqueous rows, seven tin molecular gases and one pure-liquid row. The batch
retains **86 observations and 45 new species**, fills **82 properties** and
changes **four existing selections** under the unchanged policy. All earlier
observations and all 28 original NEA request selections remain stored.

Three new free-ligand Gibbs references come from the explicitly open NBS PDR
digitization, DOI 10.18434/M32124: SCN⁻, P2O7⁴⁻ and AsO4³⁻. Their exact CSV
logical records, unit conversions, file hash and reuse basis are attached to
their source records. NIST is acknowledged separately from OECD. Pyrophosphate
has its own formula and charge. Protonated complexes use the deprotonated
free reference and residual H; the input specifies that free ion's activity.

The selected formation properties remain unchanged from NEA. The runtime
reference set includes independent evaluations and therefore represents an
assembled dataset. For example, the nickel tetracyanide, pentacyanide and
unprotonated pyrophosphate association log10K values exceed the selected NEA
reaction values by about **3.827, 4.784 and 2.891**, respectively, at 298.15 K.
These differences follow from the free-ligand evaluations and are explicit in
warnings and the external reaction ledger. A preferred formation value does
not establish consistency with a review's entire auxiliary set or covariance.

Aqueous SnCl4²⁻ retains Sn(II); neutral gaseous/liquid SnCl4 retains Sn(IV).
The liquid has selected H only, so missing G remains explicit. Tin gases use
prescribed fugacity and an independently buffered aqueous ligand activity.
The closed metal-balance solver rejects gas-containing systems; gas-free
subsets were checked separately. Ligand species remain excluded by the current
temperature extension away from 298.15 K.

Totals after NEA02c are **900 species /2,926 observations /74 systems**, with
selected G/S/H counts **801/730/601** and **15 ligand references**. All 74
sampled default diagrams are unchanged. Of 66 ligand-enabled scenarios,
33 change as the added complexes become available; 132 gas-free ideal/Davies
balances conserve metal. Historical request coverage stays **116/131**.
The 29 prior solid/model holds remain separate. The new arsenate reference
provides a route for a later mineral review; it does not complete that review.

## Completed NEA02d zirconium review and inventory

Brown, Curti and Grambow, with Ekberg (2005), *Chemical Thermodynamics of
Zirconium*, NEA volume 8, supplies a finite inventory of **97 selected rows**
in Table III-1, printed pp. 48–53 (PDF pp. 78–83). All six pages were checked.
The release identity, official source-file hash and source-specific reuse
review are recorded in the external checkpoint. No zirconium-specific errata
document was found in the checked NEA listing and targeted search; this is
not a claim that no errors exist. A later scientific caveat in NEA thorium
volume 11, Appendix F, explicitly questions two oxide gas evaluations.

The admitted batch contains **148 observations and 63 species** from 68 rows.
It fills **137 properties** and changes **11 existing selections** under the
unchanged policy. Every earlier SQL row and all original NEA request chosen
IDs are preserved. The new permission metadata supplement,
`source_permission_NEA_TDB_Zr_2005`, extends the recorded OECD terms to the
selected zirconium evaluations. Appropriate OECD citation and the same
acknowledgment requirement continue through every sublicense.

One new free-ion reference comes from the previously reviewed open NBS PDR
release: SO3²⁻, G = −486,500 J/mol, CSV logical record 573. Sixteen free-ligand
references are now available. This adds a sulfite reservoir with prescribed
free activity; total sulfite and protonation require an explicit separate model.

New polynuclear ions retain complete formulas and metal counts. Epsilon-ZrH2
retains formal valence +2 and reaction electron coefficient −2. ZrS2/ZrS3
keep source-reviewed estimate status because their evaluations use third-law
thermal functions and analogy entropies. Phase labels, hydrates and gas/aqueous
forms remain distinct. Missing G stays explicit for entropy/enthalpy-only rows.

The external ledger retains **27 specific scientific/model holds** and **two
heat-capacity-only rows for R18**. Source/legacy water-equivalent hydrolysis
mapping and physical zirconyl identity need a separate reconciliation. The
ZrH correlation concerns mixed phases; ZrS1.5 has conflicting source text and
composition descriptions. Questioned oxide gases, the bare gas's default
closed-balance integration and unsupported mixed-metal/component chemistry
remain explicit follow-ups. These holds have numerical source candidates and
locations; source permission alone does not resolve their scientific questions.

Totals after NEA02d are **963 species /3,074 observations /74 systems**, with
selected G/S/H counts **850/771/648**. The zirconium default diagram changes
at 648/7,371 sampled points; the other 73 default diagrams are unchanged.
Independent full-formula energies, aligned pymatgen, 39 plain/ligand scenarios
and 78 explicitly gas-free ideal/Davies balances pass. No bare gas is added
to default Zr calculations. Original request coverage remains **116/131**.
The 29 earlier Fe/Ni/Sn solid/model holds retain their separate review history.

## Completed NEA02e derived-route crosswalk

The targeted crosswalk covers 42,009 property slots across PSI/Nagra,
eight SUPCRT variants and three MINES releases, with routes for all440 PSI
reactions. It finds one missing original NEA observation: Ni(OH)3(-),
G=-590519 +/-9735J/mol, stored as G=-353390J/mol in the existing HNiO2(-)
component basis by subtracting one project-water reference (-237129J/mol).
Both complete-formula reactions and their transformed energies agree at
unit water activity. The policy selects this observation while preserving
all older evidence and independent H/S estimates. The source total interval
is retained; the mixed reference set supplies no new temperature validation.

Totals after NEA02e are **963 species /3,075 observations /74 systems**;
selected G/S/H counts remain **850/771/648**. Nickel changes412/7371 sampled
points; the other73 default diagrams are unchanged. Historical request
coverage stays116/131. The targeted deliverable is complete; wider R11/R12
source/version reviews and independent permission holds remain open.
See [the crosswalk results and remaining routes](nea-derived-crosswalk.md).

## Completed NEA02f adjacent-phase review

All nine G/H/S cells for Ni(g), Ni(l) and SnH4(g) are verified and admitted:
**nine observations /three species**, filling nine properties and preserving
every earlier preferred ID. Ni(l) retains its hypothetical supercooled
pure-liquid standard state. The gas observations remain fully available to
the selection policy and evidence API. A documented `optional_gas_phase`
annotation requires `include_optional_gases=True` to load these two gases for
fixed-fugacity calculations; default Ni/Sn closed balances and strict
completeness are preserved. Policy and user-species views and temperature
caches retain the same phase-selection scope. Earlier gas inclusion rules
are carried forward. The explicitly gas-containing closed-balance model
remains unsupported; this affects model capability, not source admission.

Production contains **966 species /3,084 observations /74 systems**, selected
G/S/H **853/774/651**. All74 default phase maps and uncertainty masks are
preserved; the liquid changes the nickel runner-up gap at2340/7371 points.
Eight ideal/Davies metal inventories agree with the baseline, four nickel
temperature maps agree, and the aligned pymatgen check passes. Gas-enabled
tin changes1495/7371 points, all below the water-stability window. The source
intervals retain their published interpretation. See [the source values,
phase conventions and gas-selection example](nea-adjacent-phases.md).

## NEA02g1 zirconium component reconciliation

Five of the 27 zirconium holds are resolved: two water-normalized hydrolysis
G values, the Zr(g) triplet, selected Zr(SeO3)2 H and zircon G/H/S. Nine
observations and three species bring production to **969 species /3,093
observations /74 systems**, selected G/S/H **855/776/654**. The existing policy
changes two preferred G values and retains all alternatives. Two free-reference
components come from the already reviewed open non-SRD NBS release.

The source hydroxo formulas are preserved in locators. Legacy ZrO²⁺/ZrO2(aq)
formulas specify water-subtracted components, with explicit warnings about
physical zirconyl identity. The neutral silica component uses direct free
H4SiO4 activity at unit water activity. Zr(g) requires explicit phase selection;
default closed balance remains available. Source intervals retain their
published interpretation, and independent H/S estimates remain distinct.
See [the source values and scientific checks](nea-zirconium-hydrolysis.md).

The **22 remaining zirconium holds** comprise six Te/N/C reference routes,
four disputed source evaluations and twelve mixed-metal records. Continue
with the six reference routes. The original 27-row inventory remains a
historical checkpoint; its active reconciliation records five admissions.
Two Cp-only rows stay with R18. Earlier Fe/Ni/Sn holds and other sources'
permission states remain separate. Original request coverage stays116/131.

## NEA02g2 elemental reference routes

All six Te/N/C reference holds are resolved with **16 observations /six
species /three elemental buffers**, filling 16 properties and preserving
every earlier preferred value. Production contains **975 species /3,109
observations /74 systems**, selected G/S/H **860/781/660**. Crystalline Te
and graphite use unit activity; the nitrogen reference uses prescribed
N2 fugacity. Direct component activities represent these external phases.

ZrTe1.843 and Zr5Te4 retain their exact compositions. The neutral elemental
reactions keep signed electron coefficients distinct from formal oxidation
states. The stoichiometric ZrC endmember retains NEA's ZrC0.96 thermal
approximation as a source-reviewed estimate. ZrTe3O8 has selected H only.
All 74 default maps/masks and earlier preferences are preserved; 70 buffered
scenarios and 140 closed-zirconium inventories pass. See [the reference,
source and reaction review](nea-zirconium-element-reservoirs.md).

Eleven of the original 27 zirconium holds are resolved. The **16 remaining**
comprise four disputed source evaluations, reviewed next, and twelve
mixed-metal records. The two Cp routes, earlier Fe/Ni/Sn holds, wider source
reviews and other-source permission states remain separate. Request coverage
stays116/131, including all28NEArequests.

## NEA02g3 disputed-evaluation review

The four-row review admits **nine observations /three species**. ZrO(g) and
ZrO2(g) retain their historical NEA estimates with the later thorium review's
criticism and explicit optional-gas scope. This preserves qualified evidence;
it does not resolve the scientific disagreement or import copied comparison
tables. ZrS1.5 follows the two consistent selected tables, with conflicting
discussion values recorded externally. The source identifies Zr3S4 as its
structure type at 1100 K; the stored formula stays ZrS1.5. The bulk ZrH
correlation remains held for an appropriate assemblage/phase model.

Production is **978 species /3,118 observations /74 systems**, selected
G/S/H **863/784/663**. All earlier preferred values and 74 default maps/masks
are preserved; 140 gas-free zirconium inventories pass. Fourteen of the
original 27 rows are admitted; **13 admission holds remain**: ZrH and twelve
mixed-metal records. The finite review is complete with the hydride and
gas source-upgrade follow-ups explicitly retained. Continue with NEA02g4's
twelve mixed-metal records. See [the decisions and scientific checks](nea-zirconium-disputed-evaluations.md).

## Further exploration

R11c completes the 14 metal-bearing selenium routes with 28 observations.
Distinguish the 21 selected formation observations, six qualified Appendix E
evaluations and one local FeSeO3+ estimate. NEA-authored Appendix E evaluations
retain their unreviewed-auxiliary status; importing them does not import the
independent auxiliary table or make them TDB-selected. A local derivation
records every input ID, conditions and unavailable total uncertainty.
The free-selenite reference now matches the preferred NEA observation, with
its earlier NBS pin and observation retained. See [the finite review and
next checklist](nea-metal-selenium.md).

R11a/R11b now reconcile the PSI/Nagra inventory and retain 71 selected core
selenium observations from NEA volume 7 under the documented OECD terms.
The volume-specific metadata records the existing permission evidence hashes,
source restrictions check and official errata. A selected-table/discussion
entropy discrepancy is explicitly qualified; independent auxiliary tables
remain outside this batch. Continue with R11c's 14 metal-bearing selenium
routes and carry forward the earlier source decisions. See [the finite
inventory and remaining checklist](nea-selenium.md).

The first expansion covers a useful aqueous-ion/hydrolysis subset. Continue
with the recorded solid-phase identity/model holds, ligand complexes, other NEA reviews,
and NEA-derived candidates already routed through PSI/Nagra, SUPCRT or MINES.
Review each candidate's identity, additional restrictions, scientific
conventions and calculation support. Preserve the earlier numerical reviews
and keep source permission, missing evidence and unsupported chemistry as
separate tracker states. Record a finite candidate inventory for each batch;
completion of this checkpoint does not complete the entire NEA catalogue.

## NEA02g4 mixed-component checkpoint

The twelve mixed-metal zirconium rows have been reviewed: 24 observations
and 11 species are retained, adding 20 usable 298.15 K properties. Preserve
actual source temperatures even when a generic table heading differs; keep
incompatible-temperature evidence outside calculation selection until a
justified conversion exists. Store independent buffered references separately
in schema 9 `additional_components`, validate every reference's reuse basis
and physical reaction balance, and expose source conditions through the API.
All earlier preferred selections and private permission evidence are preserved.
Two of the original 27 rows remain admission holds; three admitted observations
have separate temperature calculation holds. The gas source-upgrade route
remains open. See [the finite review](nea-zirconium-mixed-components.md).

## Formula corrections and derived values

When an inconsistent formula accompanies an internally derived value, check
the original identity, amount basis and the derivation together. A chemically
balanced formula edit may change G reconstructed from H/S. Retain hypothetical
recalculations as external diagnostics until the source assignment is justified.
A later paper reporting a related formula provides an independent candidate;
verify its numerical data and reuse basis before import. NEA02g4a documents
[this calcium example](nea-calcium-silicate-formula.md); the existing NEA
permission review is carried forward and the scientific hold remains explicit.

## Independent original studies in a NEA follow-up

R11e resolves the earlier annabergite reference/model hold with selected NEA
G/H/S and the existing free arsenate reference. It retains original PSI
bicarbonate/silicate numerical evaluations through their own individual-fact
route and complete local pyrophosphate variants using permitted NEA reaction
data and explicitly open NBS inputs. Source approximation, ionic-strength
limits and formation-cycle differences stay explicit; previous direct NEA
G values remain preferred. Keep upper bounds and unknown hydration outside
the point-value import until the missing scientific requirements are met.
See [the ten-route review](psi-nickel-carbonate-silicate.md).

R11d retains two local nickel hydrosulfide formation-G estimates from
original PSI-authored regression results, with retained NEA6 Ni2+ and
explicitly open NBS HS- anchors. The PSI results use the established
individual-original-numerical-fact route; the NEA input carries its own
OECD acknowledgment and downstream propagation requirements. Keep those
reuse bases distinct in the derivation record. The six Bjerrum ammonia
routes remain outside the database until their original numerical evidence
and reuse review are complete. See [the R11d review](psi-nickel-hydrosulfides.md).

NEA02g3b retains three original-study gas enthalpies with their own source
citations and individual-numerical-fact reuse records. The original authors'
publisher-deposited abstracts explicitly identify each value and temperature.
Their articles and protected expression retain their own rights. Keep this
route separate from the NEA grant, and retain actual nonreference temperatures
with explicit exclusions when thermal conversion is unsupported. Full article
methods can remain a follow-up when an admitted numerical result is explicitly
verified in the primary abstract; identify that limited verification scope.
A source-specific restriction or unclear reuse basis still requires a hold.
See [the gas source review](nea-zirconium-gas-upgrade.md).

R11f carries the completed NEA tin-anchor reviews into four historical local G
alternatives, with the OECD credit and downstream acknowledgment obligation
preserved. A new crystalline burtite triplet and original Nagra reaction facts
use separately documented individual-original-numerical-facts decisions; the
NEA permission does not cover those publications. The burtite article is
CC BY-NC-ND, with only its three isolated original property results admitted
under the factual-results route. See [tin source routes](tin-original-routes.md).

R11g adds separately reviewed original palladium reaction facts and local
estimates with open NBS reference inputs. The original Nagra and Rasmussen /
Jørgensen publications retain their own rights under the documented limited
numerical-facts route. The inherited JAEA mixed-chloride selections remain held.
The NEA permission and its downstream acknowledgment requirement continue for
NEA material elsewhere in the database. See
[palladium source routes](palladium-original-routes.md).

R11h carries the completed NEA permission review forward while adding six
separately reviewed original Nagra europium reaction evaluations under the
limited original-numerical-facts route. Open NBS and the existing Miron silicate
reference supply the local inputs. Amorphous original-source verification and
simple-carbonate hydration remain precise holds; the older strong silicate
model stays external. See [europium source routes](europium-original-routes.md).

R11i extends the carried iron-volume review to qualified nominal ferrihydrite
model suggestions on pp. 227–228, plus its own selected Fe3+ and evaluated OH−
auxiliary anchors on pp. 44/55. Four model alternatives retain OECD attribution
and the same downstream acknowledgment requirement. Their source-specific
review identifies no additional restriction on these NEA-authored evaluations.
They retain `source_verified_estimate` and the distinction from normally selected
NEA data. See [iron hydrolysis and carbonate routes](iron-hydrolysis-carbonate-routes.md).
