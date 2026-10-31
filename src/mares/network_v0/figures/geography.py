"""Figure C: geographic network profile.

Left: every contact as a chip, grouped by the category of its residence (Marburg and its region / rest of
Germany / abroad) and by place; each chip also states the birth country *as recorded*. Right: residence
country by birth country as a count matrix. The categories describe where a contact lives; they are not
groups of people and carry no ethnic or national interpretation. An ambiguous birth statement is shown
as such ("mehrdeutig"): it is neither resolved to one country nor counted as two.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from matplotlib.patches import FancyBboxPatch, Rectangle

from mares.core import ids

from ..analysis import AnalysisParams, SurveyStatus, geo_labels
from ..geo import GeoCategory
from ..model import NetworkDataset
from . import design
from .common import ContactView, contact_views, draw_legend
from .style import GEO_COLORS, GEO_ORDER, INK, MUTED, frame, label_color, new_figure, rc, rim_color

_CHIP_W, _CHIP_H = 1.12, 0.70
_PER_ROW = 3
_COL_W = _PER_ROW * (_CHIP_W + 0.12) + 1.05
# categories that share a column: the region of the reference place sits below the place itself
_COLUMNS = ((GeoCategory.LOCAL, GeoCategory.LOCAL_REGION), (GeoCategory.GERMANY_OTHER,), (GeoCategory.EUROPE_OTHER,), (GeoCategory.OUTSIDE_EUROPE,), (GeoCategory.UNKNOWN,))
_SPECIAL_BIRTH = ("mehrdeutig", "nicht kodiert", "–")


def _chip(ax, x: float, y: float, view: ContactView) -> None:
    fill = GEO_COLORS[view.geo]
    ax.add_patch(
        FancyBboxPatch(
            (x, y - _CHIP_H), _CHIP_W, _CHIP_H, boxstyle="round,pad=0,rounding_size=0.14", facecolor=fill,
            edgecolor=rim_color(fill), linewidth=1.0, zorder=3,
        )
    )
    color = label_color(fill)
    ax.text(x + _CHIP_W / 2, y - 0.25, view.contact_id, ha="center", va="center", fontsize=9, fontweight="bold", color=color, zorder=4)
    label = view.birth if view.birth in _SPECIAL_BIRTH else f"geb. {view.birth}"
    ax.text(x + _CHIP_W / 2, y - 0.52, label, ha="center", va="center", fontsize=6.8, color=color, zorder=4,
            fontstyle="italic" if view.birth == "mehrdeutig" else "normal")


def geography_figure(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams, *, profile: str = "clean"):
    with rc():
        views = contact_views(dataset, params)
        labels = geo_labels(params)
        by_geo: dict[GeoCategory, list[ContactView]] = defaultdict(list)
        for view in views:
            by_geo[view.geo].append(view)
        columns = [[c for c in column if by_geo[c]] for column in _COLUMNS]
        columns = [c for c in columns if c]

        fig = new_figure(14.2, 9.0)
        design.frame_for(
            profile,
            fig,
            "Geografisches Netzwerkprofil: Wohnort und Geburtsland der Kontakte",
            "Spalten = geografische Einordnung des Wohnorts; Chip = Kontakt (ID) mit Geburtsland laut Angabe der Quelle (ISO-3166-Alpha-3)",
            status,
            "Die Kategorien beschreiben den Wohnort eines Kontakts, nicht die Person; Wohnland und Geburtsland werden nicht zu Herkunftsgruppen zusammengefasst. "
            f"„{labels[GeoCategory.LOCAL]}“ nur bei exakt benanntem Ort;\n"
            "„Region …“ ist eine ungefähre Ortsangabe und bleibt regional. „mehrdeutig“: die Quelle nennt mehrere Länder; der Rohwert ist erhalten, "
            "es wird weder eines gewählt noch werden zwei gezählt. „–“ = nicht erfasst.",
            short_title="Wohnort und Geburtsland der Kontakte",
            hint="Die Kategorien beschreiben den Wohnort, nicht die Person. „–“ = nicht erfasst.",
        )
        ax = fig.add_axes([0.02, 0.14, 0.60, 0.74])
        ax.axis("off")
        column_h = 0.0
        for column, categories in enumerate(columns):
            x0 = column * _COL_W
            y = 0.0
            for category in categories:
                members = by_geo[category]
                ax.add_patch(Rectangle((x0, y), _COL_W - 0.45, 0.16, facecolor=GEO_COLORS[category], edgecolor=rim_color(GEO_COLORS[category]), linewidth=0.6, zorder=2))
                ax.text(x0, y + 0.30, labels[category].replace(" (ungefähre Angabe)", ""), fontsize=11, fontweight="bold", color=INK, va="bottom", ha="left")
                if profile == "analysis":
                    ax.text(x0 + _COL_W - 0.45, y + 0.30, f"n = {len(members)}", fontsize=9, color=MUTED, va="bottom", ha="right")
                places: dict[tuple[str, str], list[ContactView]] = defaultdict(list)
                for view in members:
                    places[(view.city or "Ort nicht erfasst", view.residence_country or "–")].append(view)
                y -= 0.25
                for (city, country), group in sorted(places.items(), key=lambda kv: (-len(kv[1]), kv[0])):
                    ax.text(x0, y, f"{city} · {country}" + (f"  (n = {len(group)})" if profile == "analysis" else ""), fontsize=8.6, color=INK, va="top", ha="left")
                    y -= 0.38
                    for index, view in enumerate(sorted(group, key=lambda v: ids.contact_number(v.contact_id))):
                        row, col = divmod(index, _PER_ROW)
                        _chip(ax, x0 + col * (_CHIP_W + 0.12), y - row * (_CHIP_H + 0.12), view)
                    rows = (len(group) + _PER_ROW - 1) // _PER_ROW
                    y -= rows * (_CHIP_H + 0.12) + 0.34
                y -= 0.55  # room for the next category header of the same column
            column_h = max(column_h, -y)
        ax.set_xlim(-0.1, max(1, len(columns)) * _COL_W)
        ax.set_ylim(-column_h - 0.1, 0.9)

        # residence country x birth country
        matrix = Counter((v.residence_country or "–", v.birth) for v in views)
        residences = sorted({r for r, _ in matrix}, key=lambda r: (r == "–", r))
        births = sorted({b for _, b in matrix if b not in _SPECIAL_BIRTH}) + [b for b in _SPECIAL_BIRTH if any(b == x for _, x in matrix)]
        mx = fig.add_axes([0.69, 0.46, 0.29, 0.34])
        mx.set_xlim(0, len(births))
        mx.set_ylim(len(residences), 0)
        mx.set_aspect("equal", adjustable="box")
        mx.set_anchor("NW")
        peak = max(matrix.values(), default=1)
        for i, res in enumerate(residences):
            for j, birth in enumerate(births):
                count = matrix.get((res, birth), 0)
                shade = 0.0 if not count else 0.25 + 0.65 * count / peak
                fill = (1 - shade * 0.80, 1 - shade * 0.55, 1 - shade * 0.25) if count else "#F4F6F8"
                mx.add_patch(Rectangle((j, i), 1, 1, facecolor=fill, edgecolor="white", linewidth=1.5))
                if count:
                    mx.text(j + 0.5, i + 0.5, str(count), ha="center", va="center", fontsize=10, fontweight="bold", color=INK if shade < 0.62 else "white")
        ticks = [b.replace("mehrdeutig", "mehr-\ndeutig").replace("nicht kodiert", "nicht\nkodiert") for b in births]
        mx.set_xticks([j + 0.5 for j in range(len(births))], ticks, fontsize=7.6)
        mx.set_yticks([i + 0.5 for i in range(len(residences))], residences, fontsize=8)
        mx.xaxis.tick_top()
        mx.tick_params(length=0)
        for spine in mx.spines.values():
            spine.set_visible(False)
        fig.text(0.69, 0.875, "Wohnland (Zeilen) × Geburtsland laut Angabe (Spalten)", fontsize=9.4, fontweight="bold", color=INK, ha="left", va="bottom")
        fig.text(0.69, 0.855, "Zahl der Kontakte", fontsize=8, color=MUTED, ha="left", va="bottom")

        legend = fig.add_axes([0.69, 0.20, 0.29, 0.24])
        geo_counts = {g: len(by_geo[g]) for g in GEO_ORDER}
        draw_legend(
            legend,
            design.lean_sections([("Wohnort des Kontakts", [("dot", GEO_COLORS[g], labels[g]) for g in GEO_ORDER if geo_counts[g]])], profile),
            line=0.12,
        )
    return fig
