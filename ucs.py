"""Uniform Cost Search implemented manually with heapq."""
import heapq
from performance import start_timer, elapsed_ms, make_result
from path_utils import reconstruct_path


def uniform_cost_search(graph, start, goal):
    timer = start_timer()
    if start not in graph or goal not in graph:
        return make_result([], None, 0, 0, elapsed_ms(timer), "Invalid station")
    frontier = [(0.0, start)]
    best_cost = {start: 0.0}
    parent = {}
    expanded_set = set()
    expanded = 0
    generated = 1

    while frontier:
        cost, current = heapq.heappop(frontier)
        # Ignore outdated queue entries.
        if cost > best_cost.get(current, float("inf")):
            continue
        if current in expanded_set:
            continue
        expanded_set.add(current)
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
                heapq.heappush(frontier, (new_cost, neighbor))
                generated += 1

    return make_result([], None, expanded, generated,
                       elapsed_ms(timer), "No route")
