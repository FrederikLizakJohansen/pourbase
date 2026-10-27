# Install

pourbase needs Python 3.11 or later.

```bash
pip install pourbase            # database, Python API and command line
pip install "pourbase[gui]"     # plus the desktop app
pourbase-gui                    # the app (or: pourbase gui, which prints errors to the terminal)
```

## Optional extras

| Extra | Adds |
|---|---|
| `gui` | The desktop app (PySide6) |
| `materials-project` | Comparisons with the official Materials Project diagrams; needs a free [API key](https://materialsproject.org/api) |
| `mcp` | The MCP server for language-model agents: `pourbase-mcp` |
| `docs` | This site: `zensical serve` |

## From the repository

```bash
git clone https://github.com/FrederikLizakJohansen/pourbase && cd pourbase
pip install -e ".[gui]"
python -m unittest discover -s tests
```
