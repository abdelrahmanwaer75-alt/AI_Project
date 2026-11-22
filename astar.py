"""A* Search implemented manually with heapq."""
import heapq
from performance import start_timer, elapsed_ms, make_result
from path_utils import reconstruct_path
from heuristic import heuristic, heuristic_is_safe


def a_star_search(graph, stations, start, goal):
    timer = start_timer()
    if start not in graph or goal not in graph or start not in stations or goal not in stations:
        return make_result([], None, 0, 0, elapsed_ms(timer), "Invalid station")

    # If the geometric lower-bound condition fails, use h(n)=0 (safe UCS behavior).
    use_euclidean = heuristic_is_safe(graph, stations)

    def h(node):
        return heuristic(stations[node], stations[goal]) if use_euclidean else 0.0

    frontier = [(h(start), 0.0, start)]
    best_cost = {start: 0.0}
    parent = {}
    expanded_best = {}
    expanded = 0
    generated = 1

    while frontier:
        estimated_total, cost, current = heapq.heappop(frontier)
        if cost > best_cost.get(current, float("inf")):
            continue
        # A node can be reopened if a cheaper route is later discovered.
        if cost >= expanded_best.get(current, float("inf")):
            continue
        expanded_best[current] = cost
        expanded += 1

        if current == goal:
            route = reconstruct_path(parent, start, goal)
            return make_result(route, cost, expanded, generated,
                               elapsed_ms(timer), "Success")

        for neighbor, edge_cost in graph[current]:
            new_cost = cost + edge_cost
            if new_cost < best_cost.get(neighbor, float("inf")):
                best_cost[neighbor] = new_cost
                parent[neighbor] = current
                heapq.heappush(frontier, (new_cost + h(neighbor), new_cost, neighbor))
                generated += 1

    return make_result([], None, expanded, generated,
                       elapsed_ms(timer), "No route")
