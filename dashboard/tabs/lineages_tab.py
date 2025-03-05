from dash import dcc, html, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import os
import json
import plotly.express as px
import dash_bootstrap_components as dbc
from utils import seconds_to_hours, load_species_data, get_simulations_base_folder  # Import helper function

def get_lineages_tab_content(sim_selected, n_intervals, simulations_base_folder):
    """
    Returns the layout for the Lineages tab, including lineage tracing, lineage population, 
    and gene evolution graphs, with an option to ignore the root species.
    Uses `load_species_data` for efficiency.
    """
    species_df, species_options = load_species_data(sim_selected, simulations_base_folder)

    # Default to the species with the most alive individuals
    default_species = species_options[0]["value"] if species_options else None

    # Dropdown to select a species
    dropdown = dcc.Dropdown(
        id="lineages-dropdown",
        options=species_options,
        placeholder="Select Species",
        clearable=False,
        value=default_species,
        style={"backgroundColor": "#343a40", "color": "white"},
    )

    # Checkbox to ignore root species
    ignore_root_checkbox = dcc.Checklist(
        id="ignore-root-checkbox",
        options=[{"label": " Ignore Root Species", "value": "ignore"}],
        value=[],  # Default: do not ignore
        inline=True,
        style={"color": "white", "padding": "10px"}
    )

    # Lineage and gene evolution graphs
    lineage_display = html.Div(id="lineages-display", style={"padding": "20px", "color": "white"})
    lineage_population_graph = html.Div(id="lineage-population-graph", style={"padding": "20px"})
    
    # Two-column layout for grouped gene graphs
    gene_graphs = dbc.Row([
        dbc.Col(html.Div(id="grouped-genes-graph"), width=6),
        dbc.Col(html.Div(id="non-combined-genes-graph"), width=6)
    ], style={"padding": "20px"})

    return html.Div(
        [
            html.H3("Lineages Analysis", style={"textAlign": "center", "color": "white"}),
            dropdown,
            html.Div([ignore_root_checkbox], style={"padding": "10px"}),  # Add checkbox below dropdown
            lineage_display,
            lineage_population_graph,  # Lineage population graph
            gene_graphs,  # Two-column gene evolution graphs
        ],
        style={"padding": "20px"},
    )



