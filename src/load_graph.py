"""Download a bounded Mumbai road network from OpenStreetMap and save it to data/.

Usage:
    python src/load_graph.py --center "Dadar, Mumbai" --dist 3000 --out data/corridor.graphml
"""
import argparse
from pathlib import Path

import networkx as nx
import osmnx as ox


def load_corridor(center: str, dist_m: int) -> nx.MultiDiGraph:
    """Return the largest strongly connected drivable network within dist_m of center."""
    G = ox.graph_from_address(center, dist=dist_m, network_type="drive")
    G = ox.truncate.largest_component(G, strongly=True)
    # 'length' (metres) is the edge weight; keeping it in metres keeps the
    # Euclidean heuristic admissible.
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    return G


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--center", default="Dadar, Mumbai, India",
                        help="Place name to centre the graph on")
    parser.add_argument("--dist", type=int, default=3000,
                        help="Radius in metres around the centre")
    parser.add_argument("--out", default="data/corridor.graphml",
                        help="Output GraphML path")
    args = parser.parse_args()

    G = load_corridor(args.center, args.dist)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(G, args.out)

    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")
    print(f"Saved to: {args.out}")


if __name__ == "__main__":
    main()
