# Remaining NEA auxiliary observations

R11j3l reconciles the final 23 non-arsenic cells in the auxiliary inventory.
It adds 36 reported observations: 18 NEA selected/evaluated properties and
18 alternatives from the explicitly open non-SRD NBS release. Five new species
gain 15 properties. The existing Ni metal entropy is linked to its completed
NEA02a review. All earlier observations remain available, and the unchanged
policy selects one value per property. Twelve earlier preferred records change,
including eleven numerical changes.

## Exact sources and scientific qualifications

Grenthe et al. (1992), *Chemical Thermodynamics of Uranium*, vol.1,
Table IV.1 pp.68,69,71 supplies Te entropy, aqueous NH3 and SCN− properties.
The discussions are Chapter VI.2.3 p.383, VI.3.1.1 p.384 and VI.4.1.2 p.394.
The original NaNO3 crystal enthalpy calculation is on Appendix A p.620;
the 2003 update p.395 points back to that original evaluation.
See the [official volume](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/uranium.pdf).
Te entropy adopts an IAEA review; the selected NH3 properties derive from
protonation evidence. SCN retains rounded NBS G/H with assigned 4 kJ/mol
confidence widths and calculated entropy, with the source's limited assessment
scope explicit. Numerical ancestry accompanies every observation.

Rard et al. (1999), *Chemical Thermodynamics of Technetium*, vol.3,
Table IV.1 p.54 and Chapter VI.1.1.1 pp.267–268 selects aqueous Tl+
G = −32.400 ±0.300 kJ/mol after checking solubility and emf evidence
([official volume](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/chemical_thermodynamics_of_technetium_volume_3.pdf)).
The last displayed equation on p.268 omits the minus sign. The selected table,
the preceding source comparison and derived value establish the negative sign;
this discrepancy is retained in its locator and warning.

Guillaumont et al. (2003), *Update*, vol.5, Table 8-1 p.139 and
Chapter 14.1.1.1 p.393 supplies TeO2 G = −265.996 ±2.500 kJ/mol,
H = −321.000 ±2.500 kJ/mol and S = 69.890 ±0.150 J/(mol K)
([official volume](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/update_on_the_chemical_thermodynamics_of_uranium_neptunium_plutonium_americium_and_technetium_volume_5.pdf)).
The review increases entropy uncertainty and discusses a typo in the underlying
assessment. The existing alpha/beta phase ambiguity remains explicit.

Gamsjäger et al. (2005), *Chemical Thermodynamics of Nickel*, vol.6,
Table VI-1 p.250 supplies the TDB-consistent formation enthalpies of KCl,
KBr and KI: −436.461 ±0.129, −393.330 ±0.188 and −329.150 ±0.137 kJ/mol
([official volume](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/chemical_thermodynamics_of_nickel_volume_6.pdf)).
The review recalculates these formation properties from assessed solution heats
and its ion references. Source locators distinguish these selected outputs from
raw Glushko solution-enthalpy inputs. Ni entropy, Table III-1 p.44 and
Chapter V.1.2 p.77, already exists and is linked without duplication.

Olin et al. (2005), *Chemical Thermodynamics of Selenium*, vol.7,
Table IV-1 p.75 and Chapter VI.2.1.1 pp.433–434 supplies HCN gas
G = 119.517 ±2.500 kJ/mol, H = 129.900 ±2.500 kJ/mol and
S = 201.710 ±0.100 J/(mol K)
([official volume](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/chemical_thermodynamics_of_selenium_volume_7.pdf)).
This is a critical evaluation combining combustion, equilibrium, spectroscopy,
statistical mechanics and quantum calculations. Its mixed ancestry remains
explicit. The older open NBS gas G =124.7 kJ/mol is retained as an alternative;
the 5.183 kJ/mol spread receives an explicit source review.

The independent open alternatives are from [NIST M32124](https://doi.org/10.18434/M32124),
logical CSV records 1955 (HCN gas), 2096 (SCN−), 10791 (NaF crystal),
11272 (NaNO3 crystal), 12270 (KBr crystal) and 12335 (KI crystal).
One-based G/H/S columns are 9/8/11. Original quantities and missing
uncertainties remain unchanged. KI's publisher explicitly relaxes its G/H/S
constraint; its approximately +1.741 kJ/mol source-cycle residual is documented.
All source URLs were accessed on 26 October 2026.

## Representation and calculation checks

The five new records are HCN gas, aqueous SCN− and crystalline NaNO3,
KBr and KI. HCN uses primary C and half an external N2 component;
its signed electron coefficient is −1. It requires explicit optional-gas
selection and a fixed fugacity. SCN− uses primary S and one external CN−
component, with zero net electron coefficient. The alkali salts use one
external free-anion component and one electron per primary atom. Complete
formulas and atom counts remain intact. New crystal structures are unresolved.

All 31 fixed free-component references remain unchanged, including the existing
SCN reference. Closed primary-element balances use explicitly buffered ligand
activities. They conserve the primary element; their external C/N or free-anion
reservoirs are prescribed. Gas/closed-balance and ligand/temperature exclusions
retain the existing model scope.

Validation covers 33 balanced energies, 22 thermal or thermal-exclusion checks,
28 supported mass balances and all 75 default phase maps. The default maps
are unchanged. Nitrogen uncertainty masks change at 44/195 grid points and
thallium masks at 113/349 points for multipliers 1/3 on the 81 ×91 grid.
Other default masks remain unchanged. Buffered-component maps are also reviewed.
Strict periodic coverage stays 53 experimental systems and 56 with fallbacks;
available-data calculations cover 75 systems. Historical request coverage stays
116/131 (NEA 28/28, NIST 88/103); six original crystalline Gibbs gaps remain.

## Reference context and separate holds

H2O2(aq) remains within the H/O reference-component scope. Metadata
`R11j3l_H2O2_reference_observations` preserves NEA Table IV.1 p.64
H = −191170 ±100 J/mol, and original open NBS record 50
G/H/S = −134030 J/mol / −191170 J/mol / 143.9 J/(mol K).
These four context properties are separate from reported-observation,
primary-species and preferred-property counts. A general reference-observation
schema remains a model follow-up.

The three NEA NaF cells are identified direct Glushko copies: Lemire et al.
(2001), *Chemical Thermodynamics of Neptunium and Plutonium*, vol.4,
Table 5.1 p.76, footnote(p) p.77. They remain held under the existing
source rule. The independently open NBS NaF triplet is retained instead.
The complete 729-cell inventory now has 203 direct links, three verified
water conversions, one reference-only context cell, 358 copied CODATA holds,
12 identified direct Glushko holds, one H2SO3 identity hold, 87 defined
references and 64 blanks. The remaining nonbold source-review count is zero.
Heat capacities remain in the separate R18 model inventory. R11j3f1,
R11j3i1, R06/R07 and other independent source/model holds remain tracked.

NEA selections and adaptations use the supplied clarification and OECD data
terms. Credit OECD/NEA and each cited source. Pass the same acknowledgment
requirement into sublicences, requiring further sublicensees to do the same.
Open NBS entries carry NIST credit, its licence and warranty statement.
See [NEA reuse](nea-tdb-reuse.md) and [distributed notices](../../THIRD_PARTY_NOTICES.md).
Metadata keys also include `R11j3l_NEA_auxiliary_review`,
`R11j3l_auxiliary_observations` and `R11j3l_source_and_model_holds`.
