from dash import Input, Output, dcc, html
import pandas as pd
import os
from utils import get_simulations_base_folder, get_update_frequency
from tabs.sim_tab import get_sim_tab_content, register_sim_tab_callbacks
from tabs.bibites_tab import get_bibites_tab_content, register_bibites_tab_callbacks
from tabs.lineages_tab import get_lineages_tab_content, register_lineages_tab_callbacks

simulations_base_folder = get_simulations_base_folder()

def register_callbacks(app):
    ### **Dynamically Populate `sim-dropdown` with Available Simulations & Default to First** ###
    @app.callback(
        [Output("sim-dropdown", "options"),
         Output("sim-dropdown", "value")],  # Ensures first available simulation is selected
        Input("main-tabs", "value")  # Trigger update when tabs change
    )
    def update_simulation_dropdown(_):
        base_folder = get_simulations_base_folder()
        try:
            simulations = [
                {'label': sim, 'value': sim} 
                for sim in os.listdir(base_folder) 
                if os.path.isdir(os.path.join(base_folder, sim))
            ]
            default_sim = simulations[0]['value'] if simulations else None  # Select first available sim
            return simulations, default_sim
        except Exception as e:
            print(f"Error loading simulations: {e}")
            return [], None

    ### **Show Sub-Tabs Only When "Bibite Analysis" is Selected** ###
    @app.callback(
        Output("bibite-analysis-tabs-container", "style"),
        Input("main-tabs", "value")
    )
    def show_bibite_analysis_subtabs(selected_tab):
        """ Show sub-tabs only when 'Bibite Analysis' is selected """
        return {'display': 'block'} if selected_tab == "bibite-analysis" else {'display': 'none'}

    ### **Update Graph Data Without Refreshing the Page** ###
    @app.callback(
        Output("tab-content", "children"),
        [Input("main-tabs", "value"),
         Input("bibite-tabs", "value"),
         Input("sim-dropdown", "value"),
         Input("interval-component", "n_intervals")]  # Use interval for live updates
    )
    def update_graph_data(selected_main_tab, selected_sub_tab, sim_selected, n_intervals):
        """ Update only the graph data without refreshing the entire layout """
        if not sim_selected:
            return html.Div("Please select a simulation.")

        if selected_main_tab == "sim":
            return get_sim_tab_content(sim_selected, n_intervals, simulations_base_folder)  # Update Sim graphs
        
        elif selected_main_tab == "bibite-analysis":
            if selected_sub_tab == "bibites":
                return get_bibites_tab_content(sim_selected, n_intervals, simulations_base_folder)  # Update Bibites graphs
            elif selected_sub_tab == "lineages":
                return get_lineages_tab_content(sim_selected, n_intervals, simulations_base_folder)  # Update Lineages graphs
            else:
                return html.Div("Select a sub-tab.")

        return html.Div("Unknown tab selected.")

    ### **Live Data Updates for Total & Alive Species Counts Without Refresh** ###
    @app.callback(
        Output("total-species", "children"),
        [Input("sim-dropdown", "value"),
         Input("interval-component", "n_intervals")]
    )
    def update_total_species(sim_selected, n_intervals):
        if not sim_selected:
            return "Total Species Seen: N/A"
        sim_folder = os.path.join(simulations_base_folder, sim_selected)
        species_file = os.path.join(sim_folder, "species_data.parquet")
        try:
            species_df = pd.read_parquet(species_file)
            return f"Total Species Seen: {species_df.shape[0]}"
        except Exception as e:
            print(f"Error loading species data: {e}")
            return "Total Species Seen: 0"

    @app.callback(
        Output("alive-species", "children"),
        [Input("sim-dropdown", "value"),
         Input("interval-component", "n_intervals")]
    )
    def update_alive_species(sim_selected, n_intervals):
        if not sim_selected:
            return "Alive Species: N/A"
        sim_folder = os.path.join(simulations_base_folder, sim_selected)
        counts_file = os.path.join(sim_folder, "species_counts.parquet")
        try:
            counts_df = pd.read_parquet(counts_file)
            if counts_df.empty:
                return "Alive Species: 0"
            max_update = counts_df['update_time'].max()
            latest = counts_df[counts_df['update_time'] == max_update]
            alive_species = (latest['count'] > 0).sum()
            return f"Alive Species: {alive_species}"
        except Exception as e:
            print(f"Error loading species counts: {e}")
            return "Alive Species: 0"

    # Register additional tab-specific callbacks to ensure they function properly
    register_sim_tab_callbacks(app)
    register_bibites_tab_callbacks(app)
    register_lineages_tab_callbacks(app)
