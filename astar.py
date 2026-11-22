"""A* Search implemented manually with heapq."""
import heapq
from performance import start_timer, elapsed_ms, make_result
from path_utils import reconstruct_path
from heuristic import heuristic, heuristic_is_safe


def _trace_contains_station(trace_nodes, node_index, station_id):
    while node_index is not None:
        node = trace_nodes[node_index]
        if node["station"] == station_id:
            return True
        node_index = node["parent"]
    return False


def a_star_search(graph, stations, start, goal, trace=None):
    timer = start_timer()
    if start not in graph or goal not in graph or start not in stations or goal not in stations:
        return make_result([], None, 0, 0, elapsed_ms(timer), "Invalid station")

    # If the geometric lower-bound condition fails, use h(n)=0 (safe UCS behavior).
    use_euclidean = heuristic_is_safe(graph, stations)
    def h(node):
        return heuristic(stations[node], stations[goal]) if use_euclidean else 0.0

    trace_nodes = trace.setdefault("nodes", []) if trace is not None else None
    root_index = None
    if trace_nodes is not None:
        trace_nodes.clear()
        trace["goal_node"] = None
        root_index = 0
        trace_nodes.append({
            "station": start, "cost": 0.0, "heuristic": h(start),
            "parent": None, "status": "Frontier",
        })
    frontier = [(h(start), 0.0, start, root_index)]
    best_cost = {start: 0.0}
    parent = {}
    best_trace_node = {start: root_index}
    expanded_best = {}
    expanded = 0
    generated = 1

    while frontier:
        estimated_total, cost, current, trace_index = heapq.heappop(frontier)
        if cost > best_cost.get(current, float("inf")):
            if trace_nodes is not None:
                trace_nodes[trace_index]["status"] = "Superseded"
            continue
        # A node can be reopened if a cheaper route is later discovered.
        if cost >= expanded_best.get(current, float("inf")):
            if trace_nodes is not None:
                trace_nodes[trace_index]["status"] = "Already expanded"
            continue
        expanded_best[current] = cost
        expanded += 1
        if trace_nodes is not None:
            trace_nodes[trace_index]["status"] = "Expanded"

        if current == goal:
            if trace_nodes is not None:
                trace_nodes[trace_index]["status"] = "Goal"
                trace["goal_node"] = trace_index
            route = reconstruct_path(parent, start, goal)
            return make_result(route, cost, expanded, generated,
                               elapsed_ms(timer), "Success")

        for neighbor, edge_cost in graph[current]:
            new_cost = cost + edge_cost
            is_cycle = (
                trace_nodes is not None
                and _trace_contains_station(trace_nodes, trace_index, neighbor)
            )
            improves_best = new_cost < best_cost.get(neighbor, float("inf"))
            child_trace_index = None
            if trace_nodes is not None:
                child_trace_index = len(trace_nodes)
                trace_nodes.append({
                    "station": neighbor, "cost": new_cost, "heuristic": h(neighbor),
                    "parent": trace_index,
                    "status": "Frontier" if improves_best and not is_cycle
                    else "Pruned cycle" if is_cycle else "Pruned higher cost",
                })

            if improves_best and not is_cycle:
                best_cost[neighbor] = new_cost
                parent[neighbor] = current
                if trace_nodes is not None:
                    previous_index = best_trace_node.get(neighbor)
                    if previous_index is not None:
                        trace_nodes[previous_index]["status"] = "Superseded"
                    best_trace_node[neighbor] = child_trace_index
                heapq.heappush(frontier, (new_cost + h(neighbor), new_cost, neighbor, child_trace_index))
                generated += 1

    return make_result([], None, expanded, generated,
                       elapsed_ms(timer), "No route")
