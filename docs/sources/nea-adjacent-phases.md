# Adjacent NEA phases: nickel gas/liquid and stannane

NEA02f reviews and admits all nine selected G/H/S cells in three source
rows. Nine observations and three species are added. All earlier observations
and preferred IDs are preserved under the unchanged selection policy. The
two new gases require explicit selection for a gas-fugacity calculation.

## Source values and admission

All quantities refer to 298.15 K and 1 bar, per complete formula unit.
G and H below are in kJ/mol; S is in J/(mol K). Published total uncertainty
intervals retain their source interpretation, corresponding in principle to
95% confidence. They are not converted to one-standard-deviation widths.

| Species | G | H | S | Admitted to reported thermochemistry |
| --- | --- | --- | --- | --- |
| Ni(g) | 384.686 ±8.400 | 430.100 ±8.400 | 182.190 ±0.080 | G, H, S; gas requires explicit selection |
| Ni(l) | 14.035 ±0.272 | 17.500 ±0.250 | 41.490 ±0.300 | G, H, S |
| SnH₄(g) | 188.065 ±2.183 | 162.800 ±2.100 | 227.800 ±2.000 | G, H, S; gas requires explicit selection |

Nickel values are from Gamsjäger et al. (2005), *Chemical Thermodynamics of
Nickel*, OECD Nuclear Energy Agency volume 6, Table III-1, printed p.44
(PDF p.72), with sections V.1.1, pp.75–76, and V.1.3, pp.78–79.
[Official source](https://www.oecd-nea.org/dbtdb/pubs/vol6-nickel.pdf).
The retained nickel errata concern other heat-capacity and interaction
entries; they leave these G/H/S selections unchanged.

Stannane values are from Gamsjäger et al. (2012), *Chemical Thermodynamics of
Tin*, OECD Nuclear Energy Agency volume 12, Table III-1, printed p.44
(PDF p.80), with section VII.3.1, pp.134–136.
[Official source](https://www.oecd.org/content/dam/oecd/en/publications/reports/2012/12/chemical-thermodynamics-of-tin-volume-12_g1g39522/9789264992061-en.pdf).
The selected table gives more digits than the chapter's rounded G. These
represent one evaluation; the rounded discussion supplies no independent
alternative observation.

The existing cleared NEA source IDs and permission metadata cover the new
observations. The source-specific reviews and private permission evidence
are carried forward. No additional restriction was identified for these
selected evaluations. Upstream citations remain scientific provenance;
independently copied third-party tables keep their own terms.

## Phase and reaction conventions

Ni(l) is a hypothetical supercooled pure-liquid standard state at 298.15 K.
The source derives it using fusion enthalpies and solid/liquid thermal
functions; nickel melts near 1728 K. It has its own species identity and
unit liquid activity. The crystalline nickel reference retains G = H = 0.
Source-calculated G and extrapolated liquid properties are critical-review
values, with their derivation stated in each locator. They supply no new
room-temperature liquid measurement or melting-kinetics model.

SnH₄ is a neutral molecular gas. Formal Sn(IV) and the signed electron
coefficient are distinct: with the metal/water basis, Sn +4H⁺ +4e⁻ → SnH₄,
so the stored proton and electron coefficients are both −4. One full formula
contains one Sn and four H. Ni(g) has zero charge, proton coefficient and
electron coefficient. Gas fugacity would enter relative to 1 bar.

Independent reconstruction of the three source G values from H, S and the
source reference entropies agrees within 0.5 J/mol, consistent with table
rounding. Their shared source covariance is unavailable.

## Explicit gas selection and calculation effects

All nine G/H/S values are stored and selected as thermochemical evidence.
The two gases carry a documented `optional_gas_phase` scope annotation in
`warnings`. The default loader reports their exclusion as
`optional_gas_not_selected`; their Gibbs energies remain available through
the evidence API and selected-value table. This preserves existing default
Ni/Sn calculations, closed balances and strict periodic-screen completeness.
Earlier gas records keep their established inclusion rules.

Use `include_optional_gases=True` to include these phases in an explicitly
loaded system, then calculate with the chosen fugacity:

```python
import pourbase as pb

database = pb.ThermodynamicDatabase.bundled()
system = database.load_system("Sn", include_optional_gases=True)
conditions = pb.PourbaixConditions(
    gas_fugacities=pb.GasFugacityModel(
        overrides={"nea02f-sn-stannane-gas": -3}))
diagram = pb.PourbaixEngine(database).calculate_system(system, conditions)
```

Scope is part of the loader cache key, including temperature, policy and
user-species views. The option selects phases; the policy still selects one
preferred value for every available property. Application GUI files remain
unchanged. The closed-balance solver continues to reject an explicitly
gas-containing system because its model has no gas/headspace inventory.
The default closed-balance API continues to work for Ni and Sn.

With gas inclusion selected at unit fugacity, the sampled tin map changes at
1,495 of 7,371 points and the nickel map stays unchanged. All changed tin
points lie below the water-stability window. Direct gas-fugacity checks
verify the signed hydride reaction and the per-decade RT ln(10) energy shift.

For the admitted batch, all 74 sampled default stability maps and uncertainty
masks are unchanged. The added liquid lowers the nickel runner-up energy gap
at 2,340 of 7,371 points, so sensitivity margins can change even where the
stable phase is preserved. Eight ideal/Davies nickel/tin balances conserve
metal and reproduce the earlier inventories. The liquid remains above
crystalline nickel throughout the checked 0–100 °C range; nickel maps agree
at four temperatures. An aligned pymatgen comparison also agrees.

Current totals are **966 species /3,084 observations /74 systems**, with
selected G/S/H counts **853/774/651**. The batch fills nine properties and
changes no earlier preferred IDs. Original request coverage remains
**116/131** (NEA28/28, NIST88/103); the six original crystalline G gaps remain
open. The earlier source/model holds stay separately tracked.

The external `nea02f-adjacent-phases/` checkpoint retains all nine source
cells, exact per-property locators, source hashes, the nine-observation
stage/import package, explicit gas-selection checks and the two-phase scope
ledger. Heat-capacity-only work remains with R18, including the source's
stannane Cp uncertainty discrepancy between Table III-1 and the chapter.

OECD and the Nuclear Energy Agency are acknowledged using the associated
review citations. Every sublicense of work using these data must include the
same OECD acknowledgment requirement and require further sublicensees to
pass it on. See [the admission instructions](nea-tdb-reuse.md) and
[distributed notices](https://github.com/FrederikLizakJohansen/pourbase/blob/main/THIRD_PARTY_NOTICES.md).
