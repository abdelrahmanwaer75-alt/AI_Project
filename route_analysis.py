"""Enumerate and summarize simple routes in a weighted station graph."""


def enumerate_simple_routes(graph, start, goal):
    """Return every loop-free route from start to goal with its total cost.

    A station cannot occur twice in one route, so cycles are excluded. The
    function is intended for the small teaching network in this project.
    """
    if start not in graph or goal not in graph:
        return []

    routes = []
    path = [start]
    visited = {start}

    def visit(current, total_cost):
        if current == goal:
            routes.append({"route": list(path), "cost": total_cost})
            return
        for neighbor, edge_cost in graph[current]:
            if neighbor in visited:
                continue
            visited.add(neighbor)
            path.append(neighbor)
            visit(neighbor, total_cost + edge_cost)
            path.pop()
            visited.remove(neighbor)

    visit(start, 0.0)
    routes.sort(key=lambda item: (item["cost"], item["route"]))
    return routes


def summarize_routes(routes):
    """Return shortest and longest route records, or (None, None)."""
    if not routes:
        return None, None
    shortest = min(routes, key=lambda item: item["cost"])
    longest = max(routes, key=lambda item: item["cost"])
    return shortest, longest
