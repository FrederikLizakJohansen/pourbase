"""The views of one system and the database viewer."""

from __future__ import annotations

import html
from contextlib import closing
from typing import Callable

from PySide6.QtCore import QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QColor, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QSizePolicy, QSplitter,
    QTableView, QTableWidget, QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget,
)

from ..database import ThermodynamicDatabase
from ..records import PropertyValue, SourceReference, SpeciesRecord
from ..scenario import Calculation, Probe
from ..uncertainty import StabilityMargin
from ..speciation import speciation_profile
from .formula import formula_delegate, phase_label, to_html
from .placeholder import StackedView
from .plots import DiagramView, DisplayOptions, PhaseStripView, SpeciationView, record_colors
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


def _swatch(color) -> "QIcon":
    from PySide6.QtGui import QIcon, QPixmap

    pixmap = QPixmap(12, 12)
    pixmap.fill(color)
    return QIcon(pixmap)


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
    table.horizontalHeader().setHighlightSections(False)  # Qt draws the selected row's header in bold
    table.verticalHeader().setHighlightSections(False)
    table.setItemDelegateForColumn(0, formula_delegate(table))
    return table


class DiagramPage(StackedView):
    """The diagram, the value under the cursor and the probe panel."""

    probeMoved = Signal(float, float)
    speciesRequested = Signal()

    def _open_link(self, url) -> None:
        if url.scheme() == "pourbase":
            self.speciesRequested.emit()
        else:
            from PySide6.QtGui import QDesktopServices

            QDesktopServices.openUrl(url)

    def __init__(self, parent=None) -> None:
        diagram = DiagramView()
        cursor = QLabel(" ")
        cursor.setTextFormat(Qt.RichText)
        cursor.setFixedHeight(cursor.fontMetrics().height() * 2)
        probe = QTextBrowser()
        probe.setOpenLinks(False)
        probe.anchorClicked.connect(self._open_link)
        from PySide6.QtWidgets import QTabWidget

        from .diagram_tools import PathPanel, PointsPanel

        self.path_panel = PathPanel()
        self.points_panel = PointsPanel()
        self.tools = QTabWidget()
        self.tools.setDocumentMode(True)
        self.tools.addTab(probe, "Probe")
        self.tools.addTab(self.path_panel, "Path")
        self.tools.addTab(self.points_panel, "Measured points")
        self.tools.setMinimumHeight(140)
        # the cursor readout sits on the bottom edge of the diagram, so it takes no height of its own
        cursor.setParent(diagram)
        cursor.setAttribute(Qt.WA_TransparentForMouseEvents)
        cursor.setFixedHeight(cursor.fontMetrics().height() + 4)
        body = QSplitter(Qt.Vertical)
        body.setChildrenCollapsible(False)
        body.addWidget(diagram)
        body.addWidget(self.tools)
        body.setStretchFactor(0, 1)
        body.setSizes([520, 320])
        super().__init__(body, parent)
        self.diagram, self.cursor, self.probe = diagram, cursor, probe
        self.dark = False
        self.display = DisplayOptions()
        self.diagram.cursorMoved.connect(self._show_cursor)
        self.cursor.hide()
        self.diagram.probeMoved.connect(self.probeMoved)
        self.diagram.boundaryClicked.connect(self.show_boundary)
        self.diagram.clickable_boundaries = True
        self.calculation: Calculation | None = None
        self.path_panel.changed.connect(self.update_tools)
        self.path_panel.probeRequested.connect(self.probeMoved)
        self.path_panel.pickRequested.connect(
            lambda: self.diagram.pick_points(self.path_panel.finish_pick, self.path_panel.smooth))
        self.path_panel.pickFinished.connect(self.diagram.finish_pick)
        self.diagram.pathEdited.connect(self.path_panel.set_vertices)
        self.points_panel.changed.connect(self.update_tools)
        self.points_panel.probeRequested.connect(self.probeMoved)

    def _show_cursor(self, text: str) -> None:
        """The value under the mouse, on the bottom-left edge of the plot area."""
        if not text:
            self.cursor.hide()
            return
        if getattr(self, "_cursor_dark", None) != self.dark:  # restyling is slow; only on a theme change
            self._cursor_dark = self.dark
            background = "rgba(30, 32, 36, 210)" if self.dark else "rgba(255, 255, 255, 210)"
            self.cursor.setStyleSheet(f"background: {background}; padding: 1px 6px; border-radius: 3px;")
        self.cursor.setText(text)
        self.cursor.adjustSize()
        area = self.diagram.getPlotItem().vb.sceneBoundingRect()
        corner = self.diagram.mapFromScene(area.bottomLeft())
        self.cursor.move(corner.x() + 4, corner.y() - self.cursor.height() - 4)
        self.cursor.show()
        self.cursor.raise_()

    def update_tools(self) -> None:
        """The path and the measured points for the current calculation, on the diagram and in their panels."""
        from ..measurements import assess_points
        from ..paths import phase_path

        calculation = self.calculation
        if calculation is None:
            return
        diagram = calculation.diagram
        self.path_panel.window_limits = ((float(diagram.pH[0]), float(diagram.pH[-1])),
                                         (float(diagram.eh_V[0]), float(diagram.eh_V[-1])))
        path = self.path_panel.path()
        if getattr(self.diagram, "_pick", None) is None:  # while picking, the diagram draws the path itself
            self.diagram.show_path(path)
        if path is not None:
            stable = [item.record_id for item in diagram.stable_species]
            self.path_panel.show_result(phase_path(calculation, *path[0], smooth=path[1]), stable,
                                        calculation.database)
        assessments = assess_points(calculation, self.points_panel.points)
        self.points_panel.show_assessments(assessments)
        self.diagram.show_points([(item.point.label, item.point.pH, item.point.eh_V, item.within_uncertainty)
                                  for item in assessments if item.inside])

    def show_boundary(self, first: str, second: str, position) -> None:
        """A popup with the reaction, equation and sources of the boundary between two species."""
        from PySide6.QtWidgets import QFrame

        self.hide_boundary()
        calculation = self.calculation
        if calculation is None or not first:
            return
        equation = next((item for item in calculation.boundaries
                         if {item.left_record_id, item.right_record_id} == {first, second}), None)
        names = {item.record_id: item.species for item in calculation.diagram.system.species}
        title = f"{to_html(names.get(first, first))} | {to_html(names.get(second, second))}"
        if equation is None:
            body = ("In the mass-balance model this boundary is a numerical equilibrium that includes the metal "
                    "concentration; it has no single equation.")
        else:
            sources = []
            for source_id in equation.source_ids:
                source = calculation.database.source(source_id)
                citation = source.citation if source else None
                sources.append(html.escape(short_citation(citation, source_id)))
            kind = {"nernst": "Redox boundary (Eq. 3)", "acid_base": "Acid–base boundary (Eq. 4)",
                    "numerical": "Numerical boundary", "degenerate": "No pH or potential dependence"}
            from .diagram_tools import reaction_html

            reaction = reaction_html(equation.reaction, calculation.database)
            body = (f"{reaction}<br>{html.escape(equation.equation).replace('-', '−')}<br>"
                    f"<span style='color:gray'>{kind.get(equation.kind, equation.kind)} · "
                    f"{'; '.join(sources)}</span>")
        # a tool-tip window takes no mouse grab, so the next click reaches the diagram directly
        popup = QFrame(self, Qt.ToolTip | Qt.FramelessWindowHint)
        popup.setFrameShape(QFrame.StyledPanel)
        label = QLabel(f"{title}<br>{body}")
        label.setTextFormat(Qt.RichText)
        label.setWordWrap(True)
        label.setMaximumWidth(460)
        layout = QVBoxLayout(popup)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.addWidget(label)
        popup.adjustSize()
        popup.move(int(position.x()) + 12, int(position.y()) + 12)
        popup.setAttribute(Qt.WA_DeleteOnClose)
        popup.show()
        self.boundary_popup = popup

    def hide_boundary(self) -> None:
        popup = getattr(self, "boundary_popup", None)
        if popup is not None:
            popup.close()
            self.boundary_popup = None

    def hideEvent(self, event) -> None:
        self.hide_boundary()
        super().hideEvent(event)

    def show_calculation(self, calculation: Calculation, display: DisplayOptions, reset_range: bool) -> None:
        self.calculation = calculation
        self.hide_boundary()
        plating = calculation.plating[0].potential_V_vs_SHE if calculation.plating else None
        self.display = display
        self.diagram.show_diagram(calculation.diagram, display, plating, reset_range=reset_range)
        self.update_tools()
        self.show_view()

    def show_probe(self, probe: Probe, record: SpeciesRecord | None, dft_phase: str | None,
                   margin: StabilityMargin | None = None) -> None:
        """The species at the probe: what it is, how firmly it holds, where its value comes from."""
        self.diagram.set_probe(probe.pH, probe.eh_V)
        self.path_panel.set_probe(probe.pH, probe.eh_V)
        species = probe.species
        muted = "#8c8f94" if self.dark else "#6a6f76"
        warn = "#d19a2a" if self.dark else "#9a6400"

        def caption(text: str) -> str:
            return f'<div style="color:{muted}; font-size:8pt; letter-spacing:1px">{text.upper()}</div>'

        def line(text: str, small: bool = False) -> str:
            size = "font-size:8pt; " if small else ""
            return f'<div style="{size}margin-top:1px">{text}</div>'

        scale = self.display.potential_scale
        scaled = (f", {float(to_scale(probe.eh_V, probe.pH, scale)):+.3f} V vs {html.escape(scale)}"
                  if scale != "SHE" else "")
        header = (f'<div style="font-size:13pt">{to_html(species.species, 13)}'
                  f'&nbsp;<span style="color:{muted}; font-size:10pt">{html.escape(phase_label(species))}</span></div>'
                  f'<div style="color:{muted}">Stable at pH {probe.pH:.2f}, Eh {probe.eh_V:+.3f} V vs SHE{scaled}</div>')

        summary = ""
        if margin is not None and margin.runner_up is not None and margin.margin_J_mol_metal is not None:
            sigma = margin.margin_uncertainty_J_mol_metal or 0.0
            gap = margin.margin_J_mol_metal / 1000
            text = (f"Next lowest is {to_html(margin.runner_up.species)}, {gap:.2f}"
                    + (f" ± {sigma / 1000:.2f}" if sigma else "") + " kJ/mol metal higher")
            if sigma and gap * 1000 < sigma:
                text += f'; <span style="color:{warn}">within the uncertainty of the data, so either could be stable here</span>'
            elif sigma and gap * 1000 < 2 * sigma:
                text += ", separated by one to two combined uncertainties"
            elif sigma:
                text += ", clearly separated"
            if margin.runner_up_uses_assumed_uncertainty:
                text += f' <span style="color:{muted}">(assumed uncertainty)</span>'
            summary = f'<div style="margin-top:4px">{text}.</div>'

        gibbs = record.thermochemistry.gibbs_energy_J_mol if record else PropertyValue(None, None, None, None)
        import math

        extrapolation = species.temperature_uncertainty_J_mol
        if extrapolation:
            temperature = self.calculation.scenario.temperature_K - 273.15 if self.calculation else 25.0
            energy = f"ΔfG° at {temperature:g} °C = {kilojoules(species.gibbs_energy_J_mol)} kJ/mol"
            if gibbs.uncertainty is not None:
                energy += f" ± {kilojoules(math.hypot(gibbs.uncertainty, extrapolation))}"
            if gibbs.value is not None:
                energy += f'<br><span style="color:{muted}">extrapolated from {kilojoules(gibbs.value)} kJ/mol at 25 °C</span>'
        else:
            energy = f"ΔfG° = {kilojoules(species.gibbs_energy_J_mol)} kJ/mol"
            if gibbs.uncertainty is not None:
                energy += f" ± {kilojoules(gibbs.uncertainty)}"
        source = gibbs.source
        citation = html.escape((source.citation or source.source_id) if source else "no source")
        if source is not None and source.url:
            citation = f'<a href="{html.escape(source.url)}">{citation}</a>'
        locator = (source.locator or "") if source is not None else ""
        if len(locator) > 140:
            locator = locator[:138].rstrip(" ,;") + "…"
        value_column = (caption("Gibbs energy") + line(energy)
                        + line(f'<span style="color:{muted}">{html.escape(status_label(species.gibbs_status.value))}</span>')
                        + line(citation, small=True)
                        + (line(f'<span style="color:{muted}">{html.escape(locator)}</span>', small=True) if locator else ""))
        if dft_phase:
            value_column += line(f'<span style="color:{muted}">Materials Project: </span>{to_html(dft_phase)}', small=True)
        columns = [f'<td valign="top" width="52%">{value_column}</td>']

        if margin is not None:
            def neighbour(boundary, change: str, unit: str, digits: int) -> str:
                if boundary is None:
                    return f'<span style="color:{muted}">{change}: no change</span>'
                amount = f"{abs(boundary.distance):.{digits}f}" + (f" {unit}" if unit else "")
                return (f'<span style="color:{muted}">{change} by {amount}:</span> '
                        f"{to_html(boundary.species.species)}")
            boundaries = (caption("Nearby boundaries")
                          + line(neighbour(margin.higher_potential, "E up", "V", 3))
                          + line(neighbour(margin.lower_potential, "E down", "V", 3))
                          + line(neighbour(margin.higher_pH, "pH up", "", 2))
                          + line(neighbour(margin.lower_pH, "pH down", "", 2)))
            columns.append(f'<td valign="top" style="padding-left:18px">{boundaries}</td>')
        if probe.dissolved_metal_mol_L is not None:
            inventory = (caption("Metal inventory")
                         + line(f"{probe.dissolved_metal_mol_L:.3g} mol/L dissolved")
                         + line(f"{probe.precipitated_fraction:.1%} precipitated")
                         + "".join(line(f'{to_html(item["species"])} <span style="color:{muted}">'
                                        f'{item["metal_fraction"]:.1%}</span>', small=True)
                                   for item in probe.speciation[:5] if item["metal_fraction"] >= 1e-3))
            columns.append(f'<td valign="top" style="padding-left:18px">{inventory}</td>')

        warnings = record.warnings if record else ()
        notes = ""
        if warnings:
            first = warnings[0].message
            first = first if len(first) <= 120 else first[:118].rstrip(" ,;") + "…"
            count = f"{len(warnings)} notes" if len(warnings) > 1 else "1 note"
            notes = (f'<div style="margin-top:6px; font-size:8pt"><span style="color:{warn}">{count} on this record:</span> '
                     f'{html.escape(first)} <a href="pourbase:species">All details in the Species tab</a></div>')
        footer = f'<div style="color:{muted}; font-size:8pt; margin-top:4px">Record {species.record_id}</div>'
        self.probe.setHtml(
            header + summary
            + f'<table width="100%" cellspacing="0" cellpadding="0" style="margin-top:6px"><tr>{"".join(columns)}</tr></table>'
            + notes + footer
        )


