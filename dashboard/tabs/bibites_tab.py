from dash import dcc, html, Output, Input, State
import pandas as pd
import os
import json
import colorsys
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
from utils import load_species_data, get_simulations_base_folder, getNodeType


def get_bibites_tab_content(sim_selected, n_intervals, simulations_base_folder):
    """
   Generates the content for the Bibites tab

    Parameters:
    - sim_selected (str): The currently selected simulation.
    - n_intervals (int): A timer-based interval input (not directly used in layout).
    - simulations_base_folder (str): The root directory containing simulation data.

    Returns:
    - html.Div: A Dash HTML layout containing dropdowns, graphs, and analysis sections.
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
                    html.Div(
                        style={
                            "flex": "1", 
                            "display": "flex", 
                            "flexDirection": "column", 
                            "gap": "5px"
                        },
                        children = [
                            html.H6("Select Output Node to filter graph: ", style={"flex": "1", "textAlign":"left", "verticalAlign":"middle", "margin":0}),
                            html.Div(output_node_dropdown, style={"marginBottom": "20px", "flex": "4"}),  # Output node filter
                        ]
                    ),
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
    Generates a visual representation of a neural network using Plotly.

    This function constructs a directed acyclic graph (DAG) representing the neural 
    network of a selected bibite species. It:
    - Categorizes nodes as input, hidden, or output neurons.
    - Positions nodes in a layered layout to improve readability.
    - Creates edges (synapses) with colors and thickness based on synapse weights.
    - Includes interactive tooltips to display synapse weights.

    The function also detects and removes cycles if any exist, ensuring the network
    remains a valid DAG.

    Parameters:
    - nodes (list of dict): A list of neuron nodes, each containing:
        - "Index" (int): Unique identifier for the node.
        - "Type" (int): Indicates if the node is input, hidden, or output.
        - "Desc" (str): Description of the node.
    - synapses (list of dict): A list of synaptic connections, each containing:
        - "NodeIn" (int): Source node index.
        - "NodeOut" (int): Target node index.
        - "Weight" (float): Strength of the synapse.
    - tooltip_points (int, optional): Number of evenly spaced invisible points along 
      each synapse to enable hover tooltips. Default is 3.

    Returns:
    - go.Figure: A Plotly figure displaying the neural network graph with nodes and 
      weighted edges.
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
    
    # Create directed graph and add nodes
    G = nx.DiGraph()
    input_nodes, hidden_nodes, output_nodes = [], [], []
    connected_inputs = set()
    
    # Add synapses (edges) and track connected input nodes
    for synapse in synapses:
        if synapse["En"] == True:
            G.add_edge(synapse["NodeIn"], synapse["NodeOut"], weight=synapse["Weight"])
            connected_inputs.add(synapse["NodeIn"])
    
    for node in nodes:
        if node["Type"] == 0 and node["Index"] not in connected_inputs:
            continue  # Skip unconnected input nodes
        
        G.add_node(node["Index"], desc=node["Desc"], activation=node.get("baseActivation", "N/A"), type = node["Type"])
        if node["Type"] == 0:
            input_nodes.append(node["Index"])
        elif "Hidden" in node["Desc"]:
            hidden_nodes.append(node["Index"])
        else:
            output_nodes.append(node["Index"])
    
    # Assign x-coordinates based on type and space hidden nodes
    positions = {}
    vertical_spacing = 5  # Increase this value to space out nodes more
    hidden_x_min, hidden_x_max = -1, 1  # Ensure hidden nodes stay between input and output
    
    def evenly_space(nodes, x_coord):
        count = len(nodes)
        return {node: (x_coord, vertical_spacing * (i - count / 2)) for i, node in enumerate(sorted(nodes))}
    
    positions.update(evenly_space(input_nodes, -2))
    positions.update(evenly_space(output_nodes, 2))
    
    # Apply force-directed layout for hidden nodes while keeping them within bounds
    if hidden_nodes:
        pos_spring = nx.spring_layout(G, seed=42, k=0.3)  # Force-directed placement
        for node in hidden_nodes:
            x, y = pos_spring[node]
            x = max(hidden_x_min, min(hidden_x_max, x))  # Ensure x stays between input and output
            y *= vertical_spacing * 5  # Scale y spacing for better clarity
            positions[node] = (x, y)
    
    node_x, node_y, node_labels, node_hovertexts, node_colors = [], [], [], [], []
    for node_id, (x, y) in positions.items():
        node_x.append(x)
        node_y.append(y)
        #print(G.nodes[node_id]["type"])
        node_labels.append(getNodeType(str(G.nodes[node_id]["type"])) if node_id in hidden_nodes else G.nodes[node_id]["desc"])
        node_hovertexts.append(f"Name: {G.nodes[node_id]['desc']}<br>Type: {getNodeType(str(G.nodes[node_id]['type']))}<br>Activation: {G.nodes[node_id]['activation']}")
        node_colors.append("cyan" if node_id in input_nodes else "orange" if node_id in hidden_nodes else "blue")
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        marker=dict(size=15, color=node_colors),
        text=node_labels,
        hovertext=node_hovertexts,
        textposition="top center",
        hoverinfo="text"
    )
    
    edge_traces = []
    tooltip_x, tooltip_y, tooltip_text = [], [], []
    arrow_size = 0.02  # Adjust arrowhead size
    for edge in G.edges:
        x0, y0 = positions[edge[0]]
        x1, y1 = positions[edge[1]]
        weight = G[edge[0]][edge[1]]["weight"]
        edge_color = weight_to_scaled_color(weight)
        
        edge_traces.append(
            go.Scatter(
                x=[x0, (x0 + x1) / 2, x1],
                y=[y0, (y0 + y1) / 2, y1],
                mode="lines+markers",
                line=dict(width=min(0.5 + 3.5 * abs(weight), 5), color=edge_color),
                marker=dict(size=min(2+6*abs(weight),15), symbol="arrow-bar-up", angleref= "previous", color=edge_color),
                hoverinfo="none"
            )
        )
        
        for i in range(1, tooltip_points + 1):
            tooltip_x.append(x0 + (x1 - x0) * (i / (tooltip_points + 1)))
            tooltip_y.append(y0 + (y1 - y0) * (i / (tooltip_points + 1)))
            tooltip_text.append(f'{getNodeType(str(G.nodes[edge[0]]["type"])) if edge[0] in hidden_nodes else G.nodes[edge[0]]["desc"]} → {getNodeType(str(G.nodes[edge[1]]["type"])) if edge[1] in hidden_nodes else G.nodes[edge[1]]["desc"]}<br>Weight: {weight:.2f}')
    
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
            height=max(600, len(input_nodes) * 50 + 100),  # Adjust height based on input nodes
            xaxis_visible=False,
            yaxis_visible=False,
            margin=dict(l=50, r=50, t=50, b=50),
        )
    )

    return fig


def create_gene_bar_chart(gene_data):
    """
    Generates a bar chart and a pie chart to visualize gene expression in a species.

    This function creates:
    - A horizontal bar chart displaying the values of all genes.
    - A pie chart specifically for "WAG" genes, which represent key biological traits.

    The function ensures:
    - Gene values are converted to numeric format for accurate visualization.
    - A predefined color mapping is applied to WAG genes for clarity.
    - The layout is optimized for display in a dashboard.

    Parameters:
    - gene_data (dict): A dictionary where keys are gene names (str) and values are 
      gene expression levels (float or convertible to float).

    Returns:
    - tuple (go.Figure, go.Figure): A tuple containing:
        - The first figure (bar chart) showing all gene values.
        - The second figure (pie chart) showing WAG gene distribution. If no WAG genes 
          are present, an empty figure is returned.
    """
    if not gene_data:
        return go.Figure(), go.Figure()

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

    color_colors = {
        "ColorR": "Red",
        "ColorG": "Green",
        "ColorB": "Blue"
        }

    sense_colors = {
        "ViewRadius": "#1f77b4",
        "ViewAngle": "#ff7f0e",
        "PheroSense": "#2ca02c"
    }

    reproduction_colors = {
        "LayTime": "#d62728",
        "BroodTime": "#9467bd",
        "HatchTime": "#8c564b"
    }

    herding_colors = {
        "HerdSeparationWeight": "#e377c2",
        "HerdVelocityWeight": "#17becf",
        "HerdAlignmentWeight": "#7f7f7f",
        "HerdCohesionWeight": "#bcbd22"
        }

    fat_colors = {
        "FatStorageDeadband":"#ff7f0e",
        "FatStorageThreshold":"#e377c2"
        }

    mutation_count_colors = {
        "AverageMutationNumber":"#1f77b4",
        "BrainAverageMutation":"#ff7f0e"
        }

    mutation_sigma_colors = {
        "MutationAmountSigma":"Blue",
        "BrainMutationSigma":"Red"
        }



    # Filter WAG genes
    wag_genes = {gene: round(value, 2) for gene, value in gene_data.items() if gene in wag_colors}
    color_genes = {gene: round(value, 2) for gene, value in gene_data.items() if gene in color_colors}
    sense_genes = {gene: round(value, 2) for gene, value in gene_data.items() if gene in sense_colors}
    reproduction_genes = {gene: round(value, 2) for gene, value in gene_data.items() if gene in reproduction_colors}
    herding_genes = {gene: round(value, 2) for gene, value in gene_data.items() if gene in herding_colors}
    fat_genes = {gene: round(value, 2) for gene, value in gene_data.items() if gene in fat_colors}
    mutation_count_genes = {gene: round(value, 2) for gene, value in gene_data.items() if gene in mutation_count_colors}
    mutation_sigma_genes = {gene: round(value, 2) for gene, value in gene_data.items() if gene in mutation_sigma_colors}
    bar_genes = {gene: round(value, 2) for gene, value in gene_data.items() if (gene not in wag_colors and gene not in color_colors and gene not in sense_colors and gene not in reproduction_colors and gene not in herding_colors and gene != "HerdSeparationDistance" and gene not in fat_colors and gene != "Diet" and gene not in mutation_count_colors  and gene not in mutation_sigma_colors)}

    # Create the bar chart
    bar_chart = go.Figure()
    bar_chart.add_trace(
        go.Bar(
            x=list(bar_genes.values()),
            y=list(bar_genes.keys()),
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
    )

    sense_bar = go.Figure()
    sense_bar.add_trace(
        go.Bar(
            y=list(sense_genes.values()),
            x=list(sense_genes.keys()),
            orientation="v",
            marker=dict(color=[sense_colors[gene] for gene in sense_colors.keys()]),
        )
    )
    sense_bar.update_layout(
        title="Sense Genes",
        xaxis_title="Gene Value",
        yaxis_title="Gene Name",
        template="plotly_dark",
        margin=dict(l=100, r=20, t=40, b=40),
    )

    if wag_genes:
        # Create the pie chart
        wag_pie = go.Figure()
        wag_pie.add_trace(
            go.Pie(
                labels=list(wag_genes.keys()),
                values=list(wag_genes.values()),
                textinfo="label+value+percent",
                hole=0.3,
                marker=dict(colors=[wag_colors[gene] for gene in wag_genes.keys()]),
            )
        )
        wag_pie.update_layout(
            title="WAG Gene Distribution",
            template="plotly_dark",
            margin=dict(l=20, r=20, t=40, b=40),
        )
    else:
        pie_chart = go.Figure()

    if color_genes:
        color_pie = go.Figure()
        color_pie.add_trace(
            go.Pie(
                labels=list(color_genes.keys()),
                values=list(color_genes.values()),
                textinfo="label+value",
                hole=0.3,
                marker=dict(colors=[color_colors[gene] for gene in color_genes.keys()]),
            )
        )
        color_pie.update_layout(
            title="Color Distribution",
            template="plotly_dark",
            margin=dict(l=20, r=20, t=40, b=40),
        )
    else:
        color_pie = go.Figure()

    if reproduction_colors:
        reproduction_bar = go.Figure()
        for cat, value in reproduction_genes.items():
            reproduction_bar.add_trace(
                go.Bar(
                    name = cat,
                    x=['Stage'],
                    y=[value],
                    marker = dict(color = reproduction_colors[cat])
                )
            )
    reproduction_bar.update_layout(
        title="Reproduction Genes",
        xaxis_title="",
        yaxis_title="Time",
        barmode= 'stack',
        template="plotly_dark",
        margin=dict(l=100, r=20, t=40, b=40),
    )

    herding_bar = go.Figure()
    herding_bar.add_trace(
        go.Bar(
            y=list(herding_genes.values()),
            x=list(herding_genes.keys()),
            orientation="v",
            marker=dict(color=[herding_colors[gene] for gene in herding_genes.keys()]),
        )
    )
    herding_bar.update_layout(
        title="Herding Genes",
        xaxis_title="Value",
        yaxis_title="Gene Name",
        template="plotly_dark",
        margin=dict(l=100, r=20, t=40, b=40),
    )

    if fat_colors:
        fat_bar = go.Figure()
        fat_bar.add_trace(
            go.Bar(
                name = "Fat to Energy",
                x=['Energy'],
                y=[fat_genes["FatStorageDeadband"]],
                marker = dict(color = fat_colors["FatStorageDeadband"]),
                hovertemplate=f"Energy: {fat_genes['FatStorageDeadband']}"
            )
        )
        fat_bar.add_trace(
            go.Bar(
                name = "No conversion",
                x=['Energy'],
                y=[ fat_genes["FatStorageThreshold"] - fat_genes["FatStorageDeadband"]],
                marker = dict(color = "#7f7f7f"),
                hovertemplate=f"Energy: {fat_genes['FatStorageDeadband']} - {fat_genes['FatStorageThreshold']}"
            )
        )
        fat_bar.add_trace(
            go.Bar(
                name = "Energy to Fat",
                x=['Energy'],
                y=[1 - fat_genes["FatStorageThreshold"]],
                marker = dict(color = "#bcbd22"),
                hovertemplate=f"Energy: {fat_genes['FatStorageThreshold']}"
            )
        )
        fat_bar.update_layout(
            title="Fat Conversion Genes",
            xaxis_title="",
            yaxis_title="Energy Level",
            barmode= 'stack',
            template="plotly_dark",
            margin=dict(l=100, r=20, t=40, b=40),
        )

    if mutation_count_colors:
        mutation_bar = go.Figure()
        mutation_bar = make_subplots(specs=[[{"secondary_y": True}]])
        mutation_bar.add_trace(
            go.Bar(
                name = "Number",
                x=['Brain Mutation'],
                y=[mutation_count_genes["BrainAverageMutation"]],
                marker = dict(color = mutation_count_colors["BrainAverageMutation"]),
            ),
            secondary_y=False
        )
        mutation_bar.add_trace(
            go.Bar(
                name = "Number",
                x=['Average Mutation'],
                y=[mutation_count_genes["AverageMutationNumber"]],
                marker = dict(color = mutation_count_colors["AverageMutationNumber"]),
            ),
            secondary_y=False
        )
        mutation_bar.add_trace(
            go.Scatter(
                name = "Sigma",
                x=['Brain Mutation'],
                y=[mutation_sigma_genes["BrainMutationSigma"]],
                marker = dict(color = mutation_sigma_colors["BrainMutationSigma"]),
            ),
            secondary_y=True
        )
        mutation_bar.add_trace(
            go.Scatter(
                name = "Sigma",
                x=['Average Mutation'],
                y=[mutation_sigma_genes["MutationAmountSigma"]],
                marker = dict(color = mutation_sigma_colors["MutationAmountSigma"]),
            ),
            secondary_y=True
        )
        mutation_bar.update_layout(
            title="Mutation Genes",
            xaxis_title="",
            template="plotly_dark",
            margin=dict(l=100, r=20, t=50, b=20),
        )
        mutation_bar.update_yaxes(title_text = "Mutation Count", secondary_y = False)
        mutation_bar.update_yaxes(title_text = "Mutation Simga", secondary_y = True)
    return bar_chart, wag_pie, color_pie, sense_bar, reproduction_bar, herding_bar, fat_bar, mutation_bar


def get_gene_bar_chart(sim_selected, species_id, simulations_base_folder):
    """
    Retrieves gene data for a selected species and generates corresponding visualizations.

    This function:
    - Loads gene expression data from the simulation files.
    - Generates a bar chart for all gene values.
    - Creates a pie chart specifically for WAG genes.
    - Ensures robust error handling for missing or malformed data.

    Parameters:
    - sim_selected (str): The name of the selected simulation.
    - species_id (int or str): The unique identifier of the selected species.
    - simulations_base_folder (str): The base directory containing simulation data.

    Returns:
    - html.Div: A Dash layout containing:
        - A bar chart visualizing gene values.
        - A pie chart for WAG gene distribution (if applicable).
        - If no data is found, an appropriate message is displayed instead.
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
        bar_chart, wag_pie, color_pie, sense_bar, reproduction_bar, herding_bar, fat_bar, mutation_bar = create_gene_bar_chart(gene_data)

        diet_cat =""
        if gene_data['Diet'] <= .14:
            diet_cat = "Herbivore"
        elif gene_data['Diet'] >= .46:
            diet_cat = "Carnivore"
        else:
            diet_cat = "Omnivore"

        # Return a layout with both graphs side by side
        return html.Div(
            style={"display": "flex", "width": "100%", "gap": "20px"},  # Outer container fills full width
            children=[
                # Left column:
                html.Div(
                    style={
                        "flex": "1", 
                        "display": "flex", 
                        "flexDirection": "column", 
                        "gap": "20px"
                    },
                    children=[
                        html.Div(
                            style={"display": "flex", "gap": "20px"},
                            children = [
                                html.Div(
                                    style={
                                        "flex": "2", 
                                        "display": "flex", 
                                        "flexDirection": "column", 
                                        "gap": "5px"
                                    },
                                    children = [
                                        html.H6(f"HerdSeparationDistance: {round(gene_data['HerdSeparationDistance'],2)}"),
                                        dcc.Graph(
                                            figure=herding_bar,
                                            config={"displayModeBar": False},
                                                style={"flex": "1", "height": 400}
                                        ),
                                    ]
                                ),
                                dcc.Graph(
                                    figure=bar_chart,
                                    config={"displayModeBar": False},
                                        style={"flex": "2", "height": 400}
                                ),
                            ]
                        ),
                        html.Div(
                            style={"display": "flex", "gap": "20px"},
                            children=[
                                dcc.Graph(
                                    figure=sense_bar,
                                    config={"displayModeBar": False},
                                    style={"flex": "2", "height": 400}
                                ),
                                dcc.Graph(
                                    figure=reproduction_bar,
                                    config={"displayModeBar": False},
                                    style={"flex": "1", "height": 400}
                                )
                            ]
                        )
                    ]
                ),
                # Right column:
                html.Div(
                    style={
                        "flex": "1", 
                        "display": "flex", 
                        "flexDirection": "column", 
                        "gap": "20px"
                    },
                    children=[
                        html.Div(
                            style={"display": "flex", "gap": "20px"},
                            children=[
                                dcc.Graph(
                                    figure=wag_pie,
                                    config={"displayModeBar": False},
                                    style={"flex": "2", "height": 400}
                                ),
                                html.Div(
                                    style={
                                        "flex": "1", 
                                        "display": "flex", 
                                        "flexDirection": "column", 
                                        "gap": "5px"
                                    },
                                    children=[
                                        html.H6(f"Diet: {round(gene_data['Diet'],2)} ({diet_cat})"),
                                        dcc.Graph(
                                            figure=fat_bar,
                                            config={"displayModeBar": False},
                                            style={"flex": "4"}
                                        ),
                                    ]
                                ),
                            ]
                        ),
                         html.Div(
                            style={"display": "flex", "gap": "20px"},
                            children=[ 
                                html.Div(
                                    style={
                                        "flex": "2", 
                                        "display": "flex", 
                                        "flexDirection": "column", 
                                        "gap": "5px"
                                    },
                                    children = [
                                        dcc.Graph(
                                            figure=color_pie,
                                            config={"displayModeBar": False},
                                            style={"flex": "5", "height": 400}
                                        ),
                                        html.Div(
                                            style={
                                                'backgroundColor': f'rgb({255*gene_data["ColorR"]}, {255*gene_data["ColorG"]}, {255*gene_data["ColorB"]})',
                                                'display': 'inline-block',
                                                "flex": ".5"
                                            }
                                        ),
                                    ]
                                ),
                                dcc.Graph(
                                    figure=mutation_bar,
                                    config={"displayModeBar": False},
                                    style={"flex": "2", "height": 400}
                                ),
                            ]
                        )
                    ]
                )
            ]
        )

    except Exception as e:
        print(f"Error generating gene bar and pie charts: {e}")
        return html.Div("Error loading gene data.")


def register_bibites_tab_callbacks(app):
    """
    Registers all Dash callbacks for the Bibites tab to enable interactive updates.

    This function ensures:
    - The species dropdown dynamically updates based on the selected simulation.
    - The output node dropdown populates with relevant neural network nodes.
    - The gene bar chart and neural network graph update dynamically when the user 
      selects a species or output node.
    - The displayed graphs and charts are filtered and formatted based on user input.

    Parameters:
    - app (Dash instance): The Dash application where the callbacks are registered.

    Returns:
    - None: This function modifies the Dash app by adding interactive callbacks.
    """
    @app.callback(
        [Output("output-node-dropdown", "options"), 
         Output("output-node-dropdown", "value")],  # Ensure both options & value are updated
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
                    "Weight": clean_value(synapse.get("Weight", 0)),
                    "En": clean_value(synapse["En"])
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


        
