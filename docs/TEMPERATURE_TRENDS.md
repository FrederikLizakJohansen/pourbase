# Temperature-dependent trends

## What can be supported now

The database has recommended Gibbs formation energies for 262 of 268 species and
formation enthalpies for 130 species. Both values are present for 129 species. No
single-metal system currently has paired Gibbs energy and enthalpy for every
calculation-ready species.

For a species with both values at the reference temperature `T0 = 298.15 K`, a
transparent first-order estimate is:

```text
Delta S_f(T0) = [Delta H_f(T0) - Delta G_f(T0)] / T0
Delta G_f(T) = Delta H_f(T0) - T Delta S_f(T0)
```

This is the constant-enthalpy, constant-entropy model. It is equivalent to setting
the heat-capacity change `Delta Cp` to zero. It can show the direction and rough
size of a temperature trend over a modest range.

## Proposed first implementation

The first temperature feature should be a clearly labelled trend tool for
individual species and reactions. Every result should report:

- the target and reference temperatures;
- the Gibbs and enthalpy source IDs used;
- the derived formation entropy;
- the exact equation above;
- the species included and excluded;
- the label `exploratory_linear_temperature_trend`.

A temperature-adjusted Pourbaix diagram needs the same model for every competing
species and for liquid water. It also needs temperature-aware water stability,
`Kw`, activity coefficients, and phase-transition checks. The present coverage is
too sparse for a complete system diagram. An explicit incomplete-data mode could
plot preliminary trends once the water reference is added, with all omitted
species listed beside the result.

## Route to quantitative diagrams

1. Add source-backed formation enthalpy for water and fill paired enthalpy gaps for
   each target system.
2. Add heat-capacity functions or tabulated values and integrate `Delta Cp(T)`.
3. Add temperature-dependent water properties, `Kw`, and activity models.
4. Record phase-transition ranges and select the stable polymorph at each
   temperature.
5. Validate against published temperature-dependent Pourbaix diagrams.

The linear model remains useful as an inspectable sensitivity analysis. The
heat-capacity model becomes the quantitative path once its inputs are available.
