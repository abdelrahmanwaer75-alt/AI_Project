"""Command-line application: PowerBank Intelligent Route Finder."""
from graph import load_data, build_graph, get_available_stations, display_name
from ucs import uniform_cost_search
from astar import a_star_search
from validation import read_station, validate_graph
from path_utils import format_route


def display_stations(stations):
    print("\nID   Station                       Coordinates   Availability")
    print("-" * 68)
    for sid, info in stations.items():
        status = "Available" if info.get("available") else "Unavailable"
        print(f"{sid:<4} {info['name']:<29} ({info['x']}, {info['y']})       {status}")


def display_connections(graph, stations):
    print("\nStation connections (open connections only):")
    for sid, neighbors in graph.items():
        details = ", ".join(
            f"{display_name(stations, other)} [{other}: {cost:g}]"
            for other, cost in neighbors
        ) or "No open connections"
        print(f"{sid} - {display_name(stations, sid)}: {details}")


def show_result(result, stations, algorithm):
    print(f"\n--- {algorithm} Result ---")
    print("Status:", result["status"])
    print("Route:", format_route(result["route"], stations))
    print("Total cost:", f"{result['cost']:g}" if result["cost"] is not None else "N/A")
    print("Expanded nodes:", result["expanded_nodes"])
    print("Generated nodes:", result["generated_nodes"])
    print("Path length (edges):", result["path_length"])
    print(f"Execution time: {result['execution_time_ms']:.6f} ms")


def choose_pair(stations):
    start = read_station("Enter starting station ID: ", stations)
    goal = read_station("Enter destination station ID: ", stations)
    return start, goal


def compare_results(ucs_result, astar_result, stations):
    print("\n{:<20} | {:<27} | {:<27}".format("Metric", "UCS", "A*"))
    print("-" * 80)
    rows = [
        ("Route", format_route(ucs_result["route"], stations), format_route(astar_result["route"], stations)),
        ("Total cost", ucs_result["cost"], astar_result["cost"]),
        ("Expanded nodes", ucs_result["expanded_nodes"], astar_result["expanded_nodes"]),
        ("Execution time (ms)", f"{ucs_result['execution_time_ms']:.6f}", f"{astar_result['execution_time_ms']:.6f}"),
        ("Search status", ucs_result["status"], astar_result["status"]),
    ]
    for metric, left, right in rows:
        print("{:<20} | {:<27} | {:<27}".format(metric, str(left), str(right)))
    if ucs_result["cost"] is not None and astar_result["cost"] is not None:
        print("\nSame optimal cost:", abs(ucs_result["cost"] - astar_result["cost"]) < 1e-9)
    if ucs_result["expanded_nodes"] < astar_result["expanded_nodes"]:
        print("UCS expanded fewer nodes in this run.")
    elif astar_result["expanded_nodes"] < ucs_result["expanded_nodes"]:
        print("A* expanded fewer nodes in this run.")
    else:
        print("Both algorithms expanded the same number of nodes.")


def main():
    data = load_data()
    stations = data["stations"]
    graph = build_graph(data)
    validate_graph(graph)

    while True:
        print("\n==================================")
        print(" POWERBANK INTELLIGENT ROUTE FINDER")
        print("==================================")
        print("1. Display all stations")
        print("2. Display station connections")
        print("3. Find route using UCS")
        print("4. Find route using A*")
        print("5. Compare UCS and A*")
        print("6. Display available stations")
        print("7. Exit")
        choice = input("Choose an option (1-7): ").strip()

        if choice == "1":
            display_stations(stations)
        elif choice == "2":
            display_connections(graph, stations)
        elif choice in ("3", "4", "5"):
            start, goal = choose_pair(stations)
            if choice == "3":
                show_result(uniform_cost_search(graph, start, goal), stations, "UCS")
            elif choice == "4":
                show_result(a_star_search(graph, stations, start, goal), stations, "A*")
            else:
                ucs_result = uniform_cost_search(graph, start, goal)
                astar_result = a_star_search(graph, stations, start, goal)
                compare_results(ucs_result, astar_result, stations)
        elif choice == "6":
            print("\nAvailable stations:")
            for sid in get_available_stations(stations):
                print(f"{sid}: {stations[sid]['name']}")
        elif choice == "7":
            print("Thank you for using PowerBank Intelligent Route Finder.")
            break
        else:
            print("Invalid menu option. Please enter a number from 1 to 7.")


if __name__ == "__main__":
    main()
