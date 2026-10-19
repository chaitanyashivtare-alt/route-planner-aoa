# RouteScope: A Comparative Study of Dijkstra and A* on the Mumbai Road Corridor

**Course:** Analysis of Algorithms (AOA), Third-Year Engineering
**Repository:** https://github.com/chaitanyashivtare-alt/route-planner-aoa

---

## Abstract

Shortest-path algorithms underpin every navigation application. This project compares two of them, Dijkstra's algorithm and A\*, on a real road network extracted from OpenStreetMap for the area around Dadar, Mumbai (3 km radius). Both algorithms were implemented from scratch and instrumented to record how many nodes each one expands, the size of its priority queue, its runtime, and the cost of the path it returns. A\* was tested with three heuristics: zero, haversine (great-circle distance), and Manhattan (grid distance). On 30 fixed test routes, A\* with the haversine heuristic returned the optimal route in every case and expanded 70 to 78 percent fewer nodes than Dijkstra. The Manhattan heuristic expanded the fewest nodes (77 to 85 percent fewer), but returned a suboptimal route in 50 to 80 percent of cases. The results confirm the theory: an admissible heuristic speeds up the search without sacrificing correctness, while an inadmissible one trades correctness for speed. The results are presented in an interactive dashboard, RouteScope, which lets users inspect any test route on a map.

---

## 1. Introduction

Route planning is a problem most engineering students use every day without thinking about its structure. A city road network can be modelled as a graph: intersections are nodes, road segments are weighted edges, and the weight is the segment length. Finding the shortest route is then the shortest-path problem.

Two classical solutions are taught in the AOA course:

- **Dijkstra's algorithm** (Dijkstra, 1959) explores the graph outward from the origin in order of distance, and is guaranteed to find the shortest path.
- **A\*** (Hart, Nilsson and Raphael, 1968) extends Dijkstra by adding a heuristic estimate of the remaining distance to the goal. If the heuristic is well chosen, A\* explores far fewer nodes.

The theory is clear, but its practical effect depends on the heuristic and the shape of the real network. This project measures that effect on real Mumbai roads, rather than on synthetic graphs.

---

## 2. Problem Statement and Objectives

**Problem:** Given a road network and two points, find the shortest drivable route between them, and compare how much work Dijkstra and A\* each need to do.

**Objectives:**

1. Build a real, bounded road graph of a Mumbai area from OpenStreetMap.
2. Implement Dijkstra and A\* with instrumentation for nodes expanded, peak queue size, runtime and path cost.
3. Implement three heuristics for A\* and check whether each one is admissible.
4. Run a reproducible benchmark over short, medium and long routes.
5. Present the results in an interactive dashboard and a written analysis.

---

## 3. Background

### 3.1 Dijkstra's Algorithm

Dijkstra maintains a priority queue of frontier nodes ordered by their distance from the origin, g(n). At each step it removes the closest node, relaxes its outgoing edges, and repeats until the target is removed. With non-negative edge weights, the first time the target is removed its distance is optimal.

### 3.2 A\* Search

A\* orders the queue by f(n) = g(n) + h(n), where h(n) estimates the remaining distance from n to the goal. With h(n) = 0 it reduces to Dijkstra. A useful heuristic points the search toward the goal, so fewer nodes are explored.

### 3.3 Admissibility and Consistency

- A heuristic is **admissible** if it never overestimates the true remaining distance. Admissibility guarantees that A\* returns the optimal path.
- A heuristic is **consistent** if h(u) ≤ w(u, v) + h(v) for every edge (u, v). Consistency guarantees that each node is expanded at most once, which the closed-set implementation in this project relies on.

Consistency implies admissibility, so a consistent heuristic is the safer choice.

---

## 4. Data and Graph Construction

### 4.1 Source and Extraction

The road network was downloaded with OSMnx (Boeing, 2017) from OpenStreetMap using the drivable network type. The centre point is Dadar, Mumbai (19.0174° N, 72.8430° E), with a 3,000 m radius. The download script is `src/load_graph.py`.

### 4.2 Cleaning and Simplification

The raw extract was processed by OSMnx as follows:

| Stage | Nodes | Edges |
|---|---|---|
| Raw OpenStreetMap extract | 15,901 | 27,126 |
| After truncation to the 3 km polygon | 15,207 (inside polygon) | — |
| After topological simplification | 4,327 | 9,429 |
| After truncation and largest weakly connected component | 3,561 | 7,799 |
| **Final: largest strongly connected component** | **3,529** | **7,760** |

Simplification merges chains of nodes that only bend the road into single edges, keeping the intersections. Restricting to the largest strongly connected component guarantees that every node can reach every other node, so every test route has an answer.

### 4.3 Edge Weights

