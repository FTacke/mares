"""Human-readable reports (Markdown, German) and their JSON/CSV counterparts.

The validation report keeps the kinds apart -- errors, warnings, and review hints in their four categories
-- and states plainly that a technical pass is not a scientific validation.
"""

from __future__ import annotations

import csv
import io

from .analysis import REFUSED_METRICS, SurveyStatus, Table
from .curation import CATEGORY_LABELS, DOCUMENTATION, ELICITATION, Curation, ReviewCategory
from .model import NetworkDataset, Severity
from .validate import OpenQuestion, ValidationReport

_DECIDERS = {"project_lead": "Projektleitung", "agent_proposal": "Vorschlag des Agenten (zu bestätigen)", "package": "Paket (empfohlene Aktion)"}


def limits(status: SurveyStatus | None) -> tuple[str, ...]:
    """The known methodological limits of a run, stated for its survey status."""
    if status is None:
        relation = "Der Erhebungsstatus der Alter-Alter-Beziehungen ist nicht bestimmt."
    elif status.completeness == "complete":
        relation = (
            "Die Erhebung deckt alle Kontaktpaare ab; fehlende Paare gelten als verneint. Strukturmaße beschreiben einen "
            "einzelnen, nicht zufällig gezogenen persönlichen Fall und tragen keine Verallgemeinerung."
        )
    elif status.elicitation == "asked_per_pair":
        relation = (
            "Die Alter-Alter-Beziehungen wurden laut Projektleitung im Interview erfragt und in der Netzwerkkarte durch "
            "Gruppenumrandungen zusammenfassend dokumentiert. Belegt sind die bestätigten Beziehungen; dass jedes Kontaktpaar "
            "erfasst wurde, ist nicht belegt. Paare ohne Angabe sind unbekannt, nicht „kennen sich nicht“."
        )
    else:
        relation = (
            "Erhebungsmethode der Alter-Alter-Beziehungen nicht angegeben. Belegt sind nur Beziehungen aus bestätigten "
            "Gruppen (Cliquenregel); Paare ohne Angabe sind unbekannt, nicht „kennen sich nicht“."
        )
    structure = (
        "Dichte, Kohäsion, Segregation und Zentralitäten werden nicht berechnet, solange die Paarabdeckung nicht belegt ist."
        if status is None or status.completeness != "complete"
        else "Strukturmaße sind explorativ-deskriptiv und beziehen sich auf diesen einen Fall."
    )
    return (
        "Die Daten sind manuell aus Fotografien der Erhebungsbögen übertragen und noch nicht gegen die Originaldokumente validiert (Datenqualität: UNREVIEWED).",
        relation,
        "Die Bestätigung von Gruppenumrandungen beruht, soweit im Paket oder in der Kuratierung vermerkt, auf einer ausdrücklichen Angabe der Projektseite, nicht auf einer unabhängigen Prüfung der Quelle.",
        "Nähe ist ausschließlich der Tabellenwert 1–5; die Position auf der handgezeichneten Karte und ihre abweichende Legende werden nicht verwendet oder umgerechnet.",
        structure,
        "Geografische Kategorien beschreiben den angegebenen Wohnort, nicht die Person; regionale und mehrdeutige Angaben sind nicht präzisiert. Wohn- und Geburtsland können in Kombination reidentifizierend sein.",
        "Handschriftliche Ergänzungen der Originalbögen lagen der Verarbeitung nicht vor; was das Paket nicht dokumentiert, wurde nicht ergänzt.",
        "Die Ergebnisse liegen im Arbeitsbereich (WORKSPACE) und sind regenerierbar; sie sind weder erhalten noch gesichert, solange PRIMARY und BACKUP nicht eingerichtet und verifiziert sind.",
        "Die studentische Herkunft der Erhebung bleibt Teil der Provenienz, auch nach professioneller Nachbearbeitung; weder Freigabe noch Fall-Registrierung liegen vor.",
    )


