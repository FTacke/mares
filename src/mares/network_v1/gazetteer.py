"""Automatic completion of the place directory of X1 from GeoNames (ADR-0028).

Before a case is drawn, every recorded residence (place + ISO3 country) that is not yet in
``ROOT:network_v1/reference/gazetteer.csv`` is looked up in the GeoNames country dump of its country and, if the match is
unambiguous, appended to the directory. Nothing is guessed and no place name leaves the machine:

* the dumps (``https://download.geonames.org/export/dump/<ISO2>.zip``, CC BY 4.0) are fetched once per country into the
  regenerable cache ``WORKSPACE:cache/geonames/``; the request names only the country code;
* the lookup is local: populated places (feature class P, not historical, abandoned or a section of another place) whose
  name, ASCII name or -- if none matches -- alternate name equals the recorded place (``places.norm``); only if no
  populated place matches, a municipality (ADM3/ADM4) of that name;
* several candidates count as one place if all lie within 40 km of the most populous one, or if the most populous one
  has at least 1,000 inhabitants and ten times as many as any namesake (Bremen the city, not a hamlet of that name);
  otherwise the place is ambiguous and stays out (reported, never chosen);
* regional statements ("Nähe München"), entries without a country and countries the basemap cannot map stay out;
* existing rows are never changed; new rows carry the GeoNames id and the dump date in ``basis``, ``group_with`` empty.

A missing dump that cannot be fetched (no network) is reported; X1 then names the place as not drawable, as before.
"""

from __future__ import annotations

import csv
import io
import math
import urllib.request
import zipfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, Iterable

from .figures.maps import GAZETTEER_COLUMNS
from .places import _REGIONAL, norm

GEONAMES_URL = "https://download.geonames.org/export/dump/{iso2}.zip"
GEONAMES_CACHE = "cache/geonames"  # in WORKSPACE
EXCLUDED_CODES = {"PPLX", "PPLH", "PPLQ", "PPLW", "PPLCH"}  # section of a place, historical, abandoned, destroyed
SAME_PLACE_KM = 40.0
DOMINANT_MIN, DOMINANT_RATIO = 1000, 10  # a far namesake does not compete with a place this much larger
MUNICIPALITY_CODES = {"ADM3", "ADM4"}


@dataclass
class Completion:
    added: list[dict] = field(default_factory=list)  # place, country_iso3, lat, lon, geonameid
    ambiguous: list[dict] = field(default_factory=list)  # place, country_iso3, candidates
    not_found: list[dict] = field(default_factory=list)  # place, country_iso3
    skipped: list[dict] = field(default_factory=list)  # place, country_iso3, reason
    fetch_errors: list[dict] = field(default_factory=list)  # iso2, error

    def to_dict(self) -> dict:
        return {"source": "GeoNames (CC BY 4.0), lokale Länderdateien", "added": self.added, "ambiguous": self.ambiguous,
                "not_found": self.not_found, "skipped": self.skipped, "fetch_errors": self.fetch_errors}


def fetch_dump(iso2: str, target: Path) -> None:
    """Download and unpack ``<ISO2>.txt``; the request carries only the country code."""
    with urllib.request.urlopen(GEONAMES_URL.format(iso2=iso2), timeout=120) as response:  # noqa: S310 (fixed https URL)
        data = response.read()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        text = archive.read(f"{iso2}.txt")
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".part")
    partial.write_bytes(text)
    partial.replace(target)


FETCH: Callable[[str, Path], None] = fetch_dump  # the tests replace it (tests/conftest.py): never a network call there


