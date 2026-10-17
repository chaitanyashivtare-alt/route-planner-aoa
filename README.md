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
- [ ] Load corridor graph from OpenStreetMap
- [ ] Dijkstra and A* implementations
- [ ] Metrics and benchmark experiments
- [ ] Dashboard
- [ ] Report
