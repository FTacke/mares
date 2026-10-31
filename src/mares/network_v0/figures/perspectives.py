"""Analytic perspectives P1-P3: three questions asked of every personal network, one design.

Each perspective is **a base layout + an attribute view + an emphasis**, not a new diagram type:

* **P1  Räumliche Einordnung und subjektive Nähe** -- a matrix of residence category x surveyed closeness, one chip per
  contact. Question: how do the geographic classification of the contacts and their subjective closeness to ego relate?
* **P2  Sprachliche Praktiken in sozialen Teilgruppen** -- the structure layout of B2/B3 (positions unchanged), the surveyed groups
  as soft areas, and a configurable *language view*. Question: how are language practices distributed over the social
  sub-groups of the network? Language belongs to the communication between ego and a contact, so the view colours the
  contacts and the ego lines, never the ties between contacts.
* **P3  Wohnort, Kontakthäufigkeit und Kommunikationsmedien** -- the same matrix with contact frequency in the rows and the
  named media as small symbols on each chip. Question: what role do media and frequency play in local and distant
  relations?

The three spatial meanings stay apart: P1/P3 place a contact by *category and ordinal rank* (no network, no distance), P2 by
the *structure of the ties* (B2). Nothing here is a result: the figures make constellations visible and claim no cause.
Emphasis (a set of contact ids, a language, a mode) steps other contacts back; it never changes a position or a tie.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Iterable

from matplotlib.patches import Rectangle

from mares.core import ids

from ..analysis import AnalysisParams, SurveyStatus
from ..build import Network
from ..geo import GeoCategory
from ..model import NetworkDataset
from . import design, geo_zones
from .common import ContactView, contact_views
from .ego_network import DrawStyle, build_ego_structure, draw_ego_structure, fit_height
from .network import _frame_axes, _to_pt, draw_groups
from .style import GEO_COLORS, INK, LANGUAGE_COLORS, MODE_COLORS, MUTED, label_color, new_figure, rc, rim_color, wrap

# ---------------------------------------------------------------- media classes (configurable) ------------
# (key, codebook codes, marker, character in the legend, legend text). Instrument-specific: a new instrument version
# edits this table, not the drawing. Codes not listed (e.g. "other medium") are neither marked nor counted.
MEDIA_CLASSES = (
    ("personal", ("1",), "o", "●", "persönlich"),
    ("phone", ("4",), "^", "▲", "Telefon"),
    ("digital", ("2", "3", "5", "6", "7"), "s", "■", "digital"),
)


def media_classes(codes: Iterable[str]) -> set[str]:
    """The classes of communication named for a contact: ``personal``, ``phone``, ``digital``. A contact may have several."""
    named = set(codes)
    return {key for key, members, *_ in MEDIA_CLASSES if named & set(members)}


# ---------------------------------------------------------------- matrix (P1, P3) --------------------------
# The matrix is laid out in points (one data unit = one point), so dots and ids keep their size at any number of contacts.
PAGE_W_PT = 13.0 * 0.96 * 72
LABEL_W_PT = 150.0
ITEM_W_PT = 50.0  # a dot with its id
ITEM_W_MEDIA_PT = 70.0  # ... and the media marks
ITEM_H_PT = 22.0
CELL_PAD_PT = 9.0
HEADER_H_PT = 46.0


def _raw(dataset: NetworkDataset, attribute: str) -> dict[str, str | None]:
    return {c.contact_id: c.single(attribute) for c in dataset.contacts}


def _ordinal_rows(dataset: NetworkDataset, field: str, values: dict[str, str | None]) -> list[tuple[str | None, str]]:
    """Codebook rows from the highest code down; a final row for 'not recorded' only if somebody has no value."""
    codes = sorted(dataset.codebook.codes(field), key=lambda c: -int(c) if c.isdigit() else 0)
    rows: list[tuple[str | None, str]] = [(c, f"{c} · {dataset.codebook.meaning(field, c)}") for c in codes]
    if any(v not in codes for v in values.values()):
        rows.append((None, "nicht erfasst"))
    return rows


def matrix_cells(dataset: NetworkDataset, params: AnalysisParams, row_attribute: str, field: str):
    """The cells of a zone x ordinal matrix: ``(rows, zones, cells)`` with ``cells[(zone, row code)] = contact ids``.

    A contact is placed by its residence category and the *surveyed* value of ``row_attribute``; a contact without a value
    stands in the row ``None`` ("nicht erfasst"), never in a guessed one. Empty rows and zones stay.
    """
    views = contact_views(dataset, params)
    values = _raw(dataset, row_attribute)
    rows = _ordinal_rows(dataset, field, values)
    known = {code for code, _ in rows}
    cells: dict[tuple[GeoCategory, str | None], list[str]] = defaultdict(list)
    for view in sorted(views, key=lambda v: ids.contact_number(v.contact_id)):
        value = values[view.contact_id]
        cells[(view.geo, value if value in known else None)].append(view.contact_id)
    return rows, geo_zones.zones_present(views), cells


def _item(ax, x: float, y: float, view: ContactView, *, marks: set[str] | None, muted: bool) -> None:
    """One contact: a dot in the colour of its residence category, its id beside it and, in P3, the media marks."""
    fill = design.MUTED_FILL if muted else GEO_COLORS[view.geo]
    ax.scatter([x], [y], s=design.NODE_DIAMETER_PT**2, c=fill, edgecolors=design.MUTED_RIM if muted else rim_color(fill), linewidths=0.8, zorder=4)
    ax.text(x + 9.5, y, view.contact_id, fontsize=design.ID_PT, color=MUTED if muted else INK, ha="left", va="center", zorder=5)
    if marks is None:
        return
    base = x + 9.5 + 25.0
    if not marks:
        ax.text(base + 9, y, "–", fontsize=design.ID_PT, color=MUTED, ha="center", va="center", zorder=5)
    for slot, (key, _, marker, _, _) in enumerate(MEDIA_CLASSES):
        if key in marks:
            ax.scatter([base + 9.0 * slot], [y], s=20, marker=marker, c=MUTED if muted else INK, linewidths=0, zorder=5)


def _matrix(
    dataset: NetworkDataset,
    status: SurveyStatus,
    params: AnalysisParams,
    *,
    row_attribute: str,
    field: str,
    row_caption: str,
    title: str,
    context: str,
    hint: str,
    note: str,
    show_media: bool,
    profile: str,
    highlight: Iterable[str] | None,
):
    design.check_profile(profile)
    with rc():
        views = contact_views(dataset, params)
        by_id = {v.contact_id: v for v in views}
        rows, zones, cells = matrix_cells(dataset, params, row_attribute, field)
        keep = None if highlight is None else set(highlight)
        media = {c.contact_id: media_classes(c.code_list("media")) if c.code_list("media") else set() for c in dataset.contacts}
        item_w = ITEM_W_MEDIA_PT if show_media else ITEM_W_PT
        column_w = (PAGE_W_PT - LABEL_W_PT) / len(zones)
        per_row = max(1, int((column_w - CELL_PAD_PT) // item_w))
        row_heights = []
        for code, _ in rows:
            need = max([math.ceil(len(cells[(z, code)]) / per_row) for z in zones] + [1])
            row_heights.append(need * ITEM_H_PT + 2 * CELL_PAD_PT - 4)
        axes_h_pt = HEADER_H_PT + sum(row_heights) + 6
        fig = new_figure(13.0, max(4.4, axes_h_pt / 72) + 2.0)
        entries = [("mark", char, text) for _, _, _, char, text in MEDIA_CLASSES] + [("mark", "–", "nicht erfasst")] if show_media else []
        top, bottom = design.clean_frame(fig, title, context, hint, status, note=note, profile=profile)
        if entries:
            top = design.legend_strip(fig, entries, top=top)
        ax = fig.add_axes([0.02, bottom, 0.96, top - bottom])
        height_pt = (top - bottom) * fig.get_figheight() * 72
        ax.set_xlim(0, PAGE_W_PT)
        ax.set_ylim(-height_pt, 0)
        ax.axis("off")
        for column, zone in enumerate(zones):  # the column heads are the zone names; the dots carry the colour
            cx = LABEL_W_PT + column * column_w
            count = sum(len(cells[(zone, code)]) for code, _ in rows)
            ax.text(cx + column_w / 2, -6, wrap(design.zone_name(zone, params), 16) + (f"\nn = {count}" if profile == "analysis" else ""),
                    fontsize=design.CAPTION_PT, fontweight="bold", color=INK, ha="center", va="top", linespacing=1.2)
        y = -HEADER_H_PT
        for index, ((code, label), height) in enumerate(zip(rows, row_heights)):
            ax.add_patch(Rectangle((0, y - height), PAGE_W_PT, height, facecolor="#F6F8FA" if index % 2 == 0 else "#FFFFFF", edgecolor="none", zorder=1))
            ax.text(8, y - height / 2, wrap(label, 24), fontsize=design.LEGEND_PT, color=INK, ha="left", va="center", linespacing=1.2, zorder=4)
            for column, zone in enumerate(zones):
                for k, contact_id in enumerate(cells[(zone, code)]):
                    r, c = divmod(k, per_row)
                    _item(ax, LABEL_W_PT + column * column_w + CELL_PAD_PT + 6 + c * item_w, y - CELL_PAD_PT - 6 - r * ITEM_H_PT, by_id[contact_id],
                          marks=media[contact_id] if show_media else None, muted=keep is not None and contact_id not in keep)
            y -= height
        ax.text(8, -HEADER_H_PT + 8, row_caption, fontsize=design.SMALL_PT, color=MUTED, ha="left", va="bottom")
    return fig


def distance_closeness_figure(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams, *, network: Network | None = None,
                              profile: str = "clean", highlight: Iterable[str] | None = None):
    """P1: residence category (columns) x subjective closeness (rows), one chip per contact.

    The rows are the *surveyed* table value (1-5); the columns are categories, not kilometres. A contact without a closeness
    value stands in its own row 'nicht erfasst' -- its closeness is never estimated. ``highlight`` is a set of contact ids that stay
    in colour while the others step back (a place to point at single contacts later).
    """
    return _matrix(
        dataset, status, params,
        row_attribute="closeness", field="closeness_1_5", row_caption="Subjektive Nähe (Tabellenwert)",
        title="Räumliche Einordnung und subjektive Nähe",
        context="Wohnort-Kategorie (Spalten) und erhobene Nähe zu Ego (Zeilen)",
        hint="Spalten sind Kategorien, keine Entfernungen.",
        note=("Gesucht sind Konstellationen wie räumlich entfernte, aber sehr nahe Kontakte oder lokal wohnende, eher periphere Kontakte. "
              "Die Zeilen sind die erhobenen Nähewerte; eine Zeile ohne Kontakt bleibt sichtbar; Kontakte ohne Nähewert stehen in der Zeile „nicht erfasst“. "
              "Das Bild zeigt Konstellationen, keine Ursachen."),
        show_media=False, profile=profile, highlight=highlight,
    )


def geography_communication_figure(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams, *, network: Network | None = None,
                                   profile: str = "clean", highlight: Iterable[str] | None = None):
    """P3: residence category (columns) x contact frequency (rows); the named media as symbols on each chip.

    The primary message is the relation of geography and contact frequency; the media are a second, quieter layer. Media are
    multiple answers: personal and digital communication can occur together, and naming a digital medium does not say that
    a relation is mainly digital. The frequency is the one asked for the relation as a whole, not per medium.
    """
    return _matrix(
        dataset, status, params,
        row_attribute="contact_frequency", field="contact_frequency", row_caption="Kontakthäufigkeit (insgesamt)",
        title="Wohnort, Kontakthäufigkeit und Kommunikationsmedien",
        context="Wohnort-Kategorie (Spalten), Kontakthäufigkeit (Zeilen), genannte Medien (Symbole)",
        hint="Medien sind Mehrfachangaben; die Häufigkeit gilt für die Beziehung insgesamt.",
        note=("Gesucht sind Konstellationen wie transnationale Kontakte mit häufiger Kommunikation, lokal wohnende Kontakte, die digital erreicht werden, "
              "oder Beziehungen mit mehreren Medien. Telefon, persönlich und digital sind getrennte Symbole; „anderes Medium“ wird nicht markiert."),
        show_media=True, profile=profile, highlight=highlight,
    )


# ---------------------------------------------------------------- P2: language views ------------------------

class LanguageView:
    """What a language view does to the contacts, resolved from a spec such as ``mode``, ``lang:1``, ``mode:2`` or ``multilingual``.

    ``fills`` colour the contacts, ``line_colors`` colour the ego lines of the emphasised contacts, ``rings`` mark contacts that
    name several languages. Contacts without a statement are white with a grey rim -- never a category colour.
    """

    def __init__(self, dataset: NetworkDataset, spec: str) -> None:
        kind, _, arg = spec.partition(":")
        if kind not in ("mode", "lang", "multilingual") or (kind == "lang") != (kind == "lang" and bool(arg)) or (kind == "multilingual" and arg):
            raise ValueError(f"unknown language view {spec!r}; use mode, mode:<code>, lang:<code> or multilingual")
        self.spec, self.kind, self.arg = spec, kind, arg
        book = dataset.codebook
        if kind == "lang" and not book.is_valid("language", arg):
            raise ValueError(f"language code {arg!r} is not in the codebook")
        if kind == "mode" and arg and not book.is_valid("language_mode", arg):
            raise ValueError(f"language mode {arg!r} is not in the codebook")
        self.dataset = dataset
        self.languages = {c.contact_id: c.code_list("language") for c in dataset.contacts}
        self.modes = {c.contact_id: c.single("language_mode") for c in dataset.contacts}

    # ---- per contact
    def _known(self, contact_id: str) -> bool:
        if self.kind == "mode":
            return self.modes[contact_id] is not None
        return bool(self.languages[contact_id])

    def emphasised(self, contact_id: str) -> bool:
        languages, mode = self.languages[contact_id], self.modes[contact_id]
        if self.kind == "lang":
            return self.arg in languages
        if self.kind == "multilingual":
            return len(languages) >= 2
        return mode == self.arg if self.arg else True

    def fill(self, contact_id: str) -> str:
        if not self._known(contact_id):
            return design.UNKNOWN_FILL
        if self.kind == "mode":
            if self.arg and not self.emphasised(contact_id):
                return design.MUTED_FILL
            return MODE_COLORS.get(self.modes[contact_id], "#FFFFFF")
        if not self.emphasised(contact_id):
            return design.MUTED_FILL
        return LANGUAGE_COLORS.get(self.arg, "#888888") if self.kind == "lang" else "#3A444D"

    def rim(self, contact_id: str) -> str | None:
        fill = self.fill(contact_id)
        if fill == design.UNKNOWN_FILL:
            return design.MUTED_RIM
        if fill == design.MUTED_FILL:
            return design.MUTED_RIM
        return "#6C757D" if fill == "#FFFFFF" else None

    def ring(self, contact_id: str) -> bool:
        return self.kind == "mode" and len(self.languages[contact_id]) >= 2

    def line_color(self, contact_id: str) -> str | None:
        if self.kind == "mode" or not self.emphasised(contact_id) or not self._known(contact_id):
            return None
        return LANGUAGE_COLORS.get(self.arg, "#888888") if self.kind == "lang" else "#3A444D"

    # ---- text
    def language_name(self) -> str:
        return self.dataset.codebook.meaning("language", self.arg)

    def context(self) -> str:
        book = self.dataset.codebook
        if self.kind == "lang":
            return f"Kontakte, mit denen {self.language_name()} genannt wird"
        if self.kind == "multilingual":
            return "Kontakte, mit denen mehrere Sprachen genannt werden"
        if self.arg:
            return f"Sprachmodus „{book.meaning('language_mode', self.arg)}“"
        return "Typischer Sprachmodus (Farbe), mehrere genannte Sprachen (Ring)"

    def entries(self, contact_ids: list[str], profile: str) -> list[tuple[str, str, str]]:
        book = self.dataset.codebook
        count = Counter()
        suffix = (lambda n: f"  (n = {n})") if profile == "analysis" else (lambda n: "")
        unknown = [c for c in contact_ids if not self._known(c)]
        out: list[tuple[str, str, str]] = []
        if self.kind == "mode":
            for code in book.codes("language_mode"):
                n = sum(1 for c in contact_ids if self.modes[c] == code)
                if n and (not self.arg or code == self.arg):
                    out.append(("dot", MODE_COLORS.get(code, "#FFFFFF"), book.meaning("language_mode", code) + suffix(n)))
            if self.arg:
                out.append(("dot", design.MUTED_FILL, "andere Sprachmodi"))
            else:
                out.append(("ring", INK, "mehrere Sprachen genannt"))
        elif self.kind == "lang":
            out += [("dot", LANGUAGE_COLORS.get(self.arg, "#888888"), f"nennt {self.language_name()}" + suffix(sum(1 for c in contact_ids if self.emphasised(c)))),
                    ("dot", design.MUTED_FILL, f"nennt {self.language_name()} nicht" + suffix(sum(1 for c in contact_ids if self._known(c) and not self.emphasised(c)))),
                    ("line", LANGUAGE_COLORS.get(self.arg, "#888888"), "Ego – Kontakt mit dieser Sprache")]
        else:
            out += [("dot", "#3A444D", "mehrere Sprachen genannt" + suffix(sum(1 for c in contact_ids if self.emphasised(c)))),
                    ("dot", design.MUTED_FILL, "eine Sprache genannt" + suffix(sum(1 for c in contact_ids if self._known(c) and not self.emphasised(c)))),
                    ("line", "#3A444D", "Ego – Kontakt mit mehreren Sprachen")]
        if unknown:
            out.append(("ring", design.MUTED_RIM, "keine Angabe" + suffix(len(unknown))))
        return out


def language_groups_figure(
    dataset: NetworkDataset,
    status: SurveyStatus,
    params: AnalysisParams,
    *,
    network: Network,
    view: str = "mode",
    profile: str = "clean",
    show_groups: bool = True,
):
    """P2: the structure layout of B2/B3 with a language view; the positions never change with the view.

    ``view``: ``mode`` (typical language mode as colour, several named languages as a ring), ``mode:<code>``, ``lang:<code>`` (who names
    this language, e.g. Spanish) or ``multilingual``. The surveyed groups are the soft areas of B2/B3.
    """
    design.check_profile(profile)
    lv = LanguageView(dataset, view)
    with rc():
        es = build_ego_structure(network)  # the contact positions of B2, ego added as in B3
        contact_ids = sorted(es.structure.positions, key=ids.contact_number)
        colors = {c: lv.fill(c) for c in contact_ids}
        style = DrawStyle(
            node_pt=design.NODE_DIAMETER_PT, ego_pt=design.EGO_DIAMETER_PT, ego_label_pt=design.EGO_LABEL_PT, font_pt=design.ID_PT,
            tie_color="#A9B3BC", tie_width=design.TIE_WIDTH_PT, tie_alpha=0.9, ego_line_color=design.EGO_LINE, ego_line_width=design.EGO_LINE_WIDTH_PT,
            ego_line_colors=tuple((c, lv.line_color(c)) for c in contact_ids if lv.line_color(c)),
            ego_line_widths=tuple((c, 1.4) for c in contact_ids if lv.line_color(c)),
            rim_colors=tuple((c, lv.rim(c)) for c in contact_ids if lv.rim(c)),
            rim_widths=tuple((c, 1.0) for c in contact_ids if lv.rim(c)),
            rings=tuple(c for c in contact_ids if lv.ring(c)),
        )
        width = 13.0
        axes_h = fit_height(es.positions, 0.16, width * 0.96, 5.6, 7.4)
        fig = new_figure(width, axes_h + 2.25)
        hint = "Die Sprache gilt für die Kommunikation zwischen Ego und Kontakt."
        note = ("Der Sprachmodus ist die codierte Angabe zum typischen Sprachgebrauch; die genannten Sprachen sind eine eigene Angabe, keine Ableitung des Modus. "
                "Die Anordnung ist die Struktur der erhobenen Kontakt–Kontakt-Beziehungen (B2); die Flächen sind die erhobenen Kontaktgruppen. "
                "Linien und Positionen ändern sich mit der Sprachansicht nicht. Der Abstand zu Ego zeigt keine Nähe.")
        top, bottom = design.clean_frame(fig, "Sprachliche Praktiken in Teilgruppen", lv.context(), hint, status,
                                         note=note + " Mehrere genannte Sprachen bleiben mehrere; aus ihnen wird keine Hauptsprache abgeleitet.", profile=profile)
        top = design.legend_strip(fig, lv.entries(contact_ids, profile), top=top)
        ax = fig.add_axes([0.02, bottom, 0.96, top - bottom])
        _frame_axes(ax, es.positions, margin=0.16)
        boxes = draw_ego_structure(ax, es, colors, style=style)
        if show_groups:
            ego_pt = _to_pt(ax, es.ego)
            draw_groups(ax, es.structure, network, boxes, fill_alpha=design.GROUP_FILL_ALPHA, line_alpha=design.GROUP_LINE_ALPHA,
                        extra_obstacles=((ego_pt[0], ego_pt[1], design.EGO_DIAMETER_PT / 2),), tag_pt=design.GROUP_TAG_PT, node_pt=design.NODE_DIAMETER_PT)
    return fig
