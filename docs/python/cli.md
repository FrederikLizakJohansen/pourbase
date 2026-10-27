# Command line and agents

## Command line

`pourbase <command> --help` lists the options of each command.

### `pourbase systems`

Lists the elemental systems with data.

### `pourbase plot`

Writes an experimental Pourbaix diagram as an image, and if asked also its grid as CSV.

```bash
pourbase plot Fe --concentration 10 --unit ppm --output fe.png --grid-csv fe.csv
pourbase plot Zn --mode mass_balance --concentration 1e-6 --unit molar --davies-ionic-strength 0.01 --output zn.png
```

| Option | Default | Sets |
|---|---|---|
| `symbol` | | The element |
| `--mode` | `fixed_activity` | `fixed_activity` or `mass_balance` |
| `--concentration` | `-6` | The metal concentration in `--unit` |
| `--unit` | `log10_molar` | `log10_molar`, `molar`, `ppm` or `wt_percent` |
| `--solution-density` | `1.0` | kg/L, for weight percent |
| `--davies-ionic-strength` | | Davies activity coefficients at this ionic strength (mass balance) |
| `--blend-width` | | Draws soft-minimum weights of this width in kJ/mol (fixed activity) |
| `--output` | `pourbaix.png` | The image. The file extension sets the format (PNG, PDF, SVG) |
| `--grid-csv` | | Also writes the grid points with their stable species |
| `--require-complete` | | Stops if a species has no recommended Gibbs energy, instead of leaving it out |
| `--use-mp-fallbacks` | | Fills missing solid Gibbs energies with the labelled Materials Project 300 K estimates |

### `pourbase sweep`

Writes a concentration sweep. This is a set of fixed-activity diagrams at evenly spaced activities, drawn as
stacked 3D boundaries with two projections through a probe point.

```bash
pourbase sweep Fe --minimum -10 --maximum 0 --points 7 --output fe-sweep.png
```

| Option | Default | Sets |
|---|---|---|
| `--minimum`, `--maximum` | `-10`, `0` | The log₁₀ activity range |
| `--points` | `7` | The number of activity levels |
| `--probe-pH`, `--probe-U` | `7`, `0` | The point the two projections pass through (U in V vs SHE) |
| `--output` | `pourbaix-sweep.png` | The image |
| `--require-complete`, `--use-mp-fallbacks` | | As for `plot` |

### `pourbase gui`

Opens the desktop app, optionally on an element: `pourbase gui Fe`. Errors are printed to the terminal.

### `pourbase mp-thermo-figures`

Compares the experimental formation energies with the stored Materials Project energies and writes the figures,
the data behind them, the metrics for each method and notes on the methods to `--output-dir` (default
`mp-thermochemistry`).

## Agents (MCP)

`pourbase-mcp` is a [Model Context Protocol](https://modelcontextprotocol.io) server. It lets language-model
agents use the database and the calculations. Install the `mcp` extra and register the server with your client,
for example:

```bash
claude mcp add pourbase -- pourbase-mcp
```

| Option | Starts the server on |
|---|---|
| `--dataset PATH` | A pourbase SQLite file or a species CSV used on its own |
| `--species PATH` | A CSV of species added to, or replacing, the bundled data |
| `--policy PATH` | A selection policy (TOML) |

The tools return JSON that includes record IDs, sources, statuses and uncertainties:

| Tool | Arguments | Returns |
|---|---|---|
| `list_systems` | | The elemental systems with data, the dataset version and the reference state |
| `list_ligands` | | The ligands that can be buffered, with the species they form per element |
| `get_species` | `symbol`, `include_ligand_species` | The species of an element with their recommended Gibbs energy, status and source |
| `get_record` | `record_id` | The full evidence record: every reported value, its source, locator and warnings |
| `search_species` | `text`, `limit` | Species whose name, formula or record ID contains the text |
| `calculate_diagram` | `symbol`, `mode`, `concentration`, `concentration_unit`, `ligands`, `ionic_strength_mol_L`, axes | The stable species, their area fractions, the boundary equations, the excluded species and the uncertain share of the diagram |
| `probe_point` | `symbol`, `pH`, `U_V` and the diagram arguments | The stable species, the margin to the runner-up and the nearby boundaries at one point; in the mass-balance model the speciation |
| `render_diagram` | The diagram arguments | The diagram as a PNG image |
| `compare_policy` | `policy_toml`, `symbol` | Every recommended Gibbs energy that a policy (as TOML text) chooses differently from the default |

Each tool is an ordinary method of `pourbase.mcp_server.Tools`, so it can also be called from Python without an
MCP client.
