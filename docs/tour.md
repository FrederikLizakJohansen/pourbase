# Tour

This tour follows iron from the periodic table to the sources behind one of its boundaries. The screenshots are
made with `docs/screens.py` and the bundled database.

## The periodic table

The app opens on a periodic table. Each tile shows the stable species of that element at the pH, potential and
temperature set at the top, here pH 7 and 0 V vs SHE, for a dissolved metal activity of 10⁻⁶. When you hover over
an element, the card at the top of the table shows its stable species, how far below the next species it lies,
and where its Gibbs energy comes from. A dashed outline means that some species of that element were left out
because they have no Gibbs energy.

![The periodic table at pH 7 and 0 V](assets/screens/periodic-table.png#only-light)![The periodic table at pH 7 and 0 V](assets/screens/dark/periodic-table.png#only-dark)

The 3D button turns the table into columns whose height is the stability margin. The Sweep button runs the table
through a range of pH or potential.

![The same table in 3D](assets/screens/periodic-table-3d.png#only-light)![The same table in 3D](assets/screens/dark/periodic-table-3d.png#only-dark)

## The iron diagram

Clicking iron opens its diagram. The settings are on the left. Below the diagram, the probe describes the point
it marks. Here it reports hematite at pH 7 and 0 V, with its Gibbs energy, uncertainty and source. The next
species, FeOOH, is only 1.25 kJ mol⁻¹ higher, which is within the uncertainty of the data. The probe also gives
the distance to the nearest boundaries.

![The iron diagram with a probe at pH 7 and 0 V](assets/screens/fe-diagram.png#only-light)![The iron diagram with a probe at pH 7 and 0 V](assets/screens/dark/fe-diagram.png#only-dark)

The row of chips above the diagram lists what the calculation uses: the element, the model, the data, the
selection policy, the ligands and the number of species left out. Clicking a chip opens that setting.

## The values behind the diagram

The Species tab lists the species of the system with their recommended values and the other published values.
It also gives the reason the policy chose each value.

![Species of the iron system](assets/screens/fe-species.png#only-light)![Species of the iron system](assets/screens/dark/fe-species.png#only-dark)

The Boundaries tab gives each boundary as a balanced reaction and an equation, with the sources used.

![Boundaries of the iron diagram](assets/screens/fe-boundaries.png#only-light)![Boundaries of the iron diagram](assets/screens/dark/fe-boundaries.png#only-dark)

The Sensitivity tab shows where the diagram depends on which published value is used. It draws many selections
of the eligible values and colors each point by how often its stable species changes. For iron, this happens on
about 4 % of the diagram, mostly along the magnetite and hydroxide boundaries above pH 8 and near the Fe³⁺
boundary around pH 2.

![Sensitivity of the iron diagram to alternative values](assets/screens/fe-sensitivity.png#only-light)![Sensitivity of the iron diagram to alternative values](assets/screens/dark/fe-sensitivity.png#only-dark)

## The database and the policy

The Database tab lets you browse the tables of the database. The Selection policy tab shows the rule that chose
the recommended values, as text you can edit. Apply recalculates everything with your version.

![The selection policy tab](assets/screens/selection-policy.png#only-light)![The selection policy tab](assets/screens/dark/selection-policy.png#only-dark)
