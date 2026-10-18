"""Generate a fixed, reproducible set of origin-destination test queries.

Pairs are sampled from the corridor graph in three straight-line distance bands,
so results can be compared by route length. The random seed is fixed, so
re-running this script produces the same queries.

Usage (from the project root):
    python experiments/make_queries.py
Output:
    experiments/queries.csv
"""
import csv
import math
import random
import sys
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from routing import haversine_m  # noqa: E402

GRAPH_PATH = Path("data/corridor.graphml")
OUT_PATH = Path("experiments/queries.csv")
SEED = 42
PAIRS_PER_BAND = 10

# Straight-line distance bands in metres. The corridor has a 3 km radius,
# so the longest straight-line span is about 6 km.
BANDS = {
    "short": (500, 1500),
    "medium": (2000, 3500),
    "long": (4000, 6000),
}


def main() -> None:
    G = nx.read_graphml(GRAPH_PATH)
    nodes = list(G.nodes)
    coords = {n: (float(G.nodes[n]["y"]), float(G.nodes[n]["x"])) for n in nodes}
    rng = random.Random(SEED)

    rows = []
    for band, (lo, hi) in BANDS.items():
        found = []
        attempts = 0
        while len(found) < PAIRS_PER_BAND and attempts < 200_000:
            attempts += 1
            s, t = rng.sample(nodes, 2)
            d = haversine_m(*coords[s], *coords[t])
            if lo <= d <= hi:
                found.append((s, t, d))
        if len(found) < PAIRS_PER_BAND:
            raise RuntimeError(f"Only found {len(found)} '{band}' pairs in {attempts} tries.")
        for i, (s, t, d) in enumerate(found, start=1):
            rows.append({
                "query_id": f"{band[0].upper()}{i:02d}",
                "band": band,
                "source": s,
                "target": t,
                "straight_line_m": round(d, 1),
            })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} queries to {OUT_PATH}")


if __name__ == "__main__":
    main()
