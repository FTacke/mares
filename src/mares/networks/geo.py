"""Country codes, the geographic classification of a residence and the status of a birth country.

The classification is deliberately coarse and rule-based. It describes *where a contact lives*,
never who a contact is: the categories are not to be read as ethnic or national groups. It is the
geographic location only; whether a place has a *biographical* meaning for the person (country of
origin, a former home) is a different dimension that cannot be derived from the country of residence
and is not classified here.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass

# ISO 3166-1 alpha-3 plus XKX (Kosovo, widely used, user-assigned).
ISO3 = frozenset(
    """AFG ALA ALB DZA ASM AND AGO AIA ATA ATG ARG ARM ABW AUS AUT AZE BHS BHR BGD BRB BLR BEL BLZ BEN BMU
    BTN BOL BES BIH BWA BVT BRA IOT BRN BGR BFA BDI CPV KHM CMR CAN CYM CAF TCD CHL CHN CXR CCK COL COM COG
    COD COK CRI CIV HRV CUB CUW CYP CZE DNK DJI DMA DOM ECU EGY SLV GNQ ERI EST SWZ ETH FLK FRO FJI FIN FRA
    GUF PYF ATF GAB GMB GEO DEU GHA GIB GRC GRL GRD GLP GUM GTM GGY GIN GNB GUY HTI HMD VAT HND HKG HUN ISL
    IND IDN IRN IRQ IRL IMN ISR ITA JAM JPN JEY JOR KAZ KEN KIR PRK KOR KWT KGZ LAO LVA LBN LSO LBR LBY LIE
    LTU LUX MAC MDG MWI MYS MDV MLI MLT MHL MTQ MRT MUS MYT MEX FSM MDA MCO MNG MNE MSR MAR MOZ MMR NAM NRU
    NPL NLD NCL NZL NIC NER NGA NIU NFK MKD MNP NOR OMN PAK PLW PSE PAN PNG PRY PER PHL PCN POL PRT PRI QAT
    REU ROU RUS RWA BLM SHN KNA LCA MAF SPM VCT WSM SMR STP SAU SEN SRB SYC SLE SGP SXM SVK SVN SLB SOM ZAF
    SGS SSD ESP LKA SDN SUR SJM SWE CHE SYR TWN TJK TZA THA TLS TGO TKL TON TTO TUN TUR TKM TCA TUV UGA UKR
    ARE GBR USA UMI URY UZB VUT VEN VNM VGB VIR WLF ESH YEM ZMB ZWE XKX""".split()
)

# Geographic Europe, after the UN geoscheme (M49, region 150). A purely geographic definition: it is not
# membership of the EU or of the Council of Europe. Conventions for transcontinental countries follow the
# geoscheme: Russia counts as Europe; Turkey, Cyprus, Georgia, Armenia, Azerbaijan and Kazakhstan as Asia.
# Overseas territories count with their continent, not with their state (French Guiana is not Europe).
EUROPE_ISO3 = frozenset(
    """ALA ALB AND AUT BEL BGR BIH BLR CHE CZE DEU DNK ESP EST FIN FRA FRO GBR GGY GIB GRC HRV HUN IMN IRL ISL ITA
    JEY LIE LTU LUX LVA MCO MDA MKD MLT MNE NLD NOR POL PRT ROU RUS SJM SMR SRB SVK SVN SWE UKR VAT XKX""".split()
)

HOME_COUNTRY = "DEU"
DEFAULT_LOCAL_PLACES = ("Marburg",)


class GeoCategory(enum.Enum):
    LOCAL = "local"  # the reference locality of the survey (Marburg), named exactly
    LOCAL_REGION = "local_region"  # a regional statement about the reference locality ("Nähe Marburg")
    GERMANY_OTHER = "germany_other"
    EUROPE_OTHER = "europe_other"  # a European country other than Germany
    OUTSIDE_EUROPE = "outside_europe"
    UNKNOWN = "unknown"  # no usable residence country (missing or not an ISO code): never guessed


@dataclass(frozen=True)
class Residence:
    category: GeoCategory
    city: str | None
    country: str | None
    region_of: str | None = None  # the place a regional statement refers to; never a concrete residence


# "Nähe Marburg", "Raum Marburg", "Region Marburg", "Umgebung Marburg", "bei Marburg", "near Marburg"
_REGION = re.compile(r"(?:n(?:ä|ae)he|raum|region|umgebung|umland|bei|near)(?:\s+von)?\s+(?P<base>.+)", re.IGNORECASE)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def classify_residence(
    city: str | None,
    country_iso3: str | None,
    local_places: tuple[str, ...] = DEFAULT_LOCAL_PLACES,
) -> Residence:
    """Marburg / region of Marburg / rest of Germany / rest of Europe / outside Europe / unknown, from the stated residence only.

    * ``LOCAL``: a German residence whose place equals one of ``local_places`` (exact, case-folded).
    * ``LOCAL_REGION``: a German residence stated as a region of a local place ("Nähe Marburg"). It is
      a regional statement and stays one: no concrete place of residence is invented, and it is
      not the city.
    * a regional statement about any other place is classified by its country, with ``region_of`` kept.
    * a missing country, or one that is no ISO code, is ``UNKNOWN`` -- the place alone does not decide, and a
      country is never guessed.
    * a residence outside Germany is ``EUROPE_OTHER`` or ``OUTSIDE_EUROPE`` by the country alone (``EUROPE_ISO3``).
    """
    if not country_iso3 or country_iso3 not in ISO3:
        return Residence(GeoCategory.UNKNOWN, city, country_iso3 or None)
    region_of = None
    if city:
        match = _REGION.fullmatch(city.strip())
        if match:
            region_of = match.group("base").strip()
    if country_iso3 != HOME_COUNTRY:
        category = GeoCategory.EUROPE_OTHER if country_iso3 in EUROPE_ISO3 else GeoCategory.OUTSIDE_EUROPE
        return Residence(category, city, country_iso3, region_of)
    local = {_norm(place) for place in local_places}
    if region_of and _norm(region_of) in local:
        return Residence(GeoCategory.LOCAL_REGION, city, country_iso3, region_of)
    if city and region_of is None and _norm(city) in local:
        return Residence(GeoCategory.LOCAL, city, country_iso3)
    return Residence(GeoCategory.GERMANY_OTHER, city, country_iso3, region_of)


class BirthStatus(enum.Enum):
    CODED = "coded"  # an ISO code is set
    AMBIGUOUS = "ambiguous"  # the source names several alternatives ("A/B"); not one fact, not two
    UNMAPPED = "unmapped"  # the source names one country but the package has no code for it
    MISSING = "missing"  # nothing recorded


@dataclass(frozen=True)
class BirthCountry:
    status: BirthStatus
    iso3: str | None
    raw: str | None  # the original statement, kept unchanged


# Separators that mean "several countries are named": "A/B", "A oder B", "A, B", "A & B"
_ALTERNATIVES = re.compile(r"\s*(?:/|\\|;|,|&|\boder\b|\bund\b|\bor\b|\band\b)\s*", re.IGNORECASE)


def classify_birth_country(iso3: str | None, source_text: str | None) -> BirthCountry:
    """The status of a birth country, keeping the raw statement.

    An ambiguous statement ("Brasilien/Paraguay") is neither resolved to one country nor counted as
    two birth countries nor treated as missing: it is its own status.
    """
    raw = source_text.strip() if source_text and source_text.strip() else None
    if iso3:
        return BirthCountry(BirthStatus.CODED, iso3, raw)
    if raw is None:
        return BirthCountry(BirthStatus.MISSING, None, None)
    parts = [part for part in _ALTERNATIVES.split(raw) if part.strip()]
    if len(parts) >= 2:
        return BirthCountry(BirthStatus.AMBIGUOUS, None, raw)
    return BirthCountry(BirthStatus.UNMAPPED, None, raw)
