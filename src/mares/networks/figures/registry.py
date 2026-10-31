"""The register of the figures: which figures exist, in which tier, with which profiles -- and how a run builds them.

Three tiers divide the repertoire (the division concerns the register and the regular exports, not the figure functions;
nothing was deleted and every figure stays reproducible):

* ``core``          -- the few central scientific figures, for the visual case portrait;
* ``supplementary`` -- further analytical views and the descriptive overviews;
* ``diagnostic``    -- technical figures: layout comparisons, measures, earlier versions kept for traceability.

Core and supplementary figures come in two profiles (``clean`` and ``analysis``, see :mod:`design`); a diagnostic figure
has one look. A run writes ``figures/<tier>/<stem>`` (clean), ``figures/analysis/<tier>/<stem>`` (analysis) and
``figures/figures_index.json`` (the register of the run).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..analysis import AnalysisParams, SurveyStatus
from ..build import Network
from ..model import NetworkDataset
from . import design, ego, ego_network, geo_network, geo_zones, geography, language, overview, perspectives
from . import network as network_figures
from .figure_notes import note_for

TIERS = ("core", "supplementary", "diagnostic")


@dataclass(frozen=True)
class FigureOptions:
    """Choices that change how the figures look, never what they show: the profiles, the language view of P2 (``mode``,
    ``mode:<code>``, ``lang:<code>``, ``multilingual``) and the emphasis of ties in G2 (``between``, ``within`` or none)."""

    profiles: tuple[str, ...] = design.PROFILES
    language_view: str = "mode"
    tie_highlight: str | None = "between"

    def __post_init__(self) -> None:
        for profile in self.profiles:
            design.check_profile(profile)
        if not self.profiles:
            raise ValueError("at least one profile")
        if self.tie_highlight not in geo_zones.HIGHLIGHTS:
            raise ValueError("tie_highlight is 'between', 'within' or None")

    def to_dict(self) -> dict[str, object]:
        return {"profiles": list(self.profiles), "language_view": self.language_view, "tie_highlight": self.tie_highlight}


@dataclass(frozen=True)
class FigureContext:
    """What a run has computed once for all figures."""

    dataset: NetworkDataset
    status: SurveyStatus
    params: AnalysisParams
    network: Network
    structure: network_figures.Structure  # one layout for B1 and B2
    ego_structure: ego_network.EgoStructure  # B3 and P2: the same contact positions, ego added
    options: FigureOptions = FigureOptions()


@dataclass(frozen=True)
class FigureSpec:
    stem: str
    tier: str
    build: Callable[[FigureContext, str], object]
    profiles: bool = True  # False: one look (diagnostic figures)
    candidate: bool = False  # the current candidate for a figure family; the final decision is the project lead's
    legacy: bool = False  # an earlier version, kept for traceability

    def __post_init__(self) -> None:
        if self.tier not in TIERS:
            raise ValueError(f"unknown tier {self.tier!r}")


def _plain(function):
    return lambda c, profile: function(c.dataset, c.status, c.params, profile=profile)


def _net(function, **kwargs):
    return lambda c, profile: function(c.dataset, c.status, c.params, network=c.network, profile=profile, **kwargs)


def _diagnostic(function):
    return lambda c, profile: function(c.dataset, c.status, c.params, network=c.network)


SPECS: tuple[FigureSpec, ...] = (
    # ---- core
    FigureSpec("fig_B3_ego_netzwerk", "core", lambda c, p: ego_network.ego_network_figure(c.dataset, c.status, c.params, network=c.network, structure=c.ego_structure, profile=p)),
    FigureSpec("fig_G2b_geografisches_kraftlayout", "core",
               lambda c, p: geo_network.geographic_radial_figure(c.dataset, c.status, c.params, network=c.network, profile=p, highlight=c.options.tie_highlight),
               candidate=True),
    FigureSpec("fig_P1_distanz_und_naehe", "core", _net(perspectives.distance_closeness_figure)),
    FigureSpec("fig_P2_sprachliche_praktiken", "core",
               lambda c, p: perspectives.language_groups_figure(c.dataset, c.status, c.params, network=c.network, view=c.options.language_view, profile=p)),
    # ---- supplementary
    FigureSpec("fig_A_ego_naehe_wohnort", "supplementary", _plain(ego.proximity_figure)),
    FigureSpec("fig_B1_netzwerkstruktur", "supplementary",
               lambda c, p: network_figures.network_structure_figure(c.dataset, c.status, c.params, network=c.network, structure=c.structure, profile=p)),
    FigureSpec("fig_B2_netzwerkstruktur_gruppen", "supplementary",
               lambda c, p: network_figures.network_structure_figure(c.dataset, c.status, c.params, network=c.network, show_groups=True, structure=c.structure, profile=p)),
    FigureSpec("fig_G1_geografische_zonen", "supplementary", _net(geo_zones.geographic_zones_figure)),
    FigureSpec("fig_G2a_geografische_baender", "supplementary",
               lambda c, p: geo_network.geographic_bands_figure(c.dataset, c.status, c.params, network=c.network, profile=p, highlight=c.options.tie_highlight)),
    FigureSpec("fig_P3_einbettung_und_kommunikation", "supplementary", _net(perspectives.geography_communication_figure)),
    FigureSpec("fig_C_geografisches_profil", "supplementary", _plain(geography.geography_figure)),
    FigureSpec("fig_D1_sprachprofil", "supplementary", _plain(language.language_profile_figure)),
    FigureSpec("fig_D2_ego_sprachmodus", "supplementary", _plain(ego.language_mode_figure)),
    FigureSpec("fig_E_deskriptive_uebersicht", "supplementary", _plain(overview.overview_figure)),
    # ---- diagnostic
    FigureSpec("fig_B0_layoutvergleich", "diagnostic", _diagnostic(network_figures.layout_comparison_figure), profiles=False),
    FigureSpec("fig_B3_0_layoutvergleich", "diagnostic", _diagnostic(ego_network.ego_layout_comparison_figure), profiles=False),
    FigureSpec("fig_G2_0_variantenvergleich", "diagnostic", _diagnostic(geo_zones.geographic_variants_figure), profiles=False),
    FigureSpec("fig_G2_1_vergleich_a_b", "diagnostic", _diagnostic(geo_network.geographic_ab_comparison_figure), profiles=False),
    FigureSpec("fig_G2_geografisches_beziehungsnetz", "diagnostic",
               lambda c, p: geo_zones.geographic_network_figure(c.dataset, c.status, c.params, network=c.network, profile="clean", highlight=c.options.tie_highlight),
               profiles=False, legacy=True),
)


def spec_for(stem: str) -> FigureSpec:
    return next(spec for spec in SPECS if spec.stem == stem)


def target_dir(figures_dir: Path, spec: FigureSpec, profile: str | None) -> Path:
    """``figures/<tier>`` for the clean profile (and diagnostics), ``figures/analysis/<tier>`` for the analysis profile."""
    base = figures_dir / "analysis" if profile == "analysis" else figures_dir
    return base / spec.tier


def profiles_of(spec: FigureSpec, options: FigureOptions) -> tuple[str | None, ...]:
    return tuple(options.profiles) if spec.profiles else (None,)


def figure_index(options: FigureOptions, formats: tuple[str, ...], status: SurveyStatus | None = None) -> dict[str, object]:
    """The register of a run: per figure its tier, question, base layout, codings, limits and files; and the full provenance and
    data-quality status that the clean figures only hint at (``MARES · 001-2 · vorläufig``)."""
    entries = {}
    for spec in SPECS:
        entry = dict(note_for(spec.stem))
        entry["tier"] = spec.tier
        if spec.candidate:
            entry["candidate"] = True
        if spec.legacy:
            entry["legacy"] = True
        if spec.profiles:
            entry["files"] = {profile: f"figures/{'analysis/' if profile == 'analysis' else ''}{spec.tier}/{spec.stem}" for profile in options.profiles}
        else:
            entry["files"] = {"standard": f"figures/{spec.tier}/{spec.stem}"}
        entries[spec.stem] = entry
    return {
        "schema": "mares-figures-index/v0-draft",
        "provenance": status.to_dict() if status is not None else None,
        "formats": list(formats),
        "options": options.to_dict(),
        "tiers": {tier: [spec.stem for spec in SPECS if spec.tier == tier] for tier in TIERS},
        "spatial_meanings": {
            "naehe": "Abstand zu Ego = erhobener Tabellenwert der subjektiven Nähe (A)",
            "struktur": "Position = erhobene Kontakt–Kontakt-Beziehungen (B1–B3, P2)",
            "geografie": "Zone/Band = Wohnort-Kategorie, keine Entfernung (G1, G2, P1, P3)",
        },
        "figures": entries,
    }
