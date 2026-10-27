# NEA iron silicates and nickel ferrite

Nine observations add two species and four missing properties. The finite
main-table inventory contains eight G/H/S cells: six are added, one links to
existing evidence, and the chromite entropy remains external pending a suitable
chromium reference. Three own body recalculations are retained as alternatives.
All earlier evidence remains.

## Sources and values

Fayalite G/H come from Lemire et al. (2013), *Chemical Thermodynamics of Iron,
Part 1*, NEA No. 6355, Table III-1, printed p. 47/PDF p. 89, with the critical
review on pp. 376–380. These same values reappear in the 2020 main table.
The [original book](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/6355-vol13a-iron.pdf)
has SHA-256 `920e6915ee23eadcc0d01c1c0391906bb2851b57c0de4dca059a286d5ccefa57`.
The entropy 151.0 ± 0.2 is the accepted Robie1982 calorimetric result already
held through USGS1995; it links to that observation.

The other selections are from Lemire, Palmer, Taylor and Schlenz (2020),
*Chemical Thermodynamics of Iron, Part 2*, NEA No. 7499, Table III-1, printed
p. 49/PDF p. 84. Its [official PDF](https://www.oecd-nea.org/upload/docs/application/pdf/2020-03/7499-vol13b-iron.pdf)
has SHA-256 `933c3b599997364d7dc1753a79d6457bfa20115826f04180e16153149c5978d1`.
Both books were accessed on 27 October 2026.

G and H below are kJ/mol; S is J/(mol K), at 298.15 K and 1 bar. Database G/H
use J/mol. Quoted source intervals and full formula units are retained.

| Phase | G | H | S |
|---|---:|---:|---:|
| α-Fe2SiO4, fayalite | −1377.720 ± 1.076 | −1476.790 ± 1.070 | 151.0 ± 0.2, existing link |
| γ-Fe2SiO4, metastable spinel | — | — | 140.2 ± 0.8 |
| NiFe2O4, trevorite | −962.271 ± 3.044 | −1070.900 ± 2.800 | 130 ± 4, qualified estimate |

The new fayalite G/H assessment becomes preferred under the source policy.
Earlier USGS values, −1379.1 and −1478.2, remain alternatives. The NEA evaluation
reanalyses calorimetric, gas-equilibrium and electrochemical results. Further
per-study NEA2013 enthalpy recalculations have a separate finite follow-up.

The gamma phase is the distinct high-pressure spinel form, metastable at 1 bar.
Its entropy follows the NEA2020 reassessment of Yong2007 heat-pulse calorimetry,
with the source's expanded interval of 0.8. The original quoted study interval
was 0.4. NEA's own polynomial re-integration gives 140.1 without a separate
interval; that related alternative is also retained. The gamma record is S-only.

Nickel ferrite's own NEA-adjusted calorimetric H values, −1066.9 ± 4.9 and
−1072.7 ± 3.3, are retained alongside the combined final assessment. A precise
policy override prefers the final H used with the source's published G/S.
The related inputs share NiO/hematite anchors. Their source intervals do not
establish independent replication.

The nickel ferrite entropy includes an uncertain cation configurational
contribution beyond measured calorimetry. It is marked `source_verified_estimate`.
The source discusses preparation dependence and possible ordering; the record
preserves those qualifications and leaves the exact specimen space group and
site occupancy unassigned. Its published G retains that source-qualified S ancestry.

## Components and calculations

The new `nickel-ni2` buffered reference reuses the already reviewed NEA2005
Ni2+ observation, G = −45773 ± 771 J/mol, from Gamsjäger et al., *Chemical
Thermodynamics of Nickel*, Table III-1, printed p. 44/PDF p. 72. Its original
observation and reuse review remain. The reference table has no uncertainty
column; the source interval, observation ID and standard state are preserved in
`metadata.R16d6f_NEA_iron_silicate_ferrite.reference_review`.

For trevorite the component balance is two Fe, one Ni2+ and four core oxygens.
Its formal and balanced net Fe coefficient is 3, and its proton coefficient is
4 per Fe. Set a free Ni2+ activity to include it in a buffered iron diagram.
Current mass balances conserve Fe while Ni stays externally buffered. A joint
closed Fe/Ni inventory remains a separate model scope.

Both Fe2SiO4 phases use the existing aqueous silica component: one SiO2
component, two core oxygens and two Fe. Formal and net Fe coefficients are 2.
This component represents H4SiO4 minus two waters at unit water activity;
the source's quartz equilibrium is a different reaction. The 31 earlier fixed
references remain unchanged, and the Ni2+ reference brings the total to 32.
Buffered-component thermal calculations keep the existing model limits.

## Reuse and the chromite follow-up

The newly retained values are NEA's own selected/evaluated outputs and
recalculations. The [recorded OECD clarification](nea-tdb-reuse.md), attribution
and source-specific terms apply. When sharing or licensing work made using
these data, include the same acknowledgment requirement in every sublicense
and require further sublicensees to do the same. The distributed notices carry
this requirement. Completed email, terms and source reviews are preserved.

Chromite S = 152.2 ± 3.0 is an eligible own NEA selection. It remains outside
the release pending an openly reusable chromium reference for its component
balance. The current selected Cr3+ value cites IUPAC1985, whose rights have not
been reviewed for this new use. The open NBS1982 table has no bare Cr3+ G cell.
An independently sourced open anchor or another reviewed representation is
needed. This model/reference follow-up is separate from NEA reuse permission.
Cp-only silicate and mixed-amphibole cells remain in the R18 thermal inventory.
