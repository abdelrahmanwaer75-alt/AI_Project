"""Graphical interface for the PowerBank route finder (Tkinter only)."""
import tkinter as tk
from tkinter import messagebox, ttk

from astar import a_star_search
from graph import build_graph, display_name, load_data
from route_analysis import enumerate_simple_routes, summarize_routes
from ucs import uniform_cost_search
from validation import validate_graph


COLORS = {
    "background": "#0b1220",
    "panel": "#121c2e",
    "panel_light": "#18253a",
    "border": "#26354b",
    "text": "#edf3fb",
    "muted": "#9aabc1",
    "accent": "#39c6a5",
    "blue": "#65a9ff",
    "orange": "#ffb45b",
    "red": "#f17676",
    "edge": "#42516a",
    "canvas": "#0e1727",
}


class PowerBankApp:
    """Interactive route finder with a station graph and route analysis."""

    def __init__(self, root, data=None):
        self.root = root
        self.root.title("PowerBank | Intelligent Route Finder")
        self.root.geometry("1240x840")
        self.root.minsize(920, 700)
        self.root.configure(bg=COLORS["background"])

        self.data = data if data is not None else load_data()
        self.stations = self.data["stations"]
        self.graph = build_graph(self.data)
        validate_graph(self.graph)
        self.station_ids = list(self.stations)
        self.available_ids = [
            station_id for station_id in self.station_ids
            if self.stations[station_id].get("available", False)
        ]
        self.start_var = tk.StringVar(value=self.available_ids[0] if self.available_ids else "")
        default_goal = self.available_ids[1] if len(self.available_ids) > 1 else self.start_var.get()
        self.goal_var = tk.StringVar(value=default_goal)
        self.algorithm_var = tk.StringVar(value="Compare UCS and A*")
        self.status_var = tk.StringVar(value="Choose two stations, then run a search.")
        self.shortest_var = tk.StringVar(value="Shortest route: run a search.")
        self.longest_var = tk.StringVar(value="Longest route: run a search.")
        self._graph_positions = {}
        self._station_click_step = 0
        self.routes = []
        self.shortest_route = None
        self.longest_route = None
        self.selected_route = None
        self._route_items = {}
        self._configure_styles()
        self._build_layout()
        self._draw_graph()
        self.root.bind("<Return>", lambda _event: self.run_search())

    def _configure_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Route.TCombobox", fieldbackground=COLORS["panel_light"],
            background=COLORS["panel_light"], foreground=COLORS["text"],
            arrowcolor=COLORS["text"], bordercolor=COLORS["border"], padding=8,
        )
        style.map("Route.TCombobox", fieldbackground=[("readonly", COLORS["panel_light"])])
        style.configure(
            "Results.Treeview", background=COLORS["panel"], foreground=COLORS["text"],
            fieldbackground=COLORS["panel"], rowheight=36, borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Results.Treeview.Heading", background=COLORS["panel_light"],
            foreground=COLORS["muted"], font=("Segoe UI", 9, "bold"), padding=8,
        )
        style.map("Results.Treeview", background=[("selected", "#29435a")])

    def _build_layout(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        header = tk.Frame(self.root, bg=COLORS["background"])
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(22, 15))
        header.grid_columnconfigure(0, weight=1)
        tk.Label(
            header, text="POWERBANK ROUTE FINDER", bg=COLORS["background"],
            fg=COLORS["accent"], font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            header, text="Compare every route across the station network",
            bg=COLORS["background"], fg=COLORS["text"],
            font=("Segoe UI", 21, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=(4, 2))
        tk.Label(
            header, text="Review all possible paths, then compare the shortest and longest.",
            bg=COLORS["background"], fg=COLORS["muted"], font=("Segoe UI", 10),
        ).grid(row=2, column=0, sticky="w")
        tk.Label(
            header, text="AI SEARCH  /  AIE111", bg=COLORS["panel"], fg=COLORS["blue"],
            font=("Segoe UI", 9, "bold"), padx=12, pady=8,
        ).grid(row=0, column=1, rowspan=2, sticky="ne", padx=(16, 0))

        body = tk.Frame(self.root, bg=COLORS["background"])
        body.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 15))
        body.grid_columnconfigure(0, weight=2, uniform="body")
        body.grid_columnconfigure(1, weight=3, uniform="body")
        body.grid_rowconfigure(0, weight=1)

        graph_panel = self._panel(body)
        graph_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        graph_panel.grid_rowconfigure(1, weight=1)
        graph_panel.grid_columnconfigure(0, weight=1)
        self._section_title(graph_panel, "Station graph", "Click a station to set start, then destination.")
        self.graph_canvas = tk.Canvas(
            graph_panel, bg=COLORS["canvas"], highlightthickness=0, height=420,
        )
        self.graph_canvas.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 10))
        self.graph_canvas.bind("<Configure>", lambda _event: self._draw_graph())
        legend = tk.Frame(graph_panel, bg=COLORS["panel"])
        legend.grid(row=2, column=0, sticky="ew", padx=17, pady=(0, 14))
        self._legend_item(legend, COLORS["accent"], "Start")
        self._legend_item(legend, COLORS["orange"], "Destination")
        self._legend_item(legend, COLORS["accent"], "Shortest")
        self._legend_item(legend, COLORS["orange"], "Longest")

        side = tk.Frame(body, bg=COLORS["background"])
        side.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        side.grid_columnconfigure(0, weight=1)
        side.grid_rowconfigure(1, weight=1)

        controls = self._panel(side)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        controls.grid_columnconfigure(0, weight=1)
        self._section_title(controls, "Plan a route", "Unavailable stations cannot be selected.")
        fields = tk.Frame(controls, bg=COLORS["panel"])
        fields.grid(row=1, column=0, sticky="ew", padx=16, pady=(3, 8))
        fields.grid_columnconfigure(0, weight=1, uniform="stations")
        fields.grid_columnconfigure(1, weight=1, uniform="stations")
        self._field_label(fields, "STARTING STATION", 0, column=0)
        self.start_combo = self._station_combo(fields, self.start_var, 1, column=0)
        if self.start_var.get():
            self.start_combo.set(self._station_choice(self.start_var.get()))
        self._field_label(fields, "DESTINATION", 0, column=1)
        self.goal_combo = self._station_combo(fields, self.goal_var, 1, column=1)
        if self.goal_var.get():
            self.goal_combo.set(self._station_choice(self.goal_var.get()))
        self._field_label(fields, "SEARCH METHOD", 2, column=0, columnspan=2)
        self.algorithm_combo = ttk.Combobox(
            fields, textvariable=self.algorithm_var, state="readonly",
            values=("Compare UCS and A*", "Uniform Cost Search (UCS)", "A* Search"),
            style="Route.TCombobox",
        )
        self.algorithm_combo.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self.algorithm_combo.bind("<<ComboboxSelected>>", self._selection_changed)

        actions = tk.Frame(controls, bg=COLORS["panel"])
        actions.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        actions.grid_columnconfigure(0, weight=2)
        actions.grid_columnconfigure(1, weight=1)
        self.run_button = tk.Button(
            actions, text="Find best route", command=self.run_search,
            bg=COLORS["accent"], fg="#071712", activebackground="#56d8b8",
            activeforeground="#071712", relief="flat", bd=0, cursor="hand2",
            font=("Segoe UI", 10, "bold"), padx=14, pady=11,
        )
        self.run_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        tk.Button(
            actions, text="Reset", command=self.reset_view,
            bg=COLORS["panel_light"], fg=COLORS["text"], activebackground="#22344c",
            activeforeground=COLORS["text"], relief="flat", bd=0, cursor="hand2",
            font=("Segoe UI", 9), padx=12, pady=9,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        results = self._panel(side)
        results.grid(row=1, column=0, sticky="nsew")
        results.grid_columnconfigure(0, weight=1)
        results.grid_rowconfigure(2, weight=1)
        self._section_title(results, "Search results", "Route quality and search effort.")
        summary = tk.Frame(results, bg=COLORS["panel_light"])
        summary.grid(row=1, column=0, sticky="ew", padx=16, pady=(2, 10))
        tk.Label(
            summary, textvariable=self.shortest_var, bg=COLORS["panel_light"],
            fg=COLORS["accent"], font=("Segoe UI", 9, "bold"), anchor="w",
            justify="left", wraplength=650,
        ).pack(fill="x", padx=12, pady=(8, 3))
        tk.Label(
            summary, textvariable=self.longest_var, bg=COLORS["panel_light"],
            fg=COLORS["orange"], font=("Segoe UI", 9, "bold"), anchor="w",
            justify="left", wraplength=650,
        ).pack(fill="x", padx=12, pady=(0, 8))

        self.results_notebook = ttk.Notebook(results)
        self.results_notebook.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 14))
        comparison_tab = tk.Frame(self.results_notebook, bg=COLORS["panel"])
        self.routes_tab = tk.Frame(self.results_notebook, bg=COLORS["panel"])
        self.results_notebook.add(comparison_tab, text="Algorithm comparison")
        self.results_notebook.add(self.routes_tab, text="All routes")
        comparison_tab.grid_columnconfigure(0, weight=1)
        comparison_tab.grid_rowconfigure(0, weight=1)
        self.routes_tab.grid_columnconfigure(0, weight=1)
        self.routes_tab.grid_rowconfigure(0, weight=1)

        table_frame = tk.Frame(comparison_tab, bg=COLORS["panel"])
        table_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        self.results_table = ttk.Treeview(
            table_frame, columns=("metric", "ucs", "astar"), show="headings",
            style="Results.Treeview", height=9,
        )
        self.results_table.heading("metric", text="METRIC", anchor="w")
        self.results_table.heading("ucs", text="UCS", anchor="center")
        self.results_table.heading("astar", text="A*", anchor="center")
        self.results_table.column("metric", width=180, minwidth=145, anchor="w")
        self.results_table.column("ucs", width=125, minwidth=100, anchor="center")
        self.results_table.column("astar", width=125, minwidth=100, anchor="center")
        self.results_table.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.results_table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.results_table.configure(yscrollcommand=scrollbar.set)
        self.results_table.insert("", "end", values=("Status", "—", "—"))

        routes_frame = tk.Frame(self.routes_tab, bg=COLORS["panel"])
        routes_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        routes_frame.grid_columnconfigure(1, weight=1)
        routes_frame.grid_rowconfigure(0, weight=1)
        self.routes_table = ttk.Treeview(
            routes_frame, columns=("number", "route", "cost", "kind"), show="headings",
            style="Results.Treeview", height=10,
        )
        for column, title in (("number", "#"), ("route", "ROUTE"), ("cost", "COST"), ("kind", "TYPE")):
            self.routes_table.heading(column, text=title, anchor="w" if column == "route" else "center")
        self.routes_table.column("number", width=48, minwidth=42, stretch=False, anchor="center")
        self.routes_table.column("route", width=330, minwidth=210, stretch=True, anchor="w")
        self.routes_table.column("cost", width=88, minwidth=70, stretch=False, anchor="center")
        self.routes_table.column("kind", width=145, minwidth=118, stretch=False, anchor="center")
        self.routes_table.grid(row=0, column=0, sticky="nsew")
        routes_scroll = ttk.Scrollbar(routes_frame, orient="vertical", command=self.routes_table.yview)
        routes_scroll.grid(row=0, column=1, sticky="ns")
        self.routes_table.configure(yscrollcommand=routes_scroll.set)
        self.routes_table.bind("<<TreeviewSelect>>", self._select_route_row)

        footer = tk.Frame(self.root, bg=COLORS["panel"], height=34)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        tk.Label(
            footer, textvariable=self.status_var, bg=COLORS["panel"],
            fg=COLORS["muted"], font=("Segoe UI", 9), anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=28, pady=9)

    def _panel(self, parent):
        return tk.Frame(
            parent, bg=COLORS["panel"], highlightbackground=COLORS["border"],
            highlightthickness=1,
        )

    def _section_title(self, parent, title, subtitle):
        block = tk.Frame(parent, bg=COLORS["panel"])
        block.grid(row=0, column=0, sticky="ew", padx=16, pady=(15, 10))
        tk.Label(
            block, text=title, bg=COLORS["panel"], fg=COLORS["text"],
            font=("Segoe UI", 12, "bold"), anchor="w",
        ).pack(fill="x")
        tk.Label(
            block, text=subtitle, bg=COLORS["panel"], fg=COLORS["muted"],
            font=("Segoe UI", 9), anchor="w",
        ).pack(fill="x", pady=(2, 0))

    def _legend_item(self, parent, color, text):
        item = tk.Frame(parent, bg=COLORS["panel"])
        item.pack(side="left", padx=(0, 13))
        tk.Label(item, text="●", bg=COLORS["panel"], fg=color, font=("Segoe UI", 10)).pack(side="left")
        tk.Label(item, text=text, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left", padx=(4, 0))

    def _field_label(self, parent, text, row, column=0, columnspan=1):
        tk.Label(
            parent, text=text, bg=COLORS["panel"], fg=COLORS["muted"],
            font=("Segoe UI", 8, "bold"), anchor="w",
        ).grid(row=row, column=column, columnspan=columnspan, sticky="ew", pady=(8 if row else 0, 0))

    def _station_combo(self, parent, variable, row, column=0):
        choices = [self._station_choice(station_id) for station_id in self.available_ids]
        combo = ttk.Combobox(
            parent, textvariable=variable, values=choices, state="readonly",
            style="Route.TCombobox",
        )
        combo.grid(row=row, column=column, sticky="ew", padx=(0, 6) if column == 0 else (6, 0), pady=(4, 0))
        combo.bind("<<ComboboxSelected>>", self._selection_changed)
        return combo

    def _station_choice(self, station_id):
        return "{}  ·  {}".format(station_id, display_name(self.stations, station_id))

    @staticmethod
    def _format_station_ids(route):
        return " -> ".join(route) if route else "No route"

    def _selection_changed(self, _event=None):
        self.routes = []
        self.shortest_route = None
        self.longest_route = None
        self.selected_route = None
        self._route_items.clear()
        self.routes_table.delete(*self.routes_table.get_children())
        self.results_table.delete(*self.results_table.get_children())
        self.results_table.insert("", "end", values=("Status", "—", "—"))
        self.results_notebook.select(0)
        self.results_notebook.tab(self.routes_tab, text="All routes")
        self.shortest_var.set("Shortest route: run a search.")
        self.longest_var.set("Longest route: run a search.")
        self.status_var.set("Selection changed. Run the search to refresh results.")
        self._draw_graph()

    def _draw_graph(self):
        if not hasattr(self, "graph_canvas"):
            return
        width = max(self.graph_canvas.winfo_width(), 380)
        height = max(self.graph_canvas.winfo_height(), 320)
        self.graph_canvas.delete("all")
        self._graph_positions = {}
        margin_x, margin_y = 52, 54
        coordinates = [
            (self.stations[sid]["x"], self.stations[sid]["y"])
            for sid in self.station_ids
        ]
        min_x = min(point[0] for point in coordinates)
        max_x = max(point[0] for point in coordinates)
        min_y = min(point[1] for point in coordinates)
        max_y = max(point[1] for point in coordinates)
        scale_x = max(width - 2 * margin_x, 1) / max(max_x - min_x, 1)
        scale_y = max(height - 2 * margin_y, 1) / max(max_y - min_y, 1)
        for station_id in self.station_ids:
            station = self.stations[station_id]
            self._graph_positions[station_id] = (
                margin_x + (station["x"] - min_x) * scale_x,
                margin_y + (station["y"] - min_y) * scale_y,
            )

        short_edges = self._route_edges(self.shortest_route)
        long_edges = self._route_edges(self.longest_route)
        chosen_edges = self._route_edges(self.selected_route)
        for connection in self.data.get("connections", []):
            if not connection.get("available", True):
                continue
            source, destination = connection["from"], connection["to"]
            x1, y1 = self._graph_positions[source]
            x2, y2 = self._graph_positions[destination]
            edge = frozenset((source, destination))
            if chosen_edges and edge in chosen_edges:
                color, line_width = COLORS["blue"], 4
            elif edge in short_edges and edge in long_edges:
                color, line_width = "#c9a5ff", 4
            elif edge in short_edges:
                color, line_width = COLORS["accent"], 3.5
            elif edge in long_edges:
                color, line_width = COLORS["orange"], 3.5
            else:
                color, line_width = COLORS["edge"], 1.5
            self.graph_canvas.create_line(
                x1, y1, x2, y2, fill=color, width=line_width,
                arrow="last" if connection.get("one_way", False) else "none",
                arrowshape=(9, 11, 4),
            )
            label_x, label_y = (x1 + x2) / 2, (y1 + y2) / 2
            self.graph_canvas.create_oval(
                label_x - 15, label_y - 10, label_x + 15, label_y + 10,
                fill=COLORS["canvas"], outline="",
            )
            self.graph_canvas.create_text(
                label_x, label_y, text="{:g}".format(connection["cost"]),
                fill=COLORS["text"], font=("Segoe UI", 8, "bold"),
            )

        start_id = self._selected_station_id(self.start_combo, self.start_var) if hasattr(self, "start_combo") else self.start_var.get()
        goal_id = self._selected_station_id(self.goal_combo, self.goal_var) if hasattr(self, "goal_combo") else self.goal_var.get()
        for station_id in self.station_ids:
            x, y = self._graph_positions[station_id]
            available = self.stations[station_id].get("available", False)
            if station_id == start_id:
                fill, outline, text_color = COLORS["accent"], COLORS["accent"], "#071712"
            elif station_id == goal_id:
                fill, outline, text_color = COLORS["orange"], COLORS["orange"], "#211405"
            elif not available:
                fill, outline, text_color = "#293548", "#66748a", "#aab6c8"
            else:
                fill, outline, text_color = COLORS["panel_light"], COLORS["border"], COLORS["text"]
            radius = 22
            tags = ("station:" + station_id, "station")
            self.graph_canvas.create_oval(
                x - radius, y - radius, x + radius, y + radius,
                fill=fill, outline=outline, width=2, tags=tags,
            )
            self.graph_canvas.create_text(
                x, y, text=station_id, fill=text_color,
                font=("Segoe UI", 9, "bold"), tags=tags,
            )
            self.graph_canvas.create_text(
                x, y + radius + 13, text=display_name(self.stations, station_id),
                fill=COLORS["muted"] if available else "#78869a",
                font=("Segoe UI", 7), width=95, justify="center", tags=tags,
            )
            self.graph_canvas.tag_bind(
                "station:" + station_id,
                "<Button-1>", lambda event, sid=station_id: self._select_graph_station(event, sid),
            )

    @staticmethod
    def _route_edges(route_record):
        if not route_record:
            return set()
        path = route_record["route"]
        return {frozenset((source, destination)) for source, destination in zip(path, path[1:])}

    def _select_graph_station(self, _event, station_id):
        if not self.stations[station_id].get("available", False):
            self.status_var.set("{} is unavailable. Choose an open station.".format(station_id))
            return
        if self._station_click_step % 2 == 0:
            self.start_var.set(station_id)
            self.start_combo.set(self._station_choice(station_id))
            message = "Start set to {}. Select the destination.".format(station_id)
        else:
            self.goal_var.set(station_id)
            self.goal_combo.set(self._station_choice(station_id))
            message = "Destination set to {}. Run the search.".format(station_id)
        self._station_click_step += 1
        self._selection_changed()
        self.status_var.set(message)

    def _selected_station_id(self, combo, variable):
        value = variable.get().strip()
        if value in self.stations:
            return value
        # Combobox display values contain the station ID followed by the name.
        station_id = value.split("  ·  ", 1)[0]
        if station_id in self.stations:
            return station_id
        # Also accept an ID entered manually if a platform permits typing.
        return combo.get().strip().split("  ·  ", 1)[0]

    def run_search(self):
        start = self._selected_station_id(self.start_combo, self.start_var)
        goal = self._selected_station_id(self.goal_combo, self.goal_var)
        if start not in self.available_ids or goal not in self.available_ids:
            messagebox.showerror("Choose valid stations", "Select an available start and destination station.", parent=self.root)
            return

        method = self.algorithm_var.get()
        ucs_result = None
        astar_result = None
        self.routes = enumerate_simple_routes(self.graph, start, goal)
        self.shortest_route, self.longest_route = summarize_routes(self.routes)
        self.selected_route = None

        if method in ("Compare UCS and A*", "Uniform Cost Search (UCS)"):
            ucs_result = uniform_cost_search(self.graph, start, goal)
        if method in ("Compare UCS and A*", "A* Search"):
            astar_result = a_star_search(self.graph, self.stations, start, goal)

        self.results_table.delete(*self.results_table.get_children())
        for label, key in (
            ("Status", "status"), ("Total cost", "cost"),
            ("Expanded nodes", "expanded_nodes"), ("Generated nodes", "generated_nodes"),
            ("Path length", "path_length"), ("Runtime (ms)", "execution_time_ms"),
        ):
            left = self._format_metric(key, ucs_result) if ucs_result else "—"
            right = self._format_metric(key, astar_result) if astar_result else "—"
            self.results_table.insert("", "end", values=(label, left, right))
        self.results_table.insert(
            "", "end", values=("Loop-free routes", len(self.routes), len(self.routes)),
        )

        self.routes_table.delete(*self.routes_table.get_children())
        self._route_items.clear()
        self.results_notebook.tab(self.routes_tab, text="All routes ({})".format(len(self.routes)))
        if self.routes:
            minimum = self.shortest_route["cost"]
            maximum = self.longest_route["cost"]
            for index, route_record in enumerate(self.routes, start=1):
                cost = route_record["cost"]
                is_shortest = abs(cost - minimum) < 1e-9
                is_longest = abs(cost - maximum) < 1e-9
                if is_shortest and is_longest:
                    kind = "Shortest + longest"
                elif is_shortest:
                    kind = "Shortest"
                elif is_longest:
                    kind = "Longest"
                else:
                    kind = "Alternative"
                item_id = "route_{}".format(index)
                self.routes_table.insert(
                    "", "end", iid=item_id,
                    values=(index, self._format_station_ids(route_record["route"]),
                            "{:g}".format(cost), kind),
                )
                self._route_items[item_id] = route_record
            self.shortest_var.set(
                "Shortest ({}): {} | cost {}".format(
                    sum(abs(route["cost"] - minimum) < 1e-9 for route in self.routes),
                    self._format_station_ids(self.shortest_route["route"]), "{:g}".format(minimum),
                )
            )
            self.longest_var.set(
                "Longest ({}): {} | cost {}".format(
                    sum(abs(route["cost"] - maximum) < 1e-9 for route in self.routes),
                    self._format_station_ids(self.longest_route["route"]), "{:g}".format(maximum),
                )
            )
            self.results_notebook.select(self.routes_tab)
            self.status_var.set(
                "Found {} loop-free routes. Select a route row to highlight it on the graph.".format(len(self.routes))
            )
        else:
            self.shortest_var.set("Shortest route: none found.")
            self.longest_var.set("Longest route: none found.")
            self.results_notebook.select(0)
            self.status_var.set("No route exists between the selected stations.")

        self._draw_graph()
        if method == "Compare UCS and A*" and ucs_result and astar_result:
            if ucs_result["status"] == astar_result["status"] == "Success":
                same_cost = abs(ucs_result["cost"] - astar_result["cost"]) < 1e-9
                self.status_var.set("{} routes found. UCS and A* agree on shortest cost: {}.".format(len(self.routes), same_cost))

    def _select_route_row(self, _event=None):
        selected = self.routes_table.selection()
        self.selected_route = self._route_items.get(selected[0]) if selected else None
        self._draw_graph()

    @staticmethod
    def _format_metric(key, result):
        value = result[key]
        if value is None:
            return "N/A"
        if key == "execution_time_ms":
            return "{:.4f}".format(value)
        if isinstance(value, float):
            return "{:g}".format(value)
        return str(value)

    def reset_view(self):
        if self.available_ids:
            self.start_var.set(self.available_ids[0])
            self.goal_var.set(self.available_ids[1] if len(self.available_ids) > 1 else self.available_ids[0])
            self.start_combo.set(self._station_choice(self.start_var.get()))
            self.goal_combo.set(self._station_choice(self.goal_var.get()))
        self._station_click_step = 0
        self._selection_changed()
        self.results_notebook.select(0)
        self.status_var.set("Choose two stations, then run a search.")


def main():
    root = tk.Tk()
    try:
        PowerBankApp(root)
    except (OSError, KeyError, TypeError, ValueError) as error:
        messagebox.showerror("Could not load project data", str(error), parent=root)
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