Each edge carries its physical length in metres (the OSMnx `length` attribute). Lengths are used rather than travel times, so the great-circle distance remains a valid lower bound for the heuristic (see Section 5.3).

---

## 5. Implementation

The project is organised into four parts:

| Folder / file | Purpose |
|---|---|
| `src/load_graph.py` | Downloads the corridor graph with retries across public Overpass servers |
| `src/routing.py` | Dijkstra, A\*, heuristics and instrumentation |
| `experiments/make_queries.py` | Generates the fixed set of test routes |
| `experiments/run_benchmark.py` | Runs every algorithm on every route and writes the results |
| `dashboard/app.py` | RouteScope interactive dashboard (Streamlit) |
| `tests/test_routing.py` | Unit tests for the algorithms and heuristics |

### 5.1 Search Procedure

Both algorithms share one function, `_search`. It keeps:

- `g_score`: the best known cost from the origin to each node
- `parent`: the predecessor of each node, used to rebuild the path
- `closed`: the set of nodes already expanded
- a binary heap of `(f, g, node)` entries

Each iteration pops the best entry, skips stale entries, expands the node, and relaxes its edges. Metrics are counted as the search runs: nodes expanded, the largest heap size reached, and the elapsed time measured with `time.perf_counter`.

### 5.2 Heuristics

| Name | Definition | Admissible? |
|---|---|---|
| zero | h(n) = 0 | Yes (A\* equals Dijkstra) |
| haversine | Great-circle distance between n and the goal, in metres | Yes |
| manhattan | North-south distance plus east-west distance, each measured along a great circle | No |

### 5.3 Why Haversine Is Admissible

Road lengths are measured along the road, which can never be shorter than the straight line between its ends. The great-circle distance is the shortest distance on the Earth's surface between two points, so it is never greater than any road between them. Hence h(n) ≤ true road distance, which is admissible. Because the great-circle distance is a metric, it also satisfies the triangle inequality, which makes the heuristic consistent.

Manhattan distance is the sum of two perpendicular legs. For a diagonal trip the sum can be larger than the direct distance, so it can exceed the true cost of the remaining road distance. It is therefore not admissible, and it can make A\* return longer routes.

A note on coordinates: an earlier draft planned to use Euclidean distance in degrees. That would be wrong for latitude and longitude, so the project uses haversine distance in metres.

---

## 6. Experimental Setup

- **Test routes:** 30 origin-destination pairs, sampled at random with a fixed seed (42) from three straight-line distance bands:
  - Short: 500 to 1,500 m (10 routes)
  - Medium: 2,000 to 3,500 m (10 routes)
  - Long: 4,000 to 6,000 m (10 routes)
- **Algorithms:** Dijkstra, and A\* with zero, haversine and Manhattan heuristics (five runs per route).
- **Reference for optimality:** Dijkstra's path cost. A result counts as optimal if its cost matches Dijkstra's within 10⁻⁶ metres.
- **Metrics:** nodes expanded (primary), peak priority-queue size, runtime, path cost, path length in nodes.
- **Environment:** Python 3.13, NetworkX 3.6 for graph handling, and the algorithm code in `src/routing.py`.

Reproducibility: `make_queries.py` and `run_benchmark.py` are deterministic apart from runtime, so the query file and the expansion counts can be regenerated exactly.

---

## 7. Results

### 7.1 Average Nodes Expanded

| Band | Dijkstra | A\* zero | A\* haversine | A\* manhattan |
|---|---|---|---|---|
| Short | 855.4 | 855.4 (0%) | 256.1 (70.1% fewer) | 201.1 (76.5% fewer) |
| Medium | 1,738.9 | 1,738.9 (0%) | 382.6 (78.0% fewer) | 253.5 (85.4% fewer) |
| Long | 2,825.8 | 2,825.8 (0%) | 821.2 (70.9% fewer) | 414.2 (85.3% fewer) |

### 7.2 Optimality

| Band | A\* zero | A\* haversine | A\* manhattan |
|---|---|---|---|
| Short | 100% | 100% | 50% |
| Medium | 100% | 100% | 20% |
| Long | 100% | 100% | 20% |

### 7.3 Runtime

Runtimes are on the order of 1 to 6 ms per search on the development machine, and differ slightly between runs and computers. Runtime follows the same pattern as expansions (A\* haversine is about two to three times faster than Dijkstra on long routes), but the expansion counts are the more reliable figure and are the basis of the conclusions.

### 7.4 Example Route

For the long-route test L05 (4.73 km), Dijkstra expanded 2,535 nodes and A\* with the haversine heuristic expanded 374. Both returned the same route cost.

---

## 8. Analysis and Discussion

**Effect of the heuristic.** The zero heuristic matches Dijkstra exactly, which is a useful sanity check: the instrumented code behaves identically when no guidance is given. The haversine heuristic gives a consistent reduction of roughly 70 to 78 percent in nodes expanded, with no loss of optimality. This is the expected result for an admissible, consistent heuristic on a road network where straight-line distance is a good approximation of remaining distance.

