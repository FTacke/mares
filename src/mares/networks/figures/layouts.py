"""Force-directed layouts for the network figures, and measures to compare them.

Positions are computed from the **structure** of the documented ties alone: no ring, no group frame, no
coordinate from the survey sheet. Every method is deterministic -- sorted node order, a fixed seed, a
deterministic start -- so the same network gives the same picture in every process (the iteration order of a
set of strings is not stable between processes, which is why nothing here iterates a set).

Variants (all numpy only; no scipy):

* ``spring``  -- Fruchterman-Reingold (networkx ``spring_layout``). Connected nodes attract, all nodes repel;
  separate components drift apart and settle freely.
* ``stress``  -- stress majorisation (SMACOF) on graph distances, the numpy counterpart of Kamada-Kawai.
  Disconnected pairs get the distance *diameter + 1*, which keeps components in one frame without
  implying a link between them.
* ``forceatlas`` -- ForceAtlas2 (networkx), with gravity: components and isolates stay near the centre.

None of them adds a tie. Distances between components carry no meaning.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations

import networkx as nx
import numpy as np

from mares.core import ids

SEED = 20260925  # fixed: the layout is reproducible
VARIANTS = ("spring", "stress", "forceatlas")
VARIANT_LABELS = {
    "spring": "Spring (Fruchterman–Reingold)",
    "stress": "Stress-Majorisierung (≈ Kamada–Kawai)",
    "forceatlas": "ForceAtlas2",
}
DEFAULT_VARIANT = "stress"


def ordered_graph(contact_ids, edges) -> nx.Graph:
    """A graph with nodes and edges in a fixed order (by contact number)."""
    graph = nx.Graph()
    nodes = sorted(contact_ids, key=ids.contact_number)
    graph.add_nodes_from(nodes)
    graph.add_edges_from(sorted((tuple(sorted(e, key=ids.contact_number)) for e in edges), key=lambda e: (ids.contact_number(e[0]), ids.contact_number(e[1]))))
    return graph


def _circle(nodes: list[str]) -> dict[str, np.ndarray]:
    n = len(nodes)
    return {c: np.array([math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)]) for i, c in enumerate(nodes)}


def smacof(dist: np.ndarray, weights: np.ndarray, nodes: list[str], scale: float, iterations: int = 400, starts: int = 12) -> dict[str, np.ndarray]:
    """Stress majorisation (SMACOF) for given target distances and weights, with several deterministic starts.

    The layout of the lowest stress wins. A single start can settle in a poor local minimum
    (structurally equivalent nodes lined up on one line). The starts differ only in a seeded jitter and
    the ties go to the first start: reproducible. ``scale`` is the radius of the circular start.
    """
    n = len(nodes)
    index = {c: i for i, c in enumerate(nodes)}
    v = np.diag(weights.sum(axis=1)) - weights
    v_plus = np.linalg.pinv(v)
    circle = _circle(nodes)

    def stress_of(x: np.ndarray) -> float:
        return float((weights * (np.sqrt(((x[:, None, :] - x[None, :, :]) ** 2).sum(axis=2)) - dist) ** 2).sum() / 2)

    best: tuple[float, np.ndarray] | None = None
    for start in range(starts):
        rng = np.random.default_rng(SEED + start)
        x = np.array([circle[c] for c in nodes]) * scale + rng.normal(0, 0.01 if start == 0 else 0.35, (n, 2))
        previous = math.inf
        for _ in range(iterations):
            diff = x[:, None, :] - x[None, :, :]
            current = np.sqrt((diff**2).sum(axis=2))
            np.fill_diagonal(current, 1.0)
            b = -weights * dist / current
            np.fill_diagonal(b, 0.0)
            np.fill_diagonal(b, -b.sum(axis=1))
            x = v_plus @ b @ x
            stress = stress_of(x)
            if previous - stress < 1e-9:
                break
            previous = stress
        if best is None or stress_of(x) < best[0] - 1e-9:
            best = (stress_of(x), x)
    return {c: best[1][index[c]] for c in nodes}


def _stress(graph: nx.Graph, nodes: list[str], iterations: int = 400, starts: int = 12) -> dict[str, np.ndarray]:
    """Stress majorisation on graph distances; disconnected pairs get the distance *diameter + 1*."""
    n = len(nodes)
    index = {c: i for i, c in enumerate(nodes)}
    inf = float("inf")
    dist = np.full((n, n), inf)
    for source, lengths in nx.all_pairs_shortest_path_length(graph):
        for target, length in lengths.items():
            dist[index[source], index[target]] = length
    finite = dist[np.isfinite(dist)]
    cap = (finite.max() if finite.size else 1.0) + 1.0  # disconnected pairs: diameter + 1
    dist = np.where(np.isfinite(dist), dist, cap)
    np.fill_diagonal(dist, 1.0)
    weights = 1.0 / dist**2
    np.fill_diagonal(weights, 0.0)
    return smacof(dist, weights, nodes, cap / 2, iterations, starts)


def _align(positions: dict[str, np.ndarray]) -> dict[str, tuple[float, float]]:
    """Centre, rotate the principal axis to horizontal, flip to a fixed handedness, rescale to a unit frame."""
    nodes = list(positions)
    points = np.array([positions[c] for c in nodes], dtype=float)
    points -= points.mean(axis=0)
    if len(nodes) > 2 and np.ptp(points, axis=0).max() > 0:
        values, vectors = np.linalg.eigh(np.cov(points.T))
        points = points @ vectors[:, ::-1]  # the principal axis becomes x
        for axis in (0, 1):  # the longer tail points right / up: a stable orientation
            if (points[:, axis] ** 3).sum() < 0:
                points[:, axis] *= -1
    span = np.ptp(points, axis=0).max() or 1.0
    points = points / span * 2.0
    return {c: (round(float(points[i, 0]), 9), round(float(points[i, 1]), 9)) for i, c in enumerate(nodes)}


def compute_layout(graph: nx.Graph, variant: str = DEFAULT_VARIANT) -> dict[str, tuple[float, float]]:
    """Positions in a frame of width/height about 2, from the graph structure only."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown layout {variant!r}; one of {', '.join(VARIANTS)}")
    nodes = sorted(graph.nodes, key=ids.contact_number)
    if not nodes:
        return {}
    if len(nodes) == 1:
        return {nodes[0]: (0.0, 0.0)}
    ordered = nx.Graph()
    ordered.add_nodes_from(nodes)
    ordered.add_edges_from(sorted((tuple(sorted(e, key=ids.contact_number)) for e in graph.edges), key=lambda e: (ids.contact_number(e[0]), ids.contact_number(e[1]))))
    n = len(nodes)
    if variant == "spring":
        raw = nx.spring_layout(ordered, pos=_circle(nodes), k=1.6 / math.sqrt(n), iterations=500, seed=SEED, threshold=1e-7)
    elif variant == "stress":
        raw = _stress(ordered, nodes)
    else:
        raw = nx.forceatlas2_layout(ordered, pos=_circle(nodes), max_iter=1000, gravity=10.0, scaling_ratio=5.0, seed=SEED)
    return _align({c: np.asarray(raw[c], dtype=float) for c in nodes})


