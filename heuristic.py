"""Heuristic calculations for A*."""
import math


def heuristic(station1, station2):
    """Euclidean distance between two station dictionaries."""
    dx = station1["x"] - station2["x"]
    dy = station1["y"] - station2["y"]
    return math.sqrt(dx * dx + dy * dy)


def heuristic_is_safe(graph, stations):
    """
    A global check: every edge cost must be at least the straight-line
    distance between its endpoints. If true, Euclidean distance is admissible.
    """
    for source, neighbors in graph.items():
        for destination, cost in neighbors:
            distance = heuristic(stations[source], stations[destination])
            if cost + 1e-12 < distance:
                return False
    return True