def _finding_lines(report: ValidationReport, severity: Severity) -> list[str]:
    items = report.of(severity)
    if not items:
        return ["– keine –"]
    return [f"- `{f.code}` · **{f.subject}**: {f.message}" for f in items]


def _question_table(questions: tuple[OpenQuestion, ...]) -> list[str]:
    if not questions:
        return ["– keine –"]
    lines = ["| ID | Bezug | Feld | Beschreibung (Paket) | Entscheidung / Begründung |", "|---|---|---|---|---|"]
    for q in questions:
        decision = f"{_DECIDERS.get(q.decided_by, q.decided_by)}"
        if q.basis:
            decision += f": {q.basis}"
        if q.note:
            decision += f" – {q.note}"
        lines.append(
            f"| {q.question_id} | {q.reference} | {q.field} | {q.description.replace('|', '/')} | {decision.replace('|', '/')} |"
        )
    return lines


_SECTION_TITLES = {
    ReviewCategory.OPEN_DECISION: ("Offene, entscheidungsrelevante Datenfragen", "Hier steht eine Entscheidung aus. Sie blockiert die Verarbeitung nicht."),
    ReviewCategory.DOCUMENTED_AMBIGUITY: ("Dokumentierte Mehrdeutigkeiten der Quelle", "Der Rohwert ist erhalten und nicht aufgelöst. Kein offener Datenfehler."),
    ReviewCategory.ACCEPTED_IMPRECISION: ("Akzeptierte Unschärfen der Erhebung", "Die Unschärfe ist bekannt und akzeptiert. Kein offener Datenfehler."),
    ReviewCategory.RESOLVED: ("Geklärte beziehungsweise abgeschlossene Hinweise", "Erledigt; zur Nachvollziehbarkeit aufgeführt."),
}


def validation_markdown(dataset: NetworkDataset, report: ValidationReport) -> str:
    groups = report.by_category()
    counts = (
        f"{len(report.errors)} Fehler · {len(report.warnings)} Warnungen · {report.open_count} offene Datenfragen "
        f"(daneben {len(groups[ReviewCategory.DOCUMENTED_AMBIGUITY])} dokumentierte Mehrdeutigkeiten, "
        f"{len(groups[ReviewCategory.ACCEPTED_IMPRECISION])} akzeptierte Unschärfen, {len(groups[ReviewCategory.RESOLVED])} geklärte Hinweise)"
    )
    lines = [
        f"# Prüfbericht – Quelle {dataset.case.source_label}",
        "",
        f"**Technischer Prüfstatus: {report.technical_status}** ({counts})",
        "",
        "Der technische Prüfstatus sagt nur, dass das Paket formal und intern widerspruchsfrei ist. Er ist **keine wissenschaftliche "
        "Validierung**; die Datenqualität bleibt `UNREVIEWED`, bis eine Person die Daten gegen die Originalbögen geprüft hat.",
        "",
        f"Kontakte: {report.contact_count} · Paketversion: {dataset.session.package_version or 'nicht angegeben'}",
        "",
        "## Harte Fehler",
        "",
        *_finding_lines(report, Severity.ERROR),
        "",
        "## Warnungen",
        "",
        *_finding_lines(report, Severity.WARNING),
        "",
        "## Hinweise",
        "",
        *_finding_lines(report, Severity.INFO),
        "",
        "# Prüfhinweise nach Kategorie",
        "",
        "Jeder Hinweis steht in genau einer Kategorie. Nur die erste ist eine offene Datenfrage; die Software entscheidet keinen "
        "Hinweis, die Kategorie stammt aus der Kuratierung (Aussage einer Person) oder der empfohlenen Aktion des Pakets.",
        "",
    ]
    for category, (title, remark) in _SECTION_TITLES.items():
        lines += [f"## {title} ({len(groups[category])})", "", remark, "", *_question_table(groups[category]), ""]
    lines += [
        "## Vollständigkeit der Attribute",
        "",
        "| Attribut | erfasst | nicht erfasst |",
        "|---|---|---|",
        *[f"| {name} | {filled} | {missing} |" for name, filled, missing in report.completeness],
        "",
        "„Nicht erfasst“ ist ein leeres Feld der Quelle; es wurde nichts ergänzt.",
        "",
    ]
    return "\n".join(lines)


