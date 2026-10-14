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
3. Record every eligible observation in schema 8 `reported_thermochemistry`.
   Preserve alternatives; a permission change updates reuse metadata without
   duplicating numerical observations. Put the exact property/table/row
   location in `source_locator` and confirm that API reads retain it.
4. Normalize formation G/H to J/mol and S to J/(mol K), per full stored formula
   unit. Preserve the source's uncertainty interval and its interpretation.
   A total interval described as corresponding in principle to 95% confidence
   remains that interval; a one-sigma conversion requires separate justification.
   Identify source-internal calculations and retain the reported precision.
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

Current totals are **855 species /2,840 observations /74 systems**, with
selected G/S/H counts **754/714/582**. Historical request coverage remains
**116/131**; the stoichiometric FeO requests retain their separate status.
The74 sampled default diagrams are unchanged. The new phase lies above the
balanced Fe/magnetite combination at298.15K under the retained G convention,
consistent with the source's metastability assessment.

## Further exploration

The first expansion covers a useful aqueous-ion/hydrolysis subset. Continue
with the recorded solid-phase identity/model holds, ligand complexes, other NEA reviews,
and NEA-derived candidates already routed through PSI/Nagra, SUPCRT or MINES.
Review each candidate's identity, additional restrictions, scientific
conventions and calculation support. Preserve the earlier numerical reviews
and keep source permission, missing evidence and unsupported chemistry as
separate tracker states. Record a finite candidate inventory for each batch;
completion of this checkpoint does not complete the entire NEA catalogue.
