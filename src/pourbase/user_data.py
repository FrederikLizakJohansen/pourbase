"""Calculations with your own species next to, or in place of, the bundled data.

A user species is defined by a formula containing only the metal, O and H, a charge, a phase and
a standard Gibbs energy of formation at 298.15 K and 1 bar. Its proton and electron coefficients
follow from the formula and charge exactly as for the bundled species. User values carry the
evidence status ``user_supplied`` and the citation given with them, so they remain
distinguishable from curated records in every result.

The CSV format has one row per species::

    symbol,species,formula,charge,phase,formation_energy_kJ_mol,uncertainty_kJ_mol,citation,replaces
    Fe,Fe(OH)2 (fresh),Fe(OH)2,0,solid,-486.5,2.0,My lab notebook p. 12,
    Cu,Cu+,Cu,1,aqueous,49.98,,Example et al. 2024,gfe-cu-cu-q+1-aqueous-aq

``species``, ``charge``, ``citation``, ``uncertainty_kJ_mol`` and ``replaces`` may be empty.
The legacy column ``gibbs_energy_kJ_mol`` is also accepted. ``replaces`` names the record ID of a
bundled species the row substitutes in calculations.
"""

from __future__ import annotations

import csv
import math
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .database import ThermodynamicDatabase
from .models import EvidenceStatus, MetalSystem, ThermodynamicSpecies

PHASES = ("aqueous", "solid", "liquid", "gas")


@dataclass(frozen=True)
class UserSpecies:
    """One species supplied by the user."""

    symbol: str
    species: str
    formula: str
    charge: float
    phase: str
    gibbs_energy_J_mol: float
    citation: str
    uncertainty_J_mol: float | None = None
    replaces: str | None = None

    @property
    def record_id(self) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", f"{self.formula} q{self.charge:+g} {self.phase} {self.species}".lower())
        return f"user-{self.symbol.lower()}-{slug.strip('-')}"

    def thermodynamic_species(self, system: str) -> ThermodynamicSpecies:
        counts = formula_counts(self.formula)
        unknown = set(counts) - {self.symbol, "O", "H"}
        if unknown or self.symbol not in counts:
            raise ValueError(f"{self.species}: the formula may contain only {self.symbol}, O and H")
        if self.phase not in PHASES:
            raise ValueError(f"{self.species}: phase must be one of {', '.join(PHASES)}")
        if self.phase != "aqueous" and self.charge:
            raise ValueError(f"{self.species}: only aqueous species may carry a charge")
        return ThermodynamicSpecies(
            record_id=self.record_id, system=system, symbol=self.symbol, species=self.species,
            formula_ascii=self.formula, phase=self.phase, phase_detail="user supplied",
            charge=float(self.charge), metal_count=counts[self.symbol],
            core_oxygen_count=counts.get("O", 0.0), core_hydrogen_count=counts.get("H", 0.0),
            ligand_id=None, ligand_count=0.0, ligand_charge=0.0,
            gibbs_energy_J_mol=self.gibbs_energy_J_mol, gibbs_status=EvidenceStatus.USER_SUPPLIED,
            source_id=self.citation, gibbs_uncertainty_J_mol=self.uncertainty_J_mol,
        )


def formula_counts(formula: str) -> Counter:
    """Element counts of a formula with optional parentheses, such as ``Fe2(OH)2``."""
    tokens = re.findall(r"[A-Z][a-z]?|\d+(?:\.\d+)?|\(|\)", formula)
    if "".join(tokens) != formula.replace(" ", ""):
        raise ValueError(f"Cannot read the formula {formula!r}")
    position = 0

    def group() -> Counter:
        nonlocal position
        counts: Counter = Counter()
        while position < len(tokens) and tokens[position] != ")":
            token = tokens[position]
            position += 1
            if token == "(":
                inner = group()
                position += 1
            else:
                inner = Counter({token: 1.0})
            factor = 1.0
            if position < len(tokens) and tokens[position][0].isdigit():
                factor = float(tokens[position])
                position += 1
            for element, count in inner.items():
                counts[element] += count * factor
        return counts

    return group()


