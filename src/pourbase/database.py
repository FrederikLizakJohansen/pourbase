"""Read-only access to the clean publication database."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from contextlib import closing
from importlib.resources import files
from pathlib import Path

from .constants import FARADAY_C_MOL
from .exceptions import DatabaseSchemaError, MetalSystemNotFoundError
from .models import (
    GibbsEnergyPolicy,
    LigandReference,
    MetalSystem,
    ReferenceState,
    SpeciesExclusion,
    ThermodynamicSpecies,
)


class ThermodynamicDatabase:
    """Validated, read-only access to one SQLite publication file."""

    REQUIRED_SCHEMA_VERSION = 7

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser().resolve()
        if not self.path.is_file():
            raise FileNotFoundError(self.path)
        self._validate_schema()

    @classmethod
    def bundled(cls) -> ThermodynamicDatabase:
        resource = files("pourbase").joinpath("data", "pourbase.sqlite")
        return cls(Path(str(resource)))

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _metadata(self) -> dict[str, str]:
        with closing(self._connect()) as connection:
            return dict(connection.execute("SELECT key,value FROM metadata"))

    def _validate_schema(self) -> None:
        try:
            metadata = self._metadata()
            version = int(metadata.get("schema_version", "0"))
        except (sqlite3.Error, ValueError) as error:
            raise DatabaseSchemaError(f"Cannot read publication metadata from {self.path}") from error
        if version < self.REQUIRED_SCHEMA_VERSION:
            raise DatabaseSchemaError(
                f"Database schema {version} is older than required schema {self.REQUIRED_SCHEMA_VERSION}"
            )
        required = {
            "reference_temperature_K", "reference_pressure_bar",
            "water_gibbs_energy_J_mol",
        }
        if missing := sorted(required - metadata.keys()):
            raise DatabaseSchemaError(f"Missing reference-state metadata: {', '.join(missing)}")

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        value = symbol.strip()
        if not value:
            raise ValueError("symbol must not be empty")
        return value[:1].upper() + value[1:].lower()

    @property
    def reference_state(self) -> ReferenceState:
        metadata = self._metadata()
        return ReferenceState(
            temperature_K=float(metadata["reference_temperature_K"]),
            pressure_bar=float(metadata["reference_pressure_bar"]),
            water_gibbs_energy_J_mol=float(metadata["water_gibbs_energy_J_mol"]),
        )

    def available_systems(self) -> tuple[tuple[str, str], ...]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT DISTINCT symbol,system FROM species ORDER BY symbol"
            )
            return tuple((row["symbol"], row["system"]) for row in rows)

    def element_coverage(self) -> tuple[dict[str, object], ...]:
        """Return the documented status of every periodic-table position."""
        with closing(self._connect()) as connection:
            return tuple(
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM element_coverage ORDER BY atomic_number"
                )
            )

    def available_ligands(self) -> tuple[LigandReference, ...]:
        with closing(self._connect()) as connection:
            rows = connection.execute("SELECT * FROM ligands ORDER BY ligand_id")
            return tuple(
                LigandReference(
                    ligand_id=row["ligand_id"], name=row["name"],
                    formula_ascii=row["formula_ascii"], charge=float(row["charge"]),
                    gibbs_energy_J_mol=float(row["gibbs_energy_J_mol"]),
                    source_id=row["source_id"], source_citation=row["source_citation"],
                    source_url=row["source_url"], value_status=row["gibbs_status"],
                )
                for row in rows
            )

    def species_details(self, record_ids: Iterable[str]) -> tuple[dict[str, object], ...]:
        """Return publication data for the requested species records."""
        identifiers = tuple(dict.fromkeys(item.strip() for item in record_ids if item.strip()))
        if not identifiers:
            return ()
        placeholders = ",".join("?" for _ in identifiers)
        with closing(self._connect()) as connection:
            rows = list(
                connection.execute(
                    f"""SELECT
                           s.*,
                           t.temperature_K,t.pressure_bar,
                           t.gibbs_energy_J_mol,t.gibbs_status,
                           t.gibbs_uncertainty_J_mol,t.gibbs_source_id,
                           t.gibbs_source_locator,
                           t.entropy_J_mol_K,t.entropy_status,
                           t.entropy_uncertainty_J_mol_K,t.entropy_source_id,
                           t.entropy_source_locator,
                           t.formation_enthalpy_J_mol,t.formation_enthalpy_status,
                           t.formation_enthalpy_uncertainty_J_mol,
                           t.formation_enthalpy_source_id AS enthalpy_source_id,
                           t.formation_enthalpy_source_locator AS enthalpy_source_locator,
                           gs.citation AS gibbs_source_citation,
                           gs.url AS gibbs_source_url,
                           es.citation AS entropy_source_citation,
                           es.url AS entropy_source_url,
                           hs.citation AS enthalpy_source_citation,
                           hs.url AS enthalpy_source_url,
                           p.identity_status,p.identified_phase,p.spacegroup_symbol,
                           p.spacegroup_number,p.possible_phases,p.evidence_summary,
                           p.source_url AS phase_source_url,p.notes AS phase_notes
                           ,f.requested_mp_id AS fallback_requested_mp_id
                           ,f.canonical_mp_id AS fallback_canonical_mp_id
                           ,f.mp_formula AS fallback_formula
                           ,f.spacegroup_symbol AS fallback_spacegroup_symbol
                           ,f.spacegroup_number AS fallback_spacegroup_number
                           ,f.selection_basis AS fallback_selection_basis
                           ,f.mapping_confidence AS fallback_mapping_confidence
                           ,f.temperature_K AS fallback_temperature_K
                           ,f.gibbs_energy_eV_atom AS fallback_gibbs_eV_atom
                           ,f.gibbs_energy_J_mol AS fallback_gibbs_J_mol
                           ,f.model AS fallback_model
                           ,f.mp_database_version AS fallback_database_version
                           ,f.source_url AS fallback_source_url
                           ,f.notes AS fallback_notes
                       FROM species AS s
                       JOIN thermochemistry AS t USING(record_id)
                       LEFT JOIN sources AS gs ON gs.source_id=t.gibbs_source_id
                       LEFT JOIN sources AS es ON es.source_id=t.entropy_source_id
                       LEFT JOIN sources AS hs ON hs.source_id=t.formation_enthalpy_source_id
                       LEFT JOIN phases AS p USING(record_id)
                       LEFT JOIN computational_fallbacks AS f USING(record_id)
                       WHERE s.record_id IN ({placeholders})""",
                    identifiers,
                )
            )
            warnings: dict[str, list[dict[str, object]]] = {
                record_id: [] for record_id in identifiers
            }
            for warning in connection.execute(
                f"""SELECT w.*,src.citation AS source_citation,
                            src.url AS citation_url
                     FROM warnings AS w
                     LEFT JOIN sources AS src USING(source_id)
                     WHERE w.record_id IN ({placeholders})
                     ORDER BY w.record_id,w.warning_type""",
                identifiers,
            ):
                warnings[warning["record_id"]].append(
                    {
                        "type": warning["warning_type"],
                        "message": warning["message"],
                        "source_id": warning["source_id"],
                        "source_citation": warning["source_citation"],
                        "source_url": warning["source_url"] or warning["citation_url"],
                        "source_locator": warning["source_locator"],
                    }
                )
            reported: dict[str, list[dict[str, object]]] = {
                record_id: [] for record_id in identifiers
            }
            for value in connection.execute(
                f"""SELECT r.*,s.citation AS source_citation,s.url AS source_url,
                            s.locator AS source_locator
                     FROM reported_thermochemistry AS r
                     LEFT JOIN sources AS s USING(source_id)
                     WHERE r.record_id IN ({placeholders})
                     ORDER BY r.record_id,r.property,r.selected_as_recommended DESC,r.value_id""",
                identifiers,
            ):
                reported[value["record_id"]].append(dict(value))

        def source(row: sqlite3.Row, prefix: str) -> dict[str, object] | None:
            source_id = row[f"{prefix}_source_id"]
            if source_id is None:
                return None
            return {
                "source_id": source_id,
                "citation": row[f"{prefix}_source_citation"],
                "url": row[f"{prefix}_source_url"],
                "locator": row[f"{prefix}_source_locator"],
            }

        by_id = {
            row["record_id"]: {
                "record_id": row["record_id"],
                "system": row["system"],
                "species": row["species"],
                "formula_ascii": row["formula_ascii"],
                "symbol": row["symbol"],
                "phase": row["phase"],
                "phase_detail": row["phase_detail"],
                "charge": row["charge"],
                "metal_oxidation_state": row["metal_oxidation_state"],
                "electron_coefficient_per_metal": row[
                    "electron_coefficient_per_metal"
                ],
                "thermochemistry": {
                    "temperature_K": row["temperature_K"],
                    "pressure_bar": row["pressure_bar"],
                    "gibbs_energy_J_mol": row["gibbs_energy_J_mol"],
                    "gibbs_status": row["gibbs_status"],
                    "gibbs_uncertainty_J_mol": row["gibbs_uncertainty_J_mol"],
                    "gibbs_source": source(row, "gibbs"),
                    "entropy_J_mol_K": row["entropy_J_mol_K"],
                    "entropy_status": row["entropy_status"],
                    "entropy_uncertainty_J_mol_K": row["entropy_uncertainty_J_mol_K"],
                    "entropy_source": source(row, "entropy"),
                    "formation_enthalpy_J_mol": row["formation_enthalpy_J_mol"],
                    "formation_enthalpy_status": row["formation_enthalpy_status"],
                    "formation_enthalpy_uncertainty_J_mol": row[
                        "formation_enthalpy_uncertainty_J_mol"
                    ],
                    "formation_enthalpy_source": source(row, "enthalpy"),
                },
                "reported_thermochemistry": reported[row["record_id"]],
                "computational_fallback": (
                    {
                        "requested_mp_id": row["fallback_requested_mp_id"],
                        "canonical_mp_id": row["fallback_canonical_mp_id"],
                        "formula": row["fallback_formula"],
                        "spacegroup_symbol": row["fallback_spacegroup_symbol"],
                        "spacegroup_number": row["fallback_spacegroup_number"],
                        "selection_basis": row["fallback_selection_basis"],
                        "mapping_confidence": row["fallback_mapping_confidence"],
                        "temperature_K": row["fallback_temperature_K"],
                        "gibbs_energy_eV_atom": row["fallback_gibbs_eV_atom"],
                        "gibbs_energy_J_mol": row["fallback_gibbs_J_mol"],
                        "model": row["fallback_model"],
                        "database_version": row["fallback_database_version"],
                        "source_url": row["fallback_source_url"],
                        "notes": row["fallback_notes"],
                    }
                    if row["fallback_canonical_mp_id"] is not None else None
                ),
                "phase_identity": (
                    {
                        "status": row["identity_status"],
                        "identified_phase": row["identified_phase"],
                        "spacegroup_symbol": row["spacegroup_symbol"],
                        "spacegroup_number": row["spacegroup_number"],
                        "possible_phases": row["possible_phases"],
                        "evidence_summary": row["evidence_summary"],
                        "source_url": row["phase_source_url"],
                        "notes": row["phase_notes"],
                    }
                    if row["identity_status"] is not None
                    else None
                ),
                "warnings": warnings[row["record_id"]],
            }
            for row in rows
        }
        return tuple(by_id[record_id] for record_id in identifiers if record_id in by_id)

    def materials_project_comparisons(
        self, symbol: str
    ) -> tuple[dict[str, object], ...]:
        """Return reviewed phase matches and selected DFT energies for one element."""
        normalized_symbol = self._normalize_symbol(symbol)
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """SELECT
                       s.record_id,s.species,s.formula_ascii,s.phase_detail,s.atom_count,
                       t.gibbs_energy_J_mol,t.gibbs_status,t.gibbs_source_id,
                       m.mp_id,m.mp_formula,m.spacegroup_symbol,m.spacegroup_number,
                       m.crystal_system,m.match_confidence,m.database_version AS match_database_version,
                       m.source_url AS match_source_url,m.notes AS match_notes,
                       e.calculation_type,e.formation_energy_eV_atom,
                       e.energy_above_hull_eV_atom,e.energy_uncertainty_eV_atom,
                       e.energy_type,e.database_version AS energy_database_version,
                       e.source_url AS energy_source_url,e.retrieved_on
                   FROM species AS s
                   JOIN thermochemistry AS t USING(record_id)
                   JOIN materials_project_matches AS m USING(record_id)
                   LEFT JOIN materials_project_energies AS e
                     ON e.record_id=s.record_id AND e.selected_for_comparison=1
                   WHERE s.symbol=?
                   ORDER BY s.record_id,e.calculation_type""",
                (normalized_symbol,),
            )
            result = []
            for row in rows:
                item = dict(row)
                gibbs = row["gibbs_energy_J_mol"]
                experimental = (
                    float(gibbs) / FARADAY_C_MOL / float(row["atom_count"])
                    if gibbs is not None else None
                )
                mp_energy = row["formation_energy_eV_atom"]
                item["experimental_gibbs_eV_atom"] = experimental
                item["mp_minus_experimental_eV_atom"] = (
                    float(mp_energy) - experimental
                    if mp_energy is not None and experimental is not None else None
                )
                result.append(item)
        return tuple(result)

    def materials_project_thermochemistry(
        self, symbol: str | None = None, *, selected_only: bool = False
    ) -> tuple[dict[str, object], ...]:
        """Return phase-matched experimental and MP formation energies."""
        clauses: list[str] = []
        parameters: list[object] = []
        if symbol is not None:
            clauses.append("s.symbol=?")
            parameters.append(self._normalize_symbol(symbol))
        if selected_only:
            clauses.append("e.selected_for_comparison=1")
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        with closing(self._connect()) as connection:
            rows = connection.execute(
                f"""SELECT
                       s.record_id,s.symbol,s.species,s.formula_ascii,s.phase_detail,
                       s.atom_count,t.gibbs_energy_J_mol,t.gibbs_source_id,
                       t.formation_enthalpy_J_mol,t.formation_enthalpy_source_id,
                       m.mp_id,m.spacegroup_symbol,m.spacegroup_number,
                       e.calculation_type,e.selected_for_comparison,
                       e.formation_energy_eV_atom,e.energy_above_hull_eV_atom,
                       e.energy_uncertainty_eV_atom,e.database_version,e.source_url,
                       e.retrieved_on
                   FROM species AS s
                   JOIN thermochemistry AS t USING(record_id)
                   JOIN materials_project_matches AS m USING(record_id)
                   JOIN materials_project_energies AS e USING(record_id,mp_id)
                   {where}
                   ORDER BY s.symbol,s.record_id,e.calculation_type""",
                parameters,
            )
            result: list[dict[str, object]] = []
            for row in rows:
                item = dict(row)
                atoms = float(row["atom_count"])
                for field, output in (
                    ("gibbs_energy_J_mol", "experimental_gibbs_eV_atom"),
                    ("formation_enthalpy_J_mol", "experimental_enthalpy_eV_atom"),
                ):
                    value = row[field]
                    item[output] = (
                        float(value) / FARADAY_C_MOL / atoms
                        if value is not None else None
                    )
                result.append(item)
        return tuple(result)

    def load_system(
        self,
        symbol: str,
        *,
        ligand_ids: Iterable[str] = (),
        energy_policy: GibbsEnergyPolicy | str = GibbsEnergyPolicy.EXPERIMENTAL_ONLY,
    ) -> MetalSystem:
        """Load calculation-ready species for one element."""
        normalized_symbol = self._normalize_symbol(symbol)
        energy_policy = GibbsEnergyPolicy(energy_policy)
        selected_ligands = frozenset(item.strip() for item in ligand_ids)
        if "" in selected_ligands:
            raise ValueError("ligand_ids must not contain empty strings")
        with closing(self._connect()) as connection:
            available_ligands = {
                row["ligand_id"] for row in connection.execute("SELECT ligand_id FROM ligands")
            }
            if unknown := sorted(selected_ligands - available_ligands):
                raise ValueError("No thermodynamic reference is available for: " + ", ".join(unknown))
            rows = list(
                connection.execute(
                    """SELECT
                           s.record_id,s.system,s.symbol,s.species,s.formula_ascii,
                           s.phase,s.phase_detail,s.charge,s.metal_count,
                           s.core_oxygen_count,s.core_hydrogen_count,s.ligand_id,
                           s.ligand_count,s.ligand_charge,s.metal_oxidation_state,
                           s.electron_coefficient_per_metal,
                           t.gibbs_energy_J_mol,t.gibbs_status,t.gibbs_source_id,
                           f.gibbs_energy_J_mol AS fallback_gibbs_energy_J_mol,
                           f.canonical_mp_id AS fallback_mp_id,
                           l.gibbs_energy_J_mol AS ligand_gibbs_energy_J_mol
                       FROM species AS s
                       JOIN thermochemistry AS t USING(record_id)
                       LEFT JOIN computational_fallbacks AS f USING(record_id)
                       LEFT JOIN ligands AS l ON l.ligand_id=s.ligand_id
                       WHERE s.symbol=? ORDER BY s.record_id""",
                    (normalized_symbol,),
                )
            )
        if not rows:
            raise MetalSystemNotFoundError(normalized_symbol)

        included: list[ThermodynamicSpecies] = []
        excluded: list[SpeciesExclusion] = []
        for row in rows:
            use_fallback = (
                row["gibbs_energy_J_mol"] is None
                and energy_policy is GibbsEnergyPolicy.EXPERIMENTAL_THEN_MP
                and row["fallback_gibbs_energy_J_mol"] is not None
            )
            effective_gibbs = (
                row["fallback_gibbs_energy_J_mol"]
                if use_fallback else row["gibbs_energy_J_mol"]
            )
            effective_status = (
                "materials_project_sisso_300K_fallback"
                if use_fallback else row["gibbs_status"]
            )
            effective_source = (
                f"Materials Project {row['fallback_mp_id']}"
                if use_fallback else row["gibbs_source_id"]
            )
            ligand_count = float(row["ligand_count"] or 0.0)
            ligand_id = row["ligand_id"] or None
            if ligand_count and ligand_id not in selected_ligands:
                excluded.append(SpeciesExclusion(row["record_id"], row["species"], "ligand_species_not_selected", row["gibbs_status"]))
                continue
            if ligand_count and row["ligand_gibbs_energy_J_mol"] is None:
                excluded.append(SpeciesExclusion(row["record_id"], row["species"], "ligand_reference_unavailable", row["gibbs_status"]))
                continue
            if effective_gibbs is None:
                excluded.append(SpeciesExclusion(row["record_id"], row["species"], "recommended_gibbs_energy_unavailable", effective_status))
                continue
            included.append(
                ThermodynamicSpecies(
                    record_id=row["record_id"], system=row["system"], symbol=row["symbol"],
                    species=row["species"], formula_ascii=row["formula_ascii"],
                    phase=row["phase"], phase_detail=row["phase_detail"] or "",
                    charge=float(row["charge"]), metal_count=float(row["metal_count"]),
                    core_oxygen_count=float(row["core_oxygen_count"]),
                    core_hydrogen_count=float(row["core_hydrogen_count"]),
                    ligand_id=ligand_id, ligand_count=ligand_count,
                    ligand_charge=float(row["ligand_charge"] or 0.0),
                    formal_metal_oxidation_state=float(row["metal_oxidation_state"]),
                    electron_coefficient_per_metal=float(
                        row["electron_coefficient_per_metal"]
                    ),
                    gibbs_energy_J_mol=float(effective_gibbs),
                    gibbs_status=effective_status, source_id=effective_source,
                    ligand_gibbs_energy_J_mol=(
                        float(row["ligand_gibbs_energy_J_mol"])
                        if row["ligand_gibbs_energy_J_mol"] is not None else None
                    ),
                )
            )
        return MetalSystem(
            system=rows[0]["system"], symbol=normalized_symbol,
            species=tuple(included), excluded=tuple(excluded),
        )
