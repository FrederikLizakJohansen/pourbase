"""The views of one system and the database viewer."""

from __future__ import annotations

import html
from contextlib import closing
from typing import Callable

from PySide6.QtCore import QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QColor, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QSplitter,
    QTableView, QTableWidget, QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget,
)

from ..database import ThermodynamicDatabase
from ..records import PropertyValue, SourceReference, SpeciesRecord
from ..scenario import Calculation, Probe
from ..uncertainty import StabilityMargin
from ..speciation import speciation_profile
from .formula import formula_delegate, phase_label, to_html
from .placeholder import StackedView
from .plots import DiagramView, DisplayOptions, PhaseStripView, SpeciationView
from .scales import to_scale

PUBLIC_TABLES = (
    "species", "selected_thermochemistry", "reported_thermochemistry", "sources", "phases", "warnings",
    "computational_fallbacks", "element_coverage", "materials_project_matches",
    "materials_project_energies", "ligands", "metadata",
)


STATUS_LABELS = {
    "verified": "verified",
    "source_verified_estimate": "published estimate",
    "defined_reference_state": "reference state",
    "not_available": "not available",
    "terminal_evidence_gap": "evidence gap",
    "materials_project_sisso_300K_fallback": "MP 300 K estimate",
    "user_supplied": "user supplied",
    "accepted": "accepted",
    "superseded_source_value": "superseded",
    "recommended_gibbs_energy_unavailable": "omitted: no Gibbs energy",
    "ligand_species_not_selected": "omitted: ligand not selected",
    "ligand_reference_unavailable": "omitted: no ligand reference",
    "mass_balance_nonmonometal_aqueous_unsupported": "omitted: polynuclear (mass balance)",
}


def status_label(status: str | None) -> str:
    return STATUS_LABELS.get(status or "", (status or "not available").replace("_", " "))


def hold_label(status: str, record: SpeciesRecord) -> str:
    """The status of a species row, naming a held Gibbs energy where the record documents one."""
    if status == "recommended_gibbs_energy_unavailable" and any(
            "formation_hold" in item.type for item in record.warnings):
        return "omitted: Gibbs energy held (inherited source)"
    return status_label(status)


def short_citation(citation: str | None, source_id: str) -> str:
    """``Robie (1995)`` from a full citation, or the source ID when there is none."""
    if not citation:
        return source_id
    import re

    surname = re.split(r"[,;.(]", citation.strip())[0].split()[0] if citation.strip() else source_id
    years = re.findall(r"\b(1[89]\d\d|20\d\d)\b", citation)
    return f"{surname} ({years[0]})" if years else surname


def kilojoules(value: float | None) -> str:
    return "" if value is None else f"{value / 1000:.2f}"


def source_html(source: SourceReference | None) -> str:
    if source is None:
        return "<i>no source</i>"
    citation = html.escape(source.citation or source.source_id)
    if source.url:
        citation = f'<a href="{html.escape(source.url)}">{citation}</a>'
    locator = f"<br><small>Locator: {html.escape(source.locator)}</small>" if source.locator else ""
    return citation + locator