def read_user_species(path: str | Path) -> tuple[UserSpecies, ...]:
    """Read user species from a CSV file in the format of the module documentation."""
    rows = []
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        for number, row in enumerate(csv.DictReader(handle), start=2):
            try:
                uncertainty = (row.get("uncertainty_kJ_mol") or "").strip()
                new_energy = (row.get("formation_energy_kJ_mol") or "").strip()
                old_energy = (row.get("gibbs_energy_kJ_mol") or "").strip()
                if not new_energy and not old_energy:
                    raise ValueError("formation_energy_kJ_mol is required")
                if new_energy and old_energy and float(new_energy) != float(old_energy):
                    raise ValueError("formation_energy_kJ_mol and gibbs_energy_kJ_mol disagree")
                gibbs = float(new_energy or old_energy) * 1000.0
                if not math.isfinite(gibbs):
                    raise ValueError("the Gibbs energy must be finite")
                rows.append(UserSpecies(
                    symbol=row["symbol"].strip().capitalize(),
                    species=(row.get("species") or row["formula"]).strip(),
                    formula=row["formula"].strip(),
                    charge=float(row.get("charge") or 0.0),
                    phase=row["phase"].strip().lower(),
                    gibbs_energy_J_mol=gibbs,
                    citation=(row.get("citation") or "").strip() or "user supplied",
                    uncertainty_J_mol=float(uncertainty) * 1000.0 if uncertainty else None,
                    replaces=(row.get("replaces") or "").strip() or None,
                ))
            except (KeyError, ValueError) as error:
                raise ValueError(f"{path}, line {number}: {error}") from error
    return tuple(rows)


class UserSpeciesDatabase(ThermodynamicDatabase):
    """The bundled database with user species added to, or substituted in, their systems."""

    def __init__(self, base: ThermodynamicDatabase, species: Iterable[UserSpecies]) -> None:
        self.base = base
        self.user_species = tuple(species)
        super().__init__(base.path, getattr(base, "_policy", None))
        known = {symbol for symbol, _name in self.available_systems()}
        for item in self.user_species:
            if item.symbol not in known:
                raise ValueError(f"{item.species}: {item.symbol} is not a supported system")
            item.thermodynamic_species(item.symbol)

    def _load_system_uncached(self, symbol, ligand_ids, energy_policy,
                              include_optional_gases=False) -> MetalSystem:
        system = self.base._load_system_uncached(symbol, ligand_ids, energy_policy, include_optional_gases)
        added = [item for item in self.user_species if item.symbol == symbol]
        if not added:
            return system
        replaced = {item.replaces for item in added if item.replaces}
        unknown = replaced - {item.record_id for item in system.species} - {item.record_id for item in system.excluded}
        if unknown:
            raise ValueError(f"No {symbol} record to replace: {', '.join(sorted(unknown))}")
        species = tuple(item for item in system.species if item.record_id not in replaced)
        species += tuple(item.thermodynamic_species(system.system) for item in added)
        excluded = tuple(item for item in system.excluded if item.record_id not in replaced)
        return MetalSystem(system=system.system, symbol=symbol, species=species, excluded=excluded)


    def species_records(self, record_ids):
        """Evidence records of bundled and user species; a user species has its single supplied value."""
        from .records import (
            PropertyValue,
            ReportedValue,
            SourceReference,
            SpeciesRecord,
            Thermochemistry,
        )

        identifiers = list(record_ids)
        user = {item.record_id: item for item in self.user_species}
        records = {record.record_id: record for record in self.base.species_records(
            [item for item in identifiers if item not in user])}
        for record_id in identifiers:
            item = user.get(record_id)
            if item is None:
                continue
            species = item.thermodynamic_species(item.symbol)
            source = SourceReference(item.citation, item.citation, None, "user CSV")
            gibbs = PropertyValue(item.gibbs_energy_J_mol, EvidenceStatus.USER_SUPPLIED.value, item.uncertainty_J_mol,
                                  source)
            missing = PropertyValue(None, EvidenceStatus.NOT_AVAILABLE.value, None, None)
            records[record_id] = SpeciesRecord(
                record_id=record_id, system=species.system, symbol=item.symbol, species=item.species,
                formula_ascii=item.formula, phase=item.phase, phase_detail="user supplied", charge=item.charge,
                metal_oxidation_state=species.electrons_per_metal,
                thermochemistry=Thermochemistry(298.15, 1.0, gibbs, missing, missing),
                reported=(ReportedValue(f"{record_id}:gibbs", "gibbs_energy_of_formation", item.gibbs_energy_J_mol,
                                        "J/mol", EvidenceStatus.USER_SUPPLIED.value, True, item.uncertainty_J_mol,
                                        source, item.replaces),),
                fallback=None, phase_identity=None, warnings=(),
            )
        return tuple(records[item] for item in identifiers if item in records)


def with_user_species(database: ThermodynamicDatabase, species: str | Path | Iterable[UserSpecies]
                      ) -> UserSpeciesDatabase:
    """``database`` with user species from a CSV path or ``UserSpecies`` objects."""
    if isinstance(species, (str, Path)):
        species = read_user_species(species)
    return UserSpeciesDatabase(database, species)


