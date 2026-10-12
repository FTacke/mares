"""Figure D1: language profile of the contacts.

Every contact is a row; a dot per language says that the language was named for this contact. Several
languages stay several languages: no dominant language is derived. The mode column is the
respondent's own coding of the typical language mode. Right: the exact language repertoires that
occur, and the mode by relation type.
"""

from __future__ import annotations

from collections import Counter

from matplotlib.patches import FancyBboxPatch, Rectangle

from mares.core import ids

from ..analysis import AnalysisParams, SurveyStatus, language_combinations
from ..model import NetworkDataset
from .common import ContactView, contact_views
from .style import BAR_COLOR, FAINT, GEO_COLORS, INK, LANGUAGE_COLORS, MODE_COLORS, MUTED, frame, label_color, new_figure, rc, wrap


def _mode_rank(dataset: NetworkDataset, view: ContactView) -> int:
    codes = dataset.codebook.codes("language_mode")
    return codes.index(view.language_mode) if view.language_mode in codes else len(codes)


def language_profile_figure(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams):
    with rc():
        views = sorted(contact_views(dataset, params), key=lambda v: (_mode_rank(dataset, v), ids.contact_number(v.contact_id)))
        languages = list(dataset.codebook.codes("language"))
        fig = new_figure(14.2, 9.4)
        frame(
            fig,
            "Sprachliches Netzwerkprofil: Sprachen und Sprachmodus der Kontakte",
            "Punkt = Sprache wurde für diesen Kontakt genannt (mehrere möglich); Modus = typischer Sprachmodus laut Tabelle; Reihenfolge: nach Modus, dann ID",
            status,
            "Mehrsprachige Angaben bleiben mehrsprachig: Es wird keine dominante Sprache konstruiert, und der Modus wird nicht aus den Sprachen berechnet. "
            "Reihenfolge der Sprachspalten = Codebuch (keine Rangfolge).\nKontakte mit mehreren Beziehungstypen zählen in der Tabelle rechts unten in jeder Spalte, die sie nennen.",
        )
        ax = fig.add_axes([0.02, 0.12, 0.45, 0.76])
        n = len(views)
        col_w = 1.5
        mode_x = len(languages) * col_w + 0.6
        ax.set_xlim(-2.3, mode_x + 1.5)
        ax.set_ylim(n + 0.4, -1.6)
        ax.axis("off")
        for j, code in enumerate(languages):
            ax.text(j * col_w + 0.75, -0.65, wrap(dataset.codebook.meaning("language", code), 9), ha="center", va="center", fontsize=8, color=INK, fontweight="bold", linespacing=1.1)
        ax.text(mode_x + 0.5, -0.65, "Sprach-\nmodus", ha="center", va="center", fontsize=8, color=INK, fontweight="bold")
        previous = object()
        for i, view in enumerate(views):
            y = i + 0.5
            if view.language_mode != previous and i:
                ax.plot([-2.2, mode_x + 1.4], [i, i], color=FAINT, linewidth=0.8, zorder=1)
            previous = view.language_mode
            ax.add_patch(Rectangle((-2.2, i + 0.1), 0.14, 0.8, facecolor=GEO_COLORS[view.geo], edgecolor="none", zorder=2))
            ax.text(-1.95, y, view.contact_id, ha="left", va="center", fontsize=8.8, fontweight="bold", color=INK)
            if view.flagged:
                ax.text(-0.85, y, "◌", ha="center", va="center", fontsize=9, color=INK)
            for j, code in enumerate(languages):
                used = code in view.languages
                ax.scatter([j * col_w + 0.75], [y], s=250 if used else 14, c=LANGUAGE_COLORS.get(code, "#888888") if used else FAINT,
                           edgecolors="white" if used else "none", linewidths=0.8, zorder=3)
            if view.language_mode:
                fill = MODE_COLORS.get(view.language_mode, "#FFFFFF")
                ax.add_patch(FancyBboxPatch((mode_x + 0.15, i + 0.12), 0.7, 0.76, boxstyle="round,pad=0,rounding_size=0.12", facecolor=fill, edgecolor="#6C757D" if fill == "#FFFFFF" else "white", linewidth=0.9, linestyle=(0, (1.5, 1.2)) if fill == "#FFFFFF" else "solid", zorder=3))
                ax.text(mode_x + 0.5, y, view.language_mode, ha="center", va="center", fontsize=9, fontweight="bold", color=label_color(fill), zorder=4)
            else:
                ax.text(mode_x + 0.5, y, "–", ha="center", va="center", fontsize=9, color=MUTED)
        ax.text(-2.2, -1.45, "■ Wohnort wie in Abbildung A;  ◌ offene Prüfhinweise", fontsize=7.2, color=MUTED, ha="left", va="center")

        # repertoires
        combos = language_combinations(dataset)
        bx = fig.add_axes([0.62, 0.55, 0.36, 0.30])
        labels = [wrap(" + ".join(dataset.codebook.meaning("language", c) for c in codes), 30) for codes, _ in combos]
        counts = [len(members) for _, members in combos]
        positions = list(range(len(combos)))
        bx.barh(positions, counts, color=BAR_COLOR, height=0.62)
        bx.set_yticks(positions, labels, fontsize=8)
        bx.invert_yaxis()
        for p, c in zip(positions, counts):
            bx.text(c + 0.1, p, str(c), va="center", fontsize=8.5, color=INK)
        bx.set_xlim(0, max(counts, default=1) + 1.2)
        bx.xaxis.set_visible(False)
        for side in ("top", "right", "bottom"):
            bx.spines[side].set_visible(False)
        bx.tick_params(length=0)
        fig.text(0.62, 0.885, "Sprachrepertoires (genaue Kombinationen, Zahl der Kontakte)", fontsize=9.4, fontweight="bold", color=INK, ha="left", va="bottom")

        # mode x relation
        relation_codes = [c for c in dataset.codebook.codes("relation") if any(c in v.relations for v in views)]
        mode_codes = [c for c in dataset.codebook.codes("language_mode") if any(v.language_mode == c for v in views)]
        if mode_codes and relation_codes:
            mx = fig.add_axes([0.70, 0.14, 0.28, 0.27])
            mx.set_xlim(0, max(len(relation_codes), 1))
            mx.set_ylim(len(mode_codes), 0)
            table = Counter((v.language_mode, r) for v in views for r in v.relations)
            peak = max(table.values(), default=1)
            for i, mode in enumerate(mode_codes):
                for j, rel in enumerate(relation_codes):
                    count = table.get((mode, rel), 0)
                    shade = 0.25 + 0.65 * count / peak if count else 0.0
                    fill = (1 - shade * 0.8, 1 - shade * 0.55, 1 - shade * 0.25) if count else "#F4F6F8"
                    mx.add_patch(Rectangle((j, i), 1, 1, facecolor=fill, edgecolor="white", linewidth=1.5))
                    if count:
                        mx.text(j + 0.5, i + 0.5, str(count), ha="center", va="center", fontsize=9.5, fontweight="bold", color=INK if shade < 0.62 else "white")
            mx.set_xticks([j + 0.5 for j in range(len(relation_codes))], [wrap(dataset.codebook.meaning("relation", c), 17) for c in relation_codes], fontsize=7)
            mx.set_yticks([i + 0.5 for i in range(len(mode_codes))], [f"{m} · " + wrap(dataset.codebook.meaning("language_mode", m), 24).replace("\n", "\n    ") for m in mode_codes], fontsize=7.4)
            mx.xaxis.tick_top()
            mx.tick_params(length=0)
            for spine in mx.spines.values():
                spine.set_visible(False)
        else:
            fig.text(0.70, 0.30, "Keine Angaben zu Sprachmodus und Beziehungstyp.", fontsize=8.5, color=MUTED)
        fig.text(0.62, 0.50, "Sprachmodus (Zeilen) × Beziehungstyp (Spalten), Zahl der Kontakte", fontsize=9.4, fontweight="bold", color=INK, ha="left", va="bottom")
    return fig
