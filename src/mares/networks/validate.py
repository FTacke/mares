"""Validation of an imported network package.

Three things are kept apart, because they mean different things to the reader and to the pipeline:

* **errors** -- hard violations of the format or of internal consistency. They stop the pipeline:
  the data cannot be used as delivered.
* **warnings** -- usable, but something a reader must know (a missing expected attribute, an
  unresolved origin statement, a review flag without a review item).
* **review hints** -- documented uncertainty about the *source* (``review_items.csv``, review flags on
  contacts, and a few questions only the software can see). Each is in exactly one of four
  categories (:class:`~mares.networks.curation.ReviewCategory`): an open decision-relevant question, a
  documented ambiguity of the source, an accepted imprecision, or resolved. Only the first is "open".
  Hints never block anything and are never decided by the validator: a category comes from the
  curation file (a person's statement) or, failing that, from the package's own recommended action.

Validation is technical. It never sets a data-quality state: a package that passes is
``UNREVIEWED`` until a person has checked it against the original documents.
Deterministic: the same dataset yields the same report in the same order.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from mares.core import ids

from .build import Network, NetworkConstructionError, build_network
from .curation import DOCUMENTATION, ELICITATION, NO_CURATION, Curation, ReviewCategory
from .geo import DEFAULT_LOCAL_PLACES, HOME_COUNTRY, ISO3, BirthStatus, GeoCategory, classify_birth_country, classify_residence
from .identity import canonical_contact_ids, local_number
from .model import CANDIDATE, CONFIRMED, NEEDS_REVIEW, Finding, NetworkDataset, Severity
from .package import CONTACT_COLUMNS

_SEVERITY_ORDER = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.INFO: 2}
_EXPECTED_RULE = "all_pairs_know_each_other"
_EXPECTED_RELATION = "know_each_other"
# Review actions after which the package itself documents a decision; every other action is open.
# Without a curation statement the package's own recommended action is the fallback.
_FALLBACK_CATEGORY = {
    "rule_confirmed": ReviewCategory.RESOLVED,
    "accepted_as_approximate": ReviewCategory.ACCEPTED_IMPRECISION,
}


@dataclass(frozen=True)
class OpenQuestion:
    """A review hint about the source data, with the category it is in now."""

    question_id: str
    origin: str  # ``package`` (review_items.csv) or ``software`` (seen by this module)
    reference: str
    field: str
    priority: str
    description: str
    action: str
    category: ReviewCategory
    affected_contacts: tuple[str, ...] = ()
    decided_by: str = "package"  # ``project_lead``, ``agent_proposal`` or ``package`` (its recommended action)
    basis: str = ""
    note: str = ""

    @property
    def is_open(self) -> bool:
        return self.category.is_open


@dataclass(frozen=True)
class ValidationReport:
    findings: tuple[Finding, ...]
    open_questions: tuple[OpenQuestion, ...]
    completeness: tuple[tuple[str, int, int], ...]  # (attribute, collected, not collected)
    contact_count: int

    def of(self, severity: Severity) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity is severity)

    @property
    def errors(self) -> tuple[Finding, ...]:
        return self.of(Severity.ERROR)

    @property
    def warnings(self) -> tuple[Finding, ...]:
        return self.of(Severity.WARNING)

    @property
    def technical_status(self) -> str:
        if self.errors:
            return "FAILED"
        return "PASSED_WITH_WARNINGS" if self.warnings else "PASSED"

    @property
    def open_count(self) -> int:
        """Open, decision-relevant data questions only: ambiguities, accepted imprecisions and
        resolved hints are not open data errors."""
        return sum(1 for q in self.open_questions if q.is_open)

    def by_category(self) -> dict[ReviewCategory, tuple[OpenQuestion, ...]]:
        return {c: tuple(q for q in self.open_questions if q.category is c) for c in ReviewCategory}


def _add(found: list[Finding], severity: Severity, code: str, subject: str, message: str) -> None:
    found.append(Finding(severity, code, subject, message))


def _contact_findings(dataset: NetworkDataset, local_places: tuple[str, ...], curation: Curation, found: list[Finding]) -> bool:
    """Contact identity, codes and plausibility. Returns whether all contact ids are usable."""
    ids_ok = True
    seen: Counter[str] = Counter(c.contact_id for c in dataset.contacts)
    if not dataset.contacts:
        _add(found, Severity.ERROR, "no_contacts", "contacts.csv", "Die Kontakttabelle enthält keine Kontakte.")
        return False
    for contact in dataset.contacts:
        cid = contact.contact_id
        if not ids.is_contact_id(cid):
            _add(found, Severity.ERROR, "contact_id_format", cid or "(leer)", "Keine gültige kanonische Kontakt-ID (A01, A02, ...).")
            ids_ok = False
        if seen[cid] > 1:
            _add(found, Severity.ERROR, "contact_id_duplicate", cid, f"Kontakt-ID kommt {seen[cid]}-mal vor.")
            ids_ok = False
        if not contact.source_block or local_number(contact.source_local_id) is None:
            _add(found, Severity.ERROR, "source_position_invalid", cid, "Quellblock oder lokale Quell-ID fehlt oder ist ungültig (erwartet: A01, ...).")
            ids_ok = False

    positions = [(c.source_block, c.source_local_id) for c in dataset.contacts]
    if len(set(positions)) != len(positions):
        _add(found, Severity.ERROR, "source_position_duplicate", "contacts.csv", "Dieselbe Kombination aus Blatt und lokaler Nummer kommt mehrfach vor.")
        ids_ok = False
    if ids_ok:
        expected = canonical_contact_ids(positions)
        for contact, canonical in zip(dataset.contacts, expected):
            if contact.contact_id != canonical:
                _add(
                    found, Severity.ERROR, "canonical_id_mismatch", contact.contact_id,
                    f"Kanonische ID passt nicht zur Quellposition (Blatt {contact.source_block}, {contact.source_local_id}); "
                    f"erwartet {canonical}.",
                )
                ids_ok = False
        numbers = sorted(c.number for c in dataset.contacts)
        if ids_ok and numbers != list(range(1, len(numbers) + 1)):
            _add(found, Severity.WARNING, "contact_id_gap", "contacts.csv", "Die kanonischen Kontakt-IDs sind nicht lückenlos fortlaufend.")

    for contact in dataset.contacts:
        cid = contact.contact_id
        for spec in CONTACT_COLUMNS:
            if spec.column not in dataset.contact_columns:
                continue
            if spec.kind == "code":
                parsed = contact.codes.get(spec.attribute)
                codes = () if parsed is None else parsed.codes
                if not codes:
                    if spec.level == "expected":
                        _add(found, Severity.WARNING, "missing_expected", cid, f"{spec.column}: nicht erfasst.")
                    continue
                if not dataset.codebook.has_field(spec.field):
                    _add(found, Severity.ERROR, "codebook_field_missing", cid, f"{spec.column}: das Codebuch kennt kein Feld {spec.field!r}.")
                    continue
                if not spec.multi and len(codes) > 1:
                    _add(found, Severity.ERROR, "multiple_codes_in_single_field", cid, f"{spec.column}: genau ein Code erwartet, {len(codes)} angegeben.")
                for code in codes:
                    if not dataset.codebook.is_valid(spec.field, code):
                        _add(found, Severity.ERROR, "unknown_code", cid, f"{spec.column}: Code {code!r} steht nicht im Codebuch ({spec.field}).")
                if parsed is not None and parsed.duplicates:
                    _add(found, Severity.WARNING, "duplicate_code", cid, f"{spec.column}: Code mehrfach angegeben ({', '.join(parsed.duplicates)}).")
            elif spec.kind == "iso3":
                value = contact.text.get(spec.attribute)
                if value is None:
                    if spec.level == "expected":
                        _add(found, Severity.WARNING, "missing_expected", cid, f"{spec.column}: nicht erfasst.")
                elif value not in ISO3:
                    _add(found, Severity.ERROR, "country_code_invalid", cid, f"{spec.column}: {value!r} ist kein ISO-3166-1-Alpha-3-Code.")
            elif spec.kind == "text" and spec.level == "expected" and spec.attribute not in contact.text:
                _add(found, Severity.WARNING, "missing_expected", cid, f"{spec.column}: nicht erfasst.")

        city, country = contact.text.get("residence_city"), contact.text.get("residence_country")
        if city and country and country != HOME_COUNTRY and city.casefold() in {p.casefold() for p in local_places}:
            _add(found, Severity.WARNING, "place_country_contradiction", cid, "Wohnort und Wohnland passen nicht zusammen.")
        birth = classify_birth_country(contact.text.get("birth_country"), contact.text.get("birth_country_source"))
        if birth.status is BirthStatus.AMBIGUOUS:
            _add(
                found, Severity.INFO, "birth_country_ambiguous", cid,
                "Geburtsland mehrdeutig (die Quelle nennt mehrere Länder): Rohwert erhalten, keines gewählt, nicht als zwei Länder gezählt.",
            )
        elif birth.status is BirthStatus.UNMAPPED:
            _add(found, Severity.WARNING, "birth_country_unmapped", cid, "Geburtsland genannt, aber ohne ISO-Code; nichts wurde ergänzt.")
        residence = classify_residence(city, country, local_places)
        if residence.region_of:
            _add(
                found, Severity.INFO, "residence_region_stated", cid,
                f"Wohnort ist eine regionale Angabe (Bezug: {residence.region_of}); kein konkreter Wohnort wurde ergänzt.",
            )

    review_refs = {item.reference for item in dataset.review_items}
    for contact in dataset.contacts:
        if contact.contact_id in review_refs:
            continue
        for flag in contact.review_flags:
            if curation.disposition(f"flag:{contact.contact_id}:{flag}") is None:
                _add(
                    found, Severity.WARNING, "flag_without_review_item", contact.contact_id,
                    f"Review-Markierung ({flag}) ohne zugehörigen Eintrag in review_items.csv und ohne Kuratierungsangabe.",
                )
    return ids_ok


def _group_findings(dataset: NetworkDataset, found: list[Finding]) -> None:
    group_ids = [g.group_id for g in dataset.groups]
    for group_id, count in Counter(group_ids).items():
        if count > 1:
            _add(found, Severity.ERROR, "group_id_duplicate", group_id, "Gruppen-ID kommt mehrfach vor.")
    groups = {g.group_id: g for g in dataset.groups}
    for group in dataset.groups:
        if group.assessment not in (CONFIRMED, NEEDS_REVIEW):
            _add(found, Severity.ERROR, "group_assessment_unknown", group.group_id, f"Unbekannter Bewertungsstatus {group.assessment!r}.")
    contacts = set(dataset.contact_ids)
    seen: Counter[tuple[str, str]] = Counter()
    for m in dataset.memberships:
        seen[(m.group_id, m.contact_id)] += 1
        if m.group_id not in groups:
            _add(found, Severity.ERROR, "membership_group_unknown", m.group_id, f"Mitgliedschaft von {m.contact_id} verweist auf eine unbekannte Gruppe.")
        if m.contact_id not in contacts:
            _add(found, Severity.ERROR, "membership_contact_unknown", m.group_id, f"Mitgliedschaft verweist auf unbekannten Kontakt {m.contact_id!r}.")
        if m.status not in (CONFIRMED, CANDIDATE):
            _add(found, Severity.ERROR, "membership_status_unknown", m.group_id, f"{m.contact_id}: unbekannter Status {m.status!r}.")
        if m.derivable_edge not in ("yes", "no") or (m.derivable_edge == "yes") != (m.status == CONFIRMED):
            _add(found, Severity.ERROR, "derivable_edge_inconsistent", m.group_id, f"{m.contact_id}: 'derivable_edge' ({m.derivable_edge}) passt nicht zum Status ({m.status}).")
        group = groups.get(m.group_id)
        if group is not None and m.status == CONFIRMED and not group.confirmed:
            _add(found, Severity.ERROR, "confirmed_member_in_unconfirmed_group", m.group_id, f"{m.contact_id}: bestätigte Mitgliedschaft in einer nicht bestätigten Gruppe.")
    for (group_id, contact_id), count in seen.items():
        if count > 1:
            _add(found, Severity.ERROR, "membership_duplicate", group_id, f"{contact_id} ist mehrfach als Mitglied eingetragen.")

    for group in dataset.groups:
        confirmed = [m for m in dataset.memberships if m.group_id == group.group_id and m.status == CONFIRMED]
        if group.confirmed and len(confirmed) < 2:
            _add(found, Severity.WARNING, "group_too_small", group.group_id, f"Bestätigte Gruppe mit {len(confirmed)} bestätigten Mitgliedern erzeugt keine Beziehung.")
        if not any(m.group_id == group.group_id for m in dataset.memberships):
            _add(found, Severity.WARNING, "group_without_members", group.group_id, "Gruppe ohne Mitgliedschaften.")

    for clar in dataset.clarifications:
        group = groups.get(clar.group_id)
        confirmed = {m.contact_id for m in dataset.memberships if m.group_id == clar.group_id and m.status == CONFIRMED}
        if group is None:
            _add(found, Severity.ERROR, "clarification_group_unknown", clar.clarification_id, f"Klärung verweist auf unbekannte Gruppe {clar.group_id!r}.")
            continue
        if set(clar.member_contact_ids) != confirmed:
            _add(found, Severity.ERROR, "clarification_mismatch", clar.clarification_id, f"Die geklärten Mitglieder von {clar.group_id} stimmen nicht mit den bestätigten Mitgliedschaften überein.")
        if clar.relationship_rule != _EXPECTED_RULE:
            _add(found, Severity.WARNING, "clarification_rule_unknown", clar.clarification_id, f"Unbekannte Beziehungsregel {clar.relationship_rule!r}.")
        _add(
            found, Severity.INFO, "group_basis_user_statement", clar.group_id,
            f"Mitgliedschaft laut {clar.clarification_id} ({clar.source_date}): {clar.source_type}, {clar.resolution}. "
            "Grundlage ist eine Angabe der Projektseite, keine unabhängige Prüfung gegen die Originalbögen.",
        )


def _review_findings(dataset: NetworkDataset, found: list[Finding]) -> None:
    for review_id, count in Counter(i.review_id for i in dataset.review_items).items():
        if count > 1:
            _add(found, Severity.ERROR, "review_id_duplicate", review_id, "Review-ID kommt mehrfach vor.")
    known = set(dataset.contact_ids) | {g.group_id for g in dataset.groups} | {"all"}
    for item in dataset.review_items:
        if item.reference not in known:
            _add(found, Severity.WARNING, "review_reference_unknown", item.review_id, f"Verweis {item.reference!r} bezeichnet weder Kontakt noch Gruppe noch 'all'.")


def _network_findings(dataset: NetworkDataset, found: list[Finding]) -> Network | None:
    try:
        network = build_network(dataset)
    except (NetworkConstructionError, ValueError) as error:
        _add(found, Severity.ERROR, "network_not_constructible", "dataset", str(error))
        return None
    derived = {tie.pair: set(tie.group_ids) for tie in network.positive_ties}
    if not dataset.provided_edges:
        _add(found, Severity.INFO, "no_edge_receipt", "observed_edges.csv", "Keine Kantentabelle im Paket; es gibt keinen Importbeleg zum Gegenprüfen.")
        return network
    contacts = set(dataset.contact_ids)
    provided: dict[tuple[str, str], set[str]] = {}
    for edge in dataset.provided_edges:
        subject = f"{edge.source_id}-{edge.target_id}"
        if edge.source_id not in contacts or edge.target_id not in contacts:
            _add(found, Severity.ERROR, "edge_contact_unknown", subject, "Kante verweist auf einen unbekannten Kontakt.")
            continue
        if edge.source_id == edge.target_id:
            _add(found, Severity.ERROR, "self_loop", subject, "Selbstverbindung.")
            continue
        if edge.relation != _EXPECTED_RELATION:
            _add(found, Severity.WARNING, "edge_relation_unknown", subject, f"Unbekannte Beziehungsart {edge.relation!r}.")
        key = tuple(sorted((edge.source_id, edge.target_id), key=ids.contact_number))
        if key in provided:
            _add(found, Severity.ERROR, "duplicate_edge", subject, "Dieselbe ungerichtete Kante kommt mehrfach vor.")
            continue
        provided[key] = set(edge.group_ids)  # type: ignore[index]
    for pair in sorted(set(derived) - set(provided), key=lambda p: (ids.contact_number(p[0]), ids.contact_number(p[1]))):
        _add(found, Severity.ERROR, "edge_receipt_missing", f"{pair[0]}-{pair[1]}", "Aus bestätigten Gruppen ableitbare Kante fehlt in der Kantentabelle.")
    for pair in sorted(set(provided) - set(derived), key=lambda p: (ids.contact_number(p[0]), ids.contact_number(p[1]))):
        _add(found, Severity.ERROR, "edge_not_derivable", f"{pair[0]}-{pair[1]}", "Kante der Kantentabelle folgt nicht aus bestätigten Gruppen; sie wird nicht übernommen.")
    for pair in sorted(set(derived) & set(provided), key=lambda p: (ids.contact_number(p[0]), ids.contact_number(p[1]))):
        if derived[pair] != provided[pair]:
            _add(found, Severity.ERROR, "edge_origin_mismatch", f"{pair[0]}-{pair[1]}", "Gruppenzugehörigkeit der Kante weicht von der Ableitung ab.")
    expected = dataset.manifest.get("edge_count_from_unambiguous_groups")
    if isinstance(expected, int) and expected != len(derived):
        _add(found, Severity.ERROR, "edge_count_mismatch", "manifest.json", f"Manifest nennt {expected} Kanten, abgeleitet wurden {len(derived)}.")
    return network


def _package_findings(dataset: NetworkDataset, found: list[Finding]) -> None:
    actual = {f.name: f.sha256 for f in dataset.files}
    if not dataset.listed_checksums:
        _add(found, Severity.WARNING, "no_checksums", "SHA256SUMS.txt", "Keine Prüfsummenliste im Paket; Integrität der Lieferung nicht gegenprüfbar.")
    for name, digest in sorted(dataset.listed_checksums.items()):
        if name not in actual:
            _add(found, Severity.ERROR, "checksum_file_missing", name, "In der Prüfsummenliste, aber nicht im Paket.")
        elif actual[name] != digest:
            _add(found, Severity.ERROR, "checksum_mismatch", name, "SHA-256 stimmt nicht mit der Prüfsummenliste überein.")
    if dataset.listed_checksums:
        for name in sorted(set(actual) - set(dataset.listed_checksums) - {"SHA256SUMS.txt"}):
            _add(found, Severity.WARNING, "file_not_in_checksums", name, "Datei ist nicht in der Prüfsummenliste aufgeführt.")

    manifest_label = dataset.manifest.get("source_case_label")
    if manifest_label is not None and manifest_label != dataset.case.source_label:
        _add(found, Severity.ERROR, "case_label_mismatch", "manifest.json", "Quellkennung des Manifests und der Kontakttabelle weichen ab.")
    count = dataset.manifest.get("contact_count")
    if isinstance(count, int) and count != len(dataset.contacts):
        _add(found, Severity.ERROR, "contact_count_mismatch", "manifest.json", f"Manifest nennt {count} Kontakte, gelesen wurden {len(dataset.contacts)}.")
    if dataset.case.canonical_case_id is None:
        _add(found, Severity.INFO, "case_id_unassigned", dataset.case.source_label, "Keine kanonische Fall-ID zugeordnet; die Quellkennung ist keine Fall-ID.")
    if "review_items.csv" not in {f.name for f in dataset.files}:
        _add(found, Severity.WARNING, "no_review_items", "review_items.csv", "Keine Review-Liste im Paket; offene Fragen sind nicht dokumentiert.")


def _completeness(dataset: NetworkDataset) -> tuple[tuple[str, int, int], ...]:
    rows = []
    for spec in CONTACT_COLUMNS:
        if spec.column not in dataset.contact_columns or spec.kind == "flags":
            continue
        filled = sum(
            1
            for c in dataset.contacts
            if (spec.attribute in c.text if spec.kind in ("text", "iso3") else bool(c.code_list(spec.attribute)))
        )
        rows.append((spec.attribute, filled, len(dataset.contacts) - filled))
    return tuple(rows)


def _open_questions(dataset: NetworkDataset, curation: Curation) -> tuple[OpenQuestion, ...]:
    contacts = set(dataset.contact_ids)
    questions: list[OpenQuestion] = []

    def categorised(ref: str, fallback: ReviewCategory) -> tuple[ReviewCategory, str, str, str]:
        item = curation.disposition(ref)
        if item is None:
            return fallback, "package", "", ""
        return item.category, item.decided_by, item.basis, item.note

    for item in dataset.review_items:
        affected = (item.reference,) if item.reference in contacts else ()
        category, decided_by, basis, note = categorised(
            item.review_id, _FALLBACK_CATEGORY.get(item.recommended_action, ReviewCategory.OPEN_DECISION)
        )
        questions.append(
            OpenQuestion(item.review_id, "package", item.reference, item.field, item.priority, item.description,
                         item.recommended_action, category, affected, decided_by, basis, note)
        )
    # Review flags on a contact that has no review item of its own: their category comes from the curation.
    review_refs = {item.reference for item in dataset.review_items}
    for contact in dataset.contacts:
        if contact.contact_id in review_refs:
            continue
        for flag in contact.review_flags:
            ref = f"flag:{contact.contact_id}:{flag}"
            if curation.disposition(ref) is not None:
                category, decided_by, basis, note = categorised(ref, ReviewCategory.OPEN_DECISION)
                questions.append(
                    OpenQuestion(f"FLAG-{contact.contact_id}", "package", contact.contact_id, flag, "low",
                                 f"Review-Markierung {flag} ohne eigenen Review-Eintrag.", "none", category,
                                 (contact.contact_id,), decided_by, basis, note)
                )
    # Questions only this software can see: they concern identity and provenance, not contact data.
    label = dataset.case.source_label
    if dataset.case.canonical_case_id is None:
        questions.append(
            OpenQuestion("SW-01", "software", label, "case_id", "high",
                         "Kanonische Fall-ID nicht zugeordnet; Verknüpfung mit einer früheren Erhebung desselben Falls offen (Register fehlt).",
                         "register_case", ReviewCategory.OPEN_DECISION)
        )
    questions.append(
        OpenQuestion("SW-02", "software", label, "provenance", "medium",
                     "Kohorte, Lehrveranstaltung, Erhebende (Pseudonym) und Instrument-Version sind im Paket nicht belegt; formale Provenienz erst mit der Registrierung.",
                     "register_provenance", ReviewCategory.OPEN_DECISION)
    )
    questions.append(
        OpenQuestion("SW-03", "software", label, "source_validation", "high",
                     "Manuell aus Fotografien übertragen und noch nicht gegen die Originalbögen geprüft; Datenqualität bleibt UNREVIEWED.",
                     "source_check", ReviewCategory.OPEN_DECISION)
    )
    return tuple(questions)


def _curation_findings(dataset: NetworkDataset, curation: Curation, found: list[Finding]) -> None:
    if curation is NO_CURATION:
        return
    if curation.source_label != dataset.case.source_label:
        _add(found, Severity.ERROR, "curation_label_mismatch", "curation",
             "Die Kuratierungsdatei gehört zu einer anderen Quellkennung als das Paket.")
    version = dataset.session.package_version
    if curation.applies_to_package_version and version and curation.applies_to_package_version != version:
        _add(found, Severity.WARNING, "curation_version_mismatch", "curation",
             f"Die Kuratierung bezieht sich auf Paketversion {curation.applies_to_package_version}, gelesen wurde {version}.")
    review_ids = {i.review_id for i in dataset.review_items}
    flags = {(c.contact_id, f) for c in dataset.contacts for f in c.review_flags}
    for disposition in curation.dispositions:
        flag = disposition.flag
        known = (flag in flags) if flag else (disposition.ref in review_ids)
        if not known:
            _add(found, Severity.WARNING, "curation_ref_unknown", disposition.ref,
                 "Kuratierungsangabe verweist auf einen Review-Eintrag oder eine Markierung, die das Paket nicht enthält.")
    method = curation.survey
    if method.stated:
        _add(found, Severity.INFO, "survey_method", "curation",
             f"Alter-Alter-Beziehungen: {ELICITATION[method.elicitation]}; dokumentiert als {DOCUMENTATION[method.documentation]}. "
             f"Grundlage: {method.basis}")
        if not method.coverage_complete:
            _add(found, Severity.INFO, "pair_coverage_not_established", "curation",
                 "Die vollständige Abdeckung aller Kontaktpaare ist nicht belegt; Paare ohne Angabe bleiben unbekannt.")


def validate(
    dataset: NetworkDataset,
    *,
    local_places: tuple[str, ...] = DEFAULT_LOCAL_PLACES,
    curation: Curation = NO_CURATION,
) -> ValidationReport:
    found: list[Finding] = list(dataset.import_findings)
    _package_findings(dataset, found)
    _curation_findings(dataset, curation, found)
    ids_ok = _contact_findings(dataset, local_places, curation, found)
    _group_findings(dataset, found)
    _review_findings(dataset, found)
    if ids_ok:
        _network_findings(dataset, found)
    found.sort(key=lambda f: (_SEVERITY_ORDER[f.severity], f.code, f.subject, f.message))
    return ValidationReport(tuple(found), _open_questions(dataset, curation), _completeness(dataset), len(dataset.contacts))
