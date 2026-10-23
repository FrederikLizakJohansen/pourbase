# Alkaline niobium: supplemental hexaniobate models

R11u, reviewed 23 October 2026, adds **four Gibbs-energy observations, four
aqueous species and four newly available properties** at 298.15 K and 1 bar.
Every earlier observation and preferred value remains. The added species
retain six niobium atoms per formula unit.

## Original evidence and reuse

[Hummel and Thoenen (2023), *The PSI Chemical Thermodynamic Database 2020*,
Nagra Technical Report 21-03](https://media.nagra.ch/uploads/2023/05/NTB-21-03.pdf),
**section 17.4.2.2, printed p. 667 / PDF p. 725**, presents the authors'
original SIT regressions and approximate monomer-to-polymer extrapolation.
The original page was inspected directly. The selected-condition table,
printed p. 687 / PDF p. 745, corroborates the evaluation's 298.15 K, 1 bar
basis and supplemental status.

The established **individual original numerical-facts route** carries forward
from R11g/R11h/R11j/R11l. Four individually cited author model results are
adapted into local formation-energy estimates. The report retains Nagra's
copyright; this route supplies no open licence for the publication or its
database export. Complete publications, tables, prose, figures and OCR stay
external. Existing NEA OECD attribution and downstream acknowledgment
requirements remain separate.

The Filella–May 2020 article and supplement carry **CC BY-NC-ND 4.0**.
Their evaluated dataset and JESS output are excluded from these additions.
The new estimates use the independently reviewed PSI authors' own analyses,
the already retained original Peiffert neutral observation and openly
released non-SRD NBS water. Their individual reuse reviews remain applicable.

## Derivation and species identity

The PSI authors evaluate the reaction

`6 Nb(OH)5(aq) = H3Nb6O19(5−) + 5 H+ + 11 H2O(l)`

with **log K° = −20.6**, estimated width **±0.8**. This is an approximate SIT
extrapolation of a reinterpretation of older precipitate-solubility data.
It supplies a weak absolute link between the monomer and polymer families.
Their cumulative protonation fits for `Nb6O19(8−) + h H+` give **14.0, 27.0
and 38.6**, with quoted widths **0.4, 0.4 and 0.5**, for h = 1, 2 and 3.

The pinned neutral observation is **HNbO3 G = −949742 J/mol**, equivalent to
**Nb(OH)5 G = −1424000 J/mol** after adding two waters. Open NBS water,
logical record 41, supplies **−237129 J/mol**. Thus:

`G(H3Nb6O19) = 6 G(Nb(OH)5) − 11 G(water) − RT ln(10) log Kcond`.

The cumulative protonation constants connect the other three cluster values.
They are cumulative constants, so the stepwise protonation constants are
**14.0, 13.0 and 11.6**.

| Species | Charge | G / kJ mol−1 of full formula |
|---|---:|---:|
| Nb6O19 | −8 | −5597.667 |
| HNb6O19 | −7 | −5677.579 |
| H2Nb6O19 | −6 | −5751.783 |
| H3Nb6O19 | −5 | −5817.996 |

Each record has six Nb, nineteen O and the displayed number of H atoms.
Nb remains in oxidation state V. The electron coefficient is 5 per Nb and
the proton coefficient is `(38 − h)/6` per Nb. Stored energies use the full
formula; the calculation engine performs its existing per-metal normalization.
No free sodium or potassium reservoir is part of these four aqueous species.

## Qualifications and calculation scope

All four observations are **class E, `source_verified_estimate`**. They share
the weak monomer–polymer link and the neutral model's oxide reference and
[phase-label qualification](niobium-standard-state.md#r11t-phase-identity-follow-up).
The original legacy solubility measurements were at 18–20 °C; the authors'
assigned 298.15 K evaluation and concentration-scale approximations remain
explicit model limitations. Their condensation extrapolation neglects
interaction and water-activity terms. No additional temperature, pressure or
medium correction is invented.

The source reaction widths and the neutral model's 8000 J/mol interval are
retained in each recipe. Covariances and systematic approximation errors are
unavailable, so **total formation-energy uncertainty remains NULL**. The
default plotting interval is an assumed interval, distinct from propagated
uncertainty for this shared model. No H, S, Cp or new thermal model is added.

Fixed-activity diagrams can use the full clusters. The existing mass-balance
solver moves polynuclear aqueous species to explicit exclusions; its closed
mononuclear inventory remains intact. These additions establish neither a
closed Nb/Na/K balance nor a validated all-pH alkaline-solubility model.

## Secondary solids and remaining work

The original [Deblonde et al. (2015) solubility study](https://doi.org/10.1016/j.hydromet.2015.05.015)
and the PSI discussion, printed pp. 679–680, identify the hydrated sodium
hexaniobate secondary phase. Its reported solubility product is conditional
on variable finite ionic strength; it is held outside standard-state
formation thermochemistry. Its hydration, activity and ion-pair treatment
remain separate from the four aqueous models.

- [x] Verify original PSI supplemental results, full formulas and scoped reuse.
- [x] Stage four G estimates and preserve all earlier alternatives and preferences.
- [x] Check cumulative/stepwise reactions and existing polynuclear exclusions.
- [ ] **R11u1:** Independently validate the absolute monomer–polymer link,
  temperature/medium treatment and covariance.
- [ ] **R11u2:** Establish a reusable, compatible standard-state sodium-salt
  evaluation before adding solid G.
- [ ] **R11u3:** Verify further polymers and alkali ion pairs with compatible
  formulas and source conditions.
- [ ] **R11u4:** A general polynuclear inventory solver and secondary-solid
  model are needed for broader closed alkaline balances.

Strict R11n2 remains open for those broader requirements. R11n1's independent
B-oxide reference requirement and all earlier source-permission holds remain.

Metadata `R11u_alkaline_niobium_review`, `R11u_hexaniobate_observations` and
`R11u_alkaline_niobium_holds` retain the original inputs, pinned observation
IDs, derivations, source hashes, reuse basis and remaining requirements.