**Effect of an inadmissible heuristic.** The Manhattan heuristic expands the fewest nodes, but it returned suboptimal routes for most medium and long queries. The speed comes directly from overestimating the remaining distance. This is a real trade-off: speed gained by breaking the admissibility rule is not free, and it is unacceptable where the shortest route matters.

**Effect of route length.** The number of nodes expanded grows with route length for every algorithm, because a longer route covers more of the network. A\* with haversine keeps a similar percentage saving across the three bands, which suggests the heuristic keeps pointing in the right direction regardless of distance.

**Peak queue size.** A\* generally holds fewer entries in its priority queue than Dijkstra, because it discards frontier nodes that point away from the goal. This is visible in the results file and supports the memory argument for A\* on large networks.

---

## 9. Complexity Analysis

Let V be the number of nodes and E the number of edges. Here V = 3,529 and E = 7,760.

| Algorithm | Best case (time) | Average case (time) | Worst case (time) | Space |
|---|---|---|---|---|
| Dijkstra (binary heap) | O((V+E) log V) | O((V+E) log V) | O((V+E) log V) | O(V) |
| A\* with admissible, consistent h | O(path length × log V) | Depends on h accuracy | O((V+E) log V) | O(V) |
| A\* with zero h | O((V+E) log V) | O((V+E) log V) | O((V+E) log V) | O(V) |

**Interpretation.** The worst case of A\* matches Dijkstra, because a heuristic cannot make the search do more work than a full Dijkstra run. The advantage is in the average case: the better the heuristic approximates the true remaining distance, the fewer nodes are expanded. On this network, the average-case constant is about 0.3 of Dijkstra's for haversine.

For this graph, (V+E) log₂ V ≈ 11,289 × 11.8 ≈ 133,000 elementary heap operations in the worst case, against the measured 855 to 2,826 expansions. The measured counts sit well below the bound, as expected, because the search stops when the target is reached.

---

## 10. Limitations

- **Graph size:** The 3 km area has about 3,500 nodes. Real navigation graphs have millions. The scaling behaviour on larger graphs is not yet measured (see future work).
- **Static weights:** Edge weights are fixed road lengths. Traffic, one-way delays, and turn penalties are not modelled.
- **Simplified graph:** Chains of bends are merged into single edges, so the routes follow intersections rather than exact road geometry.
- **Single area and 30 queries:** The conclusions are based on one area and one set of queries. A larger query set would give tighter confidence intervals.
- **Runtime variability:** Runtimes depend on the computer and background load. Expansion counts are machine-independent and are the primary measure.

---

## 11. Future Work

1. **Scaling experiment:** Repeat the comparison on graphs of increasing radius (1, 2, 3 and 5 km) and plot expansions and runtime against graph size, comparing the trend with O((V+E) log V).
2. **Larger area:** Extend the corridor along the Western or Central railway line, as originally planned.
3. **Dynamic weights:** Add traffic-dependent travel times and study how often re-planning is needed.
4. **Bidirectional search:** Compare with bidirectional Dijkstra or bidirectional A\*.

---

## 12. Conclusion

This project implemented Dijkstra's algorithm and A\* from first principles and measured them on a real Mumbai road network. A\* with the haversine heuristic returned the optimal route in every test case and expanded 70 to 78 percent fewer nodes than Dijkstra. The Manhattan heuristic was faster still but gave up optimality, which illustrates why admissibility matters. The zero-heuristic run confirmed that the instrumented code reproduces Dijkstra exactly. The results are available as a reproducible benchmark and an interactive dashboard.

---

## References

1. Dijkstra, E. W. (1959). A note on two problems in connexion with graphs. *Numerische Mathematik*, 1, 269–271.
2. Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). A formal basis for the heuristic determination of minimum cost paths. *IEEE Transactions on Systems Science and Cybernetics*, 4(2), 100–107.
3. Boeing, G. (2017). OSMnx: New methods for acquiring, constructing, analyzing, and visualizing complex street networks. *Computers, Environment and Urban Systems*, 65, 126–139.
4. OpenStreetMap contributors. https://www.openstreetmap.org
5. Hagberg, A., Schult, D., & Swart, P. NetworkX. https://networkx.org
6. Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. *Introduction to Algorithms* (CLRS), chapters on shortest paths.

---

## Appendix: Reproducing the Results

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
python src/load_graph.py          # optional: data is already committed
python experiments/make_queries.py
python experiments/run_benchmark.py
python -m unittest discover -s tests -v
streamlit run dashboard/app.py
```

Output files: `experiments/queries.csv`, `experiments/results.csv` (one row per route and algorithm), `experiments/summary.csv` (averages per band).