def _table(columns: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    table.setItemDelegateForColumn(0, formula_delegate(table))
    return table


class DiagramPage(StackedView):
    """The diagram, the value under the cursor and the probe panel."""

    probeMoved = Signal(float, float)

    def __init__(self, parent=None) -> None:
        diagram = DiagramView()
        cursor = QLabel(" ")
        cursor.setTextFormat(Qt.RichText)
        cursor.setFixedHeight(cursor.fontMetrics().height() * 2)
        probe = QTextBrowser()
        probe.setOpenExternalLinks(True)
        probe.setFixedHeight(200)
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(diagram, 1)
        layout.addWidget(cursor)
        layout.addWidget(probe)
        super().__init__(body, parent)
        self.diagram, self.cursor, self.probe = diagram, cursor, probe
        self.dark = False
        self.display = DisplayOptions()
        self.diagram.cursorMoved.connect(lambda text: self.cursor.setText(text or " "))
        self.diagram.probeMoved.connect(self.probeMoved)

    def show_calculation(self, calculation: Calculation, display: DisplayOptions, reset_range: bool) -> None:
        plating = calculation.plating[0].potential_V_vs_SHE if calculation.plating else None
        self.display = display
        self.diagram.show_diagram(calculation.diagram, display, plating, reset_range=reset_range)
        self.show_view()

    def show_probe(self, probe: Probe, record: SpeciesRecord | None, dft_phase: str | None,
                   margin: StabilityMargin | None = None) -> None:
        self.diagram.set_probe(probe.pH, probe.eh_V)
        species = probe.species
        muted = "#8c8f94" if self.dark else "#6a6f76"

        def row(label: str, value: str) -> str:
            return (f'<tr><td style="color:{muted}; padding-right:10px" valign="top">{label}</td>'
                    f"<td>{value}</td></tr>")

        gibbs = record.thermochemistry.gibbs_energy_J_mol if record else PropertyValue(None, None, None, None)
        energy = f"{kilojoules(species.gibbs_energy_J_mol)} kJ/mol"
        if gibbs.uncertainty is not None:
            energy += f" ± {kilojoules(gibbs.uncertainty)}"
        rows = [
            row("ΔfG°", energy),
            row("Status", html.escape(species.gibbs_status.value.replace("_", " "))),
            row("Source", source_html(gibbs.source)),
            row("Record", f"<code>{species.record_id}</code>"),
        ]
        if dft_phase:
            rows.append(row("DFT (MP)", to_html(dft_phase)))
        columns = [f'<td valign="top" width="58%"><b>Thermochemistry</b><table cellspacing="0" cellpadding="1">'
                   f'{"".join(rows)}</table></td>']
        if probe.dissolved_metal_mol_L is not None:
            inventory = [
                row("Dissolved", f"{probe.dissolved_metal_mol_L:.3g} mol/L"),
                row("Precipitated", f"{probe.precipitated_fraction:.1%} of the metal"),
            ] + [
                row(to_html(item["species"]), f"{item['metal_fraction']:.1%}")
                for item in probe.speciation[:6] if item["metal_fraction"] >= 1e-3
            ]
            columns.append(f'<td valign="top" style="padding-left:18px"><b>Metal inventory</b>'
                           f'<table cellspacing="0" cellpadding="1">{"".join(inventory)}</table></td>')
        if margin is not None:
            columns.append(f'<td valign="top" style="padding-left:18px"><b>Stability</b>'
                           f'<table cellspacing="0" cellpadding="1">{self._stability_rows(margin, row)}</table></td>')
        warnings = "".join(
            f'<div style="color:#c77700">⚠ {html.escape(item.message)}</div>' for item in (record.warnings if record else ())
        )
        scale = self.display.potential_scale
        scaled = (f" ({float(to_scale(probe.eh_V, probe.pH, scale)):+.3f} V vs {html.escape(scale)})"
                  if scale != "SHE" else "")
        self.probe.setHtml(
            f'<span style="font-size:12pt"><b>{to_html(species.species, 12)}</b></span>'
            f"&nbsp; {html.escape(phase_label(species))}&nbsp;&nbsp;"
            f'<span style="color:{muted}">at pH {probe.pH:.2f}, Eh {probe.eh_V:+.3f} V vs SHE{scaled}</span>'
            f'<table width="100%" cellspacing="0" cellpadding="0" style="margin-top:4px">'
            f"<tr>{''.join(columns)}</tr></table>{warnings}"
        )

    def _stability_rows(self, margin: StabilityMargin, row: Callable[[str, str], str]) -> str:
        rows = []
        if margin.runner_up is not None and margin.margin_J_mol_metal is not None:
            sigma = margin.margin_uncertainty_J_mol_metal or 0.0
            text = (f"{to_html(margin.runner_up.species)} {margin.margin_J_mol_metal / 1000:.2f} "
                    f"± {sigma / 1000:.2f} kJ/mol metal higher")
            if margin.runner_up_uses_assumed_uncertainty:
                text += " <small>(assumed σ)</small>"
            rows.append(row("Runner-up", text))
            if sigma > 0:
                ratio = margin.margin_J_mol_metal / sigma
                verdict = "distinct" if ratio >= 2 else "distinct within 1σ" if ratio >= 1 else "not distinguishable"
                rows.append(row("Verdict", f"{verdict} ({ratio:.1f}σ)"))

        def neighbour(boundary, unit: str, digits: int) -> str:
            if boundary is None:
                return "no change"
            return f"{to_html(boundary.species.species)} at {boundary.distance:+.{digits}f} {unit}"

        rows.append(row("Higher E", neighbour(margin.higher_potential, "V", 3)))
        rows.append(row("Lower E", neighbour(margin.lower_potential, "V", 3)))
        rows.append(row("Higher pH", neighbour(margin.higher_pH, "pH", 2) + " <small>at this Eh</small>"))
        rows.append(row("Lower pH", neighbour(margin.lower_pH, "pH", 2) + " <small>at this Eh</small>"))
        return "".join(rows)


class SpeciesPage(QSplitter):
    """Every species of the system with its full evidence record."""

    COLUMNS = ["Species", "Phase", "Ligand", "ΔfG° (kJ/mol)", "±", "Status", "Class", "Spread (kJ/mol)", "Stable",
               "Warnings", "Record ID"]
    STATUS, SPREAD, RECORD = 5, 7, 10
    PROPERTIES = (("Gibbs energy of formation", "gibbs_energy_of_formation", "gibbs_energy_J_mol", "kJ/mol", 1000),
                  ("Formation enthalpy", "enthalpy_of_formation", "formation_enthalpy_J_mol", "kJ/mol", 1000),
                  ("Absolute entropy", "absolute_entropy", "entropy_J_mol_K", "J/(mol K)", 1))

    def __init__(self, parent=None) -> None:
        super().__init__(Qt.Vertical, parent)
        self.table = _table(self.COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.itemSelectionChanged.connect(self._show_details)
        self.details = QTextBrowser()
        self.details.setOpenExternalLinks(True)
        self.addWidget(self.table)
        self.addWidget(self.details)
        self.setSizes([450, 350])
        self.records: dict[str, SpeciesRecord] = {}
        self.selections: dict = {}
        self.policy_name = ""

    def clear(self) -> None:
        self.table.setRowCount(0)
        self.details.clear()
        self.records = {}

    def show_calculation(self, calculation: Calculation, records: dict[str, SpeciesRecord],
                         selections: dict | None = None, policy_name: str = "") -> None:
        """``selections`` maps ``(record_id, property)`` to the active policy's :class:`Selection`."""
        self.records = records
        self.selections, self.policy_name = selections or {}, policy_name
        system = calculation.diagram.system
        stable = {item.record_id for item in calculation.stable_species}
        database = calculation.database
        ligand_of = {row["record_id"]: row["ligand_id"] for row in database._rows(
            "SELECT record_id, ligand_id FROM species WHERE symbol = ?", (system.symbol,))}
        ligand_names = {item.ligand_id: item.name for item in database.available_ligands()}
        rows = [(item.record_id, item.gibbs_energy_J_mol, item.gibbs_status.value, False) for item in system.species]
        rows += [(item.record_id, None, item.reason.value, True) for item in system.excluded]

        def order(row) -> tuple:
            record_id, _energy, status, excluded = row
            ligand = ligand_of.get(record_id)
            if not excluded:
                group = 0 if ligand is None else 1
            else:
                group = 3 if status == "ligand_species_not_selected" else 2
            return (group, ligand_names.get(ligand, ""), record_id not in stable, records[record_id].species)

        rows = [row for row in rows if row[0] in records]
        rows.sort(key=order)
        table = self.table
        table.blockSignals(True)
        table.setUpdatesEnabled(False)
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # measure once at the end, not per cell
        table.clearSelection()
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))
        for index, (record_id, energy, status, excluded) in enumerate(rows):
            record = records[record_id]
            gibbs = record.thermochemistry.gibbs_energy_J_mol
            selection = self.selections.get((record_id, "gibbs_energy_of_formation"))
            spread = selection.spread_J_mol if selection and len(selection.candidates) > 1 else None
            flagged = bool(selection and selection.needs_review)
            ligand = ligand_of.get(record_id)
            values = [
                record.species, record.phase_detail or record.phase, ligand_names.get(ligand, ligand or ""),
                kilojoules(energy if energy is not None else gibbs.value), kilojoules(gibbs.uncertainty),
                hold_label(status, record), selection.chosen.evidence_class if selection else "",
                kilojoules(spread) if spread is not None else "",
                "yes" if record_id in stable else "", str(len(record.warnings)), record_id,
            ]
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column in (3, self.SPREAD) and value:
                    cell.setData(Qt.EditRole, float(value))
                if column == self.SPREAD and flagged:
                    font = cell.font()
                    font.setBold(True)
                    cell.setFont(font)
                    cell.setForeground(QColor("#b26a00"))
                    cell.setToolTip(f"The eligible values differ by more than the policy's review threshold "
                                    f"({len(selection.candidates)} values)")
                if excluded:
                    cell.setForeground(Qt.gray)
                table.setItem(index, column, cell)
        table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        table.setSortingEnabled(True)
        table.resizeColumnsToContents()
        table.setUpdatesEnabled(True)
        table.blockSignals(False)
        self.details.clear()
        if rows:
            table.selectRow(0)

    def _show_details(self) -> None:
        selected = self.table.selectedItems()
        record = self.records.get(self.table.item(selected[0].row(), self.RECORD).text()) if selected else None
        if record is None:
            return
        parts = [f"<h3>{to_html(record.species, 13)} <small>({html.escape((record.phase_detail or record.phase).strip('()'))})"
                 f"</small></h3><code>{record.record_id}</code>"]
        thermo = record.thermochemistry
        for label, property_name, attribute, unit, divisor in self.PROPERTIES:
            value = getattr(thermo, attribute)
            selection = self.selections.get((record.record_id, property_name))
            if selection is not None:
                chosen = selection.chosen
                text = f"{chosen.value / divisor:.3f} {unit}"
                origin = ("" if chosen.family in selection.basis
                          else f" (class {html.escape(chosen.evidence_class)}, {html.escape(chosen.family)})")
                basis = (f"<br><small>Selected by {html.escape(self.policy_name)}: {html.escape(selection.basis)}"
                         f"{origin}"
                         + (", <b>sources disagree by more than the review threshold</b>" if selection.needs_review
                            else "") + "</small>")
                source = next((item.source for item in record.reported if item.source
                               and item.source.source_id == chosen.source_id), value.source)
                parts.append(f"<p><b>{label}:</b> {text} <i>({html.escape(status_label(chosen.status))})</i>"
                             f"<br>{source_html(source)}{basis}</p>")
                continue
            text = "—" if value.value is None else f"{value.value / divisor:.3f} {unit}"
            parts.append(f"<p><b>{label}:</b> {text} <i>({html.escape(status_label(value.status))})</i>"
                         f"<br>{source_html(value.source)}</p>")
        if record.fallback:
            fallback = record.fallback
            parts.append(
                f"<p><b>Materials Project fallback:</b> {html.escape(fallback.canonical_mp_id)}, "
                f"{fallback.gibbs_energy_J_mol / 1000:.2f} kJ/mol at {fallback.temperature_K:g} K "
                f"({html.escape(fallback.model)}), {html.escape(fallback.mapping_confidence)} mapping "
                f"confidence. {html.escape(fallback.notes or '')}</p>"
            )
        if record.phase_identity:
            identity = record.phase_identity
            details = ", ".join(html.escape(str(value)) for value in (
                identity.identified_phase or identity.possible_phases, identity.spacegroup_symbol,
                identity.evidence_summary,
            ) if value)
            parts.append(f"<p><b>Phase identity</b> ({html.escape(identity.status)}): {details}</p>")
        if record.warnings:
            parts.append("<p><b>Warnings</b><ul>"
                         + "".join(f"<li>{html.escape(item.message)}</li>" for item in record.warnings) + "</ul></p>")
        if record.reported:
            candidates = {candidate.value_id: candidate for (record_id, _property), selection in self.selections.items()
                          if record_id == record.record_id for candidate in selection.candidates}
            chosen = {selection.chosen.value_id for (record_id, _property), selection in self.selections.items()
                      if record_id == record.record_id}

            def row(item) -> str:
                candidate = candidates.get(item.value_id)
                recommended = item.value_id in chosen if self.selections else item.selected_as_recommended
                origin = (f"{candidate.evidence_class}, {html.escape(candidate.family)}" if candidate
                          else "<i>not eligible</i>")
                return (f"<tr><td>{html.escape(item.property)}</td><td>{item.value}</td><td>{html.escape(item.unit)}</td>"
                        f"<td>{html.escape(status_label(item.status))}</td><td>{origin}</td><td>{'✓' if recommended else ''}</td>"
                        f"<td>{html.escape(item.source.citation or '') if item.source else ''}</td></tr>")

            parts.append("<p><b>Reported values</b></p><table border='1' cellspacing='0' cellpadding='3'>"
                         "<tr><th>Property</th><th>Value</th><th>Unit</th><th>Status</th><th>Class</th>"
                         f"<th>Recommended</th><th>Source</th></tr>{''.join(row(item) for item in record.reported)}</table>")
        self.details.setHtml("".join(parts))


