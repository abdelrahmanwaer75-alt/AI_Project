"""Documented automated tests for UCS and A*."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from graph import load_data, build_graph
from ucs import uniform_cost_search
from astar import a_star_search
from validation import validate_station_id, validate_available


def run_tests():
    data = load_data()
    stations = data["stations"]
    graph = build_graph(data)
    results = []

    def record(name, expected, actual, passed):
        results.append((name, expected, actual, passed))

    # Test 1: normal route.
    u = uniform_cost_search(graph, "S1", "S6")
    a = a_star_search(graph, stations, "S1", "S6")
    record("Normal route", "Both succeed with cost 15",
           f"UCS={u['status']}/{u['cost']}; A*={a['status']}/{a['cost']}",
           u["status"] == "Success" and a["status"] == "Success"
           and u["cost"] == 15 and a["cost"] == 15)

    # Test 2: multiple paths; cheapest is S1-S2-S3-S6 = 15.
    record("Different route costs", "Optimal cost is 15",
           f"UCS={u['cost']}; A*={a['cost']}",
           u["cost"] == 15 and a["cost"] == 15)

    # Test 3: start equals goal.
    same_u = uniform_cost_search(graph, "S2", "S2")
    same_a = a_star_search(graph, stations, "S2", "S2")
    record("Start equals destination", "One-node route, cost 0",
           f"UCS={same_u['route']}/{same_u['cost']}; A*={same_a['route']}/{same_a['cost']}",
           same_u["route"] == ["S2"] and same_a["route"] == ["S2"]
           and same_u["cost"] == 0 and same_a["cost"] == 0)

    # Test 4: disconnected node.
    no_u = uniform_cost_search(graph, "S1", "S7")
    no_a = a_star_search(graph, stations, "S1", "S7")
    record("No available route", "Both return No route",
           f"UCS={no_u['status']}; A*={no_a['status']}",
           no_u["status"] == "No route" and no_a["status"] == "No route")

    # Additional validation tests.
    ok, _ = validate_station_id("BAD", stations)
    record("Invalid station ID", "Rejected", str(ok), not ok)
    ok, _ = validate_available("S8", stations)
    record("Unavailable station", "Rejected", str(ok), not ok)

    # Negative-cost validation is tested directly against the validator.
    from validation import validate_graph
    try:
        validate_graph({"A": [("B", -2)], "B": []})
        negative_rejected = False
    except ValueError:
        negative_rejected = True
    record("Negative edge cost", "ValueError raised", str(negative_rejected), negative_rejected)

    print("\nTEST RESULTS")
    print("-" * 100)
    for name, expected, actual, passed in results:
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
        print(f"  Expected: {expected}")
        print(f"  Actual:   {actual}")
    print(f"\nSummary: {sum(1 for row in results if row[3])}/{len(results)} tests passed.")
    return all(row[3] for row in results)


if __name__ == "__main__":
    raise SystemExit(0 if run_tests() else 1)
