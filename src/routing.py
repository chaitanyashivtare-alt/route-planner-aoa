"""Instrumented shortest-path search: Dijkstra and A* on a road graph.

Both algorithms record the metrics the AOA study compares:
    - nodes_expanded : nodes removed from the priority queue and processed
    - max_queue_size : largest size the priority queue reached
    - runtime_s      : wall-clock time of the search (excludes graph loading)
    - cost           : total path length in metres

Edge weights are road lengths in metres (OSMnx 'length'). With latitude and
longitude coordinates, the admissible heuristic is the great-circle (haversine)
distance in metres, not Euclidean distance in degrees.
"""
from __future__ import annotations

import heapq
import math
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Hashable, List, Optional, Tuple

Node = Hashable
Adjacency = Dict[Node, List[Tuple[Node, float]]]
Coords = Dict[Node, Tuple[float, float]]          # node -> (lat, lon)
Heuristic = Callable[[Node, Node], float]         # h(node, goal) -> estimated metres

EARTH_RADIUS_M = 6_371_000.0


@dataclass
class SearchResult:
    algorithm: str
    found: bool
    cost: float                       # metres; math.inf if no path
    path: List[Node] = field(default_factory=list)
    nodes_expanded: int = 0
    max_queue_size: int = 0
    runtime_s: float = 0.0


# ---------------------------------------------------------------------------
# Graph preparation
# ---------------------------------------------------------------------------

def build_adjacency(G) -> Tuple[Adjacency, Coords]:
    """Convert an OSMnx/NetworkX graph into a plain adjacency list and coordinates.

    Parallel edges between the same pair of nodes keep only the shortest one,
    because only the cheapest of them can appear on a shortest path.
    """
    best: Dict[Node, Dict[Node, float]] = {}
    for u, v, data in G.edges(data=True):
        w = float(data["length"])
        row = best.setdefault(u, {})
        if v not in row or w < row[v]:
            row[v] = w

    adj: Adjacency = {n: [] for n in G.nodes}
    for u, row in best.items():
        adj[u] = list(row.items())

    coords: Coords = {n: (float(d["y"]), float(d["x"])) for n, d in G.nodes(data=True)}
    return adj, coords


# ---------------------------------------------------------------------------
# Heuristics
# ---------------------------------------------------------------------------

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres between two lat/lon points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def make_heuristic(name: str, coords: Coords) -> Heuristic:
    """Return a heuristic function by name.

    zero      : h = 0. A* then behaves exactly like Dijkstra. Always admissible.
    haversine : straight-line distance on the sphere. Admissible and consistent,
                because a road is never shorter than the straight line between its ends.
    manhattan : grid-style distance (north-south plus east-west legs). It can
                overestimate the true road distance, so it is NOT admissible.
                It is included to show what happens when the heuristic breaks the rules.
    """
    if name == "zero":
        return lambda a, b: 0.0

    if name == "haversine":
        def h(a: Node, b: Node) -> float:
            lat1, lon1 = coords[a]
            lat2, lon2 = coords[b]
            return haversine_m(lat1, lon1, lat2, lon2)
        return h

    if name == "manhattan":
        def h(a: Node, b: Node) -> float:
            lat1, lon1 = coords[a]
            lat2, lon2 = coords[b]
            north_south = haversine_m(lat1, lon1, lat2, lon1)
            east_west = haversine_m(lat2, lon1, lat2, lon2)
            return north_south + east_west
        return h

    raise ValueError(f"Unknown heuristic: {name!r}. Use 'zero', 'haversine' or 'manhattan'.")


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def _search(
    adj: Adjacency,
    source: Node,
    target: Node,
    heuristic: Optional[Heuristic],
    name: str,
) -> SearchResult:
    """Best-first search with a closed set.

    With heuristic=None this is Dijkstra. With a heuristic it is A*.
    The closed-set version is guaranteed optimal only for consistent heuristics
    (haversine and zero). An inconsistent heuristic such as manhattan may return
    a path that is longer than the true shortest path, which the experiments can
    measure.
    """
    if source not in adj or target not in adj:
        raise KeyError("Source and target must both be nodes in the graph.")

    def h(n: Node) -> float:
        return 0.0 if heuristic is None else heuristic(n, target)

    start_time = time.perf_counter()

    g_score: Dict[Node, float] = {source: 0.0}
    parent: Dict[Node, Optional[Node]] = {source: None}
    closed: set = set()
    # Heap entries are (f = g + h, g, node). Ties on f are broken by larger g,
    # which prefers nodes closer to the goal.
    heap: List[Tuple[float, float, Node]] = [(h(source), 0.0, source)]
    nodes_expanded = 0
    max_queue = 1
    found = False

    while heap:
        max_queue = max(max_queue, len(heap))
        _, g_u, u = heapq.heappop(heap)
        if u in closed or g_u > g_score.get(u, math.inf):
            continue  # stale entry: a cheaper route to u was already processed

        closed.add(u)
        nodes_expanded += 1

        if u == target:
            found = True
            break

        for v, w in adj[u]:
            if v in closed:
                continue
            tentative = g_u + w
            if tentative < g_score.get(v, math.inf):
                g_score[v] = tentative
                parent[v] = u
                heapq.heappush(heap, (tentative + h(v), tentative, v))

    runtime = time.perf_counter() - start_time

    if not found:
        return SearchResult(
            algorithm=name, found=False, cost=math.inf,
            nodes_expanded=nodes_expanded, max_queue_size=max_queue, runtime_s=runtime,
        )

    path: List[Node] = []
    node: Optional[Node] = target
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()

    return SearchResult(
        algorithm=name, found=True, cost=g_score[target], path=path,
        nodes_expanded=nodes_expanded, max_queue_size=max_queue, runtime_s=runtime,
    )


def dijkstra(adj: Adjacency, source: Node, target: Node) -> SearchResult:
    """Dijkstra's algorithm: A* with no heuristic."""
    return _search(adj, source, target, heuristic=None, name="Dijkstra")


def astar(adj: Adjacency, source: Node, target: Node, heuristic: Heuristic,
          name: str = "A*") -> SearchResult:
    """A* search using the given heuristic function."""
    return _search(adj, source, target, heuristic=heuristic, name=name)
