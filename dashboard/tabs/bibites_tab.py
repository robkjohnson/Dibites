from dash import dcc, html, Output, Input
import pandas as pd
import os
import json
import colorsys
import numpy as np
import plotly.graph_objects as go
import networkx as nx
from utils import load_species_data, get_simulations_base_folder


def get_bibites_tab_content(sim_selected, n_intervals, simulations_base_folder):
    """
    Returns the layout for the Bibites tab.
    Uses the helper function `load_species_data` to reduce redundant code and improve efficiency.
    """

    # Load species data and dropdown options
    species_df, species_options = load_species_data(sim_selected, simulations_base_folder)

    # Default to the species with the most alive individuals
    default_species = species_options[0]["value"] if species_options else None

    # Species Dropdown
    dropdown = dcc.Dropdown(
        id="bibites-dropdown",
        options=species_options,
        placeholder="Select Species",
        clearable=False,
        value=default_species,
        style={"backgroundColor": "#343a40", "color": "white"},
    )

    # Dropdown for selecting an output node in the neural network
    output_node_dropdown = dcc.Dropdown(
        id="output-node-dropdown",
        options=[{"label": "Show Full Graph", "value": ""}],  # Default until callback updates
        value="",
        placeholder="Select Output Node (or Show Full Graph)",
        clearable=False,
        style={"backgroundColor": "#343a40", "color": "white"},
    )

    # Containers for displaying different sections
    genes_display = html.Div(id="bibites-genes-display", style={"padding": "20px", "color": "white"})
    nodes_display = html.Div(id="bibites-nodes-display", style={"padding": "20px", "color": "white"})
    synapses_display = html.Div(id="bibites-synapses-display", style={"padding": "20px", "color": "white"})
    network_graph = dcc.Graph(id="bibites-network-graph")

    return html.Div(
        [
            html.H3("Bibites Analysis", style={"textAlign": "center", "color": "white"}),

            # Species Dropdown with Padding
            html.Div(dropdown, style={"marginBottom": "20px"}),

            # Gene Bar Chart & Pie Chart Section (Initially Hidden)
            html.Div(
                id="gene-bar-chart-container",
                children=[
                    html.H4("Gene Analysis", style={"textAlign": "center", "color": "white"}),
                    html.Div(id="gene-bar-chart", style={"display": "none"}),  # Hidden until loaded
                ],
                style={"marginBottom": "40px"},
            ),

            # Neural Network Graph Section (Initially Hidden)
            html.Div(
                id="neural-network-container",
                children=[
                    html.H4("Neural Network Graph", style={"textAlign": "center", "color": "white"}),
                    html.Div(output_node_dropdown, style={"marginBottom": "20px"}),  # Output node filter
                    html.Div(
                        dcc.Graph(id="bibites-network-graph"),
                        id="network-graph-container",
                        style={"display": "none"},  # Hide until loaded
                    ),
                ],
            ),
        ],
        style={"padding": "20px"},
    )



