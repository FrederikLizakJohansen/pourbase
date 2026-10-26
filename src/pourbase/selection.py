"""Selection of recommended values by an editable policy.

Every reported value of a species and property is kept in ``reported_thermochemistry``. A
:class:`SelectionPolicy` decides which of them is recommended: values with ineligible statuses are
dropped, the remaining ones are ranked by evidence class and by family within the class, and ties
are broken by the policy's tie-breaks. Overrides replace the rule for single records, each with a
reason.

The bundled recommendations are the output of the default policy, ``data/selection-policy.toml``.
:func:`with_policy` calculates with any other policy without changing the database, and
:func:`compare_policies` lists every value two policies choose differently.
"""

from __future__ import annotations

import hashlib
import re
import tomllib
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from importlib.resources import files
from pathlib import Path
from typing import Any

from .database import ThermodynamicDatabase
from .models import EvidenceStatus, MetalSystem
from .records import EvaluationLineage

PROPERTIES = ("gibbs_energy_of_formation", "enthalpy_of_formation", "absolute_entropy")
TIE_BREAKS = ("element_consistency", "original_publication", "stated_uncertainty", "recency")
FALLBACK_EXPERIMENTAL = "experimental papers"
FALLBACK_ESTIMATE = "estimates"
SELECTOR_VERSION = "2-explicit-evaluation-lineage"


@dataclass(frozen=True)
class EvidenceClass:
    name: str
    description: str
    families: tuple[str, ...]


@dataclass(frozen=True)
class Override:
    record_id: str
    property_name: str
    source_id: str
    reason: str


@dataclass(frozen=True)
class SelectionPolicy:
    """An ordered rule for choosing recommended values; see ``data/selection-policy.toml``."""

    name: str
    classes: tuple[EvidenceClass, ...]
    family_patterns: tuple[tuple[str, tuple[str, ...]], ...]
    tie_breaks: tuple[str, ...] = TIE_BREAKS
    review_threshold_J_mol: float = 5000.0
    ineligible_statuses: tuple[str, ...] = ("superseded_source_value", "terminal_evidence_gap")
    overrides: tuple[Override, ...] = ()
    exclusions: tuple[Override, ...] = ()
    version: str = ""
    source_text: str = field(default="", repr=False, compare=False)

    def __post_init__(self) -> None:
        unknown = set(self.tie_breaks) - set(TIE_BREAKS)
        if unknown:
            raise ValueError(f"Unknown tie-breaks: {', '.join(sorted(unknown))}")
        listed = [family for item in self.classes for family in item.families]
        if len(listed) != len(set(listed)):
            raise ValueError("A family is listed in more than one class")

    # ---- loading and editing -----------------------------------------------------------------

    @classmethod
    def default(cls) -> SelectionPolicy:
        return cls.from_toml(files("pourbase").joinpath("data", "selection-policy.toml").read_text("utf-8"))

    @classmethod
    def load(cls, path: str | Path) -> SelectionPolicy:
        return cls.from_toml(Path(path).read_text(encoding="utf-8"))

    @classmethod
    def from_toml(cls, text: str) -> SelectionPolicy:
        data = tomllib.loads(text)
        return cls(
            name=str(data.get("name", "unnamed policy")),
            version=str(data.get("version", "")),
            classes=tuple(EvidenceClass(str(item["name"]), str(item.get("description", "")),
                                        tuple(item.get("families", ())))
                          for item in data.get("classes", ())),
            family_patterns=tuple((family, tuple(patterns)) for family, patterns in data.get("families", {}).items()),
            tie_breaks=tuple(data.get("tie_breaks", TIE_BREAKS)),
            review_threshold_J_mol=float(data.get("review_threshold_kJ_mol", 5.0)) * 1000.0,
            ineligible_statuses=tuple(data.get("ineligible_statuses", ("superseded_source_value",
                                                                        "terminal_evidence_gap"))),
            overrides=tuple(Override(str(item["record_id"]), str(item["property"]), str(item["source_id"]),
                                     str(item.get("reason", ""))) for item in data.get("overrides", ())),
            exclusions=tuple(Override(str(item["record_id"]), str(item["property"]), str(item["source_id"]),
                                      str(item.get("reason", ""))) for item in data.get("exclusions", ())),
            source_text=text,
        )

    @property
    def fingerprint(self) -> str:
        """A short hash identifying both policy configuration and selector behavior."""
        text = self.source_text or repr(self)
        return hashlib.sha256((SELECTOR_VERSION + "\n" + text).encode("utf-8")).hexdigest()[:12]

    def with_class_order(self, names: Iterable[str]) -> SelectionPolicy:
        """The same policy with the classes in a new order."""
        by_name = {item.name: item for item in self.classes}
        return replace(self, classes=tuple(by_name[name] for name in names), source_text="")

    def with_family_order(self, class_name: str, families: Iterable[str]) -> SelectionPolicy:
        """The same policy with the families of one class in a new order."""
        classes = tuple(replace(item, families=tuple(families)) if item.name == class_name else item
                        for item in self.classes)
        return replace(self, classes=classes, source_text="")

    def with_override(self, record_id: str, property: str, source_id: str, reason: str) -> SelectionPolicy:
        kept = tuple(item for item in self.overrides if (item.record_id, item.property_name) != (record_id, property))
        return replace(self, overrides=kept + (Override(record_id, property, source_id, reason),), source_text="")

    # ---- classification ----------------------------------------------------------------------

    def family_of(self, citation: str, status: str) -> str:
        for family, patterns in self.family_patterns:
            if any(pattern in citation for pattern in patterns):
                return family
        return FALLBACK_ESTIMATE if status == EvidenceStatus.SOURCE_VERIFIED_ESTIMATE.value else FALLBACK_EXPERIMENTAL

    def rank_of(self, family: str) -> tuple[int, int]:
        """``(class position, family position)``; unknown families rank last."""
        for class_index, item in enumerate(self.classes):
            if family in item.families:
                return class_index, item.families.index(family)
        return len(self.classes), 0

    def class_of(self, family: str) -> str:
        position = self.rank_of(family)[0]
        return self.classes[position].name if position < len(self.classes) else "unclassified"