def dataset_from_csv(csv_path: str | Path, output_path: str | Path | None = None,
                     reference: ThermodynamicDatabase | None = None) -> ThermodynamicDatabase:
    """A database that holds only the species of a CSV file (the format of ``read_user_species``).

    The file is written as a SQLite database with the schema of the bundled release, so every part of
    the package and application works with it. Each row becomes the only reported Gibbs energy of its
    species, which the selection policy then recommends. Only the reference state (temperature, pressure and
    the Gibbs energy of water) and the element names come from ``reference``, the bundled database by
    default. ``output_path`` defaults to a new temporary file. The ``replaces`` column is ignored.
    """
    import sqlite3
    import tempfile
    from contextlib import closing

    reference = reference or ThermodynamicDatabase.bundled()
    species = read_user_species(csv_path)
    if not species:
        raise ValueError(f"{csv_path} holds no species")
    if output_path is None:
        output_path = Path(tempfile.mkdtemp(prefix="pourbase-dataset-")) / (Path(csv_path).stem + ".sqlite")
    output_path = Path(output_path)
    if output_path.exists():
        output_path.unlink()
    names = {row["symbol"]: row["system"] for row in reference.element_coverage() if row.get("system")}
    with closing(reference.connect()) as source:
        schema = [row[0] for row in source.execute(
            "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' "
            "ORDER BY type = 'index'")]
        metadata = dict(source.execute("SELECT key, value FROM metadata").fetchall())
        coverage = source.execute("SELECT atomic_number, symbol, coverage_status FROM element_coverage").fetchall()
    symbols = {item.symbol for item in species}
    unknown = symbols - {row[1] for row in coverage}
    if unknown:
        raise ValueError(f"Unknown element symbols: {', '.join(sorted(unknown))}")
    metadata.update({"database_role": "user_dataset", "dataset_version": "user",
                     "publication_status": f"user dataset from {Path(csv_path).name}"})
    for key in ("selection_policy", "selection_policy_fingerprint", "freeze_date"):
        metadata.pop(key, None)
    with closing(sqlite3.connect(output_path)) as connection:
        for statement in schema:
            connection.execute(statement)
        connection.executemany("INSERT INTO metadata VALUES (?, ?)", sorted(metadata.items()))
        for number, symbol, status in coverage:
            if symbol in symbols:
                row = (number, symbol, "supported", names.get(symbol, symbol), "Species from the user dataset.")
            elif status == "reference_component":
                row = (number, symbol, status, None, "Used as water, proton, and electron reference components.")
            else:
                row = (number, symbol, "outside_current_scope", None, "No species in this dataset.")
            connection.execute("INSERT INTO element_coverage VALUES (?, ?, ?, ?, ?)", row)
        citations: dict[str, str] = {}
        for item in species:
            if item.citation not in citations:
                citations[item.citation] = f"user-source-{len(citations) + 1:03d}"
                connection.execute("INSERT INTO sources VALUES (?, ?, ?, ?, ?)",
                                   (citations[item.citation], item.citation, "", "", None))
            record = item.thermodynamic_species(names.get(item.symbol, item.symbol))
            if record.record_id in {row[0] for row in connection.execute("SELECT record_id FROM species")}:
                raise ValueError(f"{item.species} appears twice in {csv_path}")
            counts = formula_counts(item.formula)
            electrons = record.electrons_per_metal
            connection.execute(
                "INSERT INTO species VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (record.record_id, record.system, record.species, record.formula_ascii, record.symbol,
                 record.phase, "user supplied", record.charge, float(sum(counts.values())), record.metal_count,
                 record.core_oxygen_count, record.core_hydrogen_count, None, 0.0, 0.0, electrons, electrons))
            source_id = citations[item.citation]
            connection.execute(
                "INSERT INTO reported_thermochemistry (value_id, record_id, property, value, unit, temperature_K, "
                "pressure_bar, status, uncertainty, source_id, supersedes_value_id, source_locator) "
                "VALUES (?, ?, 'gibbs_energy_of_formation', ?, 'J/mol', 298.15, 1.0, ?, ?, ?, NULL, ?)",
                (f"{record.record_id}:gf:preferred", record.record_id, item.gibbs_energy_J_mol,
                 EvidenceStatus.USER_SUPPLIED.value, item.uncertainty_J_mol, source_id, Path(csv_path).name))
        connection.commit()
    return ThermodynamicDatabase(output_path)


def open_dataset(path: str | Path) -> ThermodynamicDatabase:
    """Open a dataset on its own: a pourbase SQLite file, or a CSV of species (see ``read_user_species``)."""
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return dataset_from_csv(path)
    return ThermodynamicDatabase(path)
