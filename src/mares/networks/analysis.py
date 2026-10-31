"""Descriptive analysis of one network dataset.

Exploratory and descriptive only: counts and distributions of what was recorded. Every structural
statement carries the survey status (:class:`SurveyStatus`): how the alter-alter relations were
obtained, how they are documented, and whether *every* pair was covered.

Structural measures (density, components, degree) are computed **only if the survey states that every
pair was covered** -- then a missing pair is a denial and the numbers mean something. Otherwise a
pair without a statement is unknown, not absent, and ``REFUSED_METRICS`` says what was not computed
and why. Even then the result describes one case and is exploratory.
"""

from __future__ import annotations

import csv
import io
from collections import Counter
from dataclasses import dataclass

from mares.core.model import QualityState

from .build import Network
from .curation import ELICITATION, DOCUMENTATION, NO_CURATION, Curation
from .geo import (
    DEFAULT_LOCAL_PLACES,
    BirthCountry,
    BirthStatus,
    GeoCategory,
    Residence,
    classify_birth_country,
    classify_residence,
)
from .model import Contact, NetworkDataset, TieState

REFUSED_METRICS = (
    "Netzwerkdichte",
    "Kohäsionsmaße",
    "Segregations- und Homophiliemaße",
    "Zentralitäten und Komponentenstatistiken",
)  # not computed while the pair coverage is not established

_GEO_LABELS = {
    GeoCategory.LOCAL_REGION: "Region {local} (ungefähre Angabe)",
    GeoCategory.GERMANY_OTHER: "übriges Deutschland",
    GeoCategory.EUROPE_OTHER: "übriges Europa",
    GeoCategory.OUTSIDE_EUROPE: "außerhalb Europas",
    GeoCategory.UNKNOWN: "Wohnort nicht zuordenbar",
}


def geo_labels(params: "AnalysisParams") -> dict[GeoCategory, str]:
    """Category labels; the local category is named after the places configured as local."""
    local = " / ".join(params.local_places)
    labels = {category: label.format(local=local) for category, label in _GEO_LABELS.items()}
    return {GeoCategory.LOCAL: local, **labels}


BIRTH_LABELS = {
    BirthStatus.AMBIGUOUS: "mehrdeutig",
    BirthStatus.UNMAPPED: "nicht kodiert",
    BirthStatus.MISSING: "–",
}


def birth_label(birth: BirthCountry) -> str:
    """How a birth country is shown in tables and figures: its ISO code, or the name of its status.
    An ambiguous statement is never turned into one country, and never counted as two."""
    return birth.iso3 if birth.status is BirthStatus.CODED and birth.iso3 else BIRTH_LABELS[birth.status]


def place_label(residence: Residence) -> str:
    """How a residence is named in tables and figures. A regional statement is normalised to
    "Region X" and stays regional: no concrete place of residence is invented."""
    if residence.region_of:
        return f"Region {residence.region_of}"
    return residence.city or "Ort nicht erfasst"


def birth_of(contact: Contact) -> BirthCountry:
    return classify_birth_country(contact.text.get("birth_country"), contact.text.get("birth_country_source"))


@dataclass(frozen=True)
class AnalysisParams:
    """Every parameter that influences a result; recorded in the run record."""

    local_places: tuple[str, ...] = DEFAULT_LOCAL_PLACES

    def to_dict(self) -> dict[str, object]:
        return {"local_places": list(self.local_places)}


