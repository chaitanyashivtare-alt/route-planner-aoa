"""Run Dijkstra and A* (three heuristics) on every query and record the metrics.

Usage (from the project root):
    python experiments/run_benchmark.py
Inputs:
    data/corridor.graphml, experiments/queries.csv
Outputs:
    experiments/results.csv   one row per query per algorithm
    experiments/summary.csv   averages per distance band and algorithm
"""
import csv
import math
import statistics
import sys
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from routing import astar, build_adjacency, dijkstra, make_heuristic  # noqa: E402

GRAPH_PATH = Path("data/corridor.graphml")
QUERIES_PATH = Path("experiments/queries.csv")
RESULTS_PATH = Path("experiments/results.csv")
SUMMARY_PATH = Path("experiments/summary.csv")
HEURISTICS = ["zero", "haversine", "manhattan"]
TOLERANCE_M = 1e-6


def run_query(adj, coords, source, target):
    """Return a list of SearchResult objects: Dijkstra first, then A* per heuristic."""
    results = [dijkstra(adj, source, target)]
    for name in HEURISTICS:
        h = make_heuristic(name, coords)
        results.append(astar(adj, source, target, h, name=f"A* ({name})"))
    return results


def main() -> None:
    G = nx.read_graphml(GRAPH_PATH)
    adj, coords = build_adjacency(G)

    with QUERIES_PATH.open(encoding="utf-8") as f:
        queries = list(csv.DictReader(f))

    rows = []
    for q in queries:
        source, target = q["source"], q["target"]
        results = run_query(adj, coords, source, target)
        reference_cost = results[0].cost  # Dijkstra is the optimal reference

        for r in results:
            optimal = r.found and math.isclose(r.cost, reference_cost, abs_tol=TOLERANCE_M)
            rows.append({
                "query_id": q["query_id"],
                "band": q["band"],
                "straight_line_m": q["straight_line_m"],
                "algorithm": r.algorithm,
                "found": r.found,
                "path_cost_m": round(r.cost, 1) if r.found else "",
                "optimal": optimal,
                "path_nodes": len(r.path),
                "nodes_expanded": r.nodes_expanded,
                "max_queue_size": r.max_queue_size,
                "runtime_ms": round(r.runtime_s * 1000, 3),
            })

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Summary: average each metric per band and algorithm.
    groups = {}
    for row in rows:
        groups.setdefault((row["band"], row["algorithm"]), []).append(row)

    summary = []
    dijkstra_expanded = {}
    for (band, algo), items in sorted(groups.items()):
        exp = statistics.mean(r["nodes_expanded"] for r in items)
        if algo == "Dijkstra":
            dijkstra_expanded[band] = exp
        summary.append({
            "band": band,
            "algorithm": algo,
            "queries": len(items),
            "mean_nodes_expanded": round(exp, 1),
            "mean_max_queue": round(statistics.mean(r["max_queue_size"] for r in items), 1),
            "mean_runtime_ms": round(statistics.mean(r["runtime_ms"] for r in items), 3),
            "optimal_rate": round(sum(bool(r["optimal"]) for r in items) / len(items), 2),
        })
    for s in summary:
        base = dijkstra_expanded[s["band"]]
        s["expansion_saving_pct"] = round(100 * (1 - s["mean_nodes_expanded"] / base), 1)

    with SUMMARY_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)

    print(f"Ran {len(queries)} queries -> {RESULTS_PATH}")
    print(f"Summary -> {SUMMARY_PATH}\n")
    for s in summary:
        print(f"{s['band']:<7}{s['algorithm']:<18}"
              f"expanded={s['mean_nodes_expanded']:>8}  "
              f"saving={s['expansion_saving_pct']:>6}%  "
              f"runtime={s['mean_runtime_ms']:>8} ms  "
              f"optimal={s['optimal_rate']}")


if __name__ == "__main__":
    main()
