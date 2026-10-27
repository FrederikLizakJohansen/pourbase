# Review of disputed zirconium evaluations

The 16 October 2026 NEA02g3 checkpoint reviews four held source rows.
It admits **nine observations and three species**: two explicitly selected
oxide gases as qualified historical estimates, and the selected-table
ZrS1.5 evaluation. All earlier observations and preferred values are preserved.
That checkpoint contained **978 species /3,118 observations /74 systems**, selected
G/S/H **863/784/663**.

This completes the finite four-row review with one admission still held:
the bulk ZrH correlation. Fourteen of the original 27 rows have now been
admitted; 13 remain held, comprising ZrH and twelve mixed-metal records.
An updated evaluation of the oxide gases remains a separate scientific
follow-up. Their admission preserves the published historical estimates;
it does not resolve the disagreement about their accuracy.

## Retained observations

Brown, Curti and Grambow, with Ekberg (2005), *Chemical Thermodynamics of
Zirconium*, NEA volume 8, selected Table III-1, supplies these values at
298.15 K and 1 bar. G/H use J/mol of the complete formula; S uses J/(mol K).

| Species | Printed/PDF page | G | H | S |
| --- | --- | ---: | ---: | ---: |
| ZrO(g) | 48/78 | 30,576 ± 27,124 | 56,200 ± 27,008 | 227.6 ± 8.4 |
| ZrO2(g) | 48/78 | −298,386 ± 47,042 | −289,600 ± 47,018 | 273.7 ± 5.0 |
| ZrS1.5(cr) | 51/81 | −502,107 ± 3,886 | −509,400 ± 1,100 | 62.7 ± 12.5 |

All nine observations have `source_verified_estimate` status. The existing
policy classifies their source as NEA-TDB, class A, and selects the sole
eligible observation for each new property. This records a preferred value
within the database's available evidence. It supplies no claim that the
historical gas set is the best current experimental assessment. Published
NEA total intervals retain their interpretation, corresponding in principle
to 95% confidence; no one-standard-deviation conversion or covariance is inferred.

## Oxide gases: qualified historical evidence

The later review by Rand et al. (2008), *Chemical Thermodynamics of Thorium*,
NEA volume 11, Appendix F, pp. 781–782, identifies an old assessment basis
and omitted later experiments. It declines a thorium calibration involving
ZrO because of its uncertain enthalpy. The appendix provides a critique and
comparison, without selecting a replacement NEA zirconium gas set.

The 2005 selected evaluations are retained with this caution in every locator
and warning. Their original G/H/S and uncertainty widths are preserved.
Independent copied JANAF/Glushko comparison values are outside this import.
The warnings cite the later review through its own source record, while the
observations retain the original zirconium review as their numerical source.

Both gases use `optional_gas_phase`. Their selected properties are available
through the evidence API; calculation requires
`load_system("Zr", include_optional_gases=True)`. Default zirconium remains
gas-free. Explicit gas-containing closed balance needs a headspace model.
The balanced water reactions have proton/electron coefficients 2 for ZrO
and 4 for ZrO2. Fugacity shifts energy by `RT ln(f/f°)`.

Source H/S arithmetic reproduces both G values within 0.51 J/mol. This checks
the published calculation, without validating the underlying experiments.
The external follow-up seeks original later mass-spectrometric studies and
verified thermal/spectral inputs before adding a revised evaluation.

## ZrS1.5: selected tables and structural notation

The page images confirm a real discrepancy. Table III-1, p. 51, and Table
V-27, p. 185, agree on positive S and the retained G/H values. Discussion
p. 184 prints negative absolute S and a different G. Using the positive
selected entropy reproduces Table III-1 G within 0.51 J/mol. The inconsistent
discussion numbers remain in the external discrepancy ledger, outside the
eligible observations. This is an explicit selected-table decision, with no
claim that an official erratum was found.

Discussion p. 183 states that ZrS1.5 has the Zr3S4 crystal structure at 1100 K.
The parentheses in Table V-27 identify this structure type; the stored
formula remains **one Zr and 1.5 S**. The original Larson/Schlechten study's
abstract also describes a composition range for the phase labelled Zr3S4.
The record assigns no unique 298.15 K polymorph, space group or solid-solution
model. H retains its third-law evaluation and S its analogy estimate; G
inherits those qualifications.

