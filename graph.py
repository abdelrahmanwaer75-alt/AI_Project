"""Graph and station-data utilities for the PowerBank route finder."""
import json
from pathlib import Path


def load_data(file_path=None):
    """Load station and connection data from JSON."""
    if file_path is None:
        file_path = Path(__file__).parent / "data" / "stations.json"
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_graph(data):
    """Build an adjacency list; only open connections are included."""
    graph = {station_id: [] for station_id in data["stations"]}
    for edge in data["connections"]:
        if not edge.get("available", True):
            continue
        source = edge["from"]
        destination = edge["to"]
        cost = edge["cost"]
        if source not in graph or destination not in graph:
            raise ValueError("A connection refers to an unknown station.")
        if not isinstance(cost, (int, float)) or cost < 0:
            raise ValueError("Connection costs must be non-negative numbers.")
        graph[source].append((destination, float(cost)))
        if not edge.get("one_way", False):
            graph[destination].append((source, float(cost)))
    return graph


def get_available_stations(stations):
    """Return station IDs whose availability is True."""
    return [sid for sid, info in stations.items() if info.get("available", False)]


def display_name(stations, station_id):
    """Return a readable station name, falling back to its ID."""
    return stations.get(station_id, {}).get("name", station_id)
