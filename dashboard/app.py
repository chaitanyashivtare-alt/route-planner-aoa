"""RouteScope: Dijkstra vs A* on the Mumbai road corridor (Dadar, 3 km).

Run from the project root:
    streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

import networkx as nx
import pandas as pd
import pydeck as pdk
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from routing import astar, build_adjacency, dijkstra, make_heuristic  # noqa: E402

DIJKSTRA_RGB = [31, 119, 180]     # blue
ASTAR_RGB = [255, 127, 14]        # orange
ORIGIN_RGB = [44, 160, 44]        # green
DEST_RGB = [214, 39, 40]          # red
BASEMAP = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"

st.set_page_config(page_title="RouteScope | Mumbai Corridor", page_icon="🗺️", layout="wide")


# ---------------------------------------------------------------------------
# Data loading (cached so the app stays fast when you switch queries)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="Loading road network...")
def load_network():
    G = nx.read_graphml(ROOT / "data" / "corridor.graphml")
    return build_adjacency(G)


@st.cache_data
def load_queries() -> pd.DataFrame:
    # Node IDs must stay text: the graph stores them as strings.
    return pd.read_csv(ROOT / "experiments" / "queries.csv",
                       dtype={"source": str, "target": str})


@st.cache_data
def load_results() -> pd.DataFrame:
    return pd.read_csv(ROOT / "experiments" / "results.csv")


@st.cache_data
def load_summary() -> pd.DataFrame:
    return pd.read_csv(ROOT / "experiments" / "summary.csv")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def path_lonlat(path, coords):
    """Convert a list of node IDs to [lon, lat] pairs for pydeck."""
    return [[coords[n][1], coords[n][0]] for n in path]


def build_map(coords, dij_path, ast_path, source, target):
    layers = []
    if dij_path:
        layers.append(pdk.Layer(
            "PathLayer",
            data=[{"path": path_lonlat(dij_path, coords)}],
            get_path="path", get_color=DIJKSTRA_RGB, width_min_pixels=5,
        ))
    if ast_path:
        layers.append(pdk.Layer(
            "PathLayer",
            data=[{"path": path_lonlat(ast_path, coords)}],
            get_path="path", get_color=ASTAR_RGB, width_min_pixels=3,
        ))
    points = pd.DataFrame([
        {"lon": coords[source][1], "lat": coords[source][0], "color": ORIGIN_RGB},
        {"lon": coords[target][1], "lat": coords[target][0], "color": DEST_RGB},
    ])
    layers.append(pdk.Layer(
        "ScatterplotLayer", data=points,
        get_position="[lon, lat]", get_fill_color="color",
        get_radius=60, radius_min_pixels=6,
    ))
    view = pdk.ViewState(
        latitude=points["lat"].mean(), longitude=points["lon"].mean(), zoom=13.5,
    )
    return pdk.Deck(layers=layers, initial_view_state=view, map_style=BASEMAP)


def metric_row(label, dij, ast):
    saving = (1 - ast / dij) * 100 if dij else 0.0
    return {"Metric": label, "Dijkstra": dij, "A*": ast, "A* saving": f"{saving:.1f}%"}


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

adj, coords = load_network()
queries = load_queries()

st.title("RouteScope")
st.caption(
    "Dijkstra vs A* on the Mumbai road corridor around Dadar (3 km radius, "
    f"{len(coords):,} intersections)."
)

with st.sidebar:
    st.header("Route")
    query_labels = {
        row.query_id: f"{row.query_id} · {row.band.title()} · {row.straight_line_m / 1000:.1f} km"
        for row in queries.itertuples()
    }
    query_id = st.selectbox("Test route", list(query_labels), format_func=query_labels.get)
    heuristic = st.radio(
        "A* heuristic",
        ["haversine", "manhattan", "zero"],
        format_func=lambda h: {
            "haversine": "Haversine (admissible)",
            "manhattan": "Manhattan (not admissible)",
            "zero": "Zero (same as Dijkstra)",
        }[h],
        help="Haversine always finds the shortest route. Manhattan can return longer routes.",
    )
    st.divider()
    st.caption("Use the tabs to compare a single route or review the 30-route benchmark.")

tab_route, tab_bench, tab_method = st.tabs(["Route comparison", "Benchmark", "Method"])

with tab_route:
    row = queries[queries.query_id == query_id].iloc[0]
    source, target = row.source, row.target

    dij = dijkstra(adj, source, target)
    ast = astar(adj, source, target, make_heuristic(heuristic, coords), name="A*")

    if not (dij.found and ast.found):
        st.error("No route found between these points.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Route length", f"{dij.cost / 1000:.2f} km",
                  help="Shortest path cost from Dijkstra (the reference).")
        c2.metric("Nodes expanded (Dijkstra)", f"{dij.nodes_expanded:,}")
        c3.metric("Nodes expanded (A*)", f"{ast.nodes_expanded:,}",
                  delta=f"{(ast.nodes_expanded / dij.nodes_expanded - 1) * 100:.0f}% vs Dijkstra",
                  delta_color="inverse")
        same = abs(ast.cost - dij.cost) < 1e-6
        c4.metric("A* finds shortest route?", "Yes" if same else "No",
                  help=f"A* cost {ast.cost / 1000:.2f} km vs Dijkstra {dij.cost / 1000:.2f} km.")

        st.pydeck_chart(build_map(coords, dij.path, ast.path, source, target))
        st.markdown(
            "<span style='color:#1f77b4'>■</span> Dijkstra route &nbsp;&nbsp; "
            "<span style='color:#ff7f0e'>■</span> A* route &nbsp;&nbsp; "
            "<span style='color:#2ca02c'>●</span> Origin &nbsp;&nbsp; "
            "<span style='color:#d62728'>●</span> Destination",
            unsafe_allow_html=True,
        )

        table = pd.DataFrame([
            metric_row("Nodes expanded", dij.nodes_expanded, ast.nodes_expanded),
            metric_row("Peak priority-queue size", dij.max_queue_size, ast.max_queue_size),
            metric_row("Runtime (ms)", round(dij.runtime_s * 1000, 2), round(ast.runtime_s * 1000, 2)),
            metric_row("Path length (m)", round(dij.cost, 1), round(ast.cost, 1)),
            metric_row("Path nodes", len(dij.path), len(ast.path)),
        ])
        st.subheader("Search metrics")
        st.dataframe(table, hide_index=True)
        st.caption("Runtimes are approximate and depend on your machine. "
                   "Nodes expanded is the more reliable comparison.")

with tab_bench:
    summary = load_summary()
    results = load_results()

    st.subheader("Average nodes expanded by distance band")
    pivot = summary.pivot(index="band", columns="algorithm", values="mean_nodes_expanded")
    order = [b for b in ["short", "medium", "long"] if b in pivot.index]
    st.bar_chart(pivot.loc[order])

    st.subheader("Summary table")
    st.dataframe(summary, hide_index=True)

    st.subheader("Nodes expanded vs straight-line distance")
    scatter = results[results.algorithm.isin(["Dijkstra", "A* (haversine)"])].copy()
    scatter["straight_line_km"] = scatter.straight_line_m / 1000
    st.scatter_chart(scatter, x="straight_line_km", y="nodes_expanded",
                     color="algorithm", size=60)

    st.subheader("Optimality check")
    st.write(
        "Share of routes where the returned path cost equals Dijkstra's optimal cost. "
        "Haversine stays at 100%. Manhattan drops below 100%, which is the expected "
        "effect of an inadmissible heuristic."
    )

with tab_method:
    st.subheader("How the comparison works")
    st.markdown(
        """
- **Graph:** OpenStreetMap drivable roads within 3 km of Dadar, simplified to road
  intersections (3,529 nodes, 7,760 directed edges). Edge weights are road lengths in metres.
- **Dijkstra:** explores nodes in order of distance from the origin. Guaranteed optimal.
- **A\\*:** explores nodes in order of *distance so far + estimated distance to goal*.
  The estimate comes from the heuristic.
- **Haversine heuristic:** great-circle distance in metres. It never overestimates the road
  distance, so A* stays optimal.
- **Manhattan heuristic:** north-south plus east-west distance. It can overestimate, so the
  returned route is not always the shortest.
- **Metrics:** nodes expanded (main measure), peak priority-queue size, runtime, path cost.
"""
    )