@dataclass(frozen=True)
class SurveyStatus:
    """What kind of data a structural statement rests on.

    ``elicitation`` (what the explorator did) and ``documentation`` (how it was written down) are
    separate; ``pair_coverage`` says whether every pair was covered, which alone decides whether a
    missing pair may count as denied.
    """

    source_label: str
    session_date: str | None
    interview_type: str | None
    package_version: str | None
    elicitation: str  # key of curation.ELICITATION
    documentation: str  # key of curation.DOCUMENTATION
    pair_coverage: str  # ``not_established`` | ``complete``
    completeness: str  # ``partial_unknown_not_absent`` | ``complete``
    quality_state: QualityState
    contacts: int
    pairs_total: int
    documented_ties: int  # pairs with a positive statement
    denied_pairs: int  # pairs explicitly denied (asked, or covered by a complete survey)
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
            return (
                f"Alle {self.pairs_total} Paare sind erfasst: {self.documented_ties} Beziehungen bestehen, "
                f"für {self.denied_pairs} Paare ist sie ausdrücklich verneint."
            )
        if self.documented_ties == 0:
            return f"Keine Alter-Alter-Beziehung dokumentiert; alle {self.pairs_without_statement} Paare sind unbekannt."
        unknown = (
            f"Ob jedes der {self.pairs_total} Paare erfasst wurde, ist nicht belegt: {self.pairs_without_statement} Paare "
            "ohne Angabe bleiben unbekannt, nicht „kennen sich nicht“."
        )
        if self.elicitation == "asked_per_pair":
            return (
                f"Die Alter-Alter-Beziehungen wurden im Interview erfragt und als Gruppenumrandungen dokumentiert "
                f"({self.documented_ties} bestätigte Beziehungen). {unknown}"
            )
        return (
            f"Erhebungsmethode nicht angegeben; {self.documented_ties} Beziehungen aus bestätigten Gruppen "
            f"(Cliquenregel). {unknown}"
        )

    def short_note(self) -> str:
        """For a figure's footnote: the relation status in one sentence."""
        if self.completeness == "complete":
            return "Alle Paare sind erfasst; nicht genannte Paare gelten als ausdrücklich verneint."
        return (
            f"Für die übrigen {self.pairs_without_statement} Paare liegt keine Angabe vor: unbekannt, nicht „kennen sich nicht“; "
            "dass jedes Paar erfasst wurde, ist nicht belegt."
            if self.pair_coverage != "complete"
            else "Für die übrigen Paare liegt keine Angabe vor."
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "source_label": self.source_label,
            "session_date": self.session_date,
            "interview_type": self.interview_type,
            "package_version": self.package_version,
            "alter_alter_elicitation": self.elicitation,
            "alter_alter_documentation": self.documentation,
            "pair_coverage": self.pair_coverage,
            "completeness": self.completeness,
            "data_quality_state": self.quality_state.value,
            "contacts": self.contacts,
            "pairs_total": self.pairs_total,
            "documented_ties": self.documented_ties,
            "denied_pairs": self.denied_pairs,
            "pairs_without_statement": self.pairs_without_statement,
            "structural_metrics_computed": self.completeness == "complete",
            "refused_metrics": [] if self.completeness == "complete" else list(REFUSED_METRICS),
        }


