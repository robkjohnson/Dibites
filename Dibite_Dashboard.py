import os
import json
import dash
from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# Load configuration from config.json for base folder and update frequency
config_file = "config.json"
try:
    with open(config_file, "r") as f:
        config = json.load(f)
    folder_path = config.get("Path_To_Autosave_Folder")
    if not folder_path:
        raise ValueError("Path_To_Autosave_Folder not found in config.json")
    update_frequency = config.get("UpdateFrequency", 600)
except Exception as e:
    raise Exception(f"Error loading config.json: {e}")

# Define the base simulation folder
simulations_base_folder = os.path.join(folder_path, "Dibite_Simulation_Data")

# Get a list of simulation options from subfolders
if os.path.exists(simulations_base_folder):
    sim_options = [
        {'label': sim, 'value': sim}
        for sim in os.listdir(simulations_base_folder)
        if os.path.isdir(os.path.join(simulations_base_folder, sim))
    ]
else:
    sim_options = []

# Default simulation selection: first available
default_sim = sim_options[0]['value'] if sim_options else None

# Initialize the Dash app with Bootstrap styling
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    # Header
    html.Div(
        html.H1("Dibites", style={
            'backgroundColor': 'lightblue',
            'padding': '20px',
            'margin': '0',
            'textAlign': 'center'
        }),
        style={'width': '100%'}
    ),
    # Row containing simulation dropdown and metric texts
    dbc.Row([
        dbc.Col(
            html.Div([
                html.Label("Select Simulation:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id="sim-dropdown",
                    options=sim_options,
                    placeholder="Choose a Simulation",
                    clearable=False,
                    value=default_sim
                )
            ]),
            width=6
        ),
        dbc.Col(
            html.Div([
                html.H3(id="total-species", style={'textAlign': 'center'}),
                html.H3(id="alive-species", style={'textAlign': 'center'})
            ]),
            width=6
        )
    ], style={'padding': '20px', 'maxWidth': '1000px', 'margin': 'auto'}),
    # Auto-refresh interval
    dcc.Interval(
        id="interval-component",
        interval=update_frequency * 1000,  # in milliseconds
        n_intervals=0
    ),
    # Tabs for different views
    dcc.Tabs(
        id="tabs",
        value="sim",  # default tab
        children=[
            dcc.Tab(label="Sim", value="sim"),
            dcc.Tab(label="Bibites", value="bibites")
        ]
    ),
    # Content area for tab-specific charts
    html.Div(id="tab-content", style={'padding': '20px'})
])

# Callback to update the metric texts (always visible)
@app.callback(
    [Output("total-species", "children"),
     Output("alive-species", "children")],
    [Input("sim-dropdown", "value"),
     Input("interval-component", "n_intervals")]
)
def update_text_data(sim_selected, n_intervals):
    if not sim_selected:
        return "Total Species Seen: N/A", "Alive Species: N/A"
    
    sim_folder = os.path.join(simulations_base_folder, sim_selected)
    species_file = os.path.join(sim_folder, "species_data.parquet")
    counts_file = os.path.join(sim_folder, "species_counts.parquet")
    
    try:
        species_df = pd.read_parquet(species_file)
        total_species = species_df.shape[0]
    except Exception as e:
        print(f"Error loading species data: {e}")
        total_species = 0

    try:
        counts_df = pd.read_parquet(counts_file)
        if counts_df.empty:
            alive_species = 0
        else:
            # Using the raw simulatedTime values as stored
            max_update = counts_df['update_time'].max()
            latest = counts_df[counts_df['update_time'] == max_update]
            alive_species = (latest['count'] > 0).sum()
    except Exception as e:
        print(f"Error loading species counts: {e}")
        alive_species = 0

    return f"Total Species Seen: {total_species}", f"Alive Species: {alive_species}"

# Callback to update the tab content (charts)
@app.callback(
    Output("tab-content", "children"),
    [Input("tabs", "value"),
     Input("sim-dropdown", "value"),
     Input("interval-component", "n_intervals")]
)
def render_tab_content(selected_tab, sim_selected, n_intervals):
    if not sim_selected:
        return html.Div("Please select a simulation.")
    
    sim_folder = os.path.join(simulations_base_folder, sim_selected)
    counts_file = os.path.join(sim_folder, "species_counts.parquet")
    
    try:
        counts_df = pd.read_parquet(counts_file)
    except Exception as e:
        print(f"Error loading counts data: {e}")
        counts_df = pd.DataFrame()
    
    if selected_tab == "sim":
        # "Sim" tab content: overall simulation details (as before)
        try:
            df_alive = counts_df[counts_df['count'] > 0]\
                        .groupby('update_time')['speciesID']\
                        .nunique()\
                        .reset_index(name='alive_species')\
                        .sort_values('update_time')
            fig_alive = px.line(
                df_alive,
                x='update_time',
                y='alive_species',
                title="Alive Species Over Simulated Time",
                markers=True,
                labels={'update_time': 'Simulated Time', 'alive_species': 'Alive Species'}
            )
        except Exception as e:
            print(f"Error creating alive species chart: {e}")
            fig_alive = {}
        
        try:
            df_total = counts_df.groupby("update_time")["count"]\
                        .sum()\
                        .reset_index(name="total_bibites")\
                        .sort_values("update_time")
            fig_total = px.line(
                df_total,
                x="update_time",
                y="total_bibites",
                title="Total Bibites Alive Over Simulated Time",
                markers=True,
                labels={"update_time": "Simulated Time", "total_bibites": "Total Bibites Alive"}
            )
        except Exception as e:
            print(f"Error creating total bibites chart: {e}")
            fig_total = {}
        
        charts = dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_alive), width=6),
            dbc.Col(dcc.Graph(figure=fig_total), width=6)
        ])
        return charts
    
    elif selected_tab == "bibites":
        # "Bibites" tab: Line graph with a separate line for each species that are alive in the last update
        try:
            # Ensure there is data
            if counts_df.empty:
                return html.Div("No bibites data available.")
            # Determine the latest update time
            latest_update = counts_df['update_time'].max()
            latest_data = counts_df[counts_df['update_time'] == latest_update]
            # Get the speciesIDs that are alive (count > 0) at the latest update
            species_alive_ids = latest_data[latest_data['count'] > 0]['speciesID'].unique()
            # Filter counts_df to include only these species
            df_line = counts_df[counts_df['speciesID'].isin(species_alive_ids)].sort_values("update_time")
            
            fig_bibites = px.line(
                df_line,
                x="update_time",
                y="count",
                color="speciesID",
                title="Bibites Alive Over Simulated Time by Species (Alive at Latest Update)",
                markers=True,
                labels={"update_time": "Simulated Time", "count": "Bibites Alive", "speciesID": "Species ID"}
            )
        except Exception as e:
            print(f"Error creating bibites line chart: {e}")
            fig_bibites = {}
        return html.Div([
            html.H3("Bibites Analysis", style={'textAlign': 'center'}),
            dcc.Graph(figure=fig_bibites)
        ])
    else:
        return html.Div("Unknown tab selected.")



if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
