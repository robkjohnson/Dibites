import os
import pandas as pd
import plotly.express as px
from dash import dcc, html, no_update
import dash_bootstrap_components as dbc
from utils import seconds_to_hours, load_species_data, get_simulations_base_folder

def get_sim_tab_content(sim_selected, n_intervals, simulations_base_folder):
    """
    Generates the content for the Simulation tab

    Parameters:
    - sim_selected (str): The name of the selected simulation.
    - n_intervals (int): Number of update intervals (not used directly).
    - simulations_base_folder (str): Base folder containing simulation data.

    Returns:
    - html.Div: A Dash HTML layout containing simulation charts.
    """

    # Ensure a simulation is selected
    if not sim_selected:
        return html.Div("Please select a simulation.")

    # Load species metadata from the selected simulation
    species_df, _ = load_species_data(sim_selected, simulations_base_folder)

    # Load species counts data from the simulation's parquet file
    counts_file = os.path.join(simulations_base_folder, sim_selected, "species_counts.parquet")

    # Check if the species count file exists
    if not os.path.exists(counts_file):
        return html.Div("Simulation data missing.")

    try:
        # Read the species count data into a DataFrame
        counts_df = pd.read_parquet(counts_file)
    except Exception as e:
        print(f"Error loading counts data: {e}")
        return html.Div("Error loading simulation data.")

    # --- Bibites Alive Per Species Chart ---
    try:
        if counts_df.empty:
            bibites_chart = html.Div("No bibites data available.")
        else:
            # Get the latest recorded update time
            latest_update = counts_df["update_time"].max()
            # Filter for the most recent data
            latest_data = counts_df[counts_df["update_time"] == latest_update]
            # Get species IDs that are still alive
            species_alive_ids = latest_data[latest_data["count"] > 0]["speciesID"].unique()
            # Filter the DataFrame to include only those species
            df_line = counts_df[counts_df["speciesID"].isin(species_alive_ids)].sort_values("update_time")
            # Convert time from seconds to hours for better readability
            df_line["hours"] = df_line["update_time"].apply(seconds_to_hours)

            # Create a line chart displaying the population of each species over time
            bibites_chart = dcc.Graph(
                figure=px.line(
                    df_line,
                    x="hours",
                    y="count",
                    color="speciesID",
                    title="Current Alive Per Species Over Simulated Time",
                    markers=True,
                    labels={"hours": "Hours", "count": "Bibites Alive", "speciesID": "Species ID"},
                    template="plotly_dark"
                )
            )
    except Exception as e:
        print(f"Error creating bibites chart: {e}")
        bibites_chart = html.Div("Error creating bibites chart.")

    # --- Unique Species Alive Chart ---
    try:
        # Count the number of unique species alive at each update time
        df_alive = (
            counts_df[counts_df["count"] > 0]
            .groupby("update_time")["speciesID"]
            .nunique()
            .reset_index(name="alive_species")
            .sort_values("update_time")
        )
        # Convert update time to hours
        df_alive["hours"] = df_alive["update_time"].apply(seconds_to_hours)

        # Create a line chart showing the number of unique species alive over time
        fig_alive = px.line(
            df_alive,
            x="hours",
            y="alive_species",
            title="Unique Species Alive Over Simulated Time",
            markers=True,
            labels={"hours": "Hours", "alive_species": "Alive Species"},
            template="plotly_dark"
        )
    except Exception as e:
        print(f"Error creating alive species chart: {e}")
        fig_alive = {}

    # --- Total Bibites Chart ---
    try:
        # Sum the total number of bibites alive at each update time
        df_total = (
            counts_df.groupby("update_time")["count"]
            .sum()
            .reset_index(name="total_bibites")
            .sort_values("update_time")
        )
        # Convert update time to hours
        df_total["hours"] = df_total["update_time"].apply(seconds_to_hours)

        # Create a line chart showing the total bibites alive over time
        fig_total = px.line(
            df_total,
            x="hours",
            y="total_bibites",
            title="Total Bibites Alive Over Simulated Time",
            markers=True,
            labels={"hours": "Hours", "total_bibites": "Total Bibites Alive"},
            template="plotly_dark"
        )
    except Exception as e:
        print(f"Error creating total bibites chart: {e}")
        fig_total = {}

    # Arrange the charts in two columns
    charts = dbc.Row([
        dbc.Col(dcc.Graph(figure=fig_alive), width=6),
        dbc.Col(dcc.Graph(figure=fig_total), width=6)
    ])

    # Return the full simulation tab layout
    return html.Div([
        html.Div(bibites_chart, style={"paddingBottom": "20px"}),  # Main bibites chart
        charts  # Additional charts for species and total count
    ])

def register_sim_tab_callbacks(app):
    """
    Registers callbacks for the Simulation tab.

    Currently, this function is a placeholder and does not register any callbacks.
    """
    pass
