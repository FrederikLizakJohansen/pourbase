# Corrected radium-solid enthalpies: R11q / R11l5

- [x] Verify original magnitudes, reaction direction and authoritative sign correction.
- [x] Check the carried individual-numerical-facts reuse route and open ionic anchors.
- [x] Add four historical H/S estimates and preserve all previous observations.

[Langmuir and Riese (1985)](https://doi.org/10.1016/0016-7037(85)90264-9),
*The thermodynamic properties of radium*, Geochimica et Cosmochimica Acta
49(7), 1593–1601, gives the original solid dissolution enthalpy magnitudes
2.8 kcal/mol for RaCO₃ and 9.4 kcal/mol for RaSO₄ in its publisher abstract.
The printed negative signs are corrected explicitly by Hummel et al. (2002),
*Nagra/PSI Chemical Thermodynamic Data Base 01/01*, NTB 02-16,
[section 5.16, pp.300–301](https://nagra.ch/wp-content/uploads/2022/08/e_ntb02-016.pdf)
(PDF pp.324–325). That review identifies the original Table 2 sign errors
and gives **positive** dissolution enthalpies for both reactions.
This scholarly correction satisfies the authoritative-correction requirement
in R11l5. It is recorded with its own citation and page locators.

## Local observations

All quantities below refer to the historical nominal crystalline endmembers
at 298.15 K and 1 bar. The conversion uses 1 kcal = 4184 J and preserves
the original magnitudes, avoiding the correction table's rounded SI values.

| Nominal solid | Corrected dissolution H (J/mol) | Local formation H (J/mol) | Local absolute S (J/mol/K) |
|---|---:|---:|---:|
| RaCO₃ | +11715.2 | −1216455.2 | 116.708515 |
| RaSO₄ | +39329.6 | −1476199.6 | 138.613089 |

The four additions are local `source_verified_estimate` observations,
evidence class E. They use the explicitly open, non-SRD NBS digitization:
Ra²⁺ logical record 10248, carbonate record 1661, sulfate record 574.
The inputs and equations are retained per observation:

```text
Hsolid = H(Ra2+) + H(anion) − Hdissolution
Gdissolution = −R × T × ln(10) × log10Ksp
Sdissolution = (Hdissolution − Gdissolution) / T
Ssolid = S(Ra2+) + S(anion) − Sdissolution
```

Entropy uses the original 1985 logKsp values −8.3 and −10.26. This keeps each
H/S derivation paired with its original G evaluation, which remains stored.
The currently preferred modern carbonate G is preserved as a separate
evaluation. Its combination with historical H/S has no newly validated
thermal interpretation. Exact modern carbonate composition/activity,
temperature correction and independent refit remain R11p1–R11p3.

The policy now selects the historical carbonate H and S, filling two missing
properties. Sulfate retains its preferred class B NBS H/S. Its historical H alternative
lies 5.0996 kJ/mol below NBS, exceeding the 5 kJ/mol review threshold. It
remains a qualified correlation estimate; the class B compilation keeps
preference. All earlier
preferred IDs remain, and no Gibbs energy changes. Uncertainty stays NULL:
the original estimated reaction widths and anchor covariance are unavailable.
No Cp, exact space group or additional temperature model is introduced.
Existing ligand-temperature exclusions continue to apply.

## Reuse and verification

This batch carries the project's established individual-original-numerical-facts
route. It adapts two original reaction facts, their explicit sign correction,
and checked open ionic references into separately cited local estimates.
Neither the 1985 article nor the Nagra report is claimed to be open licensed.
Complete publications, tables, prose, figures and database exports remain
outside the repository and distributions. Original erroneous negative signs
are recorded in the external evidence ledger. The NIST open-data notice,
attribution and warranty statement remain applicable to the ionic inputs.
This route is separate from the OECD permission covering NEA-authored data.

Staging preserves every previous SQL row and observation, passes integrity
and foreign-key checks, and is idempotent. Reaction H/S reconstruct the
corrected positive enthalpies and original logK values. All 75 default maps
and nominal uncertainty masks remain unchanged, as do 11 buffered Ra
scenarios. Eighteen supported metal balances and restricted analytical
solubilities/boundaries pass. The fixed 100-value audit and completed source
reviews carry forward.

R11l5 is complete. R11l3 (original 2019 full thermal fit), R11p1–R11p3,
R11m1, R11n1/R11n2 and other permission/scientific holds stay separate.
Historical request coverage remains 116/131 (NEA 28/28, NIST 88/103),
including the same six original crystalline-G gaps.
