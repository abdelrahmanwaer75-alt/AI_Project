"""Graphical interface for the PowerBank route finder (Tkinter only)."""
import tkinter as tk
from tkinter import messagebox, ttk

from astar import a_star_search
from graph import build_graph, display_name, load_data
from path_utils import format_route
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
    """Interactive route finder with a search tree and algorithm metrics."""

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
        self.tree_detail_var = tk.StringVar(value="Click a node to inspect its path details.")
        self._tree_zoom = 1.0
        self._tree_trace = None
        self._tree_route_nodes = set()
        self._tree_selected_index = None
        self._configure_styles()
        self._build_layout()
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
            header, text="Find the lowest-cost route across campus",
            bg=COLORS["background"], fg=COLORS["text"],
            font=("Segoe UI", 21, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=(4, 2))
        tk.Label(
            header, text="Choose stations from the lists. Compare UCS with A*.",
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

        tree_panel = self._panel(body)
        tree_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        tree_panel.grid_rowconfigure(1, weight=1)
        tree_panel.grid_columnconfigure(0, weight=1)
        self._tree_header(tree_panel)
        tree_frame = tk.Frame(tree_panel, bg=COLORS["panel"])
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 10))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        self.search_canvas = tk.Canvas(
            tree_frame, bg=COLORS["canvas"], highlightthickness=0,
            xscrollincrement=35, yscrollincrement=35,
        )
        self.search_canvas.grid(row=0, column=0, sticky="nsew")
        tree_y_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.search_canvas.yview)
        tree_y_scroll.grid(row=0, column=1, sticky="ns")
        tree_x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.search_canvas.xview)
        tree_x_scroll.grid(row=1, column=0, sticky="ew")
        self.search_canvas.configure(
            yscrollcommand=tree_y_scroll.set, xscrollcommand=tree_x_scroll.set,
        )
        self.search_canvas.bind("<ButtonPress-1>", self._start_tree_pan)
        self.search_canvas.bind("<B1-Motion>", self._drag_tree_pan)
        self.search_canvas.bind("<Configure>", lambda _event: self._render_search_tree())
        self.search_canvas.bind("<MouseWheel>", self._tree_mousewheel)
        self.search_canvas.bind("<Button-4>", lambda _event: self.zoom_tree(1.15))
        self.search_canvas.bind("<Button-5>", lambda _event: self.zoom_tree(1 / 1.15))
        self._show_tree_placeholder("Run a search to build its tree.")
        tk.Label(
            tree_panel, textvariable=self.tree_detail_var, bg=COLORS["panel"],
            fg=COLORS["text"], font=("Segoe UI", 9), anchor="w", justify="left",
            wraplength=480,
        ).grid(row=2, column=0, sticky="ew", padx=17, pady=(0, 7))
        tree_legend = tk.Label(
            tree_panel, text="Blue: expanded  ·  Orange: solution  ·  Gray: pruned",
            bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9), anchor="w",
        )
        tree_legend.grid(row=3, column=0, sticky="ew", padx=17, pady=(0, 14))

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
        self.route_card = tk.Frame(results, bg=COLORS["panel_light"])
        self.route_card.grid(row=1, column=0, sticky="ew", padx=16, pady=(2, 12))
        tk.Label(
            self.route_card, text="SELECTED ROUTE", bg=COLORS["panel_light"],
            fg=COLORS["muted"], font=("Segoe UI", 8, "bold"), anchor="w",
        ).pack(fill="x", padx=12, pady=(10, 3))
        self.route_label = tk.Label(
            self.route_card, text="Run a search to see the route.", bg=COLORS["panel_light"],
            fg=COLORS["text"], font=("Segoe UI", 10, "bold"), anchor="w", justify="left",
            wraplength=340,
        )
        self.route_label.pack(fill="x", padx=12, pady=(0, 10))

        table_frame = tk.Frame(results, bg=COLORS["panel"])
        table_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 14))
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

    def _tree_header(self, parent):
        header = tk.Frame(parent, bg=COLORS["panel"])
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(13, 7))
        header.grid_columnconfigure(0, weight=1)
        title_block = tk.Frame(header, bg=COLORS["panel"])
        title_block.grid(row=0, column=0, sticky="w")
        tk.Label(
            title_block, text="Search tree", bg=COLORS["panel"], fg=COLORS["text"],
            font=("Segoe UI", 12, "bold"), anchor="w",
        ).pack(fill="x")
        tk.Label(
            title_block, text="Click nodes for details; drag to pan.",
            bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8), anchor="w",
        ).pack(fill="x", pady=(2, 0))
        controls = tk.Frame(header, bg=COLORS["panel"])
        controls.grid(row=0, column=1, sticky="e", padx=(8, 0))
        for label, command in (("−", lambda: self.zoom_tree(1 / 1.2)),
                               ("+", lambda: self.zoom_tree(1.2)),
                               ("Fit", self.fit_tree)):
            tk.Button(
                controls, text=label, command=command, bg=COLORS["panel_light"],
                fg=COLORS["text"], activebackground="#294d78", activeforeground=COLORS["text"],
                relief="flat", bd=0, cursor="hand2", font=("Segoe UI", 9, "bold"),
                padx=9, pady=5,
            ).pack(side="left", padx=(4, 0))

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

    def _show_tree_placeholder(self, text):
        self._tree_trace = None
        self._tree_selected_index = None
        self.tree_detail_var.set("Click a node to inspect its path details.")
        self.search_canvas.delete("all")
        self.search_canvas.configure(scrollregion=(0, 0, 800, 480))
        self.search_canvas.create_text(
            400, 235, text=text, fill=COLORS["muted"],
            font=("Segoe UI", 13), anchor="center",
        )

    def _selection_changed(self, _event=None):
        self._tree_zoom = 1.0
        self._show_tree_placeholder("Run a search to build its tree.")
        self.route_label.configure(text="Run a search to see the route.", fg=COLORS["text"])
        self.status_var.set("Selection changed. Run the search to refresh the tree.")

    def _display_search_tree(self, trace):
        nodes = trace.get("nodes", [])
        if not nodes:
            self._show_tree_placeholder("No search tree is available.")
            return
        self._tree_trace = trace
        self._tree_zoom = 1.0
        self._tree_selected_index = None
        self._tree_route_nodes = set()
        cursor = trace.get("goal_node")
        while cursor is not None and cursor not in self._tree_route_nodes:
            self._tree_route_nodes.add(cursor)
            cursor = nodes[cursor]["parent"]
        self.tree_detail_var.set("Click a node to inspect its path details.")
        self._render_search_tree()

    def _render_search_tree(self):
        trace = self._tree_trace
        if not trace or not trace.get("nodes"):
            return
        nodes = trace["nodes"]
        route_nodes = self._tree_route_nodes
        chosen_by_station = {}
        for index, node in enumerate(nodes):
            station_id = node["station"]
            current = chosen_by_station.get(station_id)
            rank = (0 if index == 0 else 1, 0 if index in route_nodes else 1,
                    node["cost"], index)
            if current is None:
                chosen_by_station[station_id] = index
            else:
                old = nodes[current]
                old_rank = (0 if current == 0 else 1, 0 if current in route_nodes else 1,
                            old["cost"], current)
                if rank < old_rank:
                    chosen_by_station[station_id] = index
        display_indices = sorted(chosen_by_station.values())
        display_set = set(display_indices)
        display_parent = {}
        for index in display_indices:
            ancestor = nodes[index]["parent"]
            while ancestor is not None and (
                ancestor not in display_set
                or nodes[ancestor]["cost"] > nodes[index]["cost"]
            ):
                ancestor = nodes[ancestor]["parent"]
            display_parent[index] = ancestor

        self.search_canvas.delete("all")
        children = {index: [] for index in display_indices}
        for index in display_indices:
            parent_index = display_parent[index]
            if parent_index is not None:
                children[parent_index].append(index)

        leaf_counts = {}
        depths = {}

        def measure(index, depth=0):
            depths[index] = depth
            if not children[index]:
                leaf_counts[index] = 1
            else:
                leaf_counts[index] = sum(measure(child, depth + 1) for child in children[index])
            return leaf_counts[index]

        measure(0)
        leaf_spacing = 108
        level_spacing = 94
        left, top = 38, 44
        base_width = max(1, leaf_counts[0] * leaf_spacing + 2 * left)
        max_depth = max(depths.values()) if depths else 0
        base_height = max(1, top + max_depth * level_spacing + 75)
        viewport_width = max(self.search_canvas.winfo_width(), 380)
        viewport_height = max(self.search_canvas.winfo_height(), 300)
        fit_scale = min(
            1.0, max(0.1, (viewport_width - 24) / base_width),
            max(0.1, (viewport_height - 24) / base_height),
        )
        scale = fit_scale * self._tree_zoom
        content_width = base_width * scale + 24
        content_height = base_height * scale + 24
        offset_x = max(12, (viewport_width - content_width) / 2)
        offset_y = max(12, (viewport_height - content_height) / 2)
        node_radius = max(6, 20 * scale)
        positions = {}
        next_leaf = 0

        def place(index):
            nonlocal next_leaf
            if not children[index]:
                base_x = left + next_leaf * leaf_spacing
                next_leaf += 1
            else:
                child_x = [place(child) for child in children[index]]
                base_x = sum(child_x) / len(child_x)
            x = offset_x + base_x * scale
            y = offset_y + (top + depths[index] * level_spacing) * scale
            positions[index] = (x, y)
            return x

        place(0)

        # Draw branches first so the state circles remain in front of the arrows.
        for index in display_indices:
            parent_index = display_parent[index]
            if parent_index is None:
                continue
            node = nodes[index]
            x1, y1 = positions[parent_index]
            x2, y2 = positions[index]
            radius = node_radius
            dx, dy = x2 - x1, y2 - y1
            length = max((dx * dx + dy * dy) ** 0.5, 1)
            start_x, start_y = x1 + dx * radius / length, y1 + dy * radius / length
            end_x, end_y = x2 - dx * radius / length, y2 - dy * radius / length
            pruned = node["status"].startswith("Pruned")
            branch_color = "#59667a" if pruned else "#8090a7"
            self.search_canvas.create_line(
                start_x, start_y, end_x, end_y, fill=branch_color,
                width=max(1, 1.6 * scale), arrow="last",
                arrowshape=(max(6, 9 * scale), max(7, 11 * scale), max(3, 4 * scale)),
            )
            added_cost = node["cost"] - nodes[parent_index]["cost"]
            label_x, label_y = (x1 + x2) / 2, (y1 + y2) / 2 - max(6, 9 * scale)
            if scale >= 0.4:
                edge_label = "{:g}".format(added_cost)
                if node["parent"] != parent_index:
                    edge_label = "Δg {:g}".format(added_cost)
                self.search_canvas.create_text(
                    label_x, label_y, text=edge_label,
                    fill=COLORS["text"] if not pruned else COLORS["muted"],
                    font=("Segoe UI", max(7, int(9 * scale)), "bold"),
                )

        for index in display_indices:
            node = nodes[index]
            x, y = positions[index]
            station_id = node["station"]
            status = node["status"]
            if index in route_nodes:
                fill, outline, text_color = COLORS["orange"], "#ffe1ad", "#211405"
                status_label = "GOAL" if status == "Goal" else "SOLUTION"
            elif status == "Expanded":
                fill, outline, text_color = "#294d78", COLORS["blue"], COLORS["text"]
                status_label = "EXPANDED"
            elif status in ("Superseded", "Already expanded"):
                fill, outline, text_color = "#303d51", "#78869a", "#aab6c8"
                status_label = "SUPERSEDED" if status == "Superseded" else "DUPLICATE"
            elif status.startswith("Pruned"):
                fill, outline, text_color = "#283346", "#59667a", "#aab6c8"
                status_label = "PRUNED"
            else:
                fill, outline, text_color = COLORS["panel_light"], COLORS["blue"], COLORS["text"]
                status_label = "FRONTIER"

            radius = node_radius
            if index == self._tree_selected_index:
                outline = "#ffffff"
            self.search_canvas.create_oval(
                x - radius, y - radius, x + radius, y + radius,
                fill=fill, outline=outline, width=max(1, 2 * scale),
                tags=("tree_node_{}".format(index),),
            )
            self.search_canvas.create_text(
                x, y, text=station_id, fill=text_color,
                font=("Segoe UI", max(7, int(11 * scale)), "bold"),
                tags=("tree_node_{}".format(index),),
            )
            if scale >= 0.4:
                caption = "g={:g}".format(node["cost"])
                if scale >= 0.8:
                    caption += "  " + status_label
                self.search_canvas.create_text(
                    x, y + radius + max(9, 13 * scale),
                    text=caption,
                    fill=COLORS["muted"] if index not in route_nodes else COLORS["orange"],
                    font=("Segoe UI", max(7, int(8 * scale)), "bold"),
                    tags=("tree_node_{}".format(index),),
                )
            heuristic_value = node.get("heuristic")
            if heuristic_value is not None and scale >= 0.4:
                self.search_canvas.create_text(
                    x, y - radius - max(8, 10 * scale), text="h={:g}".format(heuristic_value),
                    fill=COLORS["red"], font=("Segoe UI", max(7, int(9 * scale)), "bold"),
                    anchor="s", tags=("tree_node_{}".format(index),),
                )
            tag = "tree_node_{}".format(index)
            self.search_canvas.tag_bind(
                tag, "<Button-1>", lambda event, node_index=index: self._select_tree_node(event, node_index),
            )

        self.search_canvas.configure(scrollregion=(0, 0, content_width, content_height))

    def _select_tree_node(self, _event, index):
        if not self._tree_trace:
            return
        self._tree_selected_index = index
        node = self._tree_trace["nodes"][index]
        station_id = node["station"]
        details = "{} — {} | g={} | {}".format(
            station_id, display_name(self.stations, station_id),
            "{:g}".format(node["cost"]), node["status"],
        )
        if node.get("heuristic") is not None:
            details += " | h={:g}".format(node["heuristic"])
        self.tree_detail_var.set(details)
        self._render_search_tree()

    def zoom_tree(self, factor):
        if not self._tree_trace:
            return
        self._tree_zoom = min(3.5, max(0.65, self._tree_zoom * factor))
        self._render_search_tree()

    def fit_tree(self):
        self._tree_zoom = 1.0
        self._render_search_tree()

    def _tree_mousewheel(self, event):
        self.zoom_tree(1.12 if event.delta > 0 else 1 / 1.12)

    def _start_tree_pan(self, event):
        self.search_canvas.scan_mark(event.x, event.y)

    def _drag_tree_pan(self, event):
        self.search_canvas.scan_dragto(event.x, event.y, gain=1)

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
        ucs_trace = {"nodes": [], "goal_node": None}
        astar_trace = {"nodes": [], "goal_node": None}
        if method in ("Compare UCS and A*", "Uniform Cost Search (UCS)"):
            ucs_result = uniform_cost_search(self.graph, start, goal, trace=ucs_trace)
        if method in ("Compare UCS and A*", "A* Search"):
            astar_result = a_star_search(self.graph, self.stations, start, goal, trace=astar_trace)

        self.results_table.delete(*self.results_table.get_children())
        rows = []
        for label, key in (
            ("Status", "status"), ("Total cost", "cost"),
            ("Expanded nodes", "expanded_nodes"), ("Generated nodes", "generated_nodes"),
            ("Path length", "path_length"), ("Runtime (ms)", "execution_time_ms"),
        ):
            left = self._format_metric(key, ucs_result) if ucs_result else "—"
            right = self._format_metric(key, astar_result) if astar_result else "—"
            rows.append((label, left, right))
        for row in rows:
            self.results_table.insert("", "end", values=row)

        chosen = astar_result if method == "A* Search" else ucs_result
        if method == "Compare UCS and A*":
            chosen = astar_result or ucs_result
        selected_trace = astar_trace if method == "A* Search" else ucs_trace
        if method == "Compare UCS and A*":
            selected_trace = astar_trace
        self._display_search_tree(selected_trace)
        if chosen and chosen["status"] == "Success":
            self.route_label.configure(text=format_route(chosen["route"], self.stations), fg=COLORS["text"])
            self.status_var.set("Search tree built. The optimal route is highlighted in orange.")
        else:
            self.route_label.configure(text="No route is available between these stations.", fg=COLORS["orange"])
            self.status_var.set("Search completed. No route was found; the explored tree is shown.")

        if method == "Compare UCS and A*" and ucs_result and astar_result:
            if ucs_result["status"] == astar_result["status"] == "Success":
                self.status_var.set(
                    "Both found a route. Same optimal cost: {}. Tree shown: A*.".format(
                        abs(ucs_result["cost"] - astar_result["cost"]) < 1e-9
                    )
                )

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
        self.route_label.configure(text="Run a search to see the route.", fg=COLORS["text"])
        self.results_table.delete(*self.results_table.get_children())
        self.results_table.insert("", "end", values=("Status", "—", "—"))
        self.status_var.set("Choose two stations, then run a search.")
        self._show_tree_placeholder("Run a search to build its tree.")


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
