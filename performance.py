"""Small helpers for consistent performance reporting."""
import time


def start_timer():
    return time.perf_counter()


def elapsed_ms(start_time):
    return (time.perf_counter() - start_time) * 1000.0


def make_result(route, cost, expanded, generated, duration_ms, status):
    """Create the common result structure returned by both algorithms."""
    return {
        "route": route,
        "cost": cost,
        "expanded_nodes": expanded,
        "generated_nodes": generated,
        "path_length": max(0, len(route) - 1),
        "execution_time_ms": duration_ms,
        "status": status,
    }
