# Selected V2O5 and magnesium pyrovanadate observations

R11j3d adds nine observations: six selected NEA V2O5/Mg2V2O7 G/H/S values
and three independent original open NBS alternatives for Mg2V2O7. It adds one
crystalline species, fills three properties and defines a fixed free-Mg reference
from an eligible observation already retained. Three earlier V2O5 preferred
values change under the existing policy; every earlier alternative remains.

## Selected data and source conventions

Grenthe et al. (2020), *Second Update on the Chemical Thermodynamics of U, Np,
Pu, Am and Tc*, Chemical Thermodynamics 14, OECD Nuclear Energy Agency,
NEA No. 7500,
[Table 14-1, p. 605](https://www.oecd-nea.org/upload/docs/application/pdf/2020-10/7500_second_update_of_u_np_pu_am_and_tc_web.pdf)
(PDF p. 669), explicitly selects these values. Chapter 14.1, pp. 602–603 and
Appendix A, p. 1204 describe their evaluation and numerical ancestry.

| Species | Selected NEA G, kJ/mol | Selected NEA H, kJ/mol | Selected NEA S, J/(mol K) |
| --- | ---: | ---: | ---: |
| V2O5(cr) | −1424.840 ±3.010 | −1556.000 ±3.000 | 130.300 ±0.200 |
| Mg2V2O7(cr) | −2650.170 ±3.240 | −2841.000 ±3.210 | 200.410 ±1.260 |

All values refer to 298.15 K and 1 bar, per complete two-V formula unit.
Mg2V2O7 also contains two Mg atoms. Stored G/H use J/mol and S uses J/(mol K).
Quoted NEA total uncertainty widths retain their approximately 95% source meaning.

For V2O5, NEA discusses the 1961 Mah/Kelley and 1989 Lavut/Chelovskaya
calorimetry and explicitly accepts the IVTAN recommended H/S evaluation.
Its formation G is recalculated. The record preserves this adopted-selection
meaning and IVTAN ancestry. Source p. 603 prints a positive formation-entropy
magnitude of 439.92 J/(mol K). The selected absolute S and source V/O reference
entropies imply −439.915 J/(mol K), reproducing the selected G within 1 J/mol.
This sign qualification accompanies the original G/H/absolute-S observations;
no separate formation-entropy observation is introduced.

For Mg2V2O7, NEA recalculates H from the 1962 King/Koehler reaction calorimetry
and its selected reference inputs: 2(−601.6) −1556.0 −81.80 = −2841.00 kJ/mol.
Selected S comes from the 1962 Weller/King low-temperature calorimetry.
Original reference inputs remain documented numerical ancestry for NEA's outputs.

Independent NBS Mg2V2O7 values are G −2645.18 kJ/mol, H −2835.92 kJ/mol
and S 200.4 J/(mol K), retained with NULL uncertainty. Exact locators are
logical CSV record 9168, columns 9/8/11, in the corrected
[open non-SRD release M32124](https://doi.org/10.18434/M32124).
Its generic crystalline identity remains unresolved at the exact structure level.
The earlier V2O5 phase metadata remains.

## Free magnesium reference and reuse

The new `magnesium-mg2` reference uses −455703 J/mol from the retained eligible
NEA 2024 Mg2+ G observation, with its exact value/source ID and original locator
recorded in metadata. This defines a fixed chemical potential for independently
prescribed free-Mg activity. It creates no new reported observation. The source's
786 J/mol total uncertainty is retained in metadata. The current fixed-buffer
model treats that reference as fixed; it does not propagate reference uncertainty.
All 30 earlier references retain their values and source identities.

OECD and NEA are acknowledged. The supplied written NEA clarification and
[OECD data terms](https://www.oecd.org/en/about/terms-conditions.html) cover the
selected/evaluated NEA outputs, including commercial adaptation and redistribution,
with citation and applicable additional restrictions checked. When sharing or
licensing work using these data, include the same OECD acknowledgment requirement
in sublicences and require further sublicensees to do the same. The retained
NEA 2024 magnesium observation carries its completed source-specific review and
these downstream conditions.

NIST is acknowledged for the three independent original NBS cells under its
[open licence](https://www.nist.gov/open/license); data are distributed without
warranty. Sources were accessed on 25 October 2026. Directly copied Glushko,
CODATA and other independent source holds retain separate decisions.

## Validation and remaining auxiliary scope

Staging preserves all earlier SQL rows, phase metadata, other preferred values
and all 30 earlier references. It verifies 21 energies, two oxide thermal
calculations with paired ligand exclusions, three magnesium-buffer diagrams
and 12 supported primary-V balances. Complete two-V/two-Mg atom counts and five
electrons per V remain explicit. All 75 default maps and 1σ/3σ masks, and the
three tested buffered maps, retain their earlier stable labels. The existing
thermal model excludes Mg2V2O7 because it contains a buffered component.
Closed magnesium inventories, reference uncertainty propagation and ligand thermal
functions remain separate model work.

All **14 own selected scalar G/H/S cells in Table 14-1** are now retained:
four through R11j3a, four through R11j3c and six through R11j3d. Informational
cells, selected Cp/functions and copied compilation rows retain their separate
source/model decisions. Borate and other auxiliary entries continue in R11j3e.
R06/R07, the original six crystalline Gibbs gaps and all earlier independent
source/model holds retain their status.
