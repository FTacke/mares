"""What every figure needs to know about a contact, computed once and identically for all."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mares.core import ids

from ..analysis import AnalysisParams, residence_of
from ..geo import GeoCategory
from ..model import NetworkDataset
from .style import GEO_ORDER


@dataclass(frozen=True)
class ContactView:
    contact_id: str
    geo: GeoCategory
    city: str | None
    residence_country: str | None
    birth_country: str | None
    closeness: str | None  # codebook code of the table value; None = not collected
    flagged: bool  # open review flags: drawn with a dashed outline everywhere
    languages: tuple[str, ...]
    language_mode: str | None
    relations: tuple[str, ...]


def contact_views(dataset: NetworkDataset, params: AnalysisParams) -> list[ContactView]:
    views = []
    for contact in dataset.contacts:
        residence = residence_of(contact, params)
        views.append(
            ContactView(
                contact_id=contact.contact_id,
                geo=residence.category,
                city=residence.city,
                residence_country=residence.country,
                birth_country=contact.text.get("birth_country"),
                closeness=contact.single("closeness"),
                flagged=bool(contact.review_flags),
                languages=contact.code_list("language"),
                language_mode=contact.single("language_mode"),
                relations=contact.code_list("relation"),
            )
        )
    return sorted(views, key=lambda v: ids.contact_number(v.contact_id))


# ---------------------------------------------------------------- ego-centred layout ----------

EGO_RADIUS = 0.55
BAND = 1.0
NODE_RADIUS = 0.29
GAP_HALF_ANGLE = 25.0  # degrees kept free around 12 o'clock for the zone badges


@dataclass(frozen=True)
class EgoLayout:
    positions: dict[str, tuple[float, float]]
    zone_codes: tuple[str, ...]  # closeness codes, innermost first
    band_bounds: tuple[tuple[float, float], ...]  # (inner, outer) radius per zone, innermost first
    unrecorded_band: tuple[float, float] | None
    outer_radius: float


def ego_layout(views: list[ContactView], zone_codes_high_to_low: list[str]) -> EgoLayout:
    """Place contacts on concentric zones by their *table* closeness value.

    The radius is a function of the table value alone. Inside a zone the angle only serves legibility:
    contacts are ordered by geography, then id, spread evenly, and each zone is rotated against its
    neighbours so labels do not line up radially. Position inside a zone carries no information.
    Contacts without a closeness value go to a separate outer band -- never into a zone.
    """
    zones = list(zone_codes_high_to_low)  # innermost = closest = highest value
    bounds = tuple((EGO_RADIUS + i * BAND, EGO_RADIUS + (i + 1) * BAND) for i in range(len(zones)))
    outer = EGO_RADIUS + len(zones) * BAND
    unrecorded = [v for v in views if v.closeness not in zones]
    unrecorded_band = (outer + 0.35, outer + 0.35 + BAND) if unrecorded else None

    positions: dict[str, tuple[float, float]] = {}

    def place(members: list[ContactView], inner: float, outer_r: float, index: int) -> None:
        members = sorted(members, key=lambda v: (GEO_ORDER.index(v.geo), ids.contact_number(v.contact_id)))
        n = len(members)
        mid = (inner + outer_r) / 2
        span = 360.0 - 2 * GAP_HALF_ANGLE
        base = 90.0 + GAP_HALF_ANGLE
        odd = index % 2 == 1  # neighbouring zones use different margins, so nodes do not line up radially
        step = span / (n + 1) if odd else span / n
        crowded = n * 2 * NODE_RADIUS * 1.25 > math.radians(span) * mid
        for k, view in enumerate(members):
            angle = math.radians(base + step * (k + 1 if odd else k + 0.5))
            radius = mid + ((0.11 if k % 2 else -0.11) if crowded else 0.0)
            positions[view.contact_id] = (radius * math.cos(angle), radius * math.sin(angle))

    for index, code in enumerate(zones):
        members = [v for v in views if v.closeness == code]
        if members:
            place(members, *bounds[index], index)
    if unrecorded_band:
        place(unrecorded, *unrecorded_band, len(zones))
    radius = unrecorded_band[1] if unrecorded_band else outer
    return EgoLayout(positions, tuple(zones), bounds, unrecorded_band, radius)


# ---------------------------------------------------------------- drawing helpers --------------

from matplotlib.axes import Axes  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

from .style import FAINT, INK, MUTED, label_color  # noqa: E402


def draw_node(ax: Axes, xy: tuple[float, float], contact_id: str, fill: str, *, flagged: bool, radius: float = NODE_RADIUS, fontsize: float = 8.4, z: int = 5) -> None:
    """A contact: a disc with its id. A dashed dark outline marks open review flags."""
    ax.add_patch(
        Circle(xy, radius, facecolor=fill, edgecolor=INK if flagged else "white", linewidth=1.5 if flagged else 1.1,
               linestyle=(0, (2.2, 1.6)) if flagged else "solid", zorder=z)
    )
    ax.text(xy[0], xy[1], contact_id, ha="center", va="center", fontsize=fontsize, fontweight="bold",
            color=label_color(fill), zorder=z + 1)


def draw_legend(ax: Axes, sections: list[tuple[str, list[tuple[str, str, str]]]], *, top: float = 1.0, line: float = 0.052) -> None:
    """A legend drawn into its own axes (0..1 coordinates). Entry: ``(kind, colour, label)`` with kind
    ``dot`` (filled disc), ``flag`` (dashed outline), ``ring`` (numbered ring), ``text`` (plain)."""
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    y = top
    for title, entries in sections:
        ax.text(0.0, y, title, fontsize=9.4, fontweight="bold", color=INK, va="top", ha="left")
        y -= line * 1.15 * (title.count(chr(10)) + 1)
        for kind, color, text in entries:
            lines = text.count("\n") + 1
            if kind in ("dot", "flag", "ring"):
                ax.scatter([0.035], [y - 0.012], s=120, transform=ax.transAxes, clip_on=False,
                           c=color if kind != "flag" else "white", edgecolors=INK if kind == "flag" else ("#8D969E" if kind == "ring" or color == "#FFFFFF" else "white"),
                           linewidths=1.3, linestyle=(0, (2.2, 1.6)) if kind == "flag" else "solid", zorder=3)
            ax.text(0.085 if kind != "text" else 0.0, y, text, fontsize=8.6, color=INK, va="top", ha="left", linespacing=1.25)
            y -= line * lines
        y -= line * 0.55
