"""Shared visual conventions of all figures.

One variable keeps one colour (and one symbol) in every figure; a colour never changes its meaning
between figures. The palettes are colour-blind-safe (Okabe-Ito and Paul Tol) and the figures stay
legible in grey scale because every colour is backed by a label or a legend entry.

* geography (where the contact lives) -- blues for Germany (dark = reference place, light = rest), light orange for the rest of Europe, strong orange outside Europe, grey unknown
* language (what is spoken)           -- one colour per language; modes 1-3 reuse their language
* groups (drawn outlines)             -- a separate set of hues, used for group figures only

Rendering is deterministic: the OO API (no pyplot state, no GUI backend), a bundled font, fixed
hash salt, and no dates or software strings in the files.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Sequence

import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from ..analysis import SurveyStatus
from ..geo import GeoCategory

FONT = "DejaVu Sans"  # shipped with matplotlib: the same glyphs on every machine
RC = {
    "font.family": FONT,
    "font.size": 9,
    "svg.fonttype": "path",
    "svg.hashsalt": "mares-figures",
    "pdf.fonttype": 42,
    "axes.unicode_minus": True,
    "savefig.facecolor": "white",
}

INK = "#1F2933"
MUTED = "#5B6770"
FAINT = "#C9CED3"
PAPER = "#FFFFFF"

# Blues from dark to light follow the distance to the reference place within Germany; oranges are abroad
# (light = the rest of Europe, strong = outside Europe).
GEO_COLORS = {
    GeoCategory.LOCAL: "#0072B2",
    GeoCategory.LOCAL_REGION: "#56B4E9",
    GeoCategory.GERMANY_OTHER: "#C3DAEC",
    GeoCategory.EUROPE_OTHER: "#F3D49A",
    GeoCategory.OUTSIDE_EUROPE: "#E69F00",
    GeoCategory.UNKNOWN: "#9A9A9A",
}
GEO_ORDER = (GeoCategory.LOCAL, GeoCategory.LOCAL_REGION, GeoCategory.GERMANY_OTHER, GeoCategory.EUROPE_OTHER, GeoCategory.OUTSIDE_EUROPE, GeoCategory.UNKNOWN)

# Colours by *codebook code* of the language field; modes 1-3 name one language each.
LANGUAGE_COLORS = {"1": "#882255", "2": "#332288", "3": "#DDCC77", "4": "#44AA99", "5": "#999933"}
LANGUAGE_SHORT = {"1": "ES", "2": "DE", "3": "EN", "4": "PT", "5": "+"}
MODE_COLORS = {"1": "#882255", "2": "#332288", "3": "#DDCC77", "4": "#555555", "5": "#B8B8B8", "6": "#FFFFFF"}

GROUP_COLORS = ("#117A8B", "#D55E00", "#CC79A7", "#7A5195", "#8C6D31", "#7BA600")
CANDIDATE_COLOR = "#8A8F94"
NEUTRAL_TIE = "#3A444D"
BAR_COLOR = "#6C8EAD"


def luminance(fill: str) -> float:
    """WCAG relative luminance of a ``#RRGGBB`` colour."""
    value = fill.lstrip("#")
    r, g, b = (int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))

    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def label_color(fill: str) -> str:
    """Black or white label, whichever contrasts with the fill."""
    return "#FFFFFF" if luminance(fill) < 0.30 else "#111111"


def rim_color(fill: str) -> str:
    """A pale fill needs a visible rim on a pale background; a dark one gets a white rim."""
    return "#6B7A88" if luminance(fill) > 0.45 else "#FFFFFF"


def group_color(group_id: str, ordered_group_ids: Sequence[str]) -> str:
    index = list(ordered_group_ids).index(group_id)
    return GROUP_COLORS[index % len(GROUP_COLORS)]


def wrap(text: str, width: int = 30) -> str:
    return "\n".join(textwrap.wrap(text, width, break_long_words=False)) or text


def new_figure(width: float, height: float) -> Figure:
    figure = Figure(figsize=(width, height), dpi=100, facecolor=PAPER)
    FigureCanvasAgg(figure)
    return figure


def frame(figure: Figure, title: str, subtitle: str, status: SurveyStatus, note: str) -> None:
    """Title block on top, status stamp and methodological note at the bottom."""
    height = figure.get_figheight()
    figure.text(0.03, 1 - 0.22 / height, title, fontsize=14.5, fontweight="bold", color=INK, ha="left", va="top")
    figure.text(0.03, 1 - 0.58 / height, subtitle, fontsize=9.2, color=MUTED, ha="left", va="top")
    width = max(60, int(figure.get_figwidth() * 13.2))  # characters per line at this size
    wrapped = "\n".join(wrap(paragraph, width) for paragraph in note.split("\n"))
    figure.text(0.03, 0.036, wrapped, fontsize=7.6, color=INK, ha="left", va="bottom", linespacing=1.35)
    figure.text(0.03, 0.012, status.stamp(), fontsize=7.2, color=MUTED, ha="left", va="bottom")


def save_figure(figure: Figure, stem: Path, formats: Sequence[str] = ("svg", "png", "pdf")) -> list[Path]:
    """Write the figure in every format, byte-reproducible; returns the paths."""
    written = []
    for fmt in formats:
        target = stem.with_suffix("." + fmt)
        kwargs: dict[str, object] = {"format": fmt}
        if fmt == "svg":
            kwargs["metadata"] = {"Date": None, "Creator": None}
        elif fmt == "png":
            kwargs.update(dpi=200, metadata={"Software": None})
        elif fmt == "pdf":
            kwargs["metadata"] = {"Creator": None, "Producer": None, "CreationDate": None}
        with matplotlib.rc_context(RC):
            figure.savefig(target, **kwargs)
        written.append(target)
    return written


def rc():
    """Context for building *and* saving a figure: text properties are fixed when text is created."""
    return matplotlib.rc_context(RC)
