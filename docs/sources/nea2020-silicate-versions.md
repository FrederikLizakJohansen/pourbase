# NEA 2020 silicon auxiliary versions

R11j3 reconciles the silicon G/H/S rows in two distinct 2020 NEA volumes.
It adds **11 older observations on existing species**, links **19 cells already
retained from the same evaluations**, and preserves every preferred value.
The database now contains 1,453 species and 4,434 reported observations.

## Source versions and numerical scope

Lemire, Palmer, Taylor and Schlenz (2020), *Chemical Thermodynamics of Iron,
Part 2*, Chemical Thermodynamics 13b, NEA No. 7499,
[Table IV-1, p. 67](https://www.oecd-nea.org/upload/docs/application/pdf/2020-03/7499-vol13b-iron.pdf)
(PDF p. 102), carries the earlier [1992GRE/FUG] selected evaluation with its
computerized-reference and rounding conventions. Eleven of its 15 populated
aqueous silicon cells were previously absent. Four cells already represented
that original evaluation and receive source links.

The [second update of U, Np, Pu, Am and Tc](https://www.oecd-nea.org/upload/docs/application/pdf/2020-10/7500_second_update_of_u_np_pu_am_and_tc_web.pdf),
Chemical Thermodynamics 14, NEA No. 7500 (2020), Table 8-1, pp. 156–157
(PDF pp. 220–221), labels its silicon evaluation “Ancillary Data–to be published”.
All 15 populated aqueous G/H/S cells and their quoted uncertainty widths match
the evaluation published in the 2024 ancillary review and retained by R14e2.
They receive links to those observations. Publication in the 2020 volume does
not create 15 independent observations.

| Disposition across the two volumes | G/H/S slots |
| --- | ---: |
| Added older observations | 11 |
| Linked earlier evaluation already retained | 4 |
| Linked forthcoming 2024 evaluation already retained | 15 |
| Own selected rows with an empty property cell | 24 |
| Bold copied CODATA/reference cells, separate source decision | 24 |
| Total silicon slots reviewed | 78 |

The added cells comprise complete G/H/S triplets for H3SiO4− and H4SiO4(aq),
and G for H4Si2O7²−, H5Si2O7−, cyclic H3Si3O9³−, linear H5Si3O10³− and
H5Si4O12³−. H2SiO4²− and H4Si4O12⁴− already retain the earlier values.
Every added observation records the exact row, column, printed/PDF page,
original value/unit, 298.15 K and 1 bar conditions, full formula unit and
approximately 95% source uncertainty convention. G/H are stored in J/mol and
S in J/(mol K). These are older critically evaluated selections; 2020 is the
citing volume's publication year.

## Reuse and model conditions

OECD and the OECD Nuclear Energy Agency are acknowledged. The supplied written
NEA clarification and [OECD data terms](https://www.oecd.org/en/about/terms-conditions.html)
cover these own selected/evaluated data, including commercial adaptation and
redistribution, with appropriate citation and applicable additional restrictions
checked. When sharing or licensing work using these data, include the same OECD
acknowledgment requirement in sublicences and require further sublicensees to
do the same. Both source PDFs were accessed on 25 October 2026.

The admitted aqueous rows are nonbold own NEA selections. Both volumes' bold
Si(cr), Si(g), alpha-quartz and SiF4(g) G/H/S rows retain their separate copied
CODATA/reference decision. All earlier independent source holds continue.

All preferred values, the Miron H3SiO4 G override, free-silicate reference,
ligand/component reference values and selection policy remain unchanged.
Multi-Si formula units and missing H/S remain explicit. Fixed-activity diagrams
support these oligomers; the existing closed-Si solver excludes polynuclear
aqueous species, and the thermal model excludes G-only records. Reaction
functions in Iron Part 2 Table IV-2 and the second update Table 8-2 retain their
source locators outside the scalar G/H/S schema. Their correlated confidence
intervals are not reconstructed from formation-property differences.

## Validation and follow-up

Staging checks preserve every earlier SQL row, prevent duplicate reimports and
verify all selected values. They check 21 older-alternative energies, four
temporary-policy thermal calculations, four Si balances and all 75 default
system diagrams and uncertainty masks. The diagrams and masks remain unchanged.
Other own selected non-silicon 2020 auxiliary candidates continue in R11j3a.
The six original crystalline Gibbs gaps and other sources' permission holds
retain their earlier status.