class SpeciesPage(QSplitter):
    """Every species of the system with its full evidence record."""

    COLUMNS = ["Species", "Phase", "Ligand", "ΔfG° (kJ/mol)", "±", "Status", "Class", "Spread (kJ/mol)", "Stable",
               "Warnings", "Record ID"]
    STATUS, SPREAD, STABLE, RECORD = 5, 7, 8, 10
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
        swatches = record_colors([item.record_id for item in calculation.stable_species])
        table = self.table
        selected = table.selectedItems()
        previous = table.item(selected[0].row(), self.RECORD).text() if selected else None
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
                    cell.setForeground(QColor("#b26a00"))
                    cell.setToolTip(f"The eligible values differ by more than the policy's review threshold "
                                    f"({len(selection.candidates)} values)")
                if column == self.STABLE and record_id in swatches:
                    cell.setIcon(_swatch(swatches[record_id]))
                    cell.setToolTip("Color of this species in the diagram")
                if excluded:
                    cell.setForeground(Qt.gray)
                table.setItem(index, column, cell)
        table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        table.setSortingEnabled(True)
        table.resizeColumnsToContents()
        table.setUpdatesEnabled(True)
        table.blockSignals(False)
        self.details.clear()
        # keep the selected species across redraws; a species asked for from search takes precedence
        wanted = getattr(self, "pending_record", None) or previous
        ids = [table.item(index, self.RECORD).text() for index in range(table.rowCount())]
        target = ids.index(wanted) if wanted in ids else 0
        if getattr(self, "pending_record", None) in ids:
            self.pending_record = None
        if rows:
            table.selectRow(target)
            table.scrollToItem(table.item(target, 0))

    def _show_details(self) -> None:
        selected = self.table.selectedItems()
        record = self.records.get(self.table.item(selected[0].row(), self.RECORD).text()) if selected else None
        if record is None:
            return
        parts = [f"<div style='font-size:13pt'>{to_html(record.species, 13)} <small>({html.escape((record.phase_detail or record.phase).strip('()'))})"
                 f"</small></div><code>{record.record_id}</code>"]
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
                         + (", the eligible sources differ by more than the review threshold" if selection.needs_review
                            else "") + "</small>")
                source = next((item.source for item in record.reported if item.source
                               and item.source.source_id == chosen.source_id), value.source)
                parts.append(f"<p>{label}: {text} <i>({html.escape(status_label(chosen.status))})</i>"
                             f"<br>{source_html(source)}{basis}</p>")
                continue
            text = "—" if value.value is None else f"{value.value / divisor:.3f} {unit}"
            parts.append(f"<p>{label}: {text} <i>({html.escape(status_label(value.status))})</i>"
                         f"<br>{source_html(value.source)}</p>")
        if record.fallback:
            fallback = record.fallback
            parts.append(
                f"<p>Materials Project fallback: {html.escape(fallback.canonical_mp_id)}, "
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
            parts.append(f"<p>Phase identity ({html.escape(identity.status)}): {details}</p>")
        if record.warnings:
            parts.append("<p>Notes on this record<ul>"
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

            parts.append("<p>Reported values</p><table border='1' cellspacing='0' cellpadding='3'>"
                         "<tr><td style='color:gray'>Property</td><td style='color:gray'>Value</td><td style='color:gray'>Unit</td><td style='color:gray'>Status</td><td style='color:gray'>Class</td>"
                         f"<td style='color:gray'>Recommended</td><td style='color:gray'>Source</td></tr>{''.join(row(item) for item in record.reported)}</table>")
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
        self.view.horizontalHeader().setHighlightSections(False)
        self.view.verticalHeader().setHighlightSections(False)
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


class SensitivityPage(StackedView):
    """Where the diagram is not fixed by the published data, and which species and sources cause it."""

    sourcesChanged = Signal()

    def __init__(self, parent=None) -> None:
        import pyqtgraph as pg
        from PySide6.QtWidgets import QButtonGroup, QRadioButton

        from .figure_export import install_export_menu

        body = QWidget()
        layout = QVBoxLayout(body)
        controls = QHBoxLayout()
        self.all_values = QRadioButton("All eligible values")
        self.critical = QRadioButton("Critical evaluations only (classes A–C)")
        self.all_values.setChecked(True)
        group = QButtonGroup(body)
        for button in (self.all_values, self.critical):
            group.addButton(button)
            controls.addWidget(button)
            button.toggled.connect(lambda checked: checked and self.sourcesChanged.emit())
        controls.addStretch(1)
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addLayout(controls)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        header_layout.addWidget(self.summary)
        self.point_info = QLabel("Click the diagram to see which species are stable at that point across the "
                                 "selections.")
        self.point_info.setWordWrap(True)
        self.point_info.setTextFormat(Qt.RichText)
        self.point_info.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        header_layout.addWidget(self.point_info)
        header.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(header)
        splitter = QSplitter(Qt.Vertical)
        self.plot = pg.PlotWidget()
        self.plot.setMenuEnabled(False)
        self.plot.setLabel("bottom", "pH")
        self.plot.setLabel("left", "Eh (V vs SHE)")
        self.plot.getPlotItem().layout.setContentsMargins(4, 12, 14, 4)  # room for the edge tick labels
        self.image = pg.ImageItem(axisOrder="row-major")
        self.plot.addItem(self.image)
        self.lines = pg.PlotDataItem(pen=pg.mkPen("#1f6f8b", width=1.2), connect="pairs")
        self.plot.addItem(self.lines)
        self.result = None
        self.diagram = None
        self.selections = None
        self.labels: dict[str, pg.TextItem] = {}
        self.marker = pg.ScatterPlotItem(size=11, symbol="+", pen=pg.mkPen("#1f6f8b", width=2), brush=None)
        self.marker.setZValue(6)
        self.plot.addItem(self.marker)
        self.plot.scene().sigMouseClicked.connect(self._clicked)
        self.plot.scene().sigMouseMoved.connect(self._hovered)
        install_export_menu(self.plot, self.export_table, "pourbase-sensitivity")
        from .plots import apply_plot_theme

        apply_plot_theme(self.plot, False)
        self.table = _table(["Species", "Spread (kJ/mol)", "Diagram changed when replaced alone", "Values (kJ/mol)",
                             "Sources"])
        splitter.addWidget(self.plot)
        splitter.addWidget(self.table)
        splitter.setSizes([520, 220])
        layout.addWidget(splitter, 1)
        super().__init__(body, parent)

    def set_dark(self, dark: bool) -> None:
        from .plots import apply_plot_theme

        apply_plot_theme(self.plot, dark)

    def critical_only(self) -> bool:
        return self.critical.isChecked()

    def _grid_point(self, scene_position):
        import numpy as np

        if self.result is None or not self.plot.sceneBoundingRect().contains(scene_position):
            return None
        point = self.plot.getPlotItem().vb.mapSceneToView(scene_position)
        pH, eh = self.result.pH, self.result.eh_V
        if not (pH[0] <= point.x() <= pH[-1] and eh[0] <= point.y() <= eh[-1]):
            return None
        return int(np.abs(eh - point.y()).argmin()), int(np.abs(pH - point.x()).argmin())

    def _hovered(self, position) -> None:
        cell = self._grid_point(position)
        if cell is None:
            self.plot.setToolTip("")
            return
        row, column = cell
        species = self.diagram.system.species[int(self.diagram.stable_species_index[row, column])]
        self.plot.setToolTip(f"{to_html(species.species)}: another species in "
                             f"{self.result.changed_fraction[row, column]:.0%} of selections")

    def _clicked(self, event) -> None:
        from ..sensitivity import point_outcomes

        if event.button() != Qt.LeftButton or self.selections is None:
            return
        cell = self._grid_point(event.scenePos())
        if cell is None:
            return
        row, column = cell
        pH, eh = float(self.result.pH[column]), float(self.result.eh_V[row])
        self.marker.setData([pH], [eh])
        current = self.diagram.system.species[int(self.diagram.stable_species_index[row, column])].species
        outcomes = point_outcomes(self.diagram, self.selections, row, column, samples=self.result.samples or 1,
                                  classes={"A", "B", "C"} if self.critical_only() else None)
        shares = ", ".join(f"{to_html(name)} {share:.0%}" for name, share in outcomes.items())
        self.point_info.setText(f"pH {pH:.2f}, Eh {eh:+.3f} V: {to_html(current)} is stable in the current "
                                f"diagram. Stable across the selections: {shares}.")
        for index in range(self.table.rowCount()):
            item = self.table.item(index, 0)
            if item is not None and item.text() in outcomes and item.text() != current:
                self.table.selectRow(index)
                break

    def show_result(self, result, diagram, selections=None) -> None:
        import numpy as np
        import pyqtgraph as pg
        from matplotlib import colormaps

        from ..grid import phase_boundary_segments

        self.result = result
        self.diagram = diagram
        self.selections = selections
        self.marker.setData([], [])
        self.point_info.setText("Click the diagram to see which species are stable at that point across the "
                                "selections.")
        lut = (colormaps["magma_r"](np.linspace(0, 1, 256))[:, :3] * 255).astype(np.uint8)
        lut[0] = (245, 245, 245)
        self.image.setImage(result.changed_fraction, lut=lut, levels=(0, 1), autoLevels=False)
        x0, x1, y0, y1 = result.pH[0], result.pH[-1], result.eh_V[0], result.eh_V[-1]
        self.image.setRect(pg.QtCore.QRectF(x0, y0, x1 - x0, y1 - y0))
        points = [point for segment in phase_boundary_segments(diagram.stable_species_index, diagram.pH, diagram.eh_V)
                  for point in segment]
        array = np.asarray(points) if points else np.zeros((0, 2))
        self.lines.setData(array[:, 0], array[:, 1]) if len(array) else self.lines.setData([], [])
        self.plot.setXRange(x0, x1, padding=0)
        self.plot.setYRange(y0, y1, padding=0)
        self._place_labels(diagram)
        sources = "critical evaluations" if self.critical_only() else "all eligible published values"
        if result.samples == 0:
            self.summary.setText(f"No species of this system has more than one eligible Gibbs energy among the "
                                 f"{sources}; the diagram is fixed by the data in the database.")
        else:
            self.summary.setText(
                f"The stable species depends on which published value is used on {result.unfixed_fraction:.1%} of the "
                f"diagram ({result.samples} random selections from {sources}). Darker regions change in more "
                "selections; lines are the boundaries of the current diagram. Right-click to export.")
        rows = result.species
        self.table.setRowCount(len(rows))
        for index, entry in enumerate(rows):
            values = ", ".join(f"{item.value_J_mol / 1000:.2f}" + (" (in use)" if item.in_use else "")
                               for item in sorted(entry.alternatives, key=lambda item: item.value_J_mol))
            sources = "; ".join(dict.fromkeys(short_citation(item.citation, item.source_id) + f" [{item.evidence_class}]"
                                              for item in entry.alternatives))
            cells = (entry.species, f"{entry.spread_J_mol / 1000:.2f}", f"{entry.changed_fraction_alone:.1%}",
                     values, sources)
            for column, value in enumerate(cells):
                cell = QTableWidgetItem(value)
                if column == 4:
                    cell.setToolTip("\n".join(dict.fromkeys(item.citation for item in entry.alternatives)))
                self.table.setItem(index, column, cell)
        self.table.resizeColumnsToContents()
        self.show_view()

    def _place_labels(self, diagram) -> None:
        import numpy as np
        import pyqtgraph as pg

        from .plots import LABEL_PT

        index = diagram.stable_species_index
        x_grid, y_grid = np.meshgrid(diagram.pH, diagram.eh_V)
        scale_x, scale_y = max(float(np.ptp(diagram.pH)), 1e-9), max(float(np.ptp(diagram.eh_V)), 1e-9)
        shown = set()
        for position, item in enumerate(diagram.system.species):
            mask = index == position
            if not mask.any():
                continue
            xs, ys = x_grid[mask], y_grid[mask]
            distances = ((xs - xs.mean()) / scale_x) ** 2 + ((ys - ys.mean()) / scale_y) ** 2
            nearest = int(np.argmin(distances))
            label = self.labels.get(item.record_id)
            if label is None:
                label = pg.TextItem(html=f'<span style="color:#000; font-size:{LABEL_PT}pt">'
                                         f"{to_html(item.species, LABEL_PT)}</span>",
                                    anchor=(0.5, 0.5), fill=pg.mkBrush(255, 255, 255, 185))
                label.setZValue(5)
                self.plot.addItem(label)
                self.labels[item.record_id] = label
            label.setPos(float(xs[nearest]), float(ys[nearest]))
            label.setVisible(True)
            shown.add(item.record_id)
        for record_id, label in self.labels.items():
            label.setVisible(record_id in shown)

    def export_table(self):
        result = self.result
        if result is None:
            return None
        rows = [(f"{pH:.6g}", f"{eh:.6g}", f"{result.changed_fraction[row, column]:.4f}")
                for row, eh in enumerate(result.eh_V) for column, pH in enumerate(result.pH)]
        return ("pH", "Eh_V_vs_SHE", "share of selections with another stable species"), rows
