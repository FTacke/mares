"""Geographic classification of a contact's residence in network_v1.

Four primary analysis categories, with the first split in two for the geographic figures:

========================  ==========================  ==================================================
display area (:class:`Area`)  primary category            rule
========================  ==========================  ==================================================
``MARBURG``               Marburg und Mittelhessen    German residence, place = the town of Marburg
``MITTELHESSEN``          Marburg und Mittelhessen    German residence in one of the five districts (below)
``GERMANY_OTHER``         übriges Deutschland         German residence outside the five districts
``EUROPE_OTHER``          übriges Europa              residence country in Europe (UN geoscheme), not Germany
``OUTSIDE_EUROPE``        außerhalb Europas           any other valid residence country
``UNRESOLVED``            --                          not decidable without guessing (see below)
========================  ==========================  ==================================================

Mittelhessen = the districts Marburg-Biedenkopf, Gießen, Lahn-Dill-Kreis, Limburg-Weilburg and Vogelsbergkreis.
A German place is placed by the municipality list below (official names plus unambiguous spellings) or by an
explicit entry of the case (``data/places.csv``); a German city of more than 100,000 inhabitants is outside the
districts by definition (all of them lie elsewhere) -- nothing is guessed. A German place that is in neither, a name
that exists in several German states ("Neustadt", "Weimar"), a regional statement ("Nähe Marburg"), a missing or
invalid country code: ``UNRESOLVED``, with the reason. The original statements stay untouched.

The municipality list follows the official lists of the five districts (101 municipalities, as of 2026-10). A
district part (Ortsteil, e.g. a part of Marburg) is not listed: it is resolved by ``places.csv``.
"""

from __future__ import annotations

import enum
import re
import unicodedata
from dataclasses import dataclass

from mares.network_v0.geo import EUROPE_ISO3, ISO3  # version-neutral country tables (ISO 3166-1, UN geoscheme)

HOME_COUNTRY = "DEU"


class Area(enum.Enum):
    MARBURG = "marburg"
    MITTELHESSEN = "mittelhessen_other"
    GERMANY_OTHER = "germany_other"
    EUROPE_OTHER = "europe_other"
    OUTSIDE_EUROPE = "outside_europe"
    UNRESOLVED = "unresolved"


AREA_ORDER = (Area.MARBURG, Area.MITTELHESSEN, Area.GERMANY_OTHER, Area.EUROPE_OTHER, Area.OUTSIDE_EUROPE)
AREA_LABELS = {
    Area.MARBURG: "Marburg (Stadt)",
    Area.MITTELHESSEN: "übriges Mittelhessen",
    Area.GERMANY_OTHER: "übriges Deutschland",
    Area.EUROPE_OTHER: "übriges Europa",
    Area.OUTSIDE_EUROPE: "außerhalb Europas",
    Area.UNRESOLVED: "nicht zuordenbar",
}


class Primary(enum.Enum):
    MARBURG_MITTELHESSEN = "marburg_mittelhessen"
    GERMANY_OTHER = "germany_other"
    EUROPE_OTHER = "europe_other"
    OUTSIDE_EUROPE = "outside_europe"
    UNRESOLVED = "unresolved"


PRIMARY_OF = {
    Area.MARBURG: Primary.MARBURG_MITTELHESSEN,
    Area.MITTELHESSEN: Primary.MARBURG_MITTELHESSEN,
    Area.GERMANY_OTHER: Primary.GERMANY_OTHER,
    Area.EUROPE_OTHER: Primary.EUROPE_OTHER,
    Area.OUTSIDE_EUROPE: Primary.OUTSIDE_EUROPE,
    Area.UNRESOLVED: Primary.UNRESOLVED,
}
PRIMARY_LABELS = {
    Primary.MARBURG_MITTELHESSEN: "Marburg und Mittelhessen",
    Primary.GERMANY_OTHER: "übriges Deutschland",
    Primary.EUROPE_OTHER: "übriges Europa",
    Primary.OUTSIDE_EUROPE: "außerhalb Europas",
    Primary.UNRESOLVED: "nicht zuordenbar",
}

