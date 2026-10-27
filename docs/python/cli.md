# Command line and agents

## Command line

```bash
pourbase systems
pourbase plot Fe --concentration 10 --unit ppm --output fe.png --grid-csv fe.csv
pourbase plot Zn --mode mass_balance --total-metal 1e-6 --output zn.png
pourbase sweep Fe --minimum -10 --maximum 0 --points 7 --output fe-sweep.png
pourbase gui
```

`pourbase <command> --help` lists every option.

## Agents (MCP)

`pourbase-mcp` is a [Model Context Protocol](https://modelcontextprotocol.io) server that gives language-model
agents the database and the engine (install the `mcp` extra):

```bash
claude mcp add pourbase -- pourbase-mcp
```

| Tool | Returns |
|---|---|
| `list_systems`, `list_ligands` | The elemental systems and the buffered ligands |
| `get_species`, `get_record`, `search_species` | Species, their recommended values and full evidence records |
| `calculate_diagram`, `render_diagram` | A diagram as data or as an image |
| `probe_point` | The stable species, margin and nearby boundaries at one point |
| `compare_policy` | The values an alternative policy changes |

`--dataset`, `--species` and `--policy` start the server on your own data or policy.
