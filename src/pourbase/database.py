"""Read-only access to the pourbase SQLite database."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from contextlib import closing
from functools import cached_property, lru_cache
from importlib.resources import files
from pathlib import Path

from .constants import FARADAY_C_MOL
from .exceptions import DatabaseSchemaError, MetalSystemNotFoundError
from .models import (
    EvidenceStatus,
    ExclusionReason,
    GibbsEnergyPolicy,
    LigandReference,
    MetalSystem,
    ReferenceState,
    SpeciesExclusion,
    ThermodynamicSpecies,
)
from .records import (
    ComputationalFallback,
    PhaseIdentity,
    PropertyValue,
    RecordWarning,
    ReportedValue,
    SourceReference,
    SpeciesRecord,
    Thermochemistry,
)

REQUIRED_SCHEMA_VERSION = 7


class ThermodynamicDatabase:
    """Validated, read-only access to one pourbase SQLite file.

    The file is opened read-only, so metadata, systems and loaded species are cached.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser().resolve()
        if not self.path.is_file():
            raise FileNotFoundError(self.path)
        self._uri = f"file:{self.path}?mode=ro"
        self._validate_schema()
        self._load_system = lru_cache(maxsize=512)(self._load_system_uncached)

    @classmethod
    @lru_cache(maxsize=1)
    def bundled(cls) -> ThermodynamicDatabase:
        return cls(Path(str(files("pourbase").joinpath("data", "pourbase.sqlite"))))

    def connect(self) -> sqlite3.Connection:
        """A new read-only connection with named-column rows."""
        connection = sqlite3.connect(self._uri, uri=True)
        connection.row_factory = sqlite3.Row
        return connection

    def _rows(self, query: str, parameters: Iterable[object] = ()) -> list[sqlite3.Row]:
        with closing(self.connect()) as connection:
            return connection.execute(query, tuple(parameters)).fetchall()

    @cached_property
    def metadata(self) -> dict[str, str]:
        return {row["key"]: row["value"] for row in self._rows("SELECT key, value FROM metadata")}

    def _validate_schema(self) -> None:
        try:
            version = int(self.metadata.get("schema_version", "0"))
        except (sqlite3.Error, ValueError) as error:
            raise DatabaseSchemaError(f"Cannot read the metadata of {self.path}") from error
        if version < REQUIRED_SCHEMA_VERSION:
            raise DatabaseSchemaError(
                f"Database schema {version} is older than required schema {REQUIRED_SCHEMA_VERSION}"
            )
        required = {"reference_temperature_K", "reference_pressure_bar", "water_gibbs_energy_J_mol"}
        if missing := sorted(required - self.metadata.keys()):
            raise DatabaseSchemaError(f"Missing reference-state metadata: {', '.join(missing)}")

    @property
    def data_version(self) -> str:
        return self.metadata.get("dataset_version", "unknown")

    @cached_property
    def reference_state(self) -> ReferenceState:
        return ReferenceState(
            temperature_K=float(self.metadata["reference_temperature_K"]),
            pressure_bar=float(self.metadata["reference_pressure_bar"]),
            water_gibbs_energy_J_mol=float(self.metadata["water_gibbs_energy_J_mol"]),
        )

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        value = symbol.strip()
        if not value:
            raise ValueError("symbol must not be empty")
        return value[:1].upper() + value[1:].lower()

    @cached_property
    def _systems(self) -> tuple[tuple[str, str], ...]:
        rows = self._rows("SELECT DISTINCT symbol, system FROM species ORDER BY symbol")
        return tuple((row["symbol"], row["system"]) for row in rows)

    def available_systems(self) -> tuple[tuple[str, str], ...]:
        """``(symbol, system name)`` of every element with species."""
        return self._systems

    @cached_property
    def _coverage(self) -> tuple[dict[str, object], ...]:
        return tuple(dict(row) for row in self._rows("SELECT * FROM element_coverage ORDER BY atomic_number"))

    def element_coverage(self) -> tuple[dict[str, object], ...]:
        """The documented status of every periodic-table position."""
        return self._coverage

    @cached_property
    def _ligands(self) -> tuple[LigandReference, ...]:
        return tuple(
            LigandReference(
                ligand_id=row["ligand_id"], name=row["name"], formula_ascii=row["formula_ascii"],
                charge=float(row["charge"]), gibbs_energy_J_mol=float(row["gibbs_energy_J_mol"]),
                source_id=row["source_id"], source_citation=row["source_citation"],
                source_url=row["source_url"], value_status=row["gibbs_status"],
            )
            for row in self._rows("SELECT * FROM ligands ORDER BY ligand_id")
        )

    def available_ligands(self) -> tuple[LigandReference, ...]:
        return self._ligands

    @cached_property
    def ligand_species(self) -> dict[str, dict[str, tuple[str, ...]]]:
        """``{symbol: {ligand_id: species names}}`` for every ligand complex."""
        result: dict[str, dict[str, list[str]]] = {}
        for row in self._rows("SELECT symbol, ligand_id, species FROM species WHERE ligand_id IS NOT NULL"):
            result.setdefault(row["symbol"], {}).setdefault(row["ligand_id"], []).append(row["species"])
        return {symbol: {key: tuple(names) for key, names in items.items()} for symbol, items in result.items()}

    @cached_property
    def _sources(self) -> dict[str, sqlite3.Row]:
        return {row["source_id"]: row for row in self._rows("SELECT * FROM sources")}

    def source(self, source_id: str | None, locator: str | None = None) -> SourceReference | None:
        """A source with a property-specific locator taking precedence over its general one."""
        if source_id is None:
            return None
        row = self._sources.get(source_id)
        return SourceReference(
            source_id=source_id,
            citation=row["citation"] if row else None,
            url=row["url"] if row else None,
            locator=locator or (row["locator"] if row else None),
        )

    def species_records(self, record_ids: Iterable[str]) -> tuple[SpeciesRecord, ...]:
        """Full evidence records in the requested order; unknown IDs are skipped."""
        identifiers = tuple(dict.fromkeys(item.strip() for item in record_ids if item.strip()))
        if not identifiers:
            return ()
        placeholders = ",".join("?" * len(identifiers))
        with closing(self.connect()) as connection:
            rows = {
                row["record_id"]: row
                for row in connection.execute(
                    f"""SELECT s.*, t.*,
                           p.identity_status, p.identified_phase,
                           p.spacegroup_symbol AS phase_spacegroup_symbol,
                           p.spacegroup_number AS phase_spacegroup_number,
                           p.possible_phases, p.evidence_summary,
                           p.source_url AS phase_source_url, p.notes AS phase_notes,
                           f.requested_mp_id, f.canonical_mp_id, f.mp_formula,
                           f.spacegroup_symbol AS fallback_spacegroup_symbol,
                           f.spacegroup_number AS fallback_spacegroup_number,
                           f.selection_basis, f.mapping_confidence,
                           f.temperature_K AS fallback_temperature_K,
                           f.gibbs_energy_eV_atom AS fallback_gibbs_eV_atom,
                           f.gibbs_energy_J_mol AS fallback_gibbs_J_mol, f.model,
                           f.mp_database_version, f.source_url AS fallback_source_url,
                           f.notes AS fallback_notes
                       FROM species AS s
                       JOIN thermochemistry AS t USING(record_id)
                       LEFT JOIN phases AS p USING(record_id)
                       LEFT JOIN computational_fallbacks AS f USING(record_id)
                       WHERE s.record_id IN ({placeholders})""",
                    identifiers,
                )
            }
            warnings: dict[str, list[RecordWarning]] = {}
            for row in connection.execute(
                f"SELECT * FROM warnings WHERE record_id IN ({placeholders}) ORDER BY record_id, warning_type",
                identifiers,
            ):
                source = self.source(row["source_id"], row["source_locator"])
                if source is not None and row["source_url"]:
                    source = SourceReference(source.source_id, source.citation, row["source_url"], source.locator)
                warnings.setdefault(row["record_id"], []).append(
                    RecordWarning(row["warning_type"], row["message"], source)
                )
            reported: dict[str, list[ReportedValue]] = {}
            for row in connection.execute(
                f"""SELECT * FROM reported_thermochemistry WHERE record_id IN ({placeholders})
                    ORDER BY record_id, property, selected_as_recommended DESC, value_id""",
                identifiers,
            ):
                reported.setdefault(row["record_id"], []).append(ReportedValue(
                    value_id=row["value_id"], property=row["property"], value=row["value"],
                    unit=row["unit"], status=row["status"],
                    selected_as_recommended=bool(row["selected_as_recommended"]),
                    uncertainty=row["uncertainty"], source=self.source(row["source_id"]),
                    supersedes_value_id=row["supersedes_value_id"],
                ))

        def value(row: sqlite3.Row, prefix: str, field: str, uncertainty: str) -> PropertyValue:
            return PropertyValue(
                value=row[field], status=row[f"{prefix}_status"], uncertainty=row[uncertainty],
                source=self.source(row[f"{prefix}_source_id"], row[f"{prefix}_source_locator"]),
            )

        records = []
        for record_id in identifiers:
            row = rows.get(record_id)
            if row is None:
                continue
            records.append(SpeciesRecord(
                record_id=record_id, system=row["system"], symbol=row["symbol"],
                species=row["species"], formula_ascii=row["formula_ascii"], phase=row["phase"],
                phase_detail=row["phase_detail"] or "", charge=row["charge"],
                metal_oxidation_state=row["metal_oxidation_state"],
                thermochemistry=Thermochemistry(
                    temperature_K=row["temperature_K"], pressure_bar=row["pressure_bar"],
                    gibbs_energy_J_mol=value(row, "gibbs", "gibbs_energy_J_mol", "gibbs_uncertainty_J_mol"),
                    entropy_J_mol_K=value(row, "entropy", "entropy_J_mol_K", "entropy_uncertainty_J_mol_K"),
                    formation_enthalpy_J_mol=value(
                        row, "formation_enthalpy", "formation_enthalpy_J_mol",
                        "formation_enthalpy_uncertainty_J_mol",
                    ),
                ),
                reported=tuple(reported.get(record_id, ())),
                fallback=ComputationalFallback(
                    requested_mp_id=row["requested_mp_id"], canonical_mp_id=row["canonical_mp_id"],
                    formula=row["mp_formula"], spacegroup_symbol=row["fallback_spacegroup_symbol"],
                    spacegroup_number=row["fallback_spacegroup_number"],
                    selection_basis=row["selection_basis"], mapping_confidence=row["mapping_confidence"],
                    temperature_K=row["fallback_temperature_K"],
                    gibbs_energy_eV_atom=row["fallback_gibbs_eV_atom"],
                    gibbs_energy_J_mol=row["fallback_gibbs_J_mol"], model=row["model"],
                    database_version=row["mp_database_version"], source_url=row["fallback_source_url"],
                    notes=row["fallback_notes"],
                ) if row["canonical_mp_id"] is not None else None,
                phase_identity=PhaseIdentity(
                    status=row["identity_status"], identified_phase=row["identified_phase"],
                    spacegroup_symbol=row["phase_spacegroup_symbol"],
                    spacegroup_number=row["phase_spacegroup_number"],
                    possible_phases=row["possible_phases"], evidence_summary=row["evidence_summary"],
                    source_url=row["phase_source_url"], notes=row["phase_notes"],
                ) if row["identity_status"] is not None else None,
                warnings=tuple(warnings.get(record_id, ())),
            ))
        return tuple(records)

    def materials_project_comparisons(self, symbol: str) -> tuple[dict[str, object], ...]:
        """Reviewed phase matches and selected DFT energies for one element."""
        rows = self._rows(
            """SELECT s.record_id, s.species, s.formula_ascii, s.phase_detail, s.atom_count,
                   t.gibbs_energy_J_mol, t.gibbs_status, t.gibbs_source_id,
                   m.mp_id, m.mp_formula, m.spacegroup_symbol, m.spacegroup_number,
                   m.crystal_system, m.match_confidence, m.database_version AS match_database_version,
                   m.source_url AS match_source_url, m.notes AS match_notes,
                   e.calculation_type, e.formation_energy_eV_atom, e.energy_above_hull_eV_atom,
                   e.energy_uncertainty_eV_atom, e.energy_type,
                   e.database_version AS energy_database_version,
                   e.source_url AS energy_source_url, e.retrieved_on
               FROM species AS s
               JOIN thermochemistry AS t USING(record_id)
               JOIN materials_project_matches AS m USING(record_id)
               LEFT JOIN materials_project_energies AS e
                 ON e.record_id = s.record_id AND e.selected_for_comparison = 1
               WHERE s.symbol = ?
               ORDER BY s.record_id, e.calculation_type""",
            (self._normalize_symbol(symbol),),
        )
        result = []
        for row in rows:
            item = dict(row)
            experimental = _eV_per_atom(row["gibbs_energy_J_mol"], row["atom_count"])
            mp_energy = row["formation_energy_eV_atom"]
            item["experimental_gibbs_eV_atom"] = experimental
            item["mp_minus_experimental_eV_atom"] = (
                float(mp_energy) - experimental if mp_energy is not None and experimental is not None else None
            )
            result.append(item)
        return tuple(result)

    def materials_project_thermochemistry(
        self, symbol: str | None = None, *, selected_only: bool = False
    ) -> tuple[dict[str, object], ...]:
        """Phase-matched experimental and MP formation energies, per atom."""
        clauses, parameters = [], []
        if symbol is not None:
            clauses.append("s.symbol = ?")
            parameters.append(self._normalize_symbol(symbol))
        if selected_only:
            clauses.append("e.selected_for_comparison = 1")
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        rows = self._rows(
            f"""SELECT s.record_id, s.symbol, s.species, s.formula_ascii, s.phase_detail,
                   s.atom_count, t.gibbs_energy_J_mol, t.gibbs_source_id,
                   t.formation_enthalpy_J_mol, t.formation_enthalpy_source_id,
                   m.mp_id, m.spacegroup_symbol, m.spacegroup_number,
                   e.calculation_type, e.selected_for_comparison,
                   e.formation_energy_eV_atom, e.energy_above_hull_eV_atom,
                   e.energy_uncertainty_eV_atom, e.database_version, e.source_url, e.retrieved_on
               FROM species AS s
               JOIN thermochemistry AS t USING(record_id)
               JOIN materials_project_matches AS m USING(record_id)
               JOIN materials_project_energies AS e USING(record_id, mp_id)
               {where}
               ORDER BY s.symbol, s.record_id, e.calculation_type""",
            parameters,
        )
        result = []
        for row in rows:
            item = dict(row)
            item["experimental_gibbs_eV_atom"] = _eV_per_atom(row["gibbs_energy_J_mol"], row["atom_count"])
            item["experimental_enthalpy_eV_atom"] = _eV_per_atom(row["formation_enthalpy_J_mol"], row["atom_count"])
            result.append(item)
        return tuple(result)

    def load_system(
        self,
        symbol: str,
        *,
        ligand_ids: Iterable[str] = (),
        energy_policy: GibbsEnergyPolicy | str = GibbsEnergyPolicy.EXPERIMENTAL_ONLY,
    ) -> MetalSystem:
        """Calculation-ready species of one element; results are cached."""
        selected = frozenset(item.strip() for item in ligand_ids)
        if "" in selected:
            raise ValueError("ligand_ids must not contain empty strings")
        if unknown := sorted(selected - {item.ligand_id for item in self._ligands}):
            raise ValueError("No thermodynamic reference is available for: " + ", ".join(unknown))
        return self._load_system(self._normalize_symbol(symbol), selected, GibbsEnergyPolicy(energy_policy))

    def _load_system_uncached(
        self, symbol: str, ligand_ids: frozenset[str], energy_policy: GibbsEnergyPolicy
    ) -> MetalSystem:
        rows = self._rows(
            """SELECT s.record_id, s.system, s.symbol, s.species, s.formula_ascii,
                   s.phase, s.phase_detail, s.charge, s.metal_count,
                   s.core_oxygen_count, s.core_hydrogen_count, s.ligand_id,
                   s.ligand_count, s.ligand_charge, s.metal_oxidation_state,
                   s.electron_coefficient_per_metal,
                   t.gibbs_energy_J_mol, t.gibbs_status, t.gibbs_source_id,
                   f.gibbs_energy_J_mol AS fallback_gibbs_energy_J_mol,
                   f.canonical_mp_id AS fallback_mp_id,
                   l.gibbs_energy_J_mol AS ligand_gibbs_energy_J_mol
               FROM species AS s
               JOIN thermochemistry AS t USING(record_id)
               LEFT JOIN computational_fallbacks AS f USING(record_id)
               LEFT JOIN ligands AS l ON l.ligand_id = s.ligand_id
               WHERE s.symbol = ? ORDER BY s.record_id""",
            (symbol,),
        )
        if not rows:
            raise MetalSystemNotFoundError(symbol)
        included: list[ThermodynamicSpecies] = []
        excluded: list[SpeciesExclusion] = []
        use_fallbacks = energy_policy is GibbsEnergyPolicy.EXPERIMENTAL_THEN_MP
        for row in rows:
            fallback = (
                use_fallbacks and row["gibbs_energy_J_mol"] is None
                and row["fallback_gibbs_energy_J_mol"] is not None
            )
            gibbs = row["fallback_gibbs_energy_J_mol"] if fallback else row["gibbs_energy_J_mol"]
            ligand_count = float(row["ligand_count"] or 0.0)
            reason = None
            if ligand_count and row["ligand_id"] not in ligand_ids:
                reason = ExclusionReason.LIGAND_NOT_SELECTED
            elif ligand_count and row["ligand_gibbs_energy_J_mol"] is None:
                reason = ExclusionReason.LIGAND_REFERENCE_UNAVAILABLE
            elif gibbs is None:
                reason = ExclusionReason.GIBBS_ENERGY_UNAVAILABLE
            if reason is not None:
                excluded.append(SpeciesExclusion(row["record_id"], row["species"], reason, row["gibbs_status"]))
                continue
            included.append(ThermodynamicSpecies(
                record_id=row["record_id"], system=row["system"], symbol=row["symbol"],
                species=row["species"], formula_ascii=row["formula_ascii"],
                phase=row["phase"], phase_detail=row["phase_detail"] or "",
                charge=float(row["charge"]), metal_count=float(row["metal_count"]),
                core_oxygen_count=float(row["core_oxygen_count"]),
                core_hydrogen_count=float(row["core_hydrogen_count"]),
                ligand_id=row["ligand_id"] or None, ligand_count=ligand_count,
                ligand_charge=float(row["ligand_charge"] or 0.0),
                formal_metal_oxidation_state=float(row["metal_oxidation_state"]),
                electron_coefficient_per_metal=float(row["electron_coefficient_per_metal"]),
                gibbs_energy_J_mol=float(gibbs),
                gibbs_status=EvidenceStatus.MATERIALS_PROJECT_FALLBACK if fallback else row["gibbs_status"],
                source_id=f"Materials Project {row['fallback_mp_id']}" if fallback else row["gibbs_source_id"],
                ligand_gibbs_energy_J_mol=(
                    float(row["ligand_gibbs_energy_J_mol"])
                    if row["ligand_gibbs_energy_J_mol"] is not None else None
                ),
            ))
        return MetalSystem(system=rows[0]["system"], symbol=symbol, species=tuple(included), excluded=tuple(excluded))


def _eV_per_atom(value: float | None, atoms: float) -> float | None:
    return float(value) / FARADAY_C_MOL / float(atoms) if value is not None else None
