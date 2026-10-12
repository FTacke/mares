"""Descriptive analysis of one network dataset.

Exploratory and descriptive only: counts and distributions of what was recorded. Every structural
statement carries the survey and completeness status (:class:`SurveyStatus`).

**Deliberately not computed**: density, cohesion, segregation, centralities, component statistics.
They are not interpretable while the alter-alter survey is incomplete -- a pair without a
statement is unknown, not absent (``docs/architecture/network-module.md`` §5). ``REFUSED_METRICS``
lists them so that a report can say so instead of staying silent.
"""

from __future__ import annotations

import csv
import io
from collections import Counter
from dataclasses import dataclass

from mares.core.model import QualityState

from .build import Network
from .geo import DEFAULT_LOCAL_PLACES, GeoCategory, Residence, classify_residence
from .model import Contact, NetworkDataset, TieState

REFUSED_METRICS = (
    "Netzwerkdichte",
    "Kohäsionsmaße",
    "Segregations- und Homophiliemaße",
    "Zentralitäten und Komponentenstatistiken",
)

_GEO_LABELS = {
    GeoCategory.GERMANY_OTHER: "übriges Deutschland",
    GeoCategory.ABROAD: "außerhalb Deutschlands",
    GeoCategory.UNKNOWN: "Wohnort unbekannt",
}


def geo_labels(params: "AnalysisParams") -> dict[GeoCategory, str]:
    """Category labels; the local category is named after the places configured as local."""
    return {GeoCategory.LOCAL: " / ".join(params.local_places), **_GEO_LABELS}


@dataclass(frozen=True)
class AnalysisParams:
    """Every parameter that influences a result; recorded in the run record."""

    local_places: tuple[str, ...] = DEFAULT_LOCAL_PLACES

    def to_dict(self) -> dict[str, object]:
        return {"local_places": list(self.local_places)}


@dataclass(frozen=True)
class SurveyStatus:
    """What kind of data a structural statement rests on."""

    source_label: str
    session_date: str | None
    interview_type: str | None
    package_version: str | None
    alter_alter: str  # ``partial_clique_derived`` | ``none`` | ``explicit_complete``
    completeness: str  # ``partial_unknown_not_absent`` | ``complete``
    quality_state: QualityState
    contacts: int
    documented_ties: int
    pairs_without_statement: int

    def stamp(self) -> str:
        """The one-line status printed into every figure."""
        parts = [f"Quelle {self.source_label}"]
        if self.session_date:
            parts.append(f"Sitzung {self.session_date}")
        if self.interview_type:
            parts.append(self.interview_type)
        parts.append(f"n = {self.contacts} Kontakte")
        parts.append(f"Datenqualität: {self.quality_state.value}")
        return " · ".join(parts)

    def structure_note(self) -> str:
        if self.completeness == "complete":
            return "Alter-Alter-Beziehungen vollständig erhoben."
        if self.alter_alter == "none":
            return "Alter-Alter-Beziehungen nicht erhoben; alle Paare unbekannt."
        return (
            f"Alter-Alter-Erhebung unvollständig: {self.documented_ties} Beziehungen aus bestätigten Gruppenumrandungen "
            f"belegt; {self.pairs_without_statement} Paare ohne Angabe sind unbekannt, nicht „kennen sich nicht“."
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "source_label": self.source_label,
            "session_date": self.session_date,
            "interview_type": self.interview_type,
            "package_version": self.package_version,
            "alter_alter_survey": self.alter_alter,
            "completeness": self.completeness,
            "data_quality_state": self.quality_state.value,
            "contacts": self.contacts,
            "documented_ties": self.documented_ties,
            "pairs_without_statement": self.pairs_without_statement,
            "refused_metrics": list(REFUSED_METRICS),
        }


def survey_status(dataset: NetworkDataset, network: Network) -> SurveyStatus:
    counts = network.pair_counts()
    if network.is_complete():
        scope, completeness = "explicit_complete", "complete"
    elif network.ties:
        scope, completeness = "partial_clique_derived", "partial_unknown_not_absent"
    else:
        scope, completeness = "none", "partial_unknown_not_absent"
    return SurveyStatus(
        source_label=dataset.case.source_label,
        session_date=dataset.session.session_date,
        interview_type=dataset.session.interview_type,
        package_version=dataset.session.package_version,
        alter_alter=scope,
        completeness=completeness,
        # Never set by software: a person's review is what changes it.
        quality_state=QualityState.UNREVIEWED,
        contacts=len(dataset.contacts),
        documented_ties=counts[TieState.YES],
        pairs_without_statement=counts[TieState.NOT_RECORDED],
    )


