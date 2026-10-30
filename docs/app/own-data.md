# Your own data

You can calculate with your own formation energies in two ways. File → Load own species (CSV)… adds species to the
bundled data or replaces bundled ones, and File → Remove own species goes back to the bundled data. File → Open
dataset (CSV or SQLite)… opens a new window that uses only your species, or another pourbase SQLite file.

Your values keep their citations and are marked *user supplied* in all results. The context bar shows which data
are in use, and the path of a loaded species file is saved with the session.

This is also how you can use values from compilations that pourbase cannot distribute (see
[Compilations not included](../excluded-compilations.md)) on your own computer.

## The CSV format

The file has one species per row:

| Column | Content |
|---|---|
| `symbol` | The element symbol, for example `Cu` |
| `species` | The name shown in diagrams and tables; defaults to the formula |
| `formula` | The metal–oxygen–hydrogen core, for example `Cu2O` or `Fe(OH)3` |
| `charge` | The charge, which is only nonzero for dissolved species; defaults to zero |
| `phase` | `aqueous`, `solid`, `liquid` or `gas` |
| `formation_energy_kJ_mol` | ΔfG° at 298.15 K and 1 bar |
| `uncertainty_kJ_mol` | The standard uncertainty (optional) |
| `citation` | The source of the value; recommended, defaults to `user supplied` |
| `replaces` | The record ID of a bundled species to replace (optional) |

```csv
symbol,species,formula,charge,phase,formation_energy_kJ_mol,uncertainty_kJ_mol,citation,replaces
Fe,Fe(OH)2 (fresh),Fe(OH)2,0,solid,-486.5,2.0,My lab notebook p. 12,
Cu,Cu+,Cu,1,aqueous,49.98,,Example et al. 2024,gfe-cu-cu-q+1-aqueous-aq
```

A formula may only contain the element, oxygen and hydrogen, so ligand complexes cannot be added this way. The
proton and electron coefficients follow from the formula and the charge, in the same way as for the bundled
species. `symbol`, `formula`, `phase` and the formation energy are required. The legacy column
`gibbs_energy_kJ_mol` is also accepted; if both energy columns are filled, they must agree.
In a file added to the bundled data, a row without `replaces` adds a new species; record IDs
are shown in the Species view and by Search. `replaces` is ignored for a standalone dataset.