def register_lineages_tab_callbacks(app):
    @ app.callback(
        [
            Output("lineages-display", "children"),
            Output("lineage-population-graph", "children"),
            Output("grouped-genes-graph", "children"),
            Output("non-combined-genes-graph", "children"),
        ],
        [
            Input("lineages-dropdown", "value"),
            Input("sim-dropdown", "value"),
            Input("ignore-root-checkbox", "value"),
        ],
    )
    def update_lineage_and_graphs(selected_species, sim_selected, ignore_root_checkbox):
        """
        Updates lineage tracking, population graphs, and gene evolution graphs.
        Uses `load_species_data` for efficiency.
        Loads `species_counts.parquet` manually for population tracking.
        """
        if not sim_selected or not selected_species:
            return "Please select a species.", html.Div(), html.Div(), html.Div()

        simulations_base_folder = get_simulations_base_folder()
        species_df, _ = load_species_data(sim_selected, simulations_base_folder)

        # Load species counts separately
        counts_file = f"{simulations_base_folder}/{sim_selected}/species_counts.parquet"
        if not os.path.exists(counts_file):
            return "Population data missing.", html.Div(), html.Div(), html.Div()

        try:
            counts_df = pd.read_parquet(counts_file)

            if "speciesID" not in counts_df.columns or "update_time" not in counts_df.columns:
                return "Invalid species counts data.", html.Div(), html.Div(), html.Div()

            # Find lineage
            lineage_species_ids = []
            current_species = selected_species
            while current_species in species_df["speciesID"].values:
                row = species_df[species_df["speciesID"] == current_species].iloc[0]
                lineage_species_ids.append(current_species)
                if pd.isna(row["parentID"]):
                    break
                current_species = row["parentID"]

            # Handle root exclusion
            if "ignore" in (ignore_root_checkbox or []) and len(lineage_species_ids) > 1:
                lineage_species_ids = lineage_species_ids[:-1]  

            # Display lineage
            lineage_text = " → ".join(map(str, lineage_species_ids))
            lineage_display = html.Div([html.P(f"Lineage: {lineage_text}")])

            # Lineage Population Graph
            df_lineage = counts_df[counts_df["speciesID"].isin(lineage_species_ids)].copy()
            df_lineage["hours"] = df_lineage["update_time"].apply(seconds_to_hours)

            if not df_lineage.empty:
                lineage_population_graph = dcc.Graph(
                    figure=px.line(
                        df_lineage,
                        x="hours",
                        y="count",
                        color="speciesID",
                        title="Lineage Population Over Simulated Time",
                        markers=True,
                        labels={"hours": "Simulated Time (Hours)", "count": "Population", "speciesID": "Species"},
                        template="plotly_dark"
                    )
                )
            else:
                lineage_population_graph = html.Div("No lineage population data available.")

            # Extract gene data
            gene_data = {}
            for species_id in lineage_species_ids:
                species_row = species_df[species_df["speciesID"] == species_id]
                if not species_row.empty and "template" in species_row.columns:
                    template = species_row.iloc[0]["template"]
                    if isinstance(template, str):
                        try:
                            template = json.loads(template)
                        except json.JSONDecodeError:
                            template = {}

                    if isinstance(template, dict) and "genes" in template:
                        for gene, value in template["genes"].items():
                            if gene not in gene_data:
                                gene_data[gene] = []
                            gene_data[gene].append(value)

            # Define WAG colors (same as bibites_tab.py)
            wag_colors = {
                "ArmorWAG": "#555555",   # Dark Grey
                "FatWAG": "#FFD700",     # Gold
                "MouthMusclesWAG": "#FF8C00",  # Deep Orange
                "MoveMusclesWAG": "#FFA07A",   # Muted Salmon
                "StomachWAG": "#228B22", # Forest Green
                "ThroatWAG": "#DC143C",  # Crimson
                "WombWAG": "#FF69B4",    # Hot Pink
            }

            # Gene Evolution Graphs
            def create_graph(title, genes, color_map=None):
                if not gene_data:
                    return html.Div(f"No data available for {title}")

                df = pd.DataFrame({gene: gene_data.get(gene, []) for gene in genes})
                df.index = range(len(df))

                if df.empty or df.shape[0] == 1:
                    return html.Div(f"No valid data for {title}")

                df["SpeciesID"] = lineage_species_ids[:len(df)]
            
                # Apply custom color mapping if provided
                if color_map:
                    fig = px.line(df, x="SpeciesID", y=df.columns[:-1], title=title, markers=True, template="plotly_dark",
                                  color_discrete_map=color_map)
                else:
                    fig = px.line(df, x="SpeciesID", y=df.columns[:-1], title=title, markers=True, template="plotly_dark")

                return dcc.Graph(figure=fig)

            # Organized Gene Graphs
            grouped_gene_graphs = [
                create_graph("Color Evolution", ["ColorR", "ColorG", "ColorB"]),
                create_graph("Incubation Time Evolution", ["LayTime", "HatchTime", "BroodTime"]),
                create_graph("WAG Evolution", ["ArmorWAG", "FatWAG", "MouthMusclesWAG", "MoveMusclesWAG", "StomachWAG", "ThroatWAG", "WombWAG"], wag_colors),
                create_graph("Fat Conversion Evolution", ["FatStorageDeadband", "FatStorageThreshold"]),
                create_graph("Herd Weights Evolution", ["HerdSeparationWeight", "HerdVelocityWeight", "HerdAlignmentWeight", "HerdCohesionWeight"]),
                create_graph("Vision Evolution", ["ViewAngle", "ViewRadius"]),
                create_graph("Mutation Count Evolution", ["AverageMutationNumber", "BrainAverageMutation"]),
                create_graph("Mutation Sigma Evolution", ["MutationAmountSigma", "BrainMutationSigma"]),
                create_graph("Diet Evolution", ["Diet"]),
                create_graph("Size Evolution", ["SizeRatio"]),
                create_graph("Speed Evolution", ["SpeedRatio"]),
                create_graph("PheroSense Evolution", ["PheroSense"]),
            ]

            # Split into two columns
            graphs_left = grouped_gene_graphs[:len(grouped_gene_graphs)//2]
            graphs_right = grouped_gene_graphs[len(grouped_gene_graphs)//2:]

            return (
                lineage_display,
                lineage_population_graph,
                html.Div(graphs_left) if graphs_left else html.Div("No grouped genes available."),
                html.Div(graphs_right) if graphs_right else html.Div("No non-combined genes available.")
            )

        except Exception as e:
            print(f"Error updating lineage and graphs: {e}")
            return "Error retrieving lineage data.", html.Div(), html.Div(), html.Div()