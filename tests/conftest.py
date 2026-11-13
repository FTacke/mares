"""Shared test setup: tests never reach the network (AGENTS.md rule 12)."""

import pytest


@pytest.fixture(autouse=True)
def _no_geonames_download(monkeypatch):
    def refuse(iso2, target):
        raise RuntimeError(f"no network in tests (GeoNames {iso2})")

    monkeypatch.setattr("mares.network_v1.gazetteer.FETCH", refuse)