def survey_status(dataset: NetworkDataset, network: Network, curation: Curation = NO_CURATION) -> SurveyStatus:
    counts = network.pair_counts()
    return SurveyStatus(
        source_label=dataset.case.source_label,
        session_date=dataset.session.session_date,
        interview_type=dataset.session.interview_type,
        package_version=dataset.session.package_version,
        elicitation=curation.survey.elicitation,
        documentation=curation.survey.documentation,
        pair_coverage="complete" if network.coverage_complete else "not_established",
        completeness="complete" if network.is_complete() else "partial_unknown_not_absent",
        # Never set by software: a person's review is what changes it.
        quality_state=QualityState.UNREVIEWED,
        contacts=len(dataset.contacts),
        pairs_total=network.pair_total,
        documented_ties=counts[TieState.YES],
        denied_pairs=counts[TieState.NO],
        pairs_without_statement=counts[TieState.NOT_RECORDED] + counts[TieState.UNKNOWN],
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


def descriptive_tables(
    dataset: NetworkDataset, network: Network, params: AnalysisParams, curation: Curation = NO_CURATION
) -> tuple[Table, ...]:
    status = survey_status(dataset, network, curation)
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
                ("Bestätigte Beziehungen (ja)", status.documented_ties),
                ("Ausdrücklich verneinte Paare (nein)", status.denied_pairs),
                ("Paare ohne Angabe (unbekannt)", status.pairs_without_statement),
                ("Bestätigte Gruppen", len(network.confirmed_groups)),
                ("Erhebung der Alter-Alter-Beziehungen", ELICITATION[status.elicitation]),
                ("Dokumentationsform", DOCUMENTATION[status.documentation]),
                ("Paarabdeckung", "alle Paare erfasst" if status.pair_coverage == "complete" else "nicht belegt"),
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
        places[(place_label(residence), residence.country or "–")] += 1
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
            f"Regel: „Marburg“ nur bei exakt benanntem Ort ({', '.join(params.local_places)}); „Europa“ geografisch nach dem UN-Geoschema (nicht EU-Mitgliedschaft); "
            "ohne verwendbares Land wird nicht geraten. Beschreibt den Wohnort, nicht die Person und nicht ihre biografische Bedeutung.",
        )
    )
    crosstab: Counter[tuple[str, str]] = Counter()
    birth_status: Counter[BirthStatus] = Counter()
    for contact in dataset.contacts:
        birth = birth_of(contact)
        birth_status[birth.status] += 1
        crosstab[(contact.text.get("residence_country", "–"), birth_label(birth))] += 1
    tables.append(
        Table(
            "residence_by_birth_country",
            "Wohnland × Geburtsland (Angabe der Quelle)",
            ("Wohnland (ISO3)", "Geburtsland (ISO3)", "Kontakte"),
            tuple((res, birth, count) for (res, birth), count in sorted(crosstab.items())),
            "„mehrdeutig“ = die Quelle nennt mehrere Länder; der Rohwert bleibt erhalten, es wird weder eines gewählt noch "
            "werden zwei gezählt. „–“ = nicht erfasst. Keine Zuschreibung von Herkunftsgruppen.",
        )
    )
    tables.append(
        Table(
            "birth_country_status",
            "Geburtsland: Status der Angabe",
            ("Status", "Kontakte"),
            (
                ("eindeutig kodiert", birth_status.get(BirthStatus.CODED, 0)),
                ("mehrdeutig (mehrere Länder genannt)", birth_status.get(BirthStatus.AMBIGUOUS, 0)),
                ("genannt, aber nicht kodiert", birth_status.get(BirthStatus.UNMAPPED, 0)),
                ("nicht erfasst", birth_status.get(BirthStatus.MISSING, 0)),
            ),
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
                ("nein (ausdrücklich verneint)", counts[TieState.NO]),
                ("unbekannt (gefragt, weiß nicht)", counts[TieState.UNKNOWN]),
                ("nicht erhoben / keine Angabe", counts[TieState.NOT_RECORDED]),
                ("alle möglichen Paare", network.pair_total),
            ),
            status.structure_note() + (
                "" if status.completeness == "complete" else " Keine Dichte: Die Zahlen sind Zählungen des Belegten, kein Maß der Vernetzung."
            ),
        )
    )
    if network.is_complete():
        tables.append(structure_table(network))
    return tuple(tables)


def structure_table(network: Network) -> Table:
    """Structural measures. Only meaningful -- and therefore only produced -- if every pair was covered.

    Exploratory: they describe this one personal network and support no generalisation.
    """
    positive = network.positive_ties
    n = len(network.contact_ids)
    neighbours: dict[str, set[str]] = {c: set() for c in network.contact_ids}
    for tie in positive:
        neighbours[tie.a].add(tie.b)
        neighbours[tie.b].add(tie.a)
    seen: set[str] = set()
    sizes = []
    for start in network.contact_ids:
        if start in seen:
            continue
        stack, size = [start], 0
        seen.add(start)
        while stack:
            node = stack.pop()
            size += 1
            for other in sorted(neighbours[node]):
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
        sizes.append(size)
    degrees = [len(v) for v in neighbours.values()]
    return Table(
        "structure",
        "Strukturmaße (explorativ, nur bei vollständiger Paarabdeckung)",
        ("Maß", "Wert"),
        (
            ("Kontakte", n),
            ("Beziehungen (ja)", len(positive)),
            ("Mögliche Paare", network.pair_total),
            ("Dichte (Beziehungen / mögliche Paare)", f"{len(positive) / network.pair_total:.3f}" if network.pair_total else "–"),
            ("Komponenten", len(sizes)),
            ("Größen der Komponenten", " · ".join(str(s) for s in sorted(sizes, reverse=True))),
            ("Kontakte ohne Beziehung", sum(1 for d in degrees if d == 0)),
            ("Mittlerer Grad", f"{sum(degrees) / n:.2f}" if n else "–"),
            ("Höchster Grad", max(degrees, default=0)),
        ),
        "Beschreibung eines Einzelfalls; keine Verallgemeinerung, keine Inferenz. Gilt nur, weil die Erhebung alle Paare abdeckt.",
    )
