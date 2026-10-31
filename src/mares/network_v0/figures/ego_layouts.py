"""Layouts for the network *including ego* (figure B3), and measures to compare them.

Ego is tied to every contact, so a plain force layout of "ego + contacts" makes ego a hub that pulls all
contacts -- and with them the surveyed groups -- towards one point. B3 therefore weighs the three kinds of
statement differently: the **alter-alter ties decide the structure**, the ego lines only attach it.

Three variants are tried (all NumPy, deterministic, a fixed seed):

* ``fixed``    -- the contacts keep exactly their positions from B1/B2 (the alter-alter layout without ego);
  ego is added at the spot, close to the centroid, where its lines cross the fewest ties and touch the
  fewest contacts. The alter-alter structure is unchanged by construction.
* ``weighted`` -- one stress-majorisation layout of ego and contacts together. Ego-alter ties are *longer* and
  count *less* in the stress (``EGO_LENGTH``, ``EGO_WEIGHT``), so the alter-alter ties dominate and ego settles
  between the groups.
* ``joint``    -- the naive baseline: ego is simply one more node, all ties equal. It documents the problem
  (the groups are pulled together) and is not used.

Position and distance to ego carry **no** information about subjective closeness (that is figure A), and the
distance between separate groups is not a social or geographic distance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations

import networkx as nx
import numpy as np

from mares.core import ids

from . import layouts

EGO = "EGO"
EGO_VARIANTS = ("fixed", "weighted", "joint")
EGO_VARIANT_LABELS = {
    "fixed": "A · Kontakte wie in B2, Ego ergänzt",
    "weighted": "B · gemeinsames gewichtetes Layout",
    "joint": "Referenz · Ego als gewöhnlicher Knoten",
}
DEFAULT_EGO_VARIANT = "fixed"
EGO_LENGTH = 2.0  # target length of an ego-alter tie, in units of an alter-alter tie
EGO_WEIGHT = 0.2  # share of the stress an ego-alter pair contributes
_HIT_RADIUS = 0.03  # a line closer than this to a contact (in picture units) counts as touching it


def _alter_nodes(graph: nx.Graph) -> list[str]:
    return sorted(graph.nodes, key=ids.contact_number)


def _segments(positions, edges):
    return [(positions[a], positions[b]) for a, b in edges]


def _crosses(p, q, r, s) -> bool:
    return layouts._ccw(p, q, r) * layouts._ccw(p, q, s) < 0 and layouts._ccw(r, s, p) * layouts._ccw(r, s, q) < 0


def _distance_to_segment(point, a, b) -> float:
    ax_, ay_ = a
    dx, dy = b[0] - ax_, b[1] - ay_
    length = dx * dx + dy * dy
    t = 0.0 if length == 0 else max(0.0, min(1.0, ((point[0] - ax_) * dx + (point[1] - ay_) * dy) / length))
    return math.hypot(point[0] - (ax_ + t * dx), point[1] - (ay_ + t * dy))


def ego_line_cost(ego_xy, positions: dict[str, tuple[float, float]], alter_edges) -> tuple[int, int]:
    """For a candidate ego position: (crossings of the ego lines with alter-alter ties, contacts touched by an ego line)."""
    crossings = hits = 0
    for contact, point in positions.items():
        for a, b in alter_edges:
            if contact in (a, b):
                continue
            if _crosses(ego_xy, point, positions[a], positions[b]):
                crossings += 1
        for other, other_point in positions.items():
            if other != contact and _distance_to_segment(other_point, ego_xy, point) < _HIT_RADIUS:
                hits += 1
    return crossings, hits


def place_ego(positions: dict[str, tuple[float, float]], alter_edges, reach: float = 0.5, step: float = 0.05) -> tuple[float, float]:
    """The ego position for the ``fixed`` variant: near the centroid, where the ego lines are least disturbing.

    Candidates form a fixed grid around the centroid; the cost is the number of ego lines that cross an
    alter-alter tie plus four times the number of contacts an ego line touches plus a pull to the centroid.
    The cheapest wins, ties go to the first candidate: deterministic.
    """
    points = list(positions.values())
    centroid = (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))
    span = max(max(p[0] for p in points) - min(p[0] for p in points), max(p[1] for p in points) - min(p[1] for p in points)) or 1.0
    offsets = [round(-reach + i * step, 10) for i in range(int(round(2 * reach / step)) + 1)]
    best = None
    for dx in offsets:
        for dy in offsets:
            candidate = (round(centroid[0] + dx, 9), round(centroid[1] + dy, 9))
            crossings, hits = ego_line_cost(candidate, positions, alter_edges)
            cost = crossings + 4 * hits + 6.0 * math.hypot(dx, dy) / span
            if best is None or cost < best[0] - 1e-12:
                best = (cost, candidate)
    return best[1]


def _joint_distances(nodes: list[str], alter_graph: nx.Graph, ego_length: float) -> np.ndarray:
    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    for a, b in alter_graph.edges:
        graph.add_edge(a, b, length=1.0)
    for contact in nodes:
        if contact != EGO:
            graph.add_edge(EGO, contact, length=ego_length)
    index = {c: i for i, c in enumerate(nodes)}
    dist = np.zeros((len(nodes), len(nodes)))
    for source, lengths in nx.all_pairs_dijkstra_path_length(graph, weight="length"):
        for target, length in lengths.items():
            dist[index[source], index[target]] = length
    np.fill_diagonal(dist, 1.0)
    return dist


def compute_ego_layout(alter_graph: nx.Graph, variant: str = DEFAULT_EGO_VARIANT) -> dict[str, tuple[float, float]]:
    """Positions of the contacts and of ``EGO`` (in a frame of about 2). The graph holds the contacts and
    their alter-alter ties only; ego is added here, joined to every contact."""
    if variant not in EGO_VARIANTS:
        raise ValueError(f"unknown ego layout {variant!r}; one of {', '.join(EGO_VARIANTS)}")
    alters = _alter_nodes(alter_graph)
    edges = [tuple(sorted(e, key=ids.contact_number)) for e in alter_graph.edges]
    if not alters:
        return {EGO: (0.0, 0.0)}
    if variant == "fixed":
        positions = layouts.compute_layout(layouts.ordered_graph(alters, edges), layouts.DEFAULT_VARIANT)
        return {**positions, EGO: place_ego(positions, edges)}
    nodes = [EGO] + alters
    if variant == "weighted":
        dist = _joint_distances(nodes, alter_graph, EGO_LENGTH)
        weights = 1.0 / dist**2
        for i, a in enumerate(nodes):
            for j, b in enumerate(nodes):
                if (a == EGO) != (b == EGO):
                    weights[i, j] *= EGO_WEIGHT
    else:
        dist = _joint_distances(nodes, alter_graph, 1.0)
        weights = 1.0 / dist**2
    np.fill_diagonal(weights, 0.0)
    raw = layouts.smacof(dist, weights, nodes, scale=float(dist.max()) / 2)
    return layouts._align(raw)


# ---------------------------------------------------------------- measures ---------------------


@dataclass(frozen=True)
class EgoLayoutMeasures:
    """Readability measures of an ego layout. They compare layouts; they say nothing about the data."""

    crossings: int  # all line pairs that cross (ego lines included, lines sharing a node excluded)
    ego_line_crossings: int  # of these: an ego line crosses an alter-alter tie
    contacts_touched: int  # contacts an ego line passes closely
    ego_offset: float  # distance of ego from the centroid of the contacts, relative to the picture
    structure_kept: float  # correlation of the alter-alter distances with the layout of B1/B2 (1 = identical)
    tie_share: float  # median alter-alter tie length as a share of the picture's longer side

    def summary(self) -> str:
        return (
            f"Kreuzungen {self.crossings} (davon Ego-Linien {self.ego_line_crossings}) · Ego-Linien streifen {self.contacts_touched} Kontakte · "
            f"Ego-Abstand zur Mitte {self.ego_offset:.2f} · Struktur wie B2 {self.structure_kept:.2f}"
        )


def measure_ego(positions: dict[str, tuple[float, float]], alter_edges, reference: dict[str, tuple[float, float]]) -> EgoLayoutMeasures:
    alters = {c: p for c, p in positions.items() if c != EGO}
    ego_edges = [(EGO, c) for c in alters]
    alter_edges = [tuple(e) for e in alter_edges]
    all_edges = alter_edges + ego_edges
    crossings = layouts.count_crossings(positions, all_edges)
    ego_crossings = sum(
        1
        for (e1, e2), (a, b) in ((ee, ae) for ee in ego_edges for ae in alter_edges)
        if e2 not in (a, b) and _crosses(positions[e1], positions[e2], positions[a], positions[b])
    )
    hits = ego_line_cost(positions[EGO], alters, alter_edges)[1]
    points = list(alters.values())
    centroid = (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)) if points else (0.0, 0.0)
    xs, ys = [p[0] for p in positions.values()], [p[1] for p in positions.values()]
    side = max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0
    names = sorted(alters, key=ids.contact_number)
    pairs = list(combinations(names, 2))
    here = np.array([math.dist(alters[a], alters[b]) for a, b in pairs])
    there = np.array([math.dist(reference[a], reference[b]) for a, b in pairs])
    kept = float(np.corrcoef(here, there)[0, 1]) if len(pairs) > 2 and here.std() and there.std() else 1.0
    lengths = [math.dist(alters[a], alters[b]) for a, b in alter_edges]
    return EgoLayoutMeasures(
        crossings=crossings,
        ego_line_crossings=ego_crossings,
        contacts_touched=hits,
        ego_offset=math.dist(positions[EGO], centroid) / side,
        structure_kept=kept,
        tie_share=(float(np.median(lengths)) / side) if lengths else 0.0,
    )
