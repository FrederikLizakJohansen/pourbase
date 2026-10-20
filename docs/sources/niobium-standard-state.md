# R11n: niobium standard-state review

Reviewed 20 October 2026. This batch adds **12 G/H/S observations**, **three
infinite-dilution aqueous ions** and **nine newly available properties**.
The existing neutral HNbO3 record receives three alternatives. All earlier
SQL rows and observations remain. Three finite-I observations remain in the
evidence tables and are excluded from standard-state selection.

## Completed review

- [x] Verify original NBS finite-I qualifiers and native hydration ancestry.
- [x] Verify Peiffert2010 original evaluation, source conditions and phase assumption.
- [x] Normalize the neutral water-equivalent notation without a duplicate species.
- [x] Stage and apply eligible fitted estimates; preserve original alternatives.
- [x] Validate chemistry, ranking, default maps, supported balances and thermal use.
- [x] Record original numerical-facts reuse, open reference inputs and separate holds.

## Source and reuse

[Peiffert, Nguyen-Trung, Palmer, Laval and Giffaut (2010), *Solubility of B-Nb2O5 and the Hydrolysis of Niobium(V) in Aqueous Solution as a Function of Temperature and Ionic Strength*](https://doi.org/10.1007/s10953-010-9495-z),
Journal of Solution Chemistry 39, 197–218, **Table 7, printed p. 216 / PDF p. 20**,
provides the original four-species fitted-model G/H/S results at **298.15 K,
0.1 MPa = 1 bar, infinite dilution**, on the standard molal and conventional
proton-reference basis. The original publisher PDF was checked directly.
Its hash is recorded in database metadata `source_reuse_R11n_niobium`.

The established **individual original numerical-facts policy** carries forward
from R11g/R11l/R11m. It covers these individually cited original model results
and the local water-equivalent normalization. The article has no asserted open
licence. Complete publication, original table layout, prose, figures and OCR
remain external. Its Crossref text-mining licence supplies no open-data grant.
NEA permission is separate from this original-study route.

The study's solid/water numerical reference inputs independently match the
explicitly open non-SRD [NIST PDR M32124](https://doi.org/10.18434/M32124)
release. The carried NBS reuse review applies. NIST is acknowledged under its
[open licence](https://www.nist.gov/open/license), without warranty. Open CSV
logical record 41 supplies water G/H/S **−237129 J/mol, −285830 J/mol,
69.91 J/(mol K)**. High-temperature-labelled oxide logical record 6881 was
already reviewed in R11l. No restricted compilation is imported.

## Phase assumption and fitted-model scope

Source p. 200 / PDF p. 4 identifies a recrystallized, XRD-characterized B-Nb2O5
sample and explicitly states that some sources, including Wagman, call B the
high-temperature phase. Source p. 213 / PDF p. 17 uses high-temperature-labelled
oxide reference thermochemistry to calculate Table 7. The new observations
retain **that published model assumption**. The pre-existing NBS oxide record
keeps its original identity separately. This batch supplies no independently
verified B-oxide absolute thermochemistry or universal equivalence between
high-temperature-labelled specimens and B.

All new observations retain **`source_verified_estimate`, class E**. They come
from the empirical four-species fit extrapolated to infinite dilution. The
study reports unreliable SIT interaction parameters, limited evidence for
Nb(OH)7(2−), alternative fits omitting that ion and secondary-solid changes
above pH 9. These limits remain in warnings and locators. The observations
supply a qualified aqueous model; they do not establish an all-pH solubility
model, polymerisation constants or a closed sodium/niobium inventory.

## Identity and normalization

Three new records describe **Nb(OH)4(+), Nb(OH)6(−) and Nb(OH)7(2−)** at
infinite dilution. They each have one Nb atom, oxidation/electron coefficient
5 and proton coefficient 4, 6 or 7 respectively. Their finite-medium legacy
counterparts remain separate evidence records.

For the neutral species, the existing record
`gfe-nb-hnbo3-q+0-aqueous-aq` already represents the water-equivalent identity:

`Nb(OH)5(aq) = HNbO3(aq) + 2 H2O(l)`.

Subtracting two source-water properties from the reported neutral evaluation
gives **G = −949742 J/mol**, **H = −1080340 J/mol** and
**S = −29.82 J/(mol K)** per HNbO3 formula unit. The transformed energy is
identical to the fully hydroxylated representation on the same water basis.
No second neutral standard-state species is added. The negative conventional
entropy belongs to this water-equivalent formula; it is not an inferred
entropy for Nb(OH)5 itself. All earlier Shock-source G/H/S observations remain.

The source's quoted G interval is **±8 kJ/mol** for each ion/neutral model.
Every Table 7 G/H/S width remains in its original and normalized units.
Tables 5/6 define their fit intervals at 2σ; Table 7 gives no separate
confidence footnote. No one-sigma rescaling, covariance or additional
phase-assumption interval is invented. Neutral normalization retains the
source model interval on fixed source-water inputs. Calculation bands use
these supplied widths as their nominal input; they are not a newly calibrated
statistical confidence statement.

## Finite-I ancestry and selection

The open NBS CSV labels **ionic strength = 1** for logical records
**6880, 6883 and 6884**, respectively NbO3(−), Nb(OH)4(+) and Nb(OH)5.
[Nagra NTB 02-16 (2002)](https://media.nagra.ch/uploads/2022/08/e_ntb02-016.pdf),
p. 236 / PDF p. 260 in the retained report, explicitly describes the aqueous
basis as **I = 1 M**. The CSV qualifier alone gives no concentration unit;
no conversion to 1 mol/kg is inferred.

Native NbO2(+) is a dehydrated notation for Nb(OH)4(+), differing by two
waters. The native reaction 257, log K **6.896**, inherits the finite-I
reference values. Applying the hydration arithmetic to the original rounded
NBS G values reconstructs approximately **6.8975**, consistent with that
ancestry. Native oxide reaction 325, log K **24.342**, inherits the same
finite-I aqueous basis. Neither becomes an I=0 constant through a change of
formula spelling. A Davies correction at I=1 is unsupported.

Three explicit policy exclusions now keep these finite-medium G observations
outside standard-state calculations. Their numerical values, citations and
historical warnings remain unchanged. The independent modern I=0 estimates
are separately scoped. The ordinary class-E ranking selects the new
fitted-model neutral alternatives ahead of its predictive correlation.
The strict periodic screen now marks Nb incomplete because it retains the
three excluded finite-medium records. Its calculated-system count changes
from 57 to 56; the existing allow-incomplete mode calculates all 75 systems.
All other previous preferred IDs remain. Ranking rules and all 46 overrides
are unchanged; the policy now has **13 exclusions**, fingerprint
**8c4739134347**. Recommendation fingerprint: **1c319430cfaf734e**.

## Scientific effects

Independent formation/reaction calculations verify charge, electron and proton
balances and the water-equivalent identity. Table 7's rounded formation
energies reconstruct stepwise hydrolysis log K **−1.5993, −5.1032 and
−9.6582**. Their differences from the study's separately printed
**−1.7, −5.0 and −9.8** fit constants are within the 1 kJ/mol rounding of the
formation-energy entries. The source fit constants remain in metadata; they
are not forced onto rounded formation energies. Restricted aqueous domain
boundaries and ideal/Davies activity ratios match the stored model.

All **75 default systems** were compared on 81 × 91 grids. **74** retain
stable maps and 1σ/3σ masks. Niobium changes **5968/7371** stable cells,
**1787** 1σ-mask cells and **4626** 3σ-mask cells. Mapping old hydrated and
dehydrated names to equivalent modern identities still leaves 5968 changes:
these are substantive thermochemical/domain changes. The high-temperature
oxide and the new higher hydrolysis ion enter the stable-map competition.
The source qualifications remain relevant when interpreting those domains.

**12** supported balance scenarios conserve metal and independently verify
aqueous activity ratios: full and aqueous-only inventories at two total
concentrations with ideal and Davies I=0.001/0.01 activity models. Thermal
checks at **323.15/343.15 K** verify the existing same-source G/H,
constant-formation-entropy approximation. These are model-use checks; source
Cp and the full empirical temperature/ionic-strength fit are not implemented.

The database has **1059 species / 3385 observations / 75 systems**, with
**933/830/715** preferred G/S/H properties. Nine new fields are supplied;
three neutral choices change and three incompatible finite-I G choices are
removed. Historical target coverage remains **116/131 (88.5%)**, including
**28/28 NEA** values. Six original crystalline-G gaps remain. The main tracker
retains **5/18 checked headline reviews (27.8%)** and separately records holds.

## Separate remaining requirements

- [ ] **R11n1:** independently establish the phase-resolved B-oxide absolute
  thermochemistry and its relation to the older high-temperature-labelled
  NBS specimen. The current aqueous model retains the original authors'
  assumption; the solid records remain distinct.
- [ ] **R11n2:** resolve higher hydrolysis/polymerisation and secondary
  sodium-niobate phases before claiming a broader alkaline solubility or
  closed-component model.

The finite-I/native-hydration review R11l1 is complete with its explicit
eligibility decision and independent I=0 model observations. These two
remaining requirements are separate from the completed source review.
Earlier source/permission holds, including the MnCO3 native variant, remain.