def create_neural_network_graph(nodes, synapses, tooltip_points=3):
    """
    Generates a Plotly graph visualization of the neural network,
    handling cases where synapses exist between the same two nodes in opposite directions.
    Also ensures the graph remains a Directed Acyclic Graph (DAG) and restores tooltips for synapse weights.
    
    Parameters:
    - nodes: List of neuron nodes
    - synapses: List of synapse connections
    - tooltip_points: Number of evenly spaced invisible points along each synapse for displaying tooltips
    """
    def weight_to_scaled_color(weight):
        white = (255, 255, 255)
        green = (0, 255, 0)
        red = (255, 0, 0)
        abs_weight = min(abs(weight), 1)
        if weight > 0:
            color = (
                int(white[0] * (1 - abs_weight) + green[0] * abs_weight),
                int(white[1] * (1 - abs_weight) + green[1] * abs_weight),
                int(white[2] * (1 - abs_weight) + green[2] * abs_weight),
            )
        elif weight < 0:
            color = (
                int(white[0] * (1 - abs_weight) + red[0] * abs_weight),
                int(white[1] * (1 - abs_weight) + red[1] * abs_weight),
                int(white[2] * (1 - abs_weight) + red[2] * abs_weight),
            )
        else:
            color = white
        return f"rgb({color[0]},{color[1]},{color[2]})"

    positions = {}
    input_nodes, hidden_nodes, output_nodes = [], [], []
    active_input_nodes = set()
    for synapse in synapses:
        active_input_nodes.add(synapse["NodeIn"])
    for node in nodes:
        node_id = node["Index"]
        node_type = node["Type"]
        node_desc = node["Desc"]
        if node_type == 0:
            if node_id in active_input_nodes:
                input_nodes.append(node_id)
        elif "Hidden" in node_desc:
            hidden_nodes.append(node_id)
        else:
            output_nodes.append(node_id)

    graph = nx.DiGraph()
    for synapse in synapses:
        graph.add_edge(synapse["NodeIn"], synapse["NodeOut"], weight=synapse["Weight"])
    
    # Detect and break cycles if they exist by removing the edge with the lowest weight
    try:
        cycle = nx.find_cycle(graph, orientation='original')
        min_weight_edge = min(cycle, key=lambda edge: graph[edge[0]][edge[1]]['weight'])
        graph.remove_edge(min_weight_edge[0], min_weight_edge[1])
    except nx.NetworkXNoCycle:
        pass  # No cycles found

    layer_mapping = {}
    for node_id in input_nodes:
        layer_mapping[node_id] = 0
    for node_id in nx.topological_sort(graph):
        if node_id in layer_mapping:
            continue
        preds = list(graph.predecessors(node_id))
        if preds:
            max_parent_layer = max(layer_mapping.get(p, 0) for p in preds)
            current_layer = max_parent_layer + 1
        else:
            current_layer = 0
        layer_mapping[node_id] = current_layer

    if hidden_nodes:
        max_hidden_layer = max(layer_mapping[n] for n in hidden_nodes)
    else:
        max_hidden_layer = 0
    for node_id in output_nodes:
        layer_mapping[node_id] = max_hidden_layer + 1

    unique_layers = sorted(set(layer_mapping.values()))
    layer_to_x = {layer: layer for layer in unique_layers}
    for node_id in layer_mapping:
        positions[node_id] = (layer_to_x[layer_mapping[node_id]], 0)

    layer_nodes = {}
    for node_id, (x, _) in positions.items():
        layer_nodes.setdefault(x, []).append(node_id)
    for x, node_ids in layer_nodes.items():
        count = len(node_ids)
        start_y = -((count - 1))
        for i, node_id in enumerate(sorted(node_ids)):
            positions[node_id] = (x, start_y + i * 2)

    node_x, node_y, node_labels, node_hovertexts, node_colors = [], [], [], [], []
    node_desc_map = {node["Index"]: node["Desc"] for node in nodes}
    node_activation_map = {node["Index"]: node.get("baseActivation", "N/A") for node in nodes}
    
    for node_id, (x, y) in positions.items():
        node_x.append(x)
        node_y.append(y)
        node_labels.append(node_desc_map.get(node_id, ""))
        node_hovertexts.append(f"Activation: {node_activation_map.get(node_id)}")
        
        if node_id in input_nodes:
            node_colors.append("cyan")
        elif node_id in hidden_nodes:
            node_colors.append("orange")
        else:
            node_colors.append("blue")

    node_trace = go.Scatter(
        x=node_x, 
        y=node_y,
        mode="markers+text",
        marker=dict(size=15, color=node_colors),
        text=node_labels,
        hovertext=node_hovertexts,
        textposition="top center",
        hoverinfo="text"
    )

    edge_traces = []
    tooltip_x, tooltip_y, tooltip_text = [], [], []
    for synapse in synapses:
        node_in, node_out, weight = synapse["NodeIn"], synapse["NodeOut"], synapse["Weight"]
        if graph.has_edge(node_in, node_out):
            x0, y0 = positions[node_in]
            x1, y1 = positions[node_out]
            edge_color = weight_to_scaled_color(weight)
            line_width = .25 + 3.75 * abs(weight)
            edge_traces.append(
                go.Scatter(
                    x=[x0, x1],
                    y=[y0, y1],
                    mode="lines",
                    line=dict(width=line_width, color=edge_color),
                    hoverinfo="none"
                )
            )
            for i in range(1, tooltip_points + 1):
                tooltip_x.append(x0 + (x1 - x0) * (i / (tooltip_points + 1)))
                tooltip_y.append(y0 + (y1 - y0) * (i / (tooltip_points + 1)))
                tooltip_text.append(f"{node_desc_map.get(node_in, 'Unknown')} → {node_desc_map.get(node_out, 'Unknown')}<br>Weight: {weight:.2f}")

    tooltip_trace = go.Scatter(
        x=tooltip_x, y=tooltip_y,
        mode="markers",
        marker=dict(size=8, color="rgba(0,0,0,0)"),
        hoverinfo="text",
        text=tooltip_text
    )
    
    fig = go.Figure(
        data=edge_traces + [tooltip_trace, node_trace],
        layout=go.Layout(
            title="Neural Network Visualization",
            template="plotly_dark",
            showlegend=False,
            height=max(500, len(input_nodes) * 60),
            xaxis_visible=False,  # Hides the x-axis
            yaxis_visible=False,  # Hides the y-axis
            xaxis=dict(title="Layers"),
            yaxis=dict(title="Neuron Position")
        )
    )
    return fig



