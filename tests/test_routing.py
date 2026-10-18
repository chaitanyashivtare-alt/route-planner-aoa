"""Unit tests for src/routing.py. Run with:

    python -m unittest discover -s tests -v
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from routing import astar, dijkstra, make_heuristic  # noqa: E402


def small_graph():
    """A tiny directed graph with a known shortest path.

    A -> B -> D costs 1 + 1 = 2 (shortest)
    A -> C -> D costs 4 + 1 = 5
    E is isolated (unreachable from A).
    """
    adj = {
        "A": [("B", 1.0), ("C", 4.0)],
        "B": [("D", 1.0)],
        "C": [("D", 1.0)],
        "D": [],
        "E": [],
    }
    # Coordinates are only used by geometric heuristics, so give them a dummy value.
    coords = {n: (19.0, 72.8) for n in adj}
    return adj, coords


class DijkstraTests(unittest.TestCase):
    def test_finds_shortest_path(self):
        adj, _ = small_graph()
        r = dijkstra(adj, "A", "D")
        self.assertTrue(r.found)
        self.assertEqual(r.cost, 2.0)
        self.assertEqual(r.path, ["A", "B", "D"])

    def test_unreachable_target(self):
        adj, _ = small_graph()
        r = dijkstra(adj, "A", "E")
        self.assertFalse(r.found)
        self.assertEqual(r.cost, math.inf)
        self.assertEqual(r.path, [])

    def test_source_equals_target(self):
        adj, _ = small_graph()
        r = dijkstra(adj, "A", "A")
        self.assertTrue(r.found)
        self.assertEqual(r.cost, 0.0)
        self.assertEqual(r.path, ["A"])
        self.assertEqual(r.nodes_expanded, 1)

    def test_metrics_are_recorded(self):
        adj, _ = small_graph()
        r = dijkstra(adj, "A", "D")
        self.assertGreater(r.nodes_expanded, 0)
        self.assertGreater(r.max_queue_size, 0)
        self.assertGreaterEqual(r.runtime_s, 0.0)


class AStarTests(unittest.TestCase):
    def test_zero_heuristic_matches_dijkstra_exactly(self):
        adj, coords = small_graph()
        h = make_heuristic("zero", coords)
        d = dijkstra(adj, "A", "D")
        a = astar(adj, "A", "D", h)
        self.assertEqual(a.cost, d.cost)
        self.assertEqual(a.path, d.path)
        self.assertEqual(a.nodes_expanded, d.nodes_expanded)

    def test_same_cost_as_dijkstra_on_small_graph(self):
        adj, coords = small_graph()
        h = make_heuristic("haversine", coords)
        d = dijkstra(adj, "A", "D")
        a = astar(adj, "A", "D", h)
        self.assertEqual(a.cost, d.cost)
        self.assertEqual(a.path, d.path)

    def test_unreachable_target(self):
        adj, coords = small_graph()
        h = make_heuristic("zero", coords)
        r = astar(adj, "A", "E", h)
        self.assertFalse(r.found)


class HeuristicTests(unittest.TestCase):
    def test_haversine_known_distance(self):
        # Churchgate to CSMT is roughly 1.4 km apart in a straight line.
        coords = {"churchgate": (18.9322, 72.8264), "csmt": (18.9400, 72.8355)}
        h = make_heuristic("haversine", coords)
        d = h("churchgate", "csmt")
        self.assertGreater(d, 1000)
        self.assertLess(d, 2000)

    def test_zero_heuristic_is_zero(self):
        coords = {"a": (19.0, 72.8), "b": (19.1, 72.9)}
        self.assertEqual(make_heuristic("zero", coords)("a", "b"), 0.0)

    def test_unknown_heuristic_raises(self):
        with self.assertRaises(ValueError):
            make_heuristic("euclidean", {})


if __name__ == "__main__":
    unittest.main()
