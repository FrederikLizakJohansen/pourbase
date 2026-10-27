# How values are selected

The database keeps all the published values we found for each species and property. When the database is
opened, a selection policy picks one of them as the recommended value, and calculations use that value. Values
are never averaged. When no value could be found, the gap is recorded and shown.

## Evidence and statuses

By evidence we mean the reported values in the database. Each one is a published value of ΔfG°, ΔfH° or S° for
a species, stored with its source, the place in the source, any reported uncertainty and a status.

| Status | Meaning |
|---|---|
| verified | Checked against the stated location in the cited source |
| source-verified estimate | A published estimate, correlation or derived value; its basis was checked against the source |
| accepted | A formation enthalpy taken from a compilation without the same level of checking |
| defined reference state | A value fixed by convention, such as ΔfG° = 0 for an element in its standard state |
| superseded source value | Replaced by a later edition or erratum of the same source; kept, but never selected |
| terminal evidence gap | A search that found no defensible value for that species and property |

The policy never selects superseded values, gap records or values it lists as exclusions. The others are
eligible. A recommended value has the status of the record it came from. When a species has no eligible value
for a property, that property is a terminal evidence gap if a search was documented, and not available
otherwise.

## The default policy

The default policy is the file `selection-policy.toml` in the package. It ranks sources by class, best first:

| Class | Sources |
|---|---|
| A | International critical reviews (NEA-TDB) |
| B | Critical compilations and internally consistent datasets (NBS Tables, NBS Technical Notes, NIST-JANAF, Robie & Hemingway, Miron) |
| C | Critical evaluations of one element or system (IUPAC standard potentials, US Bureau of Mines) |
| D | Single peer-reviewed experimental papers |
| E | Estimates, then predictive correlations (Shock and Sverjensky) |
| F | Computed values (Materials Project), used only on request |

Within a class, the source families rank in the order listed. If two values still tie, the policy prefers, in
this order, consistency with the sources already chosen for the same element, the original publication over a
later copy, a value with a stated uncertainty, and the more recent value.

A source belongs to a family when the family's pattern appears in its citation. A source that matches no pattern
counts as an estimate if its value is an estimate, and as an experimental paper otherwise.

Species whose eligible values differ by more than 5 kJ mol⁻¹ are flagged for review. The flag does not change
which value is chosen. The policy also lists overrides and exclusions for single records, each with a reason.

## Using your own rule

You can edit the policy in the app's [Selection policy](../app/policy.md) tab, or load your own copy in Python
([Policies and own data](../python/data.md)).
