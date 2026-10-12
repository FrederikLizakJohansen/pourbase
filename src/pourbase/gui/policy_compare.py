"""Compare the recommendations of two selection policies."""

from __future__ import annotations

import csv
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from ..database import ThermodynamicDatabase
from ..selection import PROPERTIES, SelectionPolicy, compare_policies
from .formula import formula_delegate

UNITS = {"gibbs_energy_of_formation": ("ΔfG°", "kJ/mol", 1000.0),
         "enthalpy_of_formation": ("ΔfH°", "kJ/mol", 1000.0),
         "absolute_entropy": ("S°", "J/(mol K)", 1.0)}
COLUMNS = ["Species", "Element", "Property", "Default", "Default source", "Policy", "Policy source", "Difference",
           "Reason"]


class PolicyComparisonDialog(QDialog):
    """Every recommended value that a policy chooses differently from the default policy."""

    def __init__(self, database: ThermodynamicDatabase, policy: SelectionPolicy | None = None,
                 policy_path: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Compare selection policies")
        self.resize(1100, 600)
        self.database = database
        self.rows: list[list[str]] = []
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        choose = QPushButton("Policy file…")
        choose.clicked.connect(self.choose)
        self.export = QPushButton("Export CSV…")
        self.export.clicked.connect(self.export_csv)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.setItemDelegateForColumn(0, formula_delegate(self.table))
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        buttons = QHBoxLayout()
        buttons.addWidget(choose)
        buttons.addStretch(1)
        buttons.addWidget(self.export)
        buttons.addWidget(close)
        layout = QVBoxLayout(self)
        layout.addWidget(self.summary)
        layout.addWidget(self.table, 1)
        layout.addLayout(buttons)
        if policy is not None and policy_path:
            self.compare(policy, Path(policy_path).name)
        else:
            self.summary.setText("Choose a selection policy (TOML) to compare its recommendations with the "
                                 "default policy.")
            self.export.setEnabled(False)

    def choose(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Selection policy", "", "TOML (*.toml);;All files (*)")
        if not path:
            return
        try:
            policy = SelectionPolicy.load(path)
        except (OSError, ValueError, KeyError) as error:
            QMessageBox.warning(self, "Selection policy", str(error))
            return
        self.compare(policy, Path(path).name)

    def compare(self, policy: SelectionPolicy, label: str) -> None:
        default = SelectionPolicy.default()
        changes = compare_policies(self.database, default, policy, PROPERTIES)
        names = {row["record_id"]: (row["species"], row["symbol"])
                 for row in self.database._rows("SELECT record_id, species, symbol FROM species")}
        self.rows = []
        for change in changes:
            symbol, unit, scale = UNITS[change.property_name]
            species, element = names.get(change.record_id, (change.record_id, ""))
            self.rows.append([
                species, element, f"{symbol} ({unit})", f"{change.first.value / scale:.2f}",
                change.first.citation, f"{change.second.value / scale:.2f}", change.second.citation,
                f"{change.difference_J_mol / scale:+.2f}", change.second_basis,
            ])
        counts = {name: sum(change.property_name == name for change in changes) for name in UNITS}
        self.summary.setText(
            f"<b>{label}</b> ({policy.name}, {policy.fingerprint}) against the default policy "
            f"({default.fingerprint}): {len(changes)} recommended values change — "
            f"{counts['gibbs_energy_of_formation']} Gibbs energies, {counts['enthalpy_of_formation']} enthalpies, "
            f"{counts['absolute_entropy']} entropies. The evidence is the same; only the choice differs.")
        table = self.table
        table.setSortingEnabled(False)
        table.setRowCount(len(self.rows))
        for index, values in enumerate(self.rows):
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column in (3, 5, 7):
                    cell.setData(Qt.EditRole, float(value))
                if column in (4, 6):
                    cell.setToolTip(value)
                table.setItem(index, column, cell)
        table.setSortingEnabled(True)
        table.resizeColumnsToContents()
        for column in (4, 6):
            table.setColumnWidth(column, min(table.columnWidth(column), 260))
        self.export.setEnabled(bool(self.rows))

    def export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export comparison", "policy-comparison.csv", "CSV (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(COLUMNS)
            writer.writerows(self.rows)
