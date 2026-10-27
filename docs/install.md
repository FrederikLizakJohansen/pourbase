# Install

pourbase needs Python 3.11 or newer.

```bash
pip install pourbase            # the database, the Python package and the command line
pip install "pourbase[gui]"     # the same, plus the desktop app
pourbase-gui                    # start the app
```

`pourbase gui` also starts the app and prints any errors to the terminal, which is useful on Windows.

## Optional extras

| Extra | Adds |
|---|---|
| `gui` | The desktop app (PySide6) |
| `materials-project` | Comparisons with the official Materials Project diagrams. This needs a free [API key](https://materialsproject.org/api) |
| `mcp` | The MCP server for language-model agents, `pourbase-mcp` |
| `docs` | The tools to build this site (`zensical serve`) |

## From the repository

```bash
git clone https://github.com/FrederikLizakJohansen/pourbase && cd pourbase
pip install -e ".[gui]"
python -m unittest discover -s tests
```
