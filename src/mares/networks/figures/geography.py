"""Figure C: geographic network profile.

Left: every contact as a chip, grouped by the category of its residence (Marburg / rest of Germany /
abroad) and by place; each chip also states the birth country *as recorded*. Right: residence country
by birth country as a count matrix. The categories describe where a contact lives; they are not
groups of people and carry no ethnic or national interpretation.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from matplotlib.patches import FancyBboxPatch, Rectangle

from mares.core import ids

from ..analysis import AnalysisParams, SurveyStatus, geo_labels
from ..geo import GeoCategory
from ..model import NetworkDataset
from .common import ContactView, contact_views, draw_legend
from .style import FAINT, GEO_COLORS, GEO_ORDER, INK, MUTED, frame, label_color, new_figure, rc

_CHIP_W, _CHIP_H = 1.12, 0.70
_PER_ROW = 3
_COL_W = _PER_ROW * (_CHIP_W + 0.12) + 0.55


def _chip(ax, x: float, y: float, view: ContactView) -> None:
    fill = GEO_COLORS[view.geo]
    ax.add_patch(
        FancyBboxPatch(
            (x, y - _CHIP_H), _CHIP_W, _CHIP_H, boxstyle="round,pad=0,rounding_size=0.14", facecolor=fill,
            edgecolor=INK if view.flagged else "white", linewidth=1.5 if view.flagged else 1.0,
            linestyle=(0, (2.2, 1.6)) if view.flagged else "solid", zorder=3,
        )
    )
    color = label_color(fill)
    ax.text(x + _CHIP_W / 2, y - 0.25, view.contact_id, ha="center", va="center", fontsize=9, fontweight="bold", color=color, zorder=4)
    ax.text(x + _CHIP_W / 2, y - 0.52, f"geb. {view.birth_country or '–'}", ha="center", va="center", fontsize=6.8, color=color, zorder=4)


def geography_figure(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams):
    with rc():
        views = contact_views(dataset, params)
        labels = geo_labels(params)
        by_geo: dict[GeoCategory, list[ContactView]] = defaultdict(list)
        for view in views:
            by_geo[view.geo].append(view)
        categories = [g for g in GEO_ORDER if by_geo[g]]

        fig = new_figure(14.2, 9.0)
        frame(
            fig,
            "Geografisches Netzwerkprofil: Wohnort und Geburtsland der Kontakte",
            "Spalten = geografische Einordnung des Wohnorts; Chip = Kontakt (ID) mit Geburtsland laut Angabe der Quelle (ISO-3166-Alpha-3, „–“ = nicht erfasst oder nicht eindeutig)",
            status,
            "Die Kategorien beschreiben den Wohnort eines Kontakts, nicht die Person; Wohnland und Geburtsland werden nicht zu Herkunftsgruppen zusammengefasst. "
            "„Marburg“ nur bei exakt benanntem Ort;\nungefähre oder mehrdeutige Angaben sind nicht präzisiert (Prüfhinweise). Die Matrix zählt Kontakte, keine Beziehungen.",
        )
        ax = fig.add_axes([0.02, 0.14, 0.60, 0.74])
        ax.axis("off")
        column_h = 0.0
        for column, category in enumerate(categories):
            x0 = column * _COL_W
            members = by_geo[category]
            ax.add_patch(Rectangle((x0, 0.0), _COL_W - 0.45, 0.16, facecolor=GEO_COLORS[category], edgecolor="none", zorder=2))
            ax.text(x0, 0.30, f"{labels[category]}", fontsize=11, fontweight="bold", color=INK, va="bottom", ha="left")
            ax.text(x0 + _COL_W - 0.45, 0.30, f"n = {len(members)}", fontsize=9, color=MUTED, va="bottom", ha="right")
            places: dict[tuple[str, str], list[ContactView]] = defaultdict(list)
            for view in members:
                places[(view.city or "Ort nicht erfasst", view.residence_country or "–")].append(view)
            y = -0.25
            for (city, country), group in sorted(places.items(), key=lambda kv: (-len(kv[1]), kv[0])):
                ax.text(x0, y, f"{city} · {country}  (n = {len(group)})", fontsize=8.6, color=INK, va="top", ha="left")
                y -= 0.38
                for index, view in enumerate(sorted(group, key=lambda v: ids.contact_number(v.contact_id))):
                    row, col = divmod(index, _PER_ROW)
                    _chip(ax, x0 + col * (_CHIP_W + 0.12), y - row * (_CHIP_H + 0.12), view)
                rows = (len(group) + _PER_ROW - 1) // _PER_ROW
                y -= rows * (_CHIP_H + 0.12) + 0.34
            column_h = max(column_h, -y)
        ax.set_xlim(-0.1, max(1, len(categories)) * _COL_W)
        ax.set_ylim(-column_h - 0.1, 0.9)

        # residence country x birth country
        matrix = Counter((v.residence_country or "–", v.birth_country or "–") for v in views)
        residences = sorted({r for r, _ in matrix}, key=lambda r: (r == "–", r))
        births = sorted({b for _, b in matrix}, key=lambda b: (b == "–", b))
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
        mx.set_xticks([j + 0.5 for j in range(len(births))], births, fontsize=8)
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
            [("Zeichen", [("dot", GEO_COLORS[g], f"{labels[g]}") for g in GEO_ORDER if geo_counts[g]] + [("flag", "#FFFFFF", "gestrichelter Rand: offene Prüfhinweise")])],
            line=0.12,
        )
    return fig
