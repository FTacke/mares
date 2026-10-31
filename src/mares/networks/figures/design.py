"""The MARES design system for the reduced ("clean") figures: tokens and a few building blocks.

Kept deliberately small: constants for type sizes, node and line sizes, tie colours and emphasis, plus
three helpers -- a title block, a compact legend strip and a one-line interpretation hint. Palettes of the
*variables* (geography, language, groups) stay in :mod:`style`; this module only adds how they are shown.

Two profiles, one analysis:

* ``clean``    -- for presentation and publication: short title, at most one context line, a compact
  legend, one short hint, a short provenance line. Everything else lives in the documentation and in
  ``figures/figures_index.json``.
* ``analysis`` -- the working version: the same data, the same layout, with the fuller notes and counts.

Font: DejaVu Sans, shipped with matplotlib (same glyphs on every machine, byte-reproducible figures). A
preferred face such as Source Sans 3 is not used: it would make the files depend on the machine.
Regular and bold only.
"""

from __future__ import annotations

import re
from typing import Sequence

from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from ..analysis import AnalysisParams, SurveyStatus, geo_labels
from ..geo import GeoCategory
from .style import FAINT, INK, MUTED, frame, label_color, rim_color, wrap

PROFILES = ("clean", "analysis")


def zone_name(category: GeoCategory, params: AnalysisParams) -> str:
    """The name of a geographic category as it is written in figures: Marburg (or the configured reference place),
    Region Marburg, übriges Deutschland, übriges Europa, außerhalb Europas."""
    return geo_labels(params)[category].replace(" (ungefähre Angabe)", "")


def check_profile(profile: str) -> str:
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}; one of {', '.join(PROFILES)}")
    return profile


# ------------------------------------------------------------------ type (points) -------------------------
# Four sizes only: a title, one text size for everything that is read (subtitle, captions, legend, hint), the contact
# ids, and a small size for the provenance line and the fuller notes of the analysis profile.
TITLE_PT = 16.0
TEXT_PT = 10.0
ID_PT = 9.0  # contact ids next to a node
SMALL_PT = 8.0
CONTEXT_PT = CAPTION_PT = LEGEND_PT = HINT_PT = TEXT_PT
STAMP_PT = NOTE_PT = SMALL_PT

# ------------------------------------------------------------------ nodes and lines -----------------------
NODE_DIAMETER_PT = 12.5
EGO_DIAMETER_PT = 26.0
EGO_LABEL_PT = 8.0

TIE_STRONG = "#1F2933"  # an emphasised tie
TIE_NORMAL = "#7D8892"  # a confirmed contact-contact tie
TIE_MUTED = "#AEB8C2"  # a tie that steps back while another kind is emphasised
EGO_LINE = "#CAD1D8"  # ego-contact line: belongs to the network, is not a surveyed relation; always the faintest
TIE_WIDTH_PT = 0.8
TIE_STRONG_WIDTH_PT = 1.8
TIE_MUTED_WIDTH_PT = 0.7
EGO_LINE_WIDTH_PT = 0.55

MUTED_FILL = "#E6E9ED"  # a node outside the emphasis
MUTED_RIM = "#B5BEC7"
UNKNOWN_FILL = "#FFFFFF"  # no statement: white with a dotted rim, never a colour of a category

GROUP_FILL_ALPHA = 0.065  # surveyed groups: soft areas that never compete with the lines
GROUP_LINE_ALPHA = 0.38
GROUP_TAG_PT = 9.0

# ------------------------------------------------------------------ page ----------------------------------
PAGE_MARGIN = 0.03  # fraction of the width


def stamp_text(status: SurveyStatus, profile: str = "clean") -> str:
    """The provenance line. Clean: ``MARES · 001-2 · vorläufig`` -- the case and that the data are not reviewed. The full
    provenance (session, survey type, n, quality state) is in ``figures_index.json`` and in the analysis profile."""
    if profile == "clean":
        return f"MARES · {status.source_label} · vorläufig"
    parts = [status.source_label]
    if status.session_date:
        parts.append(status.session_date)
    if status.interview_type:
        parts.append(status.interview_type)
    parts.append(f"n = {status.contacts}")
    parts.append(f"ungeprüft ({status.quality_state.value})")
    return " · ".join(parts)


def clean_frame(
    figure: Figure,
    title: str,
    context: str | None,
    hint: str,
    status: SurveyStatus,
    *,
    note: str | None = None,
    profile: str = "clean",
) -> tuple[float, float]:
    """Title block on top, hint and provenance at the bottom. Returns ``(top, bottom)`` of the free area (figure fractions).

    ``note`` is the fuller text of the analysis profile (printed above the hint); the clean profile ignores it.
    """
    height, width = figure.get_figheight(), figure.get_figwidth()
    x = PAGE_MARGIN
    figure.text(x, 1 - 0.20 / height, title, fontsize=TITLE_PT, fontweight="bold", color=INK, ha="left", va="top")
    top = 1 - 0.62 / height
    if context:
        figure.text(x, 1 - 0.66 / height, context, fontsize=CONTEXT_PT, color=MUTED, ha="left", va="top")
        top = 1 - 1.02 / height
    chars = lambda pt: max(40, int((width * (1 - 2 * PAGE_MARGIN)) * 72 / (0.56 * pt)))  # characters per line
    block = wrap(hint, chars(HINT_PT))
    bottom = 0.40  # inches: provenance line and its margin
    figure.text(x, 0.14 / height, stamp_text(status, profile), fontsize=STAMP_PT, color=MUTED, ha="left", va="bottom")
    figure.text(x, bottom / height, block, fontsize=HINT_PT, color=INK, ha="left", va="bottom", linespacing=1.3)
    used = bottom + (block.count("\n") + 1) * HINT_PT * 1.3 / 72
    if note and profile == "analysis":
        text = "\n".join(wrap(paragraph, chars(NOTE_PT)) for paragraph in note.split("\n"))
        figure.text(x, (used + 0.10) / height, text, fontsize=NOTE_PT, color=MUTED, ha="left", va="bottom", linespacing=1.3)
        used += 0.10 + (text.count("\n") + 1) * NOTE_PT * 1.3 / 72
    return top, (used + 0.12) / height