def _km(a: tuple[float, float], b: tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def _candidates(dump: Path, wanted: set[str]) -> dict[str, tuple[list[dict], list[dict], list[dict]]]:
    """norm(name) -> (populated places by name/ASCII name, populated places by alternate name, municipalities by name)."""
    out: dict[str, tuple[list[dict], list[dict], list[dict]]] = {w: ([], [], []) for w in wanted}
    with dump.open(encoding="utf-8") as handle:
        for line in handle:
            cols = line.rstrip("\n").split("\t")
            if len(cols) < 15:
                continue
            populated = cols[6] == "P" and cols[7] not in EXCLUDED_CODES
            municipality = cols[6] == "A" and cols[7] in MUNICIPALITY_CODES
            if not (populated or municipality):
                continue
            row = {"geonameid": cols[0], "name": cols[1], "code": cols[7], "lat": float(cols[4]), "lon": float(cols[5]),
                   "population": int(cols[14] or 0)}
            primary = {norm(cols[1]), norm(cols[2])} & wanted
            if municipality:
                for key in primary:
                    out[key][2].append(row)
                continue
            for key in primary:
                out[key][0].append(row)
            for key in ({norm(a) for a in cols[3].split(",") if a} & wanted) - primary:
                out[key][1].append(row)
    return out


def _decide(rows: list[dict]) -> dict | None:
    """One place: all candidates within SAME_PLACE_KM of the most populous one, or that one clearly dominant."""
    if not rows:
        return None
    ranked = sorted(rows, key=lambda r: (-r["population"], int(r["geonameid"])))
    top = ranked[0]
    if all(_km((r["lat"], r["lon"]), (top["lat"], top["lon"])) <= SAME_PLACE_KM for r in rows):
        return top
    if top["population"] >= DOMINANT_MIN and top["population"] >= DOMINANT_RATIO * ranked[1]["population"]:
        return top
    return None


def complete_gazetteer(
    gazetteer_path: Path,
    residences: Iterable[tuple[str | None, str | None]],
    countries: dict[str, dict],
    cache_dir: Path,
    *,
    fetch: Callable[[str, Path], None] | None = None,
    today: Callable[[], date] = date.today,
) -> Completion:
    """Append unambiguous GeoNames matches for every recorded residence missing from the directory."""
    from .figures.maps import read_gazetteer

    result = Completion()
    known = read_gazetteer(gazetteer_path)
    todo: dict[tuple[str, str], str] = {}  # (norm place, ISO3) -> place as recorded
    for place, iso3 in residences:
        place, iso3 = (place or "").strip(), (iso3 or "").strip().upper()
        if not place:
            continue
        entry = {"place": place, "country_iso3": iso3}
        if not iso3:
            result.skipped.append(entry | {"reason": "kein Wohnland codiert"})
        elif _REGIONAL.search(place):
            result.skipped.append(entry | {"reason": "regionale Angabe, kein Ort"})
        elif (norm(place), iso3) not in known:
            todo.setdefault((norm(place), iso3), place)
    by_country: dict[str, list[tuple[str, str]]] = {}
    for key in todo:
        by_country.setdefault(key[1], []).append(key)
    new_rows = []
    for iso3, keys in sorted(by_country.items()):
        props = countries.get(iso3, {}).get("properties", {})
        iso2 = props.get("ISO_A2_EH") or props.get("ISO_A2")
        if not iso2 or iso2 == "-99":
            result.skipped += [{"place": todo[k], "country_iso3": iso3, "reason": "Land ohne ISO-2-Code in der Basiskarte"} for k in keys]
            continue
        dump = cache_dir / f"{iso2}.txt"
        if not dump.is_file():
            try:
                (fetch or FETCH)(iso2, dump)
            except Exception as error:  # network or archive problem: an explicit, reported state
                result.fetch_errors.append({"iso2": iso2, "error": str(error)})
                result.not_found += [{"place": todo[k], "country_iso3": iso3} for k in keys]
                continue
        stamp = date.fromtimestamp(dump.stat().st_mtime).isoformat()
        found = _candidates(dump, {k[0] for k in keys})
        for key in sorted(keys):
            primary, alternate, municipal = found[key[0]]
            rows = primary or alternate or municipal
            chosen = _decide(rows)
            if chosen is None:
                target = result.ambiguous if rows else result.not_found
                target.append({"place": todo[key], "country_iso3": iso3} | ({"candidates": len(rows)} if rows else {}))
                continue
            lat, lon = round(chosen["lat"], 2), round(chosen["lon"], 2)
            basis = (f"GeoNames {chosen['geonameid']} ({chosen['name']}, {chosen['code']}), Länderdatei {iso2} vom {stamp}, "
                     f"automatisch ergänzt am {today().isoformat()}, gerundet auf 0,01°, CC BY 4.0, kein Online-Geocoding")
            new_rows.append([todo[key], iso3, f"{lat:.2f}", f"{lon:.2f}", basis, ""])
            result.added.append({"place": todo[key], "country_iso3": iso3, "lat": lat, "lon": lon,
                                 "geonameid": chosen["geonameid"]})
    if new_rows:
        _append(gazetteer_path, new_rows)
    return result


def _append(path: Path, rows: list[list[str]]) -> None:
    """Append rows; the file keeps its header (created with the full header if missing). Existing rows stay untouched."""
    header = list(GAZETTEER_COLUMNS) + ["group_with"]
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(";".join(header) + "\n", encoding="utf-8")
    text = path.read_text(encoding="utf-8-sig")
    first = text.splitlines()[0].split(";") if text else header
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
    for row in rows:
        writer.writerow(row if len(first) == 6 else row[:5])
    with path.open("a", encoding="utf-8", newline="") as handle:
        if text and not text.endswith("\n"):
            handle.write("\n")
        handle.write(buffer.getvalue())