def create_gene_bar_chart(gene_data):
    """
    Creates a horizontal bar chart for all gene values and a pie chart for WAG genes.
    """
    if not gene_data:
        return go.Figure(), go.Figure()

    # Convert gene data into separate lists for plotting
    gene_names = list(gene_data.keys())
    gene_values = list(gene_data.values())

    # Ensure numeric values
    try:
        gene_values = [float(v) for v in gene_values]  # Convert all values to float
    except ValueError as e:
        print(f"Error converting gene values to float: {e}")
        return go.Figure(), go.Figure()

    # Create the bar chart
    bar_chart = go.Figure()
    bar_chart.add_trace(
        go.Bar(
            x=gene_values,
            y=gene_names,
            orientation="h",
            marker=dict(color="blue"),
        )
    )
    bar_chart.update_layout(
        title="Gene Values for Selected Species",
        xaxis_title="Gene Value",
        yaxis_title="Gene Name",
        template="plotly_dark",
        margin=dict(l=100, r=20, t=40, b=40),
        height=500,  # Ensure enough space
    )

    # Define custom color mapping for WAG genes
    wag_colors = {
        "ArmorWAG": "#555555",   # Dark Grey
        "FatWAG": "#FFD700",     # Gold
        "MouthMusclesWAG": "#FF8C00",  # Deep Orange
        "MoveMusclesWAG": "#FFA07A",   # Muted Salmon
        "StomachWAG": "#228B22", # Forest Green
        "ThroatWAG": "#DC143C",  # Crimson
        "WombWAG": "#FF69B4",    # Hot Pink
    }

    # Filter WAG genes
    wag_genes = {gene: value for gene, value in gene_data.items() if gene in wag_colors}

    if wag_genes:
        # Create the pie chart
        pie_chart = go.Figure()
        pie_chart.add_trace(
            go.Pie(
                labels=list(wag_genes.keys()),
                values=list(wag_genes.values()),
                textinfo="label+percent",
                hole=0.3,  # Semi-donut style
                marker=dict(colors=[wag_colors[gene] for gene in wag_genes.keys()]),
            )
        )
        pie_chart.update_layout(
            title="WAG Gene Distribution",
            template="plotly_dark",
            margin=dict(l=20, r=20, t=40, b=40),
        )
    else:
        pie_chart = go.Figure()

    return bar_chart, pie_chart