@dataclass(frozen=True)
class Table:
    key: str
    title: str
    columns: tuple[str, ...]
    rows: tuple[tuple[object, ...], ...]
    note: str = ""

    def to_csv(self) -> str:
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
        writer.writerow(self.columns)
        writer.writerows(self.rows)
        return "﻿" + buffer.getvalue()

    def to_markdown(self) -> str:
        lines = [f"**{self.title}**", ""]
        lines.append("| " + " | ".join(self.columns) + " |")
        lines.append("|" + "|".join("---" for _ in self.columns) + "|")
        for row in self.rows:
            lines.append("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |")
        if self.note:
            lines += ["", f"*{self.note}*"]
        return "\n".join(lines)


def residence_of(contact: Contact, params: AnalysisParams) -> Residence:
    return classify_residence(contact.text.get("residence_city"), contact.text.get("residence_country"), params.local_places)


def attribute_counts(dataset: NetworkDataset, attribute: str, codebook_field: str) -> tuple[list[tuple[str, str, int]], int]:
    """``(code, meaning, number of contacts)`` for every code of the codebook field -- also those
    nobody named, so that an empty category stays visible -- and the number of contacts for whom
    the attribute was not collected. A contact with several codes is counted once for each."""
    counter: Counter[str] = Counter()
    missing = 0
    for contact in dataset.contacts:
        codes = contact.code_list(attribute)
        if not codes:
            missing += 1
        counter.update(codes)
    rows = [(code, dataset.codebook.meaning(codebook_field, code), counter.get(code, 0)) for code in dataset.codebook.codes(codebook_field)]
    return rows, missing


CODED_TABLES = (
    ("relation", "relation", "Beziehungstyp", True),
    ("contact_frequency", "contact_frequency", "Kontakthäufigkeit", False),
    ("closeness", "closeness_1_5", "Nähe (Tabellenwert 1–5)", False),
    ("media", "media", "Kommunikationsmedien", True),
    ("language", "language", "Verwendete Sprachen", True),
    ("language_mode", "language_mode", "Typischer Sprachmodus", False),
    ("function", "function", "Funktionen", True),
    ("name_generator", "name_generator", "Namensgenerator", True),
)


def language_combinations(dataset: NetworkDataset) -> list[tuple[tuple[str, ...], list[str]]]:
    """Which exact sets of languages occur, with the contacts that have each set.

    Contacts without a language statement are left out; no 'main language' is derived."""
    groups: dict[tuple[str, ...], list[str]] = {}
    order = {code: index for index, code in enumerate(dataset.codebook.codes("language"))}
    for contact in dataset.contacts:
        codes = tuple(sorted(contact.code_list("language"), key=lambda c: order.get(c, 10**6)))
        if codes:
            groups.setdefault(codes, []).append(contact.contact_id)
    return sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))


