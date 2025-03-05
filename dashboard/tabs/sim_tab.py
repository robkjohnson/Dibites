from dash import dcc, html, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import os
from utils import seconds_to_hours, load_species_data, get_simulations_base_folder  # Import our helper function

def get_sim_tab_content(sim_selected, n_intervals, simulations_base_folder):
    """
    Returns the layout for the Sim tab.
    Uses `load_species_data` for efficiency.
    Loads `species_counts.parquet` separately for time-series analysis.
    """
    if not sim_selected:
        return html.Div("Please select a simulation.")

    # Load species metadata
    species_df, _ = load_species_data(sim_selected, simulations_base_folder)

    # Load species counts separately
    counts_file = os.path.join(simulations_base_folder, sim_selected, "species_counts.parquet")

    if not os.path.exists(counts_file):
        return html.Div("Simulation data missing.")

    try:
        counts_df = pd.read_parquet(counts_file)
    except Exception as e:
        print(f"Error loading counts data: {e}")
        return html.Div("Error loading simulation data.")

    # --- Bibites Alive Per Species ---
    try:
        if counts_df.empty:
            bibites_chart = html.Div("No bibites data available.")
        else:
            latest_update = counts_df["update_time"].max()
            latest_data = counts_df[counts_df["update_time"] == latest_update]
            species_alive_ids = latest_data[latest_data["count"] > 0]["speciesID"].unique()
            df_line = counts_df[counts_df["speciesID"].isin(species_alive_ids)].sort_values("update_time")
            df_line["hours"] = df_line["update_time"].apply(seconds_to_hours)

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
        df_alive = counts_df[counts_df["count"] > 0]\
            .groupby("update_time")["speciesID"]\
            .nunique()\
            .reset_index(name="alive_species")\
            .sort_values("update_time")
        df_alive["hours"] = df_alive["update_time"].apply(seconds_to_hours)

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
        df_total = counts_df.groupby("update_time")["count"]\
            .sum()\
            .reset_index(name="total_bibites")\
            .sort_values("update_time")
        df_total["hours"] = df_total["update_time"].apply(seconds_to_hours)

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

    charts = dbc.Row([
        dbc.Col(dcc.Graph(figure=fig_alive), width=6),
        dbc.Col(dcc.Graph(figure=fig_total), width=6)
    ])

    return html.Div([
        html.Div(bibites_chart, style={"paddingBottom": "20px"}),
        charts
    ])

def register_sim_tab_callbacks(app):
    # Additional sim-tab-specific callbacks can be registered here if needed.
    pass
