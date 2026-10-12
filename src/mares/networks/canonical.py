"""Canonical, deterministic serialisation of an imported network (JSON and CSV).

These files are the *normalised* form of what the importer read -- not a correction of it. They are
research data like their source and therefore only ever written below a storage root.
"""

from __future__ import annotations

import csv
import io
import json

from .build import Network
from .model import NetworkDataset

FORMAT = "mares-network-canonical/v0-draft"
BOM = "﻿"


def _csv(header: tuple[str, ...], rows: list[tuple[object, ...]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return BOM + buffer.getvalue()


def dataset_json(dataset: NetworkDataset, network: Network) -> str:
    document = {
        "format": FORMAT,
        "case": {"source_label": dataset.case.source_label, "canonical_case_id": dataset.case.canonical_case_id},
        "session": {
            "session_date": dataset.session.session_date,
            "interview_type": dataset.session.interview_type,
            "package_version": dataset.session.package_version,
        },
        "contacts": [
            {
                "contact_id": c.contact_id,
                "source_block": c.source_block,
                "source_local_id": c.source_local_id,
                "codes": {name: list(parsed.codes) for name, parsed in sorted(c.codes.items())},
                "text": dict(sorted(c.text.items())),
                "review_flags": list(c.review_flags),
            }
            for c in dataset.contacts
        ],
        "groups": [
            {"group_id": g.group_id, "label": g.label, "map_label": g.map_label, "assessment": g.assessment, "comment": g.comment}
            for g in dataset.groups
        ],
        "memberships": [
            {"group_id": m.group_id, "contact_id": m.contact_id, "status": m.status, "source": m.source} for m in dataset.memberships
        ],
        "ties": [
            {"a": t.a, "b": t.b, "state": t.state.value, "basis": t.basis.value, "groups": list(t.group_ids)} for t in network.ties
        ],
        "tie_semantics": "pairs not listed are not recorded (unknown); only an explicit state 'no' means the two do not know each other",
        "source_files": [{"name": f.name, "sha256": f.sha256, "size": f.size} for f in dataset.files],
    }
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def contacts_csv(dataset: NetworkDataset) -> str:
    attributes = sorted({name for c in dataset.contacts for name in (*c.codes, *c.text)})
    rows = []
    for c in dataset.contacts:
        row: list[object] = [c.contact_id, c.source_block, c.source_local_id]
        for name in attributes:
            row.append("|".join(c.code_list(name)) if name in c.codes else c.text.get(name, ""))
        row.append("|".join(c.review_flags))
        rows.append(tuple(row))
    return _csv(("contact_id", "source_block", "source_local_id", *attributes, "review_flags"), rows)


def ties_csv(network: Network) -> str:
    return _csv(
        ("contact_a", "contact_b", "state", "basis", "groups"),
        [(t.a, t.b, t.state.value, t.basis.value, "|".join(t.group_ids)) for t in network.ties],
    )


def memberships_csv(dataset: NetworkDataset) -> str:
    return _csv(
        ("group_id", "contact_id", "status", "source"),
        [(m.group_id, m.contact_id, m.status, m.source) for m in dataset.memberships],
    )
