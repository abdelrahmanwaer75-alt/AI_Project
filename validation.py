"""Input and graph validation helpers."""


def validate_station_id(station_id, stations):
    if not station_id:
        return False, "Station ID cannot be empty."
    if station_id not in stations:
        return False, "Unknown station ID. Please choose an ID from the list."
    return True, ""


def validate_available(station_id, stations):
    if not stations[station_id].get("available", False):
        return False, "This station is currently unavailable."
    return True, ""


def validate_graph(graph):
    """Raise ValueError if an edge cost is invalid."""
    for source, neighbors in graph.items():
        for destination, cost in neighbors:
            if not isinstance(cost, (int, float)) or cost < 0:
                raise ValueError("Invalid negative or non-numeric cost.")
            if destination not in graph:
                raise ValueError("Connection points to an unknown station.")
    return True


def read_station(prompt, stations):
    """Keep asking until the user enters a known, available station."""
    while True:
        value = input(prompt).strip().upper()
        valid, message = validate_station_id(value, stations)
        if not valid:
            print(message)
            continue
        valid, message = validate_available(value, stations)
        if not valid:
            print(message)
            continue
        return value
