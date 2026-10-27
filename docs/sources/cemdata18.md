# R09: Cemdata18 hydrate evaluations

Reviewed 23 October 2026. This batch adds **153 observations for 53 species**,
making 153 additional G/H/S properties available. All prior observations and
preferred values remain. The selection policy is unchanged.

## Sources and reuse

[Lothenbach et al. (2019), Cemdata18](https://doi.org/10.1016/j.cemconres.2018.04.018),
*Cement and Concrete Research* 115, 472–506, supplies the original hydrate
evaluations. Exact values are checked in **Table 1**, accepted manuscript
pp. 4–5 / PDF pp. 5–6, with formula and reaction checks in Table 2. Each
observation records its column, manuscript line, original-study ancestry,
units, formula unit and conditions. Values retain the printed precision.

The [ThermoHub data mirror](https://github.com/thermohub/thermohub/tree/c3e4acf4531204e4c2974c2d4ac5a1b96f37d5ba)
uses GPL-3.0. Its licence, README and Cemdata18 file were checked against
pinned Git blobs. ThermoHub contributors and the ETH Board Open Research
Data Program are acknowledged. The import follows the project's established
individual numerical-fact route for original research evaluations also
represented in that mirror. The journal article retains its own copyright;
it is not described as open licensed. Complete publications, table images
and database exports remain outside the distribution.

Inherited PSI/Nagra support values, commercial clinker compilations and
other third-party tables retain separate source requirements. The mirror's
licence supplies no blanket clearance for those values. Existing OECD
credit and downstream acknowledgment requirements for NEA inputs continue
independently. See [the distributed notices](https://github.com/FrederikLizakJohansen/pourbase/blob/main/THIRD_PARTY_NOTICES.md).

## Evidence and physical scope

The additions are published solubility fits and author thermodynamic
estimates. They use `source_verified_estimate` and enter **class E** under
the current policy. Missing total uncertainty remains NULL; printed
precision supplies no uncertainty estimate. These are original authors'
evaluations, including their calibration assumptions and common ancestry.

Formation G/H use J/mol and entropy uses J/(mol K), per complete stored
formula unit, at **298.15 K and 1 bar** as specified in Table 1. Section 2.4
also calls the Fe-hydrate fits 1 atm; this textual discrepancy is explicit
in their locators. The admitted values follow the table's stated 1-bar
evaluation, with no new pressure correction inferred.

Distinct water contents and amorphous, microcrystalline and crystalline
identities stay separate. Al(OH)3(am), ageing-defined Al(OH)3(mic), FeOOH(mic)
and SiO2(am) are distinct from the existing crystalline phases. No
specimen-specific space group or Materials Project match is invented.
Metaettringite uses the authors' desorption-equilibrium branch and retains
the hysteresis qualification. Microcrystalline Al(OH)3 H/S describe an
ageing fit valid only to 60 °C.

Mixed hydrates use existing calcium, sodium, aluminate, silica, carbonate,
sulfate, chloride and nitrate references as required by their compositions.
Syngenite uses potassium as the primary inventory with buffered calcium and
sulfate. Every component must be selected and assigned a free activity.
O/H residuals, primary atom counts, charges and electron coefficients are
checked against the full formulas. Closed balances conserve the primary
inventory; secondary components remain externally buffered.

These records represent fixed-composition phases or pure endmembers at
unit activity. General cement hydration, ideal/nonideal solid-solution
mixing and variable-water-activity paths require additional models. Source
solubility products use a PSI/Nagra calibration; calculations with the
current pourbase references need not reproduce them exactly.

## Reconciliation and remaining work

The external `cemdata-review.csv` assigns a disposition to **714 direct
G/H/S slots and 108 reaction-property slots** across 238 substances and
27 reactions. All 27 reaction equations balance on their stored component
basis. Reaction quantities require compatible formation anchors before
conversion to absolute properties. Sixty-three mirror phase representations
link to the admitted original evaluations, including checked half/third
formula-unit aliases. Fe-Friedel's salt is an additional original Table 1
row absent from the pinned mirror.

Amorphous Al(OH)3 H/S are undefined in the original table, despite numerical
proxies in the mirror; only its original G is admitted. Microcrystalline
FeOOH has conflicting mirror H/S and inherited thermal ancestry; its
original fitted G is admitted separately. Other mirror/table discrepancies
remain recorded with the original printed values. Silica's inherited
thermal proxies remain held. An independent elemental-entropy check finds
M-S-H formation-identity differences of about 1.7–1.8 kJ/mol. Its separately
reported G/H/S remain model observations with an explicit joint thermal
consistency hold; the current temperature model excludes component-bearing
phases.

Table 3/4 solid-solution families, nitrite AFm's missing free-NO2 reference,
Fe-bearing layered-hydroxide component requirements, unresolved hydrate
formulas and inherited support routes remain explicit follow-ups. Earlier
source and scientific holds carry forward, including the six crystalline-G
gaps and unchanged historical-request coverage of 116/131.

Metadata `R09_Cemdata18_source_review`, `R09_Cemdata18_observations` and
`R09_Cemdata18_source_holds` retain the provenance, formulas and limitations.
Validation preserves all 75 default phase maps and uncertainty masks,
checks 159 component-reaction evaluations, and conserves primary inventories
in 20 buffered Al/Fe/Mg/Ca/K balance scenarios.