def get_gene_bar_chart(sim_selected, species_id, simulations_base_folder):
    """
    Retrieves gene data and generates a bar chart for all genes and a pie chart for WAG genes.
    Uses `load_species_data` for optimized file access.
    """
    if not sim_selected or not species_id:
        return html.Div("Please select a species.")

    # Load species data using the helper function
    species_df, _ = load_species_data(sim_selected, simulations_base_folder)

    try:
        # Find the row corresponding to the selected species
        species_row = species_df[species_df["speciesID"] == species_id]

        if species_row.empty:
            return html.Div("No gene data available for the selected species.")

        # Extract genes from JSON
        template = species_row.iloc[0].get("template")
        if isinstance(template, str):
            template = json.loads(template)

        gene_data = template.get("genes", {})

        if not gene_data:
            return html.Div("No genes found for this species.")

        # Generate bar and pie charts
        bar_chart, pie_chart = create_gene_bar_chart(gene_data)

        # Return a layout with both graphs side by side
        return html.Div(
            style={"display": "flex", "gap": "20px"},  # Layout adjustment
            children=[
                dcc.Graph(figure=bar_chart, config={"displayModeBar": False}, style={"flex": "2"}),  # Larger
                dcc.Graph(figure=pie_chart, config={"displayModeBar": False}, style={"flex": "1"}),  # Smaller
            ],
        )

    except Exception as e:
        print(f"Error generating gene bar and pie charts: {e}")
        return html.Div("Error loading gene data.")




