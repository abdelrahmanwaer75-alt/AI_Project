"""Utilities for rebuilding and formatting routes."""


def reconstruct_path(parent, start, goal):
    """Rebuild a route; return [] when the goal has no parent chain."""
    if start == goal:
        return [start]
    if goal not in parent:
        return []
    path = [goal]
    current = goal
    while current != start:
        if current not in parent:
            return []
        current = parent[current]
        path.append(current)
    path.reverse()
    return path


def route_length(route):
    """Return the number of edges in a route."""
    return max(0, len(route) - 1)


def format_route(route, stations):
    """Format station IDs as a readable route."""
    if not route:
        return "No route found"
    names = [stations.get(sid, {}).get("name", sid) for sid in route]
    return " -> ".join(names)