# ---------------------------------------------------------------- measures ---------------------

@dataclass(frozen=True)
class LayoutMeasures:
    """Readability measures of one layout. Descriptive: they compare variants, they prove nothing about the data."""

    crossings: int  # pairs of ties whose lines cross (ties sharing a node excluded)
    min_node_distance: float  # relative to the median tie length: below ~0.3 nodes start to touch
    edge_length_cv: float  # coefficient of variation of tie lengths: even lengths read as a calm graph
    tie_share: float  # median tie length as a share of the picture's longer side: small = the components are crushed

    def summary(self) -> str:
        return (f"Kreuzungen {self.crossings} · Knotenabstand {self.min_node_distance:.2f} · "
                f"Beziehungslänge {self.tie_share:.0%} des Bildes · Längenvariation {self.edge_length_cv:.2f}")


def _ccw(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def count_crossings(positions: dict[str, tuple[float, float]], edges) -> int:
    edge_list = [tuple(e) for e in edges]
    count = 0
    for (a, b), (c, d) in combinations(edge_list, 2):
        if len({a, b, c, d}) < 4:
            continue
        p, q, r, s = positions[a], positions[b], positions[c], positions[d]
        if _ccw(p, q, r) * _ccw(p, q, s) < 0 and _ccw(r, s, p) * _ccw(r, s, q) < 0:
            count += 1
    return count


def measure(positions: dict[str, tuple[float, float]], edges) -> LayoutMeasures:
    edge_list = [tuple(e) for e in edges]
    lengths = [math.dist(positions[a], positions[b]) for a, b in edge_list]
    median = float(np.median(lengths)) if lengths else 1.0
    points = list(positions.values())
    nearest = min((math.dist(p, q) for p, q in combinations(points, 2)), default=0.0)
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    side = max(max(xs) - min(xs), max(ys) - min(ys)) if points else 1.0
    return LayoutMeasures(
        crossings=count_crossings(positions, edge_list),
        min_node_distance=nearest / median if median else 0.0,
        edge_length_cv=float(np.std(lengths) / np.mean(lengths)) if lengths and np.mean(lengths) else 0.0,
        tie_share=median / side if side else 0.0,
    )
