# R12: SUPCRT versions and original mineral evaluations

Reviewed 24 October 2026. This batch adds **75 observations, 25 species and
75 available properties**. Every earlier observation and preferred value
remains under the unchanged policy. All additions use the carried
USGS-authored public-domain route and independently verified original cells.

## Eight-version comparison

The pinned Reaktoro commit
`f587235e692b7168faa272c8892a4c079a1f7dd9` supplies these files:

| Version | Base records | Records with organics |
|---|---:|---:|
| SUPCRT98 | 983 | 1,553 |
| SUPCRT07 | 1,018 | 1,920 |
| SUPCRT16 | 1,068 | 2,029 |
| SUPCRTBL | 1,108 | 1,671 |

The external `supcrt-version-crosswalk.csv` covers **11,350 record
representations and 34,050 G/H/S slots**. All 28 version pairs are compared.
There are 2,361 named composition/charge/state identities on their encoded
formula bases and 3,948 distinct exact identity/G/H/S representations.
These are comparison counts, with repeated versions preserved separately.

The external `unique-record-review.csv` gives every distinct representation
a source and scientific-scope decision. Compatible comparisons against
ThermoHub SLOP16 and SLOP98 retain the completed R06 property decisions and
current original observation links. An equal number or formula supplies
comparison evidence; original ancestry and crystal identity require their
own evidence. Duplicate and rounded representations create no additional
observation of a previously retained evaluation.

The [ThermoHub compilation](https://github.com/thermohub/thermohub/tree/c3e4acf4531204e4c2974c2d4ac5a1b96f37d5ba)
has its recorded GPL-3.0 route. Direct bulk numerical rights for the eight
Reaktoro files remain unresolved. Their software wrapper and download access
do not establish a blanket grant for inherited numerical sources.
[SUPCRTBL's author documentation](https://github.com/HydrogeoIU/SUPCRTBL)
identifies HP2011 mineral data, arsenic sources and updated Al/Si/dawsonite
evaluations. `HollandPowell` is a calculation-model label; it supplies no
universal source attribution or permission for every mineral using it.
Held native evaluations retain their specific source and state questions.

WaterHKF parameters `Gtr`, `Htr` and `Str` describe the triple-point reference.
They are kept separate from standard 298.15 K formation observations.

## Formula scale and phase identity

Enstatite and ferrosilite expose 24 cross-version comparisons with different
formula scales. For example, SUPCRTBL's Mg2Si2O6 formula contains two USGS
MgSiO3 units. Native G/H/S are divided by that factor for comparisons;
the source and stored formula units remain explicit. No extra scaled copy
of one observation is added. A separate comparison file records these
relations and preserves differences between the evaluations.

Low clino-enstatite maps to the named USGS clinoenstatite alternative through
an explicit hyphenated-name alias and a factor of two. High-pressure
clinoenstatite and protoenstatite remain separate source candidates.

## Original USGS additions

[Robie and Hemingway (1995), USGS Bulletin 2131](https://doi.org/10.3133/b2131),
**Table 2**, supplies all 75 independently checked G/H/S cells:

| Printed page / PDF page | Admitted named phases |
|---|---|
| 19 / 25 | Coesite, stishovite |
| 31 / 37 | Kyanite, andalusite, sillimanite, phenakite |
| 32 / 38 | Cobalt-olivine, fayalite |
| 33 / 39 | Forsterite, tephroite, liebenbergite, Ni2SiO4-spinel, willemite |
| 34 / 40 | Wollastonite, hedenbergite, diopside, ferrosilite, enstatite, clinoenstatite |
| 35 / 41 | Rhodonite, jadeite |
| 39 / 45 | Dickite, halloysite, pyrophyllite, talc |

Twenty phases have named SUPCRT counterparts; phenakite, cobalt-olivine,
liebenbergite, Ni2SiO4-spinel and willemite are an adjacent extension from
the same original USGS pages. These original evaluations retain their
identity independently of the different native SUPCRT/HP2011 values.

Every property retains its source bibliography numbers and entries, exact
page, original units and quoted interval. G/H convert from kJ/mol to J/mol;
S retains J/(mol K), all per complete formula unit, at 298.15 K and 1 bar.
The unchanged policy recognizes the critical USGS evaluation as class B.
Quoted widths retain their source convention without an invented confidence
conversion or covariance. These are critically evaluated properties with
experimental and fitted research ancestry, recorded separately by property.

For example, enstatite retains G = −1458.3 ± 1.6 kJ/mol,
H = −1545.6 ± 1.5 kJ/mol and S = 66.3 ± 0.1 J/(mol K).
Liebenbergite and the spinel retain different Ni2SiO4 evaluations, with
an 8 kJ/mol difference per two-Ni formula unit. Their difference per mole
of primary Ni is 4 kJ/mol. Halloysite retains exactly the table's formula
Al2Si2O5(OH)4; extra interlayer-water variants remain separate.

Named crystalline phases are resolved to the source mineral and composition;
space groups and specimen-to-structure matches remain unspecified.
Coesite, stishovite and the nickel spinel retain explicit high-pressure-phase
qualifications. Their source standard-state values are metastable references;
they establish no ambient occurrence, kinetics or higher-pressure model.

The [USGS public-domain statement](https://www.usgs.gov/faqs/are-usgs-reportspublications-copyrighted)
and source review carry forward. USGS and Robie/Hemingway are acknowledged in
[distributed notices](https://github.com/FrederikLizakJohansen/pourbase/blob/main/THIRD_PARTY_NOTICES.md). No additional third-party
ownership restriction was identified for these author evaluation cells.
The original report, policy evidence and hashes remain in the external
review. Complete publications and held native compilations stay outside
distributions. Earlier OECD and other source obligations remain applicable.

## Buffered reactions and verification

Twenty-three new minerals require the existing aqueous-silica reservoir,
on the H4SiO4-minus-two-waters component basis. Diopside and hedenbergite also
require free Ca2+; jadeite requires free Na+. Every required activity must be
supplied. Coesite and stishovite belong directly to the Si system.

Complete formulas determine the primary-metal count, residual O/H and
charge-balanced proton/electron coefficients. Independent energy checks use
physical H4SiO4 and water stoichiometry. Closed balances conserve the primary
element with secondary Si/Ca/Na activities externally prescribed. Joint
secondary-element balances, solid solutions and broader component thermal
or pressure models remain separate work.

Validation checks 225 full-formula energy evaluations, 39 diagram scenarios
and 156 primary-metal balances with ideal and Davies activities. All 75
default phase maps and 1σ/3σ masks remain unchanged. Selected buffered
diagrams acquire stable mineral fields. Every earlier SQL row and preferred
candidate, the policy, six crystalline-G gaps and historical requested-value
coverage remain unchanged.

The finite eight-version comparison is complete. Bulk rights, remaining
original property routes, native source/state discrepancies, unsupported
chemistry and all earlier R06 and independent source/scientific holds remain
tracked. Metadata `R12_SUPCRT_version_review`, `R12_USGS_observations` and
`R12_source_and_scientific_holds` retain the evidence and scope.
