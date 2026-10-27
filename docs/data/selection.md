# How values are selected

The database keeps every published value of every species and property. A selection policy decides at runtime
which one is recommended and used in calculations. Values are never averaged, and missing values stay visible
as evidence gaps.

## Evidence

By *evidence* we mean the reported values in the database: each published value of ΔfG°, ΔfH° or S° for a
species, stored with its source, its location in that source, any reported uncertainty and a status:

| Status | Meaning |
|---|---|
| verified | Checked against the cited source |
| accepted | Taken from a compilation without a separate check |
| source-verified estimate | A published correlation or estimate, checked against its source |
| defined reference state | Zero by convention |
| superseded source value | Replaced by a later edition or erratum; kept, never selected |
| terminal evidence gap | No usable value exists |

## The default policy

The default policy, `selection-policy.toml`, ranks sources by class, best first:

| Class | Sources |
|---|---|
| A | International critical reviews (NEA-TDB) |
| B | Critical compilations and internally consistent datasets (NBS Tables, NBS Technical Notes, NIST-JANAF, Robie & Hemingway, Miron) |
| C | Critical evaluations of one element or system (IUPAC standard potentials, US Bureau of Mines) |
| D | Single peer-reviewed experimental papers |
| E | Estimates, then predictive correlations (Shock and Sverjensky) |
| F | Computed values (Materials Project), used only on request |

Inside a class, families rank in the order listed. Ties are broken by consistency with the sources chosen for
the same element, then the original publication over a later repeat, then a stated uncertainty, then recency.
Species whose eligible values differ by more than 5 kJ mol⁻¹ are flagged for review; the flag does not change
the choice. Overrides and exclusions handle single records, each with its reason.

A source joins a family when the family's pattern occurs in its citation; a source matching no pattern counts as
an estimate if its value is an estimate, otherwise as an experimental paper.

## Your own rule

Edit the policy in the app's [Selection policy](../app/policy.md) tab, or load a copy from Python
([Policies and own data](../python/data.md)).
