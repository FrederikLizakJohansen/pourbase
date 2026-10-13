"""The publications behind a calculation, grouped one entry per publication, as text or BibTeX.

Source records of one publication carry citations written in different ways and with
value-specific notes, so they are grouped by DOI where one is given and by first-author surname
and year otherwise.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

DOI = re.compile(r"10\.\d{4,9}/[^\s,;]+", re.I)
NOTES = re.compile(r"printed ?p|PDF ?p|Table ?\d|row |column |licen[cs]e|acknowledged|lineage|locator|digiti[sz]ation",
                   re.I)


def doi_of(text: str | None) -> str | None:
    match = DOI.search(text or "")
    if not match:
        return None
    value = match.group(0).rstrip(".")
    while value.endswith(")") and value.count(")") > value.count("("):
        value = value[:-1]
    return value.rstrip(".").lower()


def _plain(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def publication_key(citation: str, url: str | None = None) -> tuple[str, str]:
    """``(group key, label)`` of the publication behind one source record."""
    head = re.split(r"[,;.(]", citation.strip())[0].split()
    surname = re.sub(r"[^a-z]", "", _plain(head[0] if head else "source")) or "source"
    years = re.findall(r"\b(1[89]\d\d|20\d\d)\b", citation)
    label = f"{surname}{years[0] if years else ''}"
    if citation.lower().startswith("explicit estimate"):
        return "estimate:" + citation, "estimate"
    for text in (url or "", citation):
        doi = doi_of(text)
        if doi:
            return "doi:" + doi, label
    return "name:" + label, label


def representative(citations: list[str]) -> str:
    """The cleanest of the citations of one publication: no locator or licence notes, then the shortest."""
    full = [text for text in citations if len(text) > 40]
    candidates = [text for text in full if not NOTES.search(text)] or full or citations
    return min(candidates, key=len)


@dataclass
class Publication:
    key: str
    label: str
    citations: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    species: list[str] = field(default_factory=list)

    @property
    def citation(self) -> str:
        return representative(self.citations)

    @property
    def doi(self) -> str | None:
        return next((doi_of(text) for text in (*self.urls, *self.citations) if doi_of(text)), None)

    @property
    def year(self) -> str | None:
        years = re.findall(r"\b(1[89]\d\d|20\d\d)\b", self.citation)
        return years[0] if years else None

    @property
    def url(self) -> str | None:
        return next((url for url in self.urls if "doi.org" in url), self.urls[0] if self.urls else None)


def group_sources(sources) -> list[Publication]:
    """Publications from ``(source reference, species name)`` pairs, one entry per publication."""
    groups: dict[str, Publication] = {}
    for source, species in sources:
        if source is None:
            continue
        citation = source.citation or source.source_id
        key, label = publication_key(citation, source.url)
        entry = groups.setdefault(key, Publication(key, label))
        if citation not in entry.citations:
            entry.citations.append(citation)
        if source.url and source.url not in entry.urls:
            entry.urls.append(source.url)
        if species not in entry.species:
            entry.species.append(species)
    publications = sorted(groups.values(), key=lambda item: _plain(item.citation))
    labels: dict[str, int] = {}
    for item in publications:
        count = labels.get(item.label, 0)
        labels[item.label] = count + 1
        if count:
            item.label = f"{item.label}{chr(ord('a') + count)}"
    return publications


def _bibtex_escape(text: str) -> str:
    return text.replace("\\", "\\textbackslash{}").replace("{", "\\{").replace("}", "\\}").replace("&", "\\&") \
        .replace("%", "\\%").replace("#", "\\#").replace("_", "\\_")


def to_bibtex(publications: list[Publication]) -> str:
    """BibTeX entries; the full citation is kept as a note, with the year, DOI and URL where known."""
    entries = []
    for item in publications:
        fields = [f"  note = {{{_bibtex_escape(item.citation)}}}"]
        if item.year:
            fields.append(f"  year = {{{item.year}}}")
        if item.doi:
            fields.append(f"  doi = {{{item.doi}}}")
        if item.url:
            fields.append(f"  url = {{{item.url}}}")
        fields.append(f"  keywords = {{pourbase; {_bibtex_escape(', '.join(item.species))}}}")
        entries.append(f"@misc{{{item.label},\n" + ",\n".join(fields) + "\n}")
    return "\n\n".join(entries) + "\n"


def to_text(publications: list[Publication]) -> str:
    return "\n".join(f"[{index}] {item.citation}" + (f" {item.url}" if item.url else "")
                     + f"  (used for: {', '.join(item.species)})"
                     for index, item in enumerate(publications, start=1)) + "\n"


def diagram_sources(calculation) -> list[Publication]:
    """The publications of the Gibbs energies of every species in a calculation, and of its ligands."""
    database = calculation.database
    pairs = []
    for item in calculation.diagram.system.species:
        pairs.append((database.source(item.source_id), item.species))
    for ligand in calculation.scenario.ligands:
        reference = next((ref for ref in database.available_ligands() if ref.ligand_id == ligand.ligand_id), None)
        if reference is not None:
            pairs.append((database.source(reference.source_id) or _reference_source(reference), reference.name))
    return group_sources(pairs)


def _reference_source(reference):
    from .records import SourceReference

    return SourceReference(reference.source_id, reference.source_citation, reference.source_url, None)
