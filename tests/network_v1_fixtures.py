"""Helpers for the network_v1 tests: the synthetic case 002 and modified copies of it, temporary roots, and the map
sources of X1 (a tiny artificial basemap and a place directory of the invented places of 002)."""

from __future__ import annotations

import csv
import io
import json
import shutil
from pathlib import Path

from mares.core.roots import Roots, load_root_specs
from mares.network_v1.case import read_case
from mares.network_v1.figures.base import Geo
from mares.network_v1.figures.maps import BASEMAP, GAZETTEER, read_gazetteer
from mares.network_v1.testcases import SYNTHETIC_CODE, synthetic_source
from mares.network_v1.validate import validate

SPECS = load_root_specs()

# country: (continent, German name, label point lat, lon, half size of the square in degrees)
COUNTRIES = {
    "DEU": ("Europe", "Deutschland", 51.0, 10.0, 4.0), "ESP": ("Europe", "Spanien", 40.0, -4.0, 4.0),
    "FRA": ("Europe", "Frankreich", 46.5, 2.5, 4.0), "COL": ("South America", "Kolumbien", 4.0, -73.0, 5.0),
    "ECU": ("South America", "Ecuador", -1.5, -78.0, 2.0), "USA": ("North America", "Vereinigte Staaten", 39.0, -98.0, 15.0),
    "CAN": ("North America", "Kanada", 56.0, -100.0, 12.0), "JPN": ("Asia", "Japan", 36.0, 138.0, 3.0),
    "UKR": ("Europe", "Ukraine", 49.0, 31.0, 4.0),
}
PLACES = {  # public coordinates of the invented places of case 002 (as in pilots/network_v1_map)
    ("Marburg", "DEU"): (50.81, 8.77), ("Wehrda", "DEU"): (50.84, 8.76), ("Cölbe", "DEU"): (50.85, 8.78),
    ("Lahntal", "DEU"): (50.87, 8.69), ("Kirchhain", "DEU"): (50.83, 8.92), ("Gießen", "DEU"): (50.58, 8.68),
    ("Wetzlar", "DEU"): (50.56, 8.50), ("Kassel", "DEU"): (51.31, 9.48), ("Frankfurt am Main", "DEU"): (50.11, 8.68),
    ("Berlin", "DEU"): (52.52, 13.40), ("Madrid", "ESP"): (40.42, -3.70), ("Barcelona", "ESP"): (41.39, 2.17),
    ("Lyon", "FRA"): (45.76, 4.84), ("Bogotá", "COL"): (4.71, -74.07), ("Medellín", "COL"): (6.24, -75.58),
    ("Quito", "ECU"): (-0.18, -78.47), ("Miami", "USA"): (25.76, -80.19), ("Toronto", "CAN"): (43.65, -79.38),
    ("Kyjiw", "UKR"): (50.45, 30.52), ("Chía", "COL"): (4.86, -74.06),
}


def basemap() -> dict:
    features = []
    for iso, (continent, name, lat, lon, h) in COUNTRIES.items():
        ring = [[lon - h, lat - h], [lon + h, lat - h], [lon + h, lat + h], [lon - h, lat + h], [lon - h, lat - h]]
        features.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring]},
                         "properties": {"ADM0_A3": iso, "CONTINENT": continent, "NAME_DE": name, "LABEL_X": lon, "LABEL_Y": lat}})
    return {"type": "FeatureCollection", "features": features}


GROUP_WITH = {"Wehrda": "Marburg", "Cölbe": "Marburg", "Lahntal": "Marburg", "Kirchhain": "Marburg", "Wetzlar": "Gießen",
              "Chía": "Bogotá"}  # the regional assignment of the place directory (synthetic)


def gazetteer_text(places=PLACES, *, group_with=GROUP_WITH) -> str:
    if group_with is None:
        return "place;country_iso3;lat;lon;basis\n" + "".join(f"{p};{iso};{lat};{lon};synthetic\n" for (p, iso), (lat, lon) in places.items())
    return "place;country_iso3;lat;lon;basis;group_with\n" + "".join(
        f"{p};{iso};{lat};{lon};synthetic;{group_with.get(p, '')}\n" for (p, iso), (lat, lon) in places.items())


def countries() -> dict:
    return {f["properties"]["ADM0_A3"]: f for f in basemap()["features"]}


def gazetteer(tmp_path, places=PLACES, *, group_with=GROUP_WITH) -> dict:
    path = tmp_path / "gazetteer.csv"
    path.write_text(gazetteer_text(places, group_with=group_with), encoding="utf-8")
    return read_gazetteer(path)


def geo(tmp_path) -> Geo:
    """The map sources as a case run hands them to the figures."""
    return Geo(gazetteer(tmp_path), countries())


def install_map_sources(folders: dict[str, Path]) -> None:
    """Place directory in INTAKE and basemap in WORKSPACE, where a case run reads them."""
    path = folders["intake"] / GAZETTEER
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(gazetteer_text(), encoding="utf-8")
    path = folders["workspace"] / BASEMAP
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(basemap()), encoding="utf-8")


def copy_002(base: Path, *, kind: str = "pilots", name: str = SYNTHETIC_CODE) -> Path:
    """A writable copy of case 002 at ``base/network_v1/<kind>/<name>``."""
    target = base / "network_v1" / kind / name
    shutil.copytree(synthetic_source(), target)
    if name != SYNTHETIC_CODE:
        set_metadata(target, case_code=name)
    return target


def read_rows(case: Path, table: str) -> list[dict[str, str]]:
    text = (case / "data" / table).read_text(encoding="utf-8-sig")
    return list(csv.DictReader(io.StringIO(text), delimiter=";"))


def write_rows(case: Path, table: str, rows: list[dict[str, str]], header: list[str] | None = None) -> None:
    header = header or list(rows[0])
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, header, delimiter=";", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    (case / "data" / table).write_text(buffer.getvalue(), encoding="utf-8")


def edit(case: Path, table: str, contact_or_key: str, column: str, value: str, key: str = "contact_id") -> None:
    rows = read_rows(case, table)
    for row in rows:
        if row[key] == contact_or_key:
            row[column] = value
    write_rows(case, table, rows)


def append(case: Path, table: str, row: dict[str, str]) -> None:
    rows = read_rows(case, table)
    write_rows(case, table, rows + [row], list(rows[0]) if rows else list(row))


def set_metadata(case: Path, **changes) -> None:
    path = case / "data" / "metadata.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta.update(changes)
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def check(case: Path):
    return validate(read_case(case))


def codes_of(validation, level: str | None = None) -> set[str]:
    return {f.code for f in validation.findings if level is None or f.level == level}


def machine(tmp_path: Path) -> dict[str, Path]:
    folders = {name: tmp_path / name for name in ("checkout", "workspace", "intake", "primary")}
    for folder in folders.values():
        folder.mkdir()
    (folders["workspace"] / "runs").mkdir()
    (folders["intake"] / "inbox").mkdir()
    install_map_sources(folders)
    return folders


def roots_for(folders: dict[str, Path]) -> Roots:
    env = {"MARES_WORKSPACE_ROOT": str(folders["workspace"]), "MARES_INTAKE_ROOT": str(folders["intake"])}
    return Roots(SPECS, env, checkout=folders["checkout"])
