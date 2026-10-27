# The app

Start the app with `pourbase-gui`. `pourbase gui Fe` opens it directly on iron and prints any errors to the
terminal.

The window has four tabs. The last two are tinted because they configure the data that the other two use.

| Tab | Shows |
|---|---|
| [Periodic table](periodic-table.md) | The stable species of each element at one pH, potential and temperature |
| [An element](system.md) | One element's diagram, its [settings](settings.md) and its [views](views.md). The tab carries the element's name |
| [Database](database.md) | The tables of the database |
| [Selection policy](policy.md) | The rule that picks the recommended values, as text you can edit |

## General use

The search field at the top right (Ctrl+K, or Tools → Search…) finds elements, species, sources and menu
commands. Picking a species opens its element, and picking a command runs it.

![Searching for hematite](../assets/screens/search.png#only-light)![Searching for hematite](../assets/screens/dark/search.png#only-dark)

Changes to the settings and display options of an element can be undone with Ctrl+Z and redone with
Ctrl+Shift+Z.

The row of chips above an element's diagram says what the result is calculated from: the element, the model, the
data (bundled, your own species or your own dataset), the selection policy, the ligands, the number of species
left out, and any display options that change the picture. Hovering over a chip explains it, and clicking it
opens the setting.

View → Pop out diagram (Ctrl+Shift+D) opens the current diagram in a separate window. That window keeps its result
when you change the main window, so you can put several elements or conditions next to each other. The probes in
the popped-out windows move together. View → Arrange popped-out diagrams lines them up, and View → Close
popped-out diagrams closes them.

You can right-click any figure to export it as an image, export its numbers, pop it out or copy the Python code
that draws it ([Files and export](files.md)). In a diagram, scrolling zooms and dragging pans; View → Reset zoom
(Ctrl+0) returns to the full axes. View → Theme switches between light, dark and the system setting.

The comparison with the Materials Project needs the `materials-project` extra and a free
[API key](https://materialsproject.org/api). Enter the key under Tools → Materials Project API key…. It is kept in
the operating system's credential store if the `keyring` package is installed, and otherwise in the app's
settings file. If no key is stored, the app uses the `MP_API_KEY` environment variable.

## Menus

| Menu | Commands |
|---|---|
| File | Open session…, Save session…; Export figure…, Export grid as CSV…, Copy Python code; Open dataset (CSV or SQLite)…, Load own species (CSV)…, Remove own species; Load selection policy (TOML)…, Use the default selection policy, Edit selection policy…; Quit |
| Edit | Undo, Redo |
| View | Theme; Reset zoom; Pop out diagram, Arrange popped-out diagrams, Close popped-out diagrams |
| Tools | Search…; Sources behind this diagram…; Compare selection policies…; DFT comparison (Materials Project); Materials Project API key… |
| Help | About pourbase |