@dataclass(frozen=True)
class Candidate:
    value_id: str
    record_id: str
    property_name: str
    value: float
    uncertainty: float | None
    status: str
    source_id: str
    citation: str
    family: str
    evidence_class: str
    year: int | None
    evaluation_lineage: EvaluationLineage | None = None


@dataclass(frozen=True)
class Selection:
    """The value a policy recommends for one species and property, and why."""

    record_id: str
    property_name: str
    chosen: Candidate
    candidates: tuple[Candidate, ...]
    basis: str
    needs_review: bool

    @property
    def spread_J_mol(self) -> float:
        values = [item.value for item in self.candidates]
        return max(values) - min(values)


def _year(citation: str) -> int | None:
    years = [int(value) for value in re.findall(r"\((\d{4})\)", citation)] or \
            [int(value) for value in re.findall(r"\b(1[89]\d\d|20\d\d)\b", citation)]
    return years[0] if years else None


def candidates(database: ThermodynamicDatabase, policy: SelectionPolicy,
               properties: Iterable[str] = PROPERTIES) -> dict[tuple[str, str], list[Candidate]]:
    """Eligible reported values grouped by ``(record_id, property)``."""
    wanted = tuple(properties)
    rows = database._rows(
        "SELECT r.value_id, r.record_id, r.property, r.value, r.uncertainty, r.status, r.source_id, "
        "r.source_locator, s.citation FROM reported_thermochemistry AS r JOIN sources AS s USING(source_id) "
        f"WHERE r.value IS NOT NULL AND r.property IN ({','.join('?' * len(wanted))})",
        wanted,
    )
    grouped: dict[tuple[str, str], list[Candidate]] = defaultdict(list)
    lineages = {row["value_id"]: EvaluationLineage.from_locator(row["source_locator"]) for row in rows}
    by_id = {row["value_id"]: row for row in rows}
    # Validate explicit links against evidence, including observations excluded by policy.
    # A linked reprint remains a reprint when its original has an ineligible status.
    for value_id, lineage in lineages.items():
        chain = set()
        current = value_id
        while (current_lineage := lineages[current]) is not None and current_lineage.reprint_of_value_id:
            if current in chain:
                raise ValueError(f"Cyclic evaluation_lineage reprint link at {current}")
            chain.add(current)
            parent = current_lineage.reprint_of_value_id
            if parent not in by_id:
                raise ValueError(f"evaluation_lineage {current} references missing value {parent}")
            target = lineages[parent]
            if target is None or (target.evaluation_id, target.derivation_id) != (
                    current_lineage.evaluation_id, current_lineage.derivation_id) or any(
                    by_id[parent][key] != by_id[current][key] for key in ("record_id", "property")):
                raise ValueError(f"Incompatible evaluation_lineage reprint link from {current} to {parent}")
            current = parent
    excluded = {(item.record_id, item.property_name, item.source_id) for item in policy.exclusions}
    for row in rows:
        if row["status"] in policy.ineligible_statuses or \
                (row["record_id"], row["property"], row["source_id"]) in excluded:
            continue
        family = policy.family_of(row["citation"], row["status"])
        grouped[(row["record_id"], row["property"])].append(Candidate(
            value_id=row["value_id"], record_id=row["record_id"], property_name=row["property"],
            value=float(row["value"]), uncertainty=row["uncertainty"], status=row["status"],
            source_id=row["source_id"], citation=row["citation"], family=family,
            evidence_class=policy.class_of(family), year=_year(row["citation"]),
            evaluation_lineage=lineages[row["value_id"]],
        ))
    return grouped


