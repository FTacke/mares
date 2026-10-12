"""Human-readable reports (Markdown, German) and their JSON counterparts.

The validation report keeps the three kinds apart -- errors, warnings, open research questions --
and states plainly that a technical pass is not a scientific validation.
"""

from __future__ import annotations

from .analysis import REFUSED_METRICS, SurveyStatus, Table
from .model import NetworkDataset, Severity
from .validate import OpenQuestion, ValidationReport

LIMITS = (
    "Die Daten sind manuell aus Fotografien der Erhebungsbögen übertragen und noch nicht gegen die Originaldokumente validiert (Datenqualität: UNREVIEWED).",
    "Die Alter-Alter-Erhebung ist unvollständig. Belegt sind nur Beziehungen, die aus bestätigten Gruppenumrandungen nach der Cliquenregel folgen; alle anderen Paare sind unbekannt, nicht „kennen sich nicht“.",
    "Die Bestätigung von Gruppenumrandungen beruht, soweit im Paket vermerkt, auf einer ausdrücklichen Angabe der Projektseite, nicht auf einer unabhängigen Prüfung der Quelle.",
    "Nähe ist ausschließlich der Tabellenwert 1–5; die Position auf der handgezeichneten Karte und ihre abweichende Legende werden nicht verwendet oder umgerechnet.",
    "Es werden keine Dichte-, Kohäsions-, Segregations- oder Zentralitätsmaße berechnet; solche Aussagen setzen eine vollständige oder explizit modellierte Alter-Alter-Erhebung voraus.",
    "Geografische Kategorien beschreiben den angegebenen Wohnort, nicht die Person; ungefähre Ortsangaben sind nicht präzisiert. Wohn- und Geburtsland können in Kombination reidentifizierend sein.",
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
    lines = ["| ID | Herkunft | Bezug | Feld | Priorität | Stand | Beschreibung | empfohlene Aktion |", "|---|---|---|---|---|---|---|---|"]
    for q in questions:
        state = "offen" if q.state == "open" else "im Paket entschieden"
        lines.append(
            f"| {q.question_id} | {q.origin} | {q.reference} | {q.field} | {q.priority} | {state} | "
            f"{q.description.replace('|', '/')} | {q.action} |"
        )
    return lines


def validation_markdown(dataset: NetworkDataset, report: ValidationReport) -> str:
    counts = f"{len(report.errors)} Fehler · {len(report.warnings)} Warnungen · {report.open_count} offene Forschungsfragen"
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
        "## Offene Forschungsfragen",
        "",
        "Dokumentierte Unsicherheiten über die Quelle. Sie blockieren nichts und werden von der Software nicht entschieden.",
        "",
        *_question_table(report.open_questions),
        "",
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


def validation_dict(report: ValidationReport) -> dict[str, object]:
    return {
        "technical_status": report.technical_status,
        "scientific_validation": "not performed",
        "counts": {
            "errors": len(report.errors),
            "warnings": len(report.warnings),
            "info": len(report.of(Severity.INFO)),
            "open_research_questions": report.open_count,
        },
        "findings": [
            {"severity": f.severity.value, "code": f.code, "subject": f.subject, "message": f.message} for f in report.findings
        ],
        "open_questions": [
            {
                "id": q.question_id, "origin": q.origin, "reference": q.reference, "field": q.field, "priority": q.priority,
                "state": q.state, "description": q.description, "recommended_action": q.action,
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
    tables: tuple[Table, ...],
    outputs: list[dict[str, object]],
) -> str:
    software = record["software"]
    params = record["parameters"]
    lines = [
        f"# Verarbeitungsbericht {record['run_id']}",
        "",
        f"Schritt: `{record['command']}` · Ergebnis: **{record['status']}** · Beginn {record['started_utc']} · Ende {record['finished_utc']}",
        "",
        "## Eingangsdaten",
        "",
        f"Paket: `{record['input']['ref']['root']}:{record['input']['ref']['rel']}` (logische Referenz)",
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
        "## Software und Parameter",
        "",
        f"- mares {software['mares_version']} · Git-Stand: {software['git_commit'] or 'kein Commit vorhanden'}"
        f"{' (Arbeitsverzeichnis mit uncommitteten Änderungen)' if software['git_dirty'] else ''}",
        f"- Python {software['python']} · " + " · ".join(f"{k} {v}" for k, v in software["dependencies"].items()),
        f"- Parameter: Orte der Referenzlokalität = {', '.join(params['local_places'])}; Formate = {', '.join(params['figure_formats'])}; "
        f"Layout-Seed (Gruppenfigur) = {params['layout_seed']}",
        "",
        "## Datenqualitätsstatus",
        "",
        f"- Technische Prüfung: **{report.technical_status}** ({len(report.errors)} Fehler, {len(report.warnings)} Warnungen, "
        f"{report.open_count} offene Forschungsfragen) – Details im Prüfbericht",
        "- Datenqualität (fachlich): `UNREVIEWED` · Freigabe: `NOT_DECIDED` · Erhaltung: `NOT_PRESERVED` · Backup: `NO_COPY`",
        "- Wissenschaftlich validiert: **nein**. Implementierte Änderungen und bestandene technische Prüfungen sind kein Nachweis der Datenrichtigkeit.",
        "",
    ]
    if status is not None:
        lines += [
            "## Netzwerkstatus",
            "",
            f"- {status.structure_note()}",
            f"- Kontakte: {status.contacts} · dokumentierte Beziehungen: {status.documented_ties} · Paare ohne Angabe: {status.pairs_without_statement}",
            f"- Nicht berechnet (bewusst): {', '.join(REFUSED_METRICS)}.",
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
        *[f"{i}. {text}" for i, text in enumerate(LIMITS, 1)],
        "",
    ]
    return "\n".join(lines)