def descriptive_tables(dataset: NetworkDataset, network: Network, params: AnalysisParams) -> tuple[Table, ...]:
    status = survey_status(dataset, network)
    n = len(dataset.contacts)
    tables: list[Table] = []

    tables.append(
        Table(
            "overview",
            "Überblick",
            ("Merkmal", "Wert"),
            (
                ("Quellkennung (keine Fall-ID)", status.source_label),
                ("Kanonische Fall-ID", dataset.case.canonical_case_id or "nicht zugeordnet"),
                ("Sitzung", status.session_date or "nicht angegeben"),
                ("Erhebungsart laut Paket", status.interview_type or "nicht angegeben"),
                ("Paketversion", status.package_version or "nicht angegeben"),
                ("Kontakte", n),
                ("Dokumentierte Beziehungen (ja)", status.documented_ties),
                ("Paare ohne Angabe (unbekannt)", status.pairs_without_statement),
                ("Bestätigte Gruppen", len(network.confirmed_groups)),
                ("Alter-Alter-Erhebung", status.alter_alter),
                ("Vollständigkeit", status.completeness),
                ("Datenqualität", status.quality_state.value),
            ),
            status.structure_note(),
        )
    )

    for attribute, field_name, title, multi in CODED_TABLES:
        if not dataset.codebook.has_field(field_name):
            continue
        rows, missing = attribute_counts(dataset, attribute, field_name)
        note = "Mehrfachnennungen möglich; die Summe kann n übersteigen." if multi else ""
        tables.append(
            Table(
                f"dist_{attribute}",
                title,
                ("Code", "Bedeutung", "Kontakte"),
                tuple(rows) + (("–", "nicht erfasst", missing),),
                note,
            )
        )

    places: Counter[tuple[str, str]] = Counter()
    categories: Counter[GeoCategory] = Counter()
    for contact in dataset.contacts:
        residence = residence_of(contact, params)
        categories[residence.category] += 1
        places[(residence.city or "nicht erfasst", residence.country or "–")] += 1
    tables.append(
        Table(
            "residence_places",
            "Aufenthaltsorte (Wohnort der Kontakte)",
            ("Wohnort", "Wohnland (ISO3)", "Kontakte"),
            tuple((city, country, count) for (city, country), count in sorted(places.items(), key=lambda kv: (-kv[1], kv[0]))),
            "Angaben wie erhoben; ungefähre Angaben (Review-Markierung) sind nicht präzisiert.",
        )
    )
    tables.append(
        Table(
            "geo_category",
            "Geografische Einordnung des Wohnorts",
            ("Kategorie", "Kontakte"),
            tuple((geo_labels(params)[category], categories.get(category, 0)) for category in GeoCategory),
            f"Regel: „Marburg“ nur bei exakt benanntem Ort ({', '.join(params.local_places)}); beschreibt den Wohnort, nicht die Person.",
        )
    )
    crosstab: Counter[tuple[str, str]] = Counter()
    for contact in dataset.contacts:
        crosstab[(contact.text.get("residence_country", "–"), contact.text.get("birth_country", "–"))] += 1
    tables.append(
        Table(
            "residence_by_birth_country",
            "Wohnland × Geburtsland (Angabe der Quelle)",
            ("Wohnland (ISO3)", "Geburtsland (ISO3)", "Kontakte"),
            tuple((res, birth, count) for (res, birth), count in sorted(crosstab.items())),
            "„–“ = nicht erfasst oder nicht eindeutig. Keine Zuschreibung von Herkunftsgruppen.",
        )
    )

    combos = language_combinations(dataset)
    tables.append(
        Table(
            "language_combinations",
            "Sprachrepertoires der Kontakte (exakte Kombinationen)",
            ("Sprachen", "Kontakte"),
            tuple(
                (" + ".join(dataset.codebook.meaning("language", code) for code in codes), len(members))
                for codes, members in combos
            ),
            "Mehrsprachige Angaben bleiben Kombinationen; es wird keine Hauptsprache abgeleitet.",
        )
    )

    group_rows = []
    for group in dataset.groups:
        members = dict(network.confirmed_groups).get(group.group_id) or dict(network.unconfirmed_groups).get(group.group_id, ())
        implied = sum(1 for tie in network.positive_ties if group.group_id in tie.group_ids)
        group_rows.append((group.group_id, group.assessment, len(members), implied))
    tables.append(
        Table(
            "groups",
            "Dokumentierte Kontaktgruppen",
            ("Gruppe", "Bewertung", "Mitglieder", "Beziehungen (aus dieser Gruppe)"),
            tuple(group_rows),
            "Überlappende Gruppen teilen Beziehungen; jede Beziehung zählt in jeder Gruppe, die sie impliziert.",
        )
    )
    memberships = Counter(len(network.groups_of(contact_id)) for contact_id in network.contact_ids)
    tables.append(
        Table(
            "group_memberships_per_contact",
            "Zugehörigkeit zu bestätigten Gruppen",
            ("Anzahl bestätigter Gruppen", "Kontakte"),
            tuple((count, memberships[count]) for count in range(0, max(memberships, default=0) + 1)),
            "„Keine Gruppe“ heißt: nicht in einer bestätigten Umrandung – nicht: ohne Beziehungen.",
        )
    )
    multi = [(cid, "|".join(network.groups_of(cid))) for cid in network.contact_ids if len(network.groups_of(cid)) > 1]
    tables.append(Table("multi_group_contacts", "Kontakte in mehreren bestätigten Gruppen", ("Kontakt", "Gruppen"), tuple(multi)))
    counts = network.pair_counts()
    tables.append(
        Table(
            "ties_documented",
            "Belegte Beziehungen und Paare ohne Angabe",
            ("Zustand", "Paare"),
            (
                ("ja (dokumentiert)", counts[TieState.YES]),
                ("nein (ausdrücklich)", counts[TieState.NO]),
                ("unbekannt (gefragt, weiß nicht)", counts[TieState.UNKNOWN]),
                ("nicht erhoben / keine Angabe", counts[TieState.NOT_RECORDED]),
                ("alle möglichen Paare", network.pair_total),
            ),
            status.structure_note() + " Keine Dichte: Die Zahlen sind Zählungen des Belegten, kein Maß der Vernetzung.",
        )
    )
    return tuple(tables)