def register_bibites_tab_callbacks(app):
    """
    Registers callbacks for the Bibites tab, ensuring:
    - The species dropdown is correctly populated and sorted by most alive first.
    - The default species selection is the one with the most alive individuals.
    - The Gene Bar Chart and Neural Network Graph update dynamically.
    """
    @app.callback(
        [Output("output-node-dropdown", "options"), Output("output-node-dropdown", "value")],  # Ensure both options & value are updated
        [Input("bibites-dropdown", "value"),
         Input("sim-dropdown", "value")]
    )
    def update_output_node_dropdown(selected_species, sim_selected):
        """
        Populate the dropdown with available output nodes from the species' neural network.
        Ensures only valid output nodes are included (Type > 0 and not "Hidden").
        """
        if not sim_selected or not selected_species:
            return [{"label": "Show Full Graph", "value": ""}], ""  # Return options and default selection

        simulations_base_folder = get_simulations_base_folder()
        sim_folder = os.path.join(simulations_base_folder, sim_selected)
        species_file = os.path.join(sim_folder, "species_data.parquet")

        try:
            species_df = pd.read_parquet(species_file)
            species_row = species_df[species_df["speciesID"] == selected_species]

            if species_row.empty:
                print("No species data found.")
                return [{"label": "Show Full Graph", "value": ""}], ""

            # Load template safely (ensure it's a dictionary)
            template = species_row.iloc[0]["template"]
            if isinstance(template, str):
                template = json.loads(template)

            nodes = template.get("nodes", [])
            synapses = template.get("synapses", [])

            #print(f"Retrieved {len(nodes)} nodes and {len(synapses)} synapses.")

            if len(nodes) == 0:
                print("No nodes found in template.")
                return [{"label": "Show Full Graph", "value": ""}], ""

            # Ensure all node properties are standard Python types
            def clean_value(value):
                """ Convert NumPy arrays or lists to standard Python single values. """
                if isinstance(value, np.ndarray):
                    return value.item() if value.size == 1 else value.tolist()
                return value

            # Convert all node properties to standard Python types
            for node in nodes:
                node["Index"] = clean_value(node.get("Index"))
                node["Desc"] = clean_value(node.get("Desc", "Unknown"))
                node["Type"] = clean_value(node.get("Type"))

            # Create a directed graph from synapses
            G = nx.DiGraph()
            for synapse in synapses:
                G.add_edge(clean_value(synapse["NodeIn"]), clean_value(synapse["NodeOut"]))

            # Identify output nodes based on criteria:
            # - Type > 0 (not input)
            # - "Hidden" should NOT be in the description
            output_nodes = [
                node for node in nodes
                if node["Type"] > 0 and "Hidden" not in node["Desc"]
            ]

            # Extract details for the output nodes
            dropdown_options = [
                {"label": f"{node['Index']} - {node['Desc']}", "value": str(node["Index"])}
                for node in output_nodes
            ]

            # Add "Show Full Graph" option at the top and set it as the default
            options = [{"label": "Show Full Graph", "value": ""}] + dropdown_options

            return options, ""  # Default value is "Show Full Graph"

        except Exception as e:
            print(f"Error loading output nodes: {e}")
            return [{"label": "Show Full Graph", "value": ""}], ""




    @ app.callback(
        [Output("bibites-dropdown", "options"), Output("bibites-dropdown", "value")],
        [Input("sim-dropdown", "value")]
    )
    def update_species_dropdown(sim_selected):
        """
        Uses `load_species_data` to update the species dropdown dynamically.
        """
        _, species_options = load_species_data(sim_selected, get_simulations_base_folder())

        default_species = species_options[0]["value"] if species_options else None
        return species_options, default_species

    
    @ app.callback(
        [
            Output("gene-bar-chart", "children"),
            Output("gene-bar-chart", "style"),
            Output("bibites-network-graph", "figure"),
            Output("network-graph-container", "style"),
        ],
        [
            Input("bibites-dropdown", "value"),
            Input("sim-dropdown", "value"),
            Input("output-node-dropdown", "value")  # Capture dropdown selection
        ]
    )
    def update_gene_and_network_graph(selected_species, sim_selected, selected_output_node):
        """
        Updates the Gene Bar Chart and Neural Network Graph dynamically.
        Uses `load_species_data` for efficiency.
        Filters the graph if an output node is selected but ensures standalone output nodes still appear.
        """

        if not sim_selected or not selected_species:
            return html.Div("Please select a species."), {"display": "none"}, go.Figure(), {"display": "none"}

        simulations_base_folder = get_simulations_base_folder()
    
        # Load species data using the helper function
        species_df, _ = load_species_data(sim_selected, simulations_base_folder)

        try:
            # Find the row corresponding to the selected species
            species_row = species_df[species_df["speciesID"] == selected_species]

            if species_row.empty:
                return html.Div("No data available."), {"display": "none"}, go.Figure(), {"display": "none"}

            # Load species template (Ensure it's a dictionary)
            template = species_row.iloc[0]["template"]
            if isinstance(template, str):
                template = json.loads(template)

            nodes = template.get("nodes", [])
            synapses = template.get("synapses", [])

            if len(nodes) == 0:
                return html.Div("No network data available."), {"display": "none"}, go.Figure(), {"display": "none"}

            # Convert node and synapse properties to standard Python types
            def clean_value(value):
                """ Convert NumPy arrays or lists to standard Python single values. """
                if isinstance(value, np.ndarray):
                    return value.item() if value.size == 1 else value.tolist()
                return value

            for node in nodes:
                node["Index"] = clean_value(node.get("Index"))
                node["Desc"] = clean_value(node.get("Desc", "Unknown"))

            cleaned_synapses = [
                {
                    "NodeIn": clean_value(synapse["NodeIn"]),
                    "NodeOut": clean_value(synapse["NodeOut"]),
                    "Weight": clean_value(synapse.get("Weight", 0))
                }
                for synapse in synapses
            ]

            # If "Show Full Graph" is selected, show the full network
            if selected_output_node == "":
                filtered_nodes, filtered_synapses = nodes, cleaned_synapses
            else:
                selected_output_node = int(selected_output_node)

                # Create a directed graph from synapses
                G = nx.DiGraph()
                for synapse in cleaned_synapses:
                    G.add_edge(synapse["NodeIn"], synapse["NodeOut"], weight=synapse["Weight"])

                # Find all nodes leading to the selected output node
                reachable_nodes = set()

                def trace_backwards(node):
                    """ Recursively find all nodes leading to the selected output node. """
                    if node in reachable_nodes:
                        return
                    reachable_nodes.add(node)
                    for src, dest in G.edges:
                        if dest == node:
                            trace_backwards(src)

                trace_backwards(selected_output_node)

                # Ensure standalone output nodes are included
                reachable_nodes.add(selected_output_node)

                # Filter nodes and synapses
                filtered_nodes = [n for n in nodes if n["Index"] in reachable_nodes]
                filtered_synapses = [s for s in cleaned_synapses if s["NodeIn"] in reachable_nodes and s["NodeOut"] in reachable_nodes]

            # Generate the neural network graph
            network_graph = create_neural_network_graph(filtered_nodes, filtered_synapses)

            # Generate the gene bar chart
            gene_chart = get_gene_bar_chart(sim_selected, selected_species, simulations_base_folder)

            return gene_chart, {"display": "block"}, network_graph, {"display": "block"}

        except Exception as e:
            print(f"Error processing species data: {e}")
            return html.Div("Error loading data."), {"display": "none"}, go.Figure(), {"display": "none"}


        