MARBURG = "Marburg"
MITTELHESSEN_DISTRICTS: dict[str, tuple[str, ...]] = {
    "Marburg-Biedenkopf": (
        "Amöneburg", "Angelburg", "Bad Endbach", "Biedenkopf", "Breidenbach", "Cölbe", "Dautphetal", "Ebsdorfergrund",
        "Fronhausen", "Gladenbach", "Kirchhain", "Lahntal", "Lohra", "Marburg", "Münchhausen", "Neustadt (Hessen)",
        "Rauschenberg", "Stadtallendorf", "Steffenberg", "Weimar (Lahn)", "Wetter (Hessen)", "Wohratal",
    ),
    "Gießen": (
        "Allendorf (Lumda)", "Biebertal", "Buseck", "Fernwald", "Gießen", "Grünberg", "Heuchelheim an der Lahn", "Hungen",
        "Langgöns", "Laubach", "Lich", "Linden", "Lollar", "Pohlheim", "Rabenau", "Reiskirchen", "Staufenberg", "Wettenberg",
    ),
    "Lahn-Dill-Kreis": (
        "Aßlar", "Bischoffen", "Braunfels", "Breitscheid", "Dietzhölztal", "Dillenburg", "Driedorf", "Ehringshausen",
        "Eschenburg", "Greifenstein", "Haiger", "Herborn", "Hohenahr", "Hüttenberg", "Lahnau", "Leun", "Mittenaar",
        "Schöffengrund", "Siegbach", "Sinn", "Solms", "Waldsolms", "Wetzlar",
    ),
    "Limburg-Weilburg": (
        "Bad Camberg", "Beselich", "Brechen", "Dornburg", "Elbtal", "Elz", "Hadamar", "Hünfelden", "Limburg an der Lahn",
        "Löhnberg", "Mengerskirchen", "Merenberg", "Runkel", "Selters (Taunus)", "Villmar", "Waldbrunn (Westerwald)",
        "Weilburg", "Weilmünster", "Weinbach",
    ),
    "Vogelsbergkreis": (
        "Alsfeld", "Antrifttal", "Feldatal", "Freiensteinau", "Gemünden (Felda)", "Grebenau", "Grebenhain", "Herbstein",
        "Homberg (Ohm)", "Kirtorf", "Lauterbach (Hessen)", "Lautertal (Vogelsberg)", "Mücke", "Romrod", "Schlitz", "Schotten",
        "Schwalmtal", "Ulrichstein", "Wartenberg",
    ),
}
# Further unambiguous spellings of listed municipalities.
ALIASES = {
    "Marburg an der Lahn": "Marburg",
    "Marburg/Lahn": "Marburg",
    "Marburg (Lahn)": "Marburg",
    "Heuchelheim a. d. Lahn": "Heuchelheim an der Lahn",
    "Limburg": "Limburg an der Lahn",
    "Limburg a. d. Lahn": "Limburg an der Lahn",
    "Limburg (Lahn)": "Limburg an der Lahn",
    "Neustadt/Hessen": "Neustadt (Hessen)",
    "Wetter/Hessen": "Wetter (Hessen)",
}
# Short names that also denote municipalities in other German states: they are not placed without places.csv.
AMBIGUOUS = frozenset(
    "Neustadt Weimar Wetter Allendorf Heuchelheim Homberg Lautertal Gemünden Selters Waldbrunn Lauterbach Linden Breitscheid "
    "Staufenberg Elz Sinn Grünberg Wartenberg Schwalmtal".split()
)
# Of these, Linden, Breitscheid, Staufenberg, Elz, Sinn, Grünberg, Wartenberg and Schwalmtal are official names of a
# municipality in Mittelhessen *and* of places elsewhere; the official name wins only when places.csv confirms it.


def norm(text: str) -> str:
    """Case, whitespace, ß/ss and umlaut spellings (ö/oe) are not distinguished."""
    text = unicodedata.normalize("NFC", text).strip().casefold()
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    return re.sub(r"\s+", " ", text)


