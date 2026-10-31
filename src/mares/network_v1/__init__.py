"""network_v1: the stand-alone MARES network survey (context sheet, table A contacts, table B communication,
table C groups and connections) -- data model, validation, derived features and the eight standard figures.

A case is a folder ``network_v1/{pilots,cases}/<case_code>/`` with ``data/`` (structured data, metadata,
provenance) and ``graphics/`` (finished figures only). Format: ``mares-network-case/v1``.

Contract: ``docs/architecture/network-v1.md``; versions: ``docs/architecture/network-versions.md``.
Entry point: ``python -m mares.networks v1 ...`` (see :mod:`.cli`).
"""

FORMAT = "mares-network-case/v1"
DATASET_VERSION = "network_v1"