def review_register_csv(report: ValidationReport) -> str:
    """The revised review register: every hint with its category, decision and basis (UTF-8 with BOM, ``;``)."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
    writer.writerow(("id", "origin", "reference", "field", "priority", "category", "category_de", "decided_by", "basis", "note", "description"))
    for q in report.open_questions:
        writer.writerow((q.question_id, q.origin, q.reference, q.field, q.priority, q.category.value, CATEGORY_LABELS[q.category],
                         q.decided_by, q.basis, q.note, q.description))
    return "﻿" + buffer.getvalue()


def validation_dict(report: ValidationReport) -> dict[str, object]:
    groups = report.by_category()
    return {
        "technical_status": report.technical_status,
        "scientific_validation": "not performed",
        "counts": {
            "errors": len(report.errors),
            "warnings": len(report.warnings),
            "info": len(report.of(Severity.INFO)),
            "open_data_questions": report.open_count,
            "by_category": {c.value: len(q) for c, q in groups.items()},
        },
        "findings": [
            {"severity": f.severity.value, "code": f.code, "subject": f.subject, "message": f.message} for f in report.findings
        ],
        "review_hints": [
            {
                "id": q.question_id, "origin": q.origin, "reference": q.reference, "field": q.field, "priority": q.priority,
                "category": q.category.value, "decided_by": q.decided_by, "basis": q.basis, "note": q.note,
                "description": q.description, "recommended_action": q.action,
            }
            for q in report.open_questions
        ],
        "completeness": [{"attribute": a, "collected": c, "not_collected": m} for a, c, m in report.completeness],
    }


def processing_markdown(
    *,
    record: dict[str, object],
    dataset: NetworkDataset,
    report: ValidationReport,
    status: SurveyStatus | None,
    curation: Curation,
    tables: tuple[Table, ...],
    outputs: list[dict[str, object]],
) -> str:
    software = record["software"]
    params = record["parameters"]
    groups = report.by_category()
    curation_line = (
        f"Kuratierung: `{record['input']['curation']['ref']['root']}:{record['input']['curation']['ref']['rel']}` "
        f"(SHA-256 `{curation.sha256}`; vom {curation.made_on}, {curation.made_by})"
        if record["input"].get("curation")
        else "Kuratierung: keine – alle Prüfhinweise nach der empfohlenen Aktion des Pakets, Erhebungsmethode nicht angegeben."
    )
    lines = [
        f"# Verarbeitungsbericht {record['run_id']}",
        "",
        f"Schritt: `{record['command']}` · Ergebnis: **{record['status']}** · Beginn {record['started_utc']} · Ende {record['finished_utc']}",
        "",
        "## Eingangsdaten",
        "",
        f"Paket: `{record['input']['ref']['root']}:{record['input']['ref']['rel']}` (logische Referenz)",
        "",
        curation_line,
        "",
        "| Datei | SHA-256 | Bytes |",
        "|---|---|---|",
        *[f"| {f['name']} | `{f['sha256']}` | {f['size']} |" for f in record["input"]["files"]],
        "",
        "## Quelle und Identität",
        "",
        f"- Quellkennung: `{dataset.case.source_label}` – historische Kennung der Erhebung, **keine** Fall-ID",
        f"- Kanonische Fall-ID: {dataset.case.canonical_case_id or 'nicht zugeordnet (kein Register); Verknüpfung mit früherer Erhebung offen'}",
        f"- Sitzung: {dataset.session.session_date or 'nicht angegeben'} · Erhebungsart laut Paket: {dataset.session.interview_type or 'nicht angegeben'}",
        "- Provenienz: studentische Erhebung laut Paket; Kohorte, Erhebende, Instrument-Version nicht belegt (Registrierung offen). Die Herkunft bleibt erhalten.",
        f"- Paketversion: {dataset.session.package_version or 'nicht angegeben'}",
        "",
        "## Erhebung der Alter-Alter-Beziehungen",
        "",
        f"- Erhebungsmethode: {ELICITATION[curation.survey.elicitation]}",
        f"- Dokumentationsform: {DOCUMENTATION[curation.survey.documentation]}",
        f"- Regel: {'alle Mitglieder derselben bestätigten Gruppe kennen sich gegenseitig' if curation.survey.group_rule else 'nicht angegeben'}",
        f"- Paarabdeckung: {'alle Paare erfasst' if curation.survey.coverage_complete else 'nicht belegt'}",
        f"- Grundlage: {curation.survey.basis or 'keine Kuratierung'}",
        "",
        "## Software und Parameter",
        "",
        f"- mares {software['mares_version']} · Git-Stand: {software['git_commit'] or 'kein Commit vorhanden'}"
        f"{' (Arbeitsverzeichnis mit uncommitteten Änderungen)' if software['git_dirty'] else ''}",
        f"- Python {software['python']} · " + " · ".join(f"{k} {v}" for k, v in software["dependencies"].items()),
        f"- Parameter: Orte der Referenzlokalität = {', '.join(params['local_places'])}; Formate = {', '.join(params['figure_formats'])}; "
        f"Layout-Seed (Netzwerkfigur) = {params['layout_seed']}; Layout = {params['network_layout']}; Ego-Layout (B3) = {params['ego_layout']}",
        "",
        "## Datenqualitätsstatus",
        "",
        f"- Technische Prüfung: **{report.technical_status}** ({len(report.errors)} Fehler, {len(report.warnings)} Warnungen) – Details im Prüfbericht",
        f"- Prüfhinweise: {report.open_count} offene Datenfragen · {len(groups[ReviewCategory.DOCUMENTED_AMBIGUITY])} dokumentierte Mehrdeutigkeiten · "
        f"{len(groups[ReviewCategory.ACCEPTED_IMPRECISION])} akzeptierte Unschärfen · {len(groups[ReviewCategory.RESOLVED])} geklärt",
        "- Datenqualität (fachlich): `UNREVIEWED` · Freigabe: `NOT_DECIDED` · Erhaltung: `NOT_PRESERVED` · Backup: `NO_COPY`",
        "- Wissenschaftlich validiert: **nein**. Implementierte Änderungen und bestandene technische Prüfungen sind kein Nachweis der Datenrichtigkeit.",
        "",
    ]
    if status is not None:
        lines += [
            "## Netzwerkstatus",
            "",
            f"- {status.structure_note()}",
            f"- Kontakte: {status.contacts} · bestätigte Beziehungen: {status.documented_ties} · ausdrücklich verneinte Paare: {status.denied_pairs} · "
            f"Paare ohne Angabe: {status.pairs_without_statement}",
            (
                "- Strukturmaße: berechnet (explorativ, Einzelfall)."
                if status.completeness == "complete"
                else f"- Nicht berechnet (bewusst, Paarabdeckung nicht belegt): {', '.join(REFUSED_METRICS)}."
            ),
            "",
        ]
    if tables:
        lines += ["## Deskriptive Tabellen", ""]
        for table in tables:
            lines += [table.to_markdown(), ""]
    lines += [
        "## Erzeugte Dateien",
        "",
        "Ablage im Arbeitsbereich (`WORKSPACE`), logische Referenzen relativ zum Run-Ordner. Der `run_record.json` listet sie mit SHA-256 und ist selbst nicht darin enthalten.",
        "",
        "| Datei | SHA-256 | Bytes |",
        "|---|---|---|",
        *[f"| {o['rel']} | `{o['sha256']}` | {o['size']} |" for o in outputs],
        "",
        "## Bekannte methodische Grenzen",
        "",
        *[f"{i}. {text}" for i, text in enumerate(limits(status), 1)],
        "",
    ]
    return "\n".join(lines)