class BoundariesPage(StackedView):
    def __init__(self, parent=None) -> None:
        table = _table(["Reaction", "Equation", "Kind", "Sources of the Gibbs energies"])
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.addWidget(QLabel("Balanced reactions and activity-conditioned Nernst equations for adjacent domains."))
        layout.addWidget(table, 1)
        super().__init__(body, parent)
        self.table = table

    def show_calculation(self, calculation: Calculation) -> None:
        rows = calculation.boundaries
        kinds = {"nernst": "redox", "acid_base": "acid–base", "numerical": "numerical", "degenerate": "degenerate"}
        self.table.setUpdatesEnabled(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setRowCount(len(rows))
        for index, item in enumerate(rows):
            sources = [calculation.database.source(source_id) for source_id in item.source_ids]
            short = ", ".join(dict.fromkeys(short_citation(source.citation if source else None, source_id)
                                            for source, source_id in zip(sources, item.source_ids)))
            full = "\n".join((source.citation or source_id) if source else source_id
                              for source, source_id in zip(sources, item.source_ids))
            for column, value in enumerate((item.reaction, item.equation, kinds.get(item.kind, item.kind), short)):
                cell = QTableWidgetItem(value)
                if column == 3:
                    cell.setToolTip(full)
                self.table.setItem(index, column, cell)
        self.table.resizeColumnsToContents()
        self.table.setUpdatesEnabled(True)
        self.show_view()


class SpeciationPage(StackedView):
    """Metal fractions along pH, and the predominant species of each dataset."""

    def __init__(self, parent=None) -> None:
        profile, strip, note, button = SpeciationView(), PhaseStripView(), QLabel(), QPushButton()
        note.setWordWrap(True)
        row = QHBoxLayout()
        row.addWidget(note, 1)
        row.addWidget(button)
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.addWidget(QLabel("Metal fractions along pH at the probe potential, from the closed total-metal solver."))
        layout.addWidget(profile, 1)
        layout.addWidget(QLabel("Predominant species along pH at the probe potential"))
        layout.addWidget(strip)
        layout.addLayout(row)
        super().__init__(body, parent)
        self.profile, self.strip, self.note, self.button = profile, strip, note, button
        self._action: Callable[[], None] | None = None
        button.clicked.connect(lambda: self._action and self._action())

    def show_calculation(self, calculation: Calculation, eh_V: float, rows: list, note: str,
                         action: tuple[str, Callable[[], None]] | None) -> None:
        diagram = calculation.diagram
        self.profile.show_profile(speciation_profile(diagram, eh_V))
        self.strip.show_rows(diagram.pH, rows)
        self.note.setText(note)
        self.button.setVisible(action is not None)
        if action is not None:
            self.button.setText(action[0])
            self._action = action[1]
        self.show_view()

    def set_dark(self, dark: bool) -> None:
        self.profile.set_dark(dark)
        self.strip.set_dark(dark)


class DatabasePage(QWidget):
    """Every public table, with filtering and sorting."""

    def set_database(self, database: ThermodynamicDatabase) -> None:
        """Show ``database``, for example after a selection policy or own species were loaded."""
        self.database = database
        self._loaded = None
        self.load()

    def __init__(self, database: ThermodynamicDatabase, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.tables = QComboBox()
        self.tables.addItems(PUBLIC_TABLES)
        self.tables.currentIndexChanged.connect(lambda _index: self.load())
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter rows…")
        self.filter.setClearButtonEnabled(True)
        self.model = QStandardItemModel(self)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterKeyColumn(-1)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.filter.textChanged.connect(self._filter)
        self.view = QTableView()
        self.view.setModel(self.proxy)
        self.view.setSortingEnabled(True)
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.count = QLabel()
        self.note = QLabel("Derived when the database is opened: the recommended value of every species and "
                           "property under the active selection policy. The file itself stores only the "
                           "reported values.")
        self.note.setWordWrap(True)
        self.note.hide()
        row = QHBoxLayout()
        row.addWidget(QLabel("Table"))
        row.addWidget(self.tables)
        row.addWidget(self.filter, 1)
        row.addWidget(self.count)
        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addWidget(self.note)
        layout.addWidget(self.view, 1)
        self._loaded: str | None = None

    def load(self) -> None:
        name = self.tables.currentText()
        if name == self._loaded:
            return
        self.note.setVisible(name == "selected_thermochemistry")
        with closing(self.database.connect()) as connection:
            cursor = connection.execute(f'SELECT * FROM "{name}"')
            columns = [item[0] for item in cursor.description]
            rows = cursor.fetchall()
        self.model.clear()
        self.model.setHorizontalHeaderLabels(columns)
        for values in rows:
            items = []
            for value in values:
                item = QStandardItem("" if value is None else str(value))
                if isinstance(value, (int, float)):
                    item.setData(value, Qt.EditRole)
                items.append(item)
            self.model.appendRow(items)
        self.view.resizeColumnsToContents()
        for column in range(len(columns)):
            self.view.setColumnWidth(column, min(self.view.columnWidth(column), 360))
        self._loaded = name
        self._filter(self.filter.text())

    def _filter(self, text: str) -> None:
        self.proxy.setFilterFixedString(text)
        self.count.setText(f"{self.proxy.rowCount()} of {self.model.rowCount()} rows")
