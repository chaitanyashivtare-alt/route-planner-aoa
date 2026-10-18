# Dijkstra vs A* Route Finder on a Real Map

Analysis of Algorithms (AOA) project, third-year engineering.

Builds a route planner over a bounded slice of the Mumbai road network
(Western or Central line corridor) and compares Dijkstra's algorithm with A*
on nodes expanded, runtime, and path length, showing how the choice of
heuristic changes the analysis.

## Structure

```
route-planner-aoa/
├── data/          # saved OSM graph extract (small, committed)
├── src/           # graph loading, Dijkstra, A*, metrics
├── experiments/   # benchmark scripts, queries.csv, result CSVs
├── dashboard/     # Streamlit benchmark dashboard
└── report/        # report drafts and figures
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Status

- [x] Repository scaffold
- [x] Load corridor graph from OpenStreetMap
- [x] Dijkstra and A* implementations
- [x] Metrics and benchmark experiments
- [x] Dashboard
- [ ] Scaling experiment
- [ ] Report

## Running

```bash
python src/load_graph.py                 # download the corridor graph (optional, data is committed)
python experiments/make_queries.py       # regenerate the fixed test queries
python experiments/run_benchmark.py      # run Dijkstra and A* on all queries
streamlit run dashboard/app.py           # open the RouteScope dashboard
python -m unittest discover -s tests -v  # run unit tests
```
