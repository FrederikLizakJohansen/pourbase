# R08: NASA thermochemistry and open atomic references

Reviewed 23 October 2026. This batch retains **250 observations**, adds
**116 species**, and fills **198 properties**. Every earlier observation and
preferred value remains. New atomic gases require explicit inclusion and
external fugacities. Charged gases receive entropy only.

## Releases and conventions

The pinned [NASA CEA release](https://github.com/nasa/cea/tree/2f79a647e85737742fb08a127da00d1ea1d069da)
contains 2,099 records. Its Apache-2.0 NOTICE explicitly covers
`data/thermo.inp`. Licence, NOTICE and data were checked against pinned Git
blob hashes. The unmodified licence and NOTICE accompany the distribution.
The legacy Reaktoro JSON groups 2,074 phase labels into 1,658 species; its
version and rights remain separate. No legacy value is imported.

The external `nasa-review.csv` records **11,271 property dispositions** across
both releases. Legacy phase labels are expanded before matching; unique
case-normalized aliases remain distinguishable from exact matches.

[McBride, Zehe and Gordon (2002), NASA TP-2002-211556](https://ntrs.nasa.gov/citations/20020085330),
p. 2, defines ideal gases at 1 bar, condensed species at 1 atm, and assigned
enthalpies. Its gas constant is **8.314510 J/(mol K)**. Assigned `H − TS`
is distinct from formation G, which also requires elemental reference
entropies. Polynomial evaluation is limited to the stated interval.

## Atomic observations

**118 absolute entropies** come directly from original **Table B1 at
298.15 K**: 43 neutral atoms and 75 atomic ions. Every locator retains the
row and printed/PDF page. These original partition-function calculations,
documented in [Gordon and McBride (1999)](https://ntrs.nasa.gov/citations/19990063361),
enter as **class E, `source_verified_estimate`**. Printed precision
0.001 J/(mol K) supplies no uncertainty estimate.

For 42 records the newer fit starts at 300 K. Their admission uses the
explicit original 298.15 K table, independently of that newer interval.
In-range fits reproduce the tabulated entropies within printed precision.
Gas-ion energies and their electron-reference conversion remain held.
The upstream In+ assigned-enthalpy header also conflicts with its fit and
original reference; only verified entropy is admitted.

The explicitly open, non-SRD [NIST PDR M32124 digitization](https://doi.org/10.18434/M32124)
supplies **124** neutral-atom G/H/S observations. Three existing Hg(g)
observations are linked instead of duplicated. Existing NEA Ni(g)/Zr(g)
recommendations remain preferred. New cells retain logical row, column,
units and raw source representation under the carried NIST reuse review.

Digitized Ba(g) and V(g) Gibbs cells fail `Gf = Hf − T ΔfS` checks beyond
rounding and reference differences. Those cells remain external pending
an original-table/erratum check. **Two separate class-E G estimates** use
verified gas H/S and stable-element S from the same open release. Their
input rows and missing total uncertainty are explicit; the rejected cells
are preserved in the hold evidence.

## Nominal Fe0.947O

Open NBS row **5806**, named wustite, has the malformed formula `FeO0.947O`.
Its molar mass **68.8865 g/mol**, the NASA phase label and the original
reaction in [Pankratz (1982), Bulletin 672](https://stacks.cdc.gov/view/cdc/219421),
**pp. 155–156 / PDF pp. 163–164**, independently establish **Fe0.947O**.
The raw label remains in the locator. No exact specimen or space group is
inferred. This composition stays distinct from Fe0.932O and stoichiometric FeO.

The formula has 0.947 Fe and 1 O, with mean oxidation state and electron
coefficient **2/0.947 per Fe**. The original evaluation states instability
below **833 K**; these are metastable 298.15 K properties.

Preferred open NBS values are **G = −245120 J/mol, H = −266270 J/mol,
S = 57.49 J/(mol K)**. Three class-E NASA alternatives retain fitted H/S
and locally derived formation G using explicit open elemental entropies.
The NASA alternatives use a pressure-flat approximation from the original
1 atm convention to 1 bar, with no invented volume correction or total
uncertainty. Independently, the NBS release specifies 1 bar. These
representations share ancestry and are not independent measurements.

## Validation and remaining work

All 75 default maps and 1σ/3σ masks remain. Twelve Fe/Ag/Nb balance scenarios
conserve metal with unchanged dissolved/precipitated inventories. Explicit
gas inclusion is checked separately; ions lacking G remain exclusions.
Wustite G/H thermal use is verified at 323.15 and 373.15 K. No general NASA
temperature model is added. Its decomposition to Fe plus magnetite is
favourable under the current reference values.

JANAF/Chase, TRC, commercial-compilation and uncertain inherited properties
remain held individually. King1973, the Cu(OH)2(cr) source, is an INCRA
commercial monograph; federal affiliations supply no blanket permission.
Other original evaluations, phase/component mappings, reactant-only assigned
quantities and out-of-range fits retain explicit holds. The original six
crystalline-G gaps remain unchanged.

Metadata `R08_NASA_source_review`, `R08_NASA_observations` and
`R08_NASA_source_holds` preserve source hashes, rights, derivations and holds.
Complete publications and full database exports remain external. Existing
NEA OECD credit and downstream acknowledgment obligations remain separate.
