"""Country codes and the geographic classification of a residence.

The classification is deliberately coarse and rule-based. It describes *where a contact lives*,
never who a contact is: the categories are not to be read as ethnic or national groups.
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

HOME_COUNTRY = "DEU"
DEFAULT_LOCAL_PLACES = ("Marburg",)


class GeoCategory(enum.Enum):
    LOCAL = "local"  # the reference locality of the survey (Marburg)
    GERMANY_OTHER = "germany_other"
    ABROAD = "abroad"
    UNKNOWN = "unknown"  # no usable residence country


@dataclass(frozen=True)
class Residence:
    category: GeoCategory
    city: str | None
    country: str | None


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def classify_residence(
    city: str | None,
    country_iso3: str | None,
    local_places: tuple[str, ...] = DEFAULT_LOCAL_PLACES,
) -> Residence:
    """Marburg / rest of Germany / abroad / unknown, from the stated residence only.

    * ``LOCAL``: a German residence whose city equals one of ``local_places`` (exact, case-folded).
      A vaguer statement such as "near X" is *not* made precise; it is classified by its country,
      and the review flag of the contact says that it is approximate.
    * a missing country is ``UNKNOWN`` -- the city alone does not decide.
    """
    if not country_iso3:
        return Residence(GeoCategory.UNKNOWN, city, None)
    if country_iso3 != HOME_COUNTRY:
        return Residence(GeoCategory.ABROAD, city, country_iso3)
    if city and _norm(city) in {_norm(place) for place in local_places}:
        return Residence(GeoCategory.LOCAL, city, country_iso3)
    return Residence(GeoCategory.GERMANY_OTHER, city, country_iso3)