def select(database: ThermodynamicDatabase, policy: SelectionPolicy | None = None,
           properties: Iterable[str] = PROPERTIES) -> dict[tuple[str, str], Selection]:
    """The recommended value of every species and property under ``policy`` (default policy)."""
    policy = policy or SelectionPolicy.default()
    grouped = candidates(database, policy, properties)
    symbols = {row["record_id"]: row["symbol"] for row in database._rows("SELECT record_id, symbol FROM species")}
    # how many species of each element a family supplies, for the consistency tie-break
    supplies: Counter = Counter()
    for (record_id, _property), items in grouped.items():
        for family in {item.family for item in items}:
            supplies[(symbols.get(record_id), family)] += 1
    overrides = {(item.record_id, item.property_name): item for item in policy.overrides}

    def first_author(item: Candidate) -> str:
        return item.citation.split(",")[0].strip().lower()

    def key(item: Candidate, items: list[Candidate]) -> tuple:
        class_rank, family_rank = policy.rank_of(item.family)
        ties = []
        for name in policy.tie_breaks:
            if name == "element_consistency":
                ties.append(-supplies[(symbols.get(item.record_id), item.family)])
            elif name == "stated_uncertainty":
                ties.append(0 if item.uncertainty is not None else 1)
            elif name == "original_publication":
                lineage = item.evaluation_lineage
                if lineage is not None:
                    # Independent revisions compete in the remaining tie-breaks. Within
                    # one reviewed evaluation/derivation, prefer the original publication.
                    same = [other for other in items if other.family == item.family
                            and other.evaluation_lineage is not None
                            and (other.evaluation_lineage.evaluation_id, other.evaluation_lineage.derivation_id)
                            == (lineage.evaluation_id, lineage.derivation_id)]
                    earlier = any(other.evaluation_lineage.reprint_of_value_id is None
                                  and other.year is not None and (item.year is None or other.year < item.year)
                                  for other in same)
                    ties.append(int(bool(lineage.reprint_of_value_id or earlier)))
                else:
                    # Compatibility stage: retain the historical author/year rule only
                    # between observations whose evaluation lineage is still unreviewed.
                    repeated = any(other is not item and other.family == item.family
                                   and other.evaluation_lineage is None
                                   and first_author(other) == first_author(item) and other.year != item.year
                                   for other in items)
                    ties.append((item.year or 9999) if repeated else 0)
            elif name == "recency":
                ties.append(-(item.year or 0))
        return (class_rank, family_rank, *ties, item.value_id)

    result = {}
    for (record_id, property_name), items in grouped.items():
        override = overrides.get((record_id, property_name))
        chosen = None
        if override is not None:
            chosen = next((item for item in items if item.source_id == override.source_id), None)
            if chosen is None:
                raise ValueError(f"Override for {record_id} {property_name}: no eligible value from "
                                 f"{override.source_id}")
            basis = f"override: {override.reason}"
        else:
            ranked = sorted(items, key=lambda item: key(item, items))
            chosen = ranked[0]
            runner = ranked[1] if len(ranked) > 1 else None
            if runner is None:
                basis = f"only eligible value (class {chosen.evidence_class}, {chosen.family})"
            elif policy.rank_of(chosen.family)[0] != policy.rank_of(runner.family)[0]:
                basis = f"class {chosen.evidence_class} before class {runner.evidence_class}"
            elif chosen.family != runner.family:
                basis = f"class {chosen.evidence_class}: {chosen.family} before {runner.family}"
            else:
                basis = f"class {chosen.evidence_class}, {chosen.family}: tie-break"
        spread = max(item.value for item in items) - min(item.value for item in items)
        threshold = policy.review_threshold_J_mol if property_name != "absolute_entropy" else float("inf")
        result[(record_id, property_name)] = Selection(record_id, property_name, chosen, tuple(items), basis,
                                                       spread > threshold)
    return result


