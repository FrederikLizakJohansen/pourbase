# Zirconium hydrolysis and reference components

The 15 October 2026 NEA02g1 checkpoint resolves five of the 27 zirconium
scientific/model holds. It adds nine observations, three species and two
open NBS reference components. Seven properties become available and two
preferred Gibbs energies change under the existing selection policy. Every
earlier observation remains stored. Production contains **969 species,
3,093 observations and 74 systems**, with selected G/S/H **855/776/654**.

## Selected source values

Brown, Curti and Grambow, with Ekberg (2005), *Chemical Thermodynamics of
Zirconium*, OECD Nuclear Energy Agency volume 8, selected Table III-1,
provides the following values at 298.15 K and 0.1 MPa. Observation locators
record the exact printed/PDF page, units, conversion and source interval.

| Source species | G (J/mol) | H (J/mol) | S (J/(mol K)) |
| --- | ---: | ---: | ---: |
| Zr(g) | 566,882 ± 1,400 | 609,800 ± 1,400 | 183.027 ± 0.010 |
| Zr(OH)2²⁺ | −1,008,384 ± 11,034 | — | — |
| Zr(OH)4(aq) | −1,464,570 ± 13,391 | — | — |
| Zr(SeO3)2(cr) | — | −1,609,550 ± 2,689 | — |
| ZrSiO4(cr), zircon | −1,919,712 ± 3,115 | −2,034,200 ± 3,100 | 84.2 ± 1.0 |

The NEA intervals correspond in principle to 95% confidence. They retain
that interpretation; the database sensitivity screen uses mixed source
intervals and has no uniform confidence-level meaning. The water-basis
conversions below preserve these widths under the pinned reference
convention; shared source covariance is unavailable.

## Hydrolysis in the existing water-component basis

The existing ZrO²⁺ and ZrO2(aq) records use water-subtracted component
formulas. Shock et al. (1997), *Geochimica et Cosmochimica Acta* 61,
907–950, p. 932, Eq. 50 and its adjoining discussion, explicitly describe
this convention and explain that such formulas need not describe molecular
structure. NEA section V.2.2, pp. 99–100, rejects a separately identified
physical zirconyl ion. Here the formulas specify thermodynamic components;
the source hydroxo identity and this structural caution remain explicit.

At unit water activity, using the project liquid-water reference
G(H2O) = −237,129 J/mol:

| Source → stored component | Calculation (J/mol) |
| --- | ---: |
| Zr(OH)2²⁺ → ZrO²⁺ + H2O | −1,008,384 − (−237,129) = **−771,255** |
| Zr(OH)4(aq) → ZrO2(aq) + 2H2O | −1,464,570 − 2(−237,129) = **−990,312** |

Charge, primary-metal count and the balanced electron/proton coefficients
are preserved. Independent calculations with the complete hydroxo formulas
give the same transformed energy across pH, potential and aqueous activity.
The source second/fourth hydrolysis log constants are +0.98 and −2.19;
the mixed runtime references reproduce these within 0.02 log units.
Re-normalize these components if the project water convention changes.

The policy selects the new Gibbs observations and retains the older
−784,918.4 and −976,545.6 J/mol estimates as alternatives. Existing H/S
selections keep their independent source identities. This combination
supplies no new source-verified temperature model or joint covariance.

## Open free-reference components

Two references come from the previously reviewed, explicitly open non-SRD
NIST Public Data Repository release, *NBS Tables with errata*,
[DOI 10.18434/M32124](https://doi.org/10.18434/M32124).
Logical record numbers include the two header records; column 9 supplies G.

| Reference ID | NBS logical record | Source G (J/mol) | Stored reference G (J/mol) |
| --- | ---: | ---: | ---: |
| `selenite-seo3` | 759, SeO3²⁻(ao) | −369,800 | −369,800 |
| `silica-sio2-component` | 2941, H4SiO4(ao) | −1,316,600 | −842,342 |

The neutral silica reference removes two project-water units from H4SiO4.
Its `formula_ascii="SiO2"` specifies this component basis. Its prescribed
free activity equals that of neutral aqueous H4SiO4 at unit water activity.
Use direct `log10_free_activity`: the existing total/pKa expression describes
a deprotonated ligand and does not model this neutral silica reservoir.
Total silica, acid/base speciation and silicon inventory require an explicit
separate model. The earlier charged silicate reference remains available.

For zircon, one silica component leaves two core oxygen atoms and gives
electron/proton coefficients of four. The runtime energy agrees exactly
with the complete physical reaction
`Zr + H4SiO4 -> ZrSiO4 + 4H+ + 4e-` across the tested free activities.
Zircon keeps its source-selected crystalline identity; an unreported space
group or a Materials Project match is not assigned.

The selenite reservoir uses prescribed free SeO3²⁻ activity. Total selenite
and protonation need their own model. The selected zirconium selenite entry
has H only and remains explicitly unavailable for a G-based phase diagram.
NEA section V.5.2.2, p. 194, discusses two other entropy estimates without
selecting either in Table III-1. Those estimates retain a separate original
evaluation follow-up; a Gibbs energy is not inferred here.

## Gas scope and validation

Zr(g) uses the existing `optional_gas_phase` convention. Its G/H/S are selected
and accessible as evidence. Include it in a fixed-fugacity calculation with
`database.load_system("Zr", include_optional_gases=True)`. Default Zr systems
return an `optional_gas_not_selected` exclusion and support closed metal
balance. A gas-containing closed balance requires a separate headspace model.

The two hydrolysis selections change 488/7,371 default zirconium stability
points and 560/7,371 uncertainty-mask points. The other 73 default phase maps
and masks are unchanged. Aligned pymatgen energies agree; all 57 plain/ligand
scenarios run and all 114 explicitly gas-free ideal/Davies metal balances
conserve metal. Four temperature scenarios record the effects of the mixed
selected G/H/S without establishing a coherent NEA temperature model.

## Reuse and remaining work

OECD and NEA are acknowledged for the selected zirconium evaluations.
The written NEA-TDB clarification permits use, adaptation and redistribution,
including commercially, under the [OECD data terms](https://www.oecd.org/en/about/terms-conditions.html),
subject to source-specific additional restrictions. The completed volume-8
review is carried forward for these selected numerical evaluations. Every
sublicense of work using these data must include the same OECD acknowledgment
requirement and require further sublicensees to pass it on. See
[distributed notices](https://github.com/FrederikLizakJohansen/pourbase/blob/main/THIRD_PARTY_NOTICES.md). NIST is acknowledged for
the two reference values under its [open licence](https://www.nist.gov/open/license).
Private correspondence and complete publications remain outside the package.

**22 of the original 27 zirconium holds remain:** six Te/N/C reference routes,
four disputed source evaluations and twelve mixed-metal records. The next
batch reviews the six buffered-element/reference routes. Two Cp-only rows
remain with R18, and the earlier 29 Fe/Ni/Sn solid/model holds retain their
own completed reviews. The new silica component also provides a potential
route for earlier silicate holds; those entries still need individual review.
Historical request coverage stays **116/131 (NEA 28/28; NIST 88/103)**, and
the six original crystalline Gibbs gaps remain open. Other sources retain
their independent permission status.

Sources: [NEA volume 8](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/chemical_thermodynamics_of_zirconium_volume_8.pdf),
[Shock et al. (1997)](https://doi.org/10.1016/S0016-7037(96)00339-0).
