# AIE111 – PowerBank Intelligent Route Finder

## Overview
A route-search system that models PowerBank stations as a weighted graph and compares two manually implemented AI search algorithms: Uniform Cost Search (UCS) and A*. It includes a graphical interface and a command-line interface.

## Requirements
- Python 3.8 or newer
- No third-party packages

## Run
Open a terminal in this project folder and run:

```bash
python gui.py
```

The GUI displays the station network as a graph. Choose start and destination from the lists or click two stations on the graph. It enumerates every loop-free route between them, displays paths using station IDs (for example, `S1 -> S2 -> S6`), identifies the shortest and longest costs, and lists the alternatives in the **All routes** tab. Selecting a route highlights it on the graph. The **Algorithm comparison** tab reports UCS/A* status, path cost, expanded and generated nodes, path length, and runtime.

To use the command-line interface instead, run:

```bash
python main.py
```

Choose a menu option. Station IDs are S1 through S8. S8 is intentionally unavailable; S7 is disconnected for no-route testing.

## Run automated tests
```bash
python tests/test_cases.py
```

## Project files
- `main.py`: interactive menu and output
- `gui.py`: Tkinter graphical interface
- `route_analysis.py`: simple-route enumeration and shortest/longest summaries
- `graph.py`: JSON loading and adjacency-list construction
- `ucs.py`: UCS algorithm
- `astar.py`: A* algorithm
- `heuristic.py`: Euclidean heuristic and admissibility check
- `path_utils.py`: route reconstruction and formatting
- `performance.py`: execution-time and metric helpers
- `validation.py`: station and graph validation
- `data/stations.json`: sample station network
- `tests/test_cases.py`: documented tests

## Graph and costs
Each connection has a numeric travel cost. A connection is two-way unless `one_way` is true. Connections marked `available: false` are omitted from the usable graph. Station availability is checked before a search is launched from either interface.

## Heuristic safety
Euclidean distance is used only when every included edge cost is at least the straight-line distance between its endpoints. Otherwise A* automatically uses `h(n)=0`, preserving optimality while behaving like UCS. This avoids an overestimating heuristic.

## Metrics
- Expanded nodes: nodes removed from the priority queue and actually expanded (the goal is counted when popped).
- Generated nodes: start plus successful best-cost insertions into the frontier.
- Path length: number of edges in the returned route.
- Execution time: measured with `time.perf_counter()` and reported in milliseconds.

Small execution-time differences are noisy and can change between runs. Expanded-node counts are usually more informative on this small example.