class PolicyDatabase(ThermodynamicDatabase):
    """A database whose recommended values, and so its calculations, follow a selection policy.

    On the bundled or another pourbase file the policy derives every recommended value. On a
    database that adds its own species to another (``with_user_species``), the policy replaces the
    Gibbs energies of the species it covers.
    """

    def __init__(self, base: ThermodynamicDatabase, policy: SelectionPolicy) -> None:
        self.base = base
        self._wraps = type(base) not in (ThermodynamicDatabase, PolicyDatabase) or base._stores_recommendations
        super().__init__(base.path, policy)

    def _load_system_uncached(self, symbol, ligand_ids, energy_policy,
                              include_optional_gases=False) -> MetalSystem:
        if not self._wraps:
            return super()._load_system_uncached(symbol, ligand_ids, energy_policy, include_optional_gases)
        system = self.base._load_system_uncached(symbol, ligand_ids, energy_policy, include_optional_gases)
        chosen = {record_id: item.chosen for (record_id, name), item in self.selections.items()
                  if name == "gibbs_energy_of_formation"}
        species = []
        for item in system.species:
            value = chosen.get(item.record_id)
            if value is None or item.gibbs_status in (EvidenceStatus.DEFINED_REFERENCE_STATE,
                                                      EvidenceStatus.MATERIALS_PROJECT_FALLBACK,
                                                      EvidenceStatus.USER_SUPPLIED):
                species.append(item)
                continue
            status = value.status if value.status in {status.value for status in EvidenceStatus} else item.gibbs_status
            species.append(replace(item, gibbs_energy_J_mol=value.value, source_id=value.source_id,
                                   gibbs_uncertainty_J_mol=value.uncertainty, gibbs_status=status))
        return MetalSystem(system=system.system, symbol=symbol, species=tuple(species), excluded=system.excluded)


def with_policy(database: ThermodynamicDatabase, policy: SelectionPolicy | str | Path) -> PolicyDatabase:
    """``database`` calculating with the Gibbs energies chosen by ``policy`` (a policy or a TOML path)."""
    if not isinstance(policy, SelectionPolicy):
        policy = SelectionPolicy.load(policy)
    return PolicyDatabase(database, policy)


@dataclass(frozen=True)
class PolicyChange:
    record_id: str
    property_name: str
    first: Candidate
    second: Candidate
    second_basis: str

    @property
    def difference_J_mol(self) -> float:
        return self.second.value - self.first.value


def compare_policies(database: ThermodynamicDatabase, first: SelectionPolicy, second: SelectionPolicy,
                     properties: Iterable[str] = PROPERTIES) -> tuple[PolicyChange, ...]:
    """Every species and property for which the two policies choose different values."""
    a, b = select(database, first, properties), select(database, second, properties)
    changes = [
        PolicyChange(key[0], key[1], a[key].chosen, b[key].chosen, b[key].basis)
        for key in sorted(a.keys() & b.keys())
        if a[key].chosen.value_id != b[key].chosen.value_id
    ]
    return tuple(changes)


def stored_selection(database: ThermodynamicDatabase, properties: Iterable[str] = PROPERTIES
                     ) -> dict[tuple[str, str], str]:
    """The value IDs ``database`` recommends: stored in files of schema 7, derived by its policy otherwise."""
    wanted = set(properties)
    if database._stores_recommendations:
        rows = database._evidence_rows(
            "SELECT value_id, record_id, property FROM reported_thermochemistry WHERE selected_as_recommended = 1")
        return {(row["record_id"], row["property"]): row["value_id"] for row in rows if row["property"] in wanted}
    return {key: item.chosen.value_id for key, item in database.selections.items() if key[1] in wanted}


def describe(policy: SelectionPolicy) -> dict[str, Any]:
    """A JSON-serializable summary of a policy for results and reports."""
    return {"name": policy.name, "version": policy.version, "fingerprint": policy.fingerprint,
            "selector_version": SELECTOR_VERSION,
            "classes": [{"name": item.name, "families": list(item.families)} for item in policy.classes],
            "tie_breaks": list(policy.tie_breaks), "review_threshold_kJ_mol": policy.review_threshold_J_mol / 1000,
            "overrides": len(policy.overrides), "exclusions": len(policy.exclusions)}