def frame_for(profile: str, figure: Figure, title: str, subtitle: str, status: SurveyStatus, note: str, *,
              short_title: str | None = None, hint: str | None = None) -> None:
    """The frame of the older figures (A, B1, B2, G1, C, D1, D2, E).

    ``analysis``: the frame they always had (long title, subtitle, methodological note, full status line).
    ``clean``: a short title, one short hint and the provenance line -- the explanations are in the figure register.
    """
    check_profile(profile)
    if profile == "analysis":
        frame(figure, title, subtitle, status, note)
        return
    height = figure.get_figheight()
    figure.text(PAGE_MARGIN, 1 - 0.22 / height, short_title or title, fontsize=TITLE_PT, fontweight="bold", color=INK, ha="left", va="top")
    if hint:
        figure.text(PAGE_MARGIN, 0.40 / height, hint, fontsize=HINT_PT, color=INK, ha="left", va="bottom")
    figure.text(PAGE_MARGIN, 0.14 / height, stamp_text(status, "clean"), fontsize=STAMP_PT, color=MUTED, ha="left", va="bottom")


_COUNT = re.compile(r"\s*\(n = \d+\)")
_SIZE = re.compile(r": \d+ Kontakte")


def lean_sections(sections, profile: str):
    """The legend sections of the older figures for the ``clean`` profile: no contact counts, no remarks in brackets, no place lists --
    the categories are named once, directly. ``analysis`` keeps the sections as they are."""
    if profile == "analysis":
        return sections
    lean = []
    for title, entries in sections:
        cleaned = []
        for kind, color, text in entries:
            text = text.split("\n     ")[0]  # the place list / "(keine Kontakte)" tail of an entry
            text = _SIZE.sub("", _COUNT.sub("", text)).replace(" (ungefähre Angabe)", "")
            cleaned.append((kind, color, text))
        lean.append((title, cleaned))
    return lean


# ------------------------------------------------------------------ legend strip --------------------------

# entry: (kind, colour, label); kind: dot | ring | line | area | mark (colour = the character)
Entry = tuple[str, str, str]


def _text_width_pt(label: str, size: float) -> float:
    return 0.58 * size * len(label)


def legend_strip(figure: Figure, entries: Sequence[Entry], *, top: float, x: float = PAGE_MARGIN, width: float | None = None,
                 size: float = LEGEND_PT) -> float:
    """A compact legend as one or two rows below the title; returns the figure fraction where it ends.

    ``top`` is the figure fraction of its upper edge. Entries wrap to a new row when the row is full.
    """
    fig_w, fig_h = figure.get_figwidth(), figure.get_figheight()
    right = x + (width if width is not None else 1 - 2 * PAGE_MARGIN)
    cursor_x, row_y = x, top
    row_h = 0.30 / fig_h  # figure fraction per row
    gap = 20.0 / 72 / fig_w
    marker_w = 17.0 / 72 / fig_w
    for kind, color, label in entries:
        need = marker_w + _text_width_pt(label, size) / 72 / fig_w + gap
        if cursor_x + need > right and cursor_x > x:
            cursor_x, row_y = x, row_y - row_h
        y = row_y - 0.11 / fig_h
        if kind in ("dot", "ring"):
            figure.add_artist(Line2D([cursor_x + 5 / 72 / fig_w], [y], transform=figure.transFigure, marker="o", markersize=8.2,
                                     markerfacecolor="none" if kind == "ring" else color, markeredgecolor=color if kind == "ring" else rim_color(color),
                                     markeredgewidth=1.4 if kind == "ring" else 0.9, linestyle="none"))
        elif kind == "line":
            figure.add_artist(Line2D([cursor_x, cursor_x + 11 / 72 / fig_w], [y, y], transform=figure.transFigure, color=color, linewidth=2.0,
                                     solid_capstyle="round"))
        elif kind == "area":
            figure.add_artist(Rectangle((cursor_x, y - 0.065 / fig_h), 11 / 72 / fig_w, 0.13 / fig_h, transform=figure.transFigure,
                                        facecolor=color, alpha=0.35, edgecolor=color, linewidth=0.9))
        elif kind == "mark":
            figure.text(cursor_x + 5 / 72 / fig_w, y, color, fontsize=size, color=INK, ha="center", va="center")
        figure.text(cursor_x + marker_w, y, label, fontsize=size, color=INK, ha="left", va="center")
        cursor_x += need
    return row_y - row_h * 0.85
