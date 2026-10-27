# Your own data

File → Load own species (CSV) adds species to the bundled data or replaces bundled ones, and File → Open dataset
calculates with your species alone, in a new window. Your values keep their citations and are marked *user
supplied* in every result. Both are saved in sessions.

The CSV has one species per row:

| Column | Content |
|---|---|
| `symbol` | Element symbol, e.g. `Cu` |
| `species` | Name shown in diagrams and tables |
| `formula` | Metal–oxygen–hydrogen core, e.g. `Cu2O` or `Fe(OH)3` |
| `charge` | Charge; nonzero only for aqueous species |
| `phase` | `aqueous`, `solid`, `liquid` or `gas` |
| `gibbs_energy_kJ_mol` | ΔfG° at 298.15 K and 1 bar |
| `uncertainty_kJ_mol` | Standard uncertainty; optional |
| `citation` | The source of the value |
| `replaces` | A bundled record ID to replace; optional |

Values from compilations that pourbase cannot distribute (see [Compilations not included](../excluded-compilations.md))
can be used this way on your own computer.