# German cities with more than 100,000 inhabitants: all lie outside the five districts. A short name that denotes
# several such cities ("Frankfurt", "Halle", "Oldenburg") still decides the area, because every reading is outside.
LARGE_CITIES_OUTSIDE = (
    "Aachen", "Augsburg", "Bergisch Gladbach", "Berlin", "Bielefeld", "Bochum", "Bonn", "Bottrop", "Braunschweig", "Bremen",
    "Bremerhaven", "Chemnitz", "Cottbus", "Darmstadt", "Dortmund", "Dresden", "Duisburg", "Düren", "Düsseldorf", "Erfurt",
    "Erlangen", "Essen", "Esslingen", "Esslingen am Neckar", "Flensburg", "Frankfurt", "Frankfurt am Main", "Frankfurt (Oder)",
    "Freiburg", "Freiburg im Breisgau", "Fürth", "Gelsenkirchen", "Gera", "Göttingen", "Gütersloh", "Hagen", "Halle",
    "Halle (Saale)", "Hamburg", "Hamm", "Hanau", "Hannover", "Heidelberg", "Heilbronn", "Herne", "Hildesheim", "Ingolstadt",
    "Iserlohn", "Jena", "Kaiserslautern", "Karlsruhe", "Kassel", "Kiel", "Koblenz", "Köln", "Krefeld", "Leipzig",
    "Leverkusen", "Lübeck", "Ludwigsburg", "Ludwigshafen", "Ludwigshafen am Rhein", "Magdeburg", "Mainz", "Mannheim",
    "Moers", "Mönchengladbach", "Mülheim an der Ruhr", "München", "Münster", "Neuss", "Nürnberg", "Oberhausen",
    "Offenbach", "Offenbach am Main", "Oldenburg", "Osnabrück", "Paderborn", "Pforzheim", "Potsdam", "Recklinghausen",
    "Regensburg", "Remscheid", "Reutlingen", "Rostock", "Saarbrücken", "Salzgitter", "Schwerin", "Siegen", "Solingen",
    "Stuttgart", "Trier", "Tübingen", "Ulm", "Wiesbaden", "Witten", "Wolfsburg", "Wuppertal", "Würzburg", "Zwickau",
)
_LARGE_OUTSIDE = {norm(n) for n in LARGE_CITIES_OUTSIDE}

_DISTRICT_OF: dict[str, tuple[str, str]] = {}
for _district, _names in MITTELHESSEN_DISTRICTS.items():
    for _name in _names:
        _DISTRICT_OF[norm(_name)] = (_name, _district)
for _alias, _name in ALIASES.items():
    _DISTRICT_OF[norm(_alias)] = _DISTRICT_OF[norm(_name)]
_AMBIGUOUS = {norm(n) for n in AMBIGUOUS}
_REGIONAL = re.compile(r"\b(?:n(?:ä|ae)he|raum|region|umgebung|umland|bei|near|landkreis|kreis)\b", re.IGNORECASE)


@dataclass(frozen=True)
class PlaceResolution:
    """An explicit statement of the case about one German place (``data/places.csv``)."""

    place: str
    area: Area
    basis: str


@dataclass(frozen=True)
class Residence:
    area: Area
    basis: str  # how the area was decided, or why it was not
    place: str | None
    country_iso3: str | None
    district: str | None = None  # the Mittelhessen district, when known

    @property
    def primary(self) -> Primary:
        return PRIMARY_OF[self.area]


def classify(place: str | None, country_iso3: str | None, resolutions: dict[str, PlaceResolution] | None = None) -> Residence:
    """Area of one residence from the coded country and the stated place. Never guesses."""
    place = (place or "").strip() or None
    iso = (country_iso3 or "").strip().upper() or None
    if iso is None:
        return Residence(Area.UNRESOLVED, "kein Wohnland codiert", place, None)
    if iso not in ISO3:
        return Residence(Area.UNRESOLVED, f"{iso!r} ist kein ISO-3166-Ländercode", place, iso)
    if iso != HOME_COUNTRY:
        area = Area.EUROPE_OTHER if iso in EUROPE_ISO3 else Area.OUTSIDE_EUROPE
        return Residence(area, "Wohnland", place, iso)
    if place is None:
        return Residence(Area.UNRESOLVED, "Deutschland ohne Ortsangabe", None, iso)
    key = norm(place)
    resolution = (resolutions or {}).get(key)
    if resolution is not None:
        return Residence(resolution.area, f"places.csv: {resolution.basis}", place, iso)
    if _REGIONAL.search(place):
        return Residence(Area.UNRESOLVED, "regionale Angabe, kein Wohnort", place, iso)
    if key in _AMBIGUOUS:
        return Residence(Area.UNRESOLVED, "Ortsname in mehreren Bundesländern; places.csv nötig", place, iso)
    hit = _DISTRICT_OF.get(key)
    if hit is not None:
        name, district = hit
        area = Area.MARBURG if name == MARBURG else Area.MITTELHESSEN
        return Residence(area, f"Gemeindeverzeichnis Mittelhessen ({district})", place, iso, district)
    if key in _LARGE_OUTSIDE:
        return Residence(Area.GERMANY_OTHER, "Großstadt außerhalb Mittelhessens", place, iso)
    return Residence(Area.UNRESOLVED, "deutscher Ort nicht im Gemeindeverzeichnis Mittelhessen; places.csv nötig", place, iso)


def resolution_key(place: str) -> str:
    return norm(place)