The existing free S²⁻ reference supplies 1.5 sulfide ions. Core O/H are zero,
and the balanced electron coefficient is +3 per Zr. Full-formula checks
preserve this reaction, with no invented conversion to a Zr3S4 formula unit.

## ZrH: bulk correlation remains held

Sections V.3.4, pp. 129–133, and Table V-13 describe composition-dependent
hydride measurements and mixed-phase samples. The selected ZrH quantities
come from bulk-composition correlations. A bulk reference energy alone
does not establish a pure phase that can compete independently in the
current phase model. The three published numbers remain in the external
candidate ledger. No pure solid ZrH record is added. The existing epsilon-ZrH2
record retains its separate identity and observations.

Admission needs the original hydride studies, phase fractions and endmember
data, and a validated assemblage or solid-solution representation. This is
a scientific/model hold; the NEA reuse permission remains available.

## Effects, reuse and next work

All 74 default phase maps and uncertainty masks are preserved. At free
sulfide log activities −6/−3/−1, the new sulfide changes 8/10/7 of 1,271
sampled stable points. The other 67 tested buffered cases are unchanged.
All 140 explicitly gas-free ideal/Davies zirconium inventories conserve metal.
Gas-enabled maps at log fugacity 0/−3/−12 keep their stable labels, and aligned
pymatgen checks agree. Four temperature checks preserve default maps and gas
selection scope; they establish no new temperature accuracy for these estimates.

OECD and NEA are acknowledged for the selected numerical evaluations and
the later scientific critique. Completed volume-8 reuse checks are carried
forward under the written NEA-TDB clarification and
[OECD data terms](https://www.oecd.org/en/about/terms-conditions.html), subject
to source-specific additional restrictions. Every sublicense of work using
these data must include the same OECD acknowledgment requirement and require
further sublicensees to pass it on. See [distributed notices](https://github.com/FrederikLizakJohansen/pourbase/blob/main/THIRD_PARTY_NOTICES.md).
Private correspondence and complete publications remain outside the package.

Next is the twelve-record mixed-metal review, NEA02g4. The hydride admission
hold and original-gas source-upgrade route remain separately tracked.
Earlier Fe/Ni/Sn holds, Cp/R18 routes and other sources' permission states
retain their histories. Historical request coverage stays **116/131
(NEA 28/28; NIST 88/103)**, and the six original crystalline Gibbs gaps remain.

Sources: [NEA zirconium volume 8](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/chemical_thermodynamics_of_zirconium_volume_8.pdf),
[NEA thorium volume 11](https://www.oecd.org/content/dam/oecd/en/publications/reports/2008/12/chemical-thermodynamics-of-thorium-volume-11_g1gh9fd7/9789264056688-en.pdf),
[Larson and Schlechten (1964), original abstract](https://www.onemine.org/documents/extractive-metallurgy-division-a-thermodynamic-study-of-the-zirconium-sulfur-system-in-the-region-zrs1-49-to-zrs2-00).

## Original-gas follow-up

NEA02g3b retains two original1975formation-H alternatives at298.15K and one
1974ZrO formation-H observation at0K. The latter is explicitly excluded from
298.15Kselection. All historicalNEAobservations and preferred values remain
unchanged. The [original-source review](nea-zirconium-gas-upgrade.md) records
primaryabstract verification,individualnumerical-fact reuse,sourceconditions
and remaining full-method/thermal/G/S work. This is a later checkpoint; the
earlier counts and validation results above remain its historical record.

## Original hydride follow-up

The [original-source and assemblage review](nea-zirconium-hydride-assemblage.md)
recovers the 1958 NBS measurements and 1963 NBS evaluation. Their phase
labels and lever-rule treatment confirm the bulk identity of the held ZrH
correlation. All three held values remain external; admission needs a
validated assemblage or solution model. The review also records an internal
NEA per-H2 unit/basis discrepancy. Release counts and preferred values stay
unchanged.
