# PSI nickel hydrosulfides: R11d

The eight-route R11d review retains two local formation-G estimates:
one alternative for existing NiHS+ and one new Ni(HS)2(aq) species.
The database now contains **1,026 species and 3,249 observations** across
74 systems, with **903/812/696 selected G/S/H properties**. Every earlier
observation and preferred value is preserved. Six nickel ammonia routes
remain outside the release pending their original numerical source.

## Original source and reuse

Hummel, W. and Thoenen, T. (2014), *The PSI/Nagra Chemical Thermodynamic
Database 12/07: Data Selection for Nickel*, PSI Technical Memorandum
TM-44-14-05, 4 June 2014, section 5.5.1.2, pp. 11/13 and Table 5.5,
p. 30, reports its own weighted SIT extrapolations to infinite dilution at
298.15 K. [Official report](https://www.psi.ch/en/media/47948/download),
accessed 16 October 2026; SHA256
`0517483b829b4364b559491eca928c826189674ebbe644a64991fa4ffb344599`.

| Reaction | log10 beta | Stated width | Original evaluation |
|---|---:|---:|---|
| Ni2+ + HS- = NiHS+ | 5.5 | 0.2 | p. 11 |
| Ni2+ + 2HS- = Ni(HS)2(aq) | 11.1 | 0.1 | p. 13 |

The import follows the established **individual original numerical facts**
route for these two PSI-authored regression results, with full attribution.
This route carries no open licence for the complete report or PSI database.
The report and [PSI imprint](https://www.psi.ch/en/imprint) were checked for
source-specific restrictions on the isolated results; none was identified.
The distinction between facts and protected expression follows the
[Copyright Office guidance](https://www.copyright.gov/help/faq/faq-protect.html)
used by the project's existing individual-source policy. Complete publications,
source tables, figures, native database files and private evidence remain in
the external review workspace.

The original report identifies measurements by Zhang and Millero (1994),
Luther et al. (1996), and Al-Farawati and van den Berg (1999). PSI's own
side-reaction corrections and weighted extrapolations produce the retained
results. Its comparison with the older NEA evaluation remains provenance.
The NEA permission applies separately to the retained Ni2+ input used below.

## Local derivation and preferred values

Both formation energies are calculated locally as
`Gf(complex) = Gf(Ni2+) + n Gf(HS-) - RT ln(10) log10(beta_n)`.
The retained Ni2+ formation G is −45,773 J/mol from the permitted NEA6
evaluation. Retained HS- formation G is 12,080 J/mol, independently matched
to the explicitly open non-SRD NIST NBS PDR
[M32124](https://doi.org/10.18434/M32124), CSV logical record 584,
aqueous-ion state `ao`, zero-based column 8: 12.08 kJ/mol × 1000.
The CSV SHA256 is
`cb8a8b8b94a287e6e8c82eed8bad2cf9b611d574d1cfd95c8528d318dfef4b44`.
NIST is acknowledged under its [open licence](https://www.nist.gov/open/license);
the data are supplied without warranty.

Each local observation retains the equation, exact input observation IDs,
R = 8.31446261815324 J/(mol K), T = 298.15 K, source log-beta width and
the local standard-state 1 bar pressure-flat assumption. These are G-only
`source_verified_estimate` observations. Missing anchor uncertainty and
unestablished confidence/covariance prevent a supported total G interval;
the stored total uncertainty is NULL. H, S and Cp remain unavailable.
The native constant-logK representation supplies no new thermal model.

The unchanged selection policy keeps the existing NEA NiHS+ G of
−63,098 J/mol preferred and retains the PSI-derived estimate as an
alternative. Ni(HS)2(aq) fills one missing formation-G property.
No supersession or manual preference override is introduced.

OECD and NEA are acknowledged for the Ni2+ input. Their carried terms permit
use, adaptation and redistribution, including commercially, subject to
source-specific additional restrictions. Every sublicense of work using these
data must include the same OECD acknowledgment requirement and require further
sublicensees to pass it on. See [distributed notices](../../THIRD_PARTY_NOTICES.md)
and [the source instructions](nea-tdb-reuse.md).

## Reaction and calculation scope

Both complexes use the existing `sulfide-s` free S2- reference, preserving
one physical identity for NiHS+. All sulfur atoms belong to that external
component; the full formula retains one or two core hydrogens. Both species
have electron coefficient 2. The proton coefficients are −1 and −2.
The free S2- reference remains 85,800 J/mol.

The explicit reference relation is
`log10 a(S2-) = log10 a(HS-) + pH - pKa(HS-)`, where
`pKa = (85800 - 12080)/(RT ln(10))`.
Full-formula energies and one-/two-ligand activity responses were checked
using that relation. The source's SIT coefficients remain external evidence;
the runtime uses its existing ideal/Davies models and externally prescribed
free-component activities. Closed balance conserves primary nickel. Total
sulfur inventory and total-sulfide protonation are separate model tasks.

All 74 default maps and uncertainty masks are unchanged. Three sulfide-buffer
scenarios at log10 free S2- activities −16/−12/−8 and pH 7–14 preserve their
phase maps; six ideal/Davies nickel balances conserve total metal. The new
complex changes dissolved nickel concentrations in those balances.

## Checklist and remaining work

- [x] Review all eight nickel routes and preserve completed source decisions.
- [x] Verify the two original PSI evaluations and independent reuse basis.
- [x] Stage and apply the two eligible local formation-G observations.
- [x] Preserve prior rows and preferred values; verify formula/activity and balance behavior.
- [x] Update tests, notices, statistics and manuscript assets.
- [ ] **R11d1:** Obtain Bjerrum (1941), *Metal Ammine Formation in Aqueous
  Solution*, original nickel numerical pages (1957 reprint acceptable),
  confirm constants/conditions and reuse basis, then review the six ammines.
- [ ] **R11e:** Reconcile the remaining PSI original-source reaction routes
  and choose the next bounded eligible-source batch. Wider R11 stays open.

PSI p. 21 and Table 5.5 attribute the six ammonia constants to Bjerrum.
Available catalogue records, Google Books snippets and Bjerrum's 1982
author commentary establish the bibliography; they provide insufficient
original numerical evidence for import. Free access and publication age
establish no open licence. No ammonia reference or observation is added.

Historical requested coverage remains **116/131: NEA 28/28, NIST 88/103**.
Six original crystalline G gaps, zirconium scientific/thermal follow-ups
and other sources' permission holds retain their separate status.
The full eight-route ledger, source evidence, candidate package, calculations,
validation and release records remain in the external running-plan checkpoint
`r11d-nickel-ammonia-hydrosulfide`.
