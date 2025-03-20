from dash import dcc, html, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import os
import json
import plotly.express as px
import dash_bootstrap_components as dbc
from utils import seconds_to_hours, load_pellet_data, get_simulations_base_folder, load_pellet_data


def get_zone_list(pellet_df):
    zone_names = []
    zones = []
    for zone in pellet_df['zone_name']:
        if zone not in zone_names:
            zone_names.append(zone)
    return zone_names



def build_zone_section(zone_names, pellet_df):
    """
    Builds Zone info pannels
    """

    
    zones_html = []
    for zone in zone_names:
        latest_index = pellet_df[pellet_df['zone_name'] == zone]['update_time'].idxmax()
        current_plant_count = pellet_df.loc[latest_index, 'plant_total_amount']

        zones_html.append(
                html.Div([
                        html.H4(f"Zone: {zone}", style={"textAlign": "center", "color": "white"}),
                        html.Div(
                            style={
                                "flex": "1", 
                                "display": "flex", 
                                "flexDirection": "row", 
                                "gap": "20px",
                                "padding": "20px",
                                'justifyContent': 'center',
                                'borderBottom': '4px solid #106881',
                            },
                            children = [
                                html.Div(
                                    style={
                                        "flex": "1", 
                                        "display": "flex", 
                                        "flexDirection": "column", 
                                        "gap": "20px",
                                        'justifyContent': 'center',
                                    },
                                    children = [
                                        html.H6(f"Latest Plant Count: {pellet_df.loc[latest_index, 'plant_pellet_count']}", style={"textAlign": "center", "color": "white"}),
                                        html.H6(f"Latest Plant Amount: {round(pellet_df.loc[latest_index, 'plant_total_amount'], 2)}", style={"textAlign": "center", "color": "white"}),
                                        html.H6(f"Latest Plant avg Amount: {round(pellet_df.loc[latest_index, 'plant_pellet_count']/pellet_df.loc[latest_index, 'plant_total_amount'], 2) if pellet_df.loc[latest_index, 'plant_total_amount'] > 0 else 0}", style={"textAlign": "center", "color": "white"}),
                                        html.H6(f"Latest Plant avg Scale: {round(pellet_df.loc[latest_index, 'plant_avg_scale'], 2)}", style={"textAlign": "center", "color": "white"}),
                                    ]
                                ),
                                html.Div(
                                    style={
                                        "flex": "1", 
                                        "display": "flex", 
                                        "flexDirection": "column", 
                                        "gap": "20px",
                                        'justifyContent': 'center',
                                    },
                                    children = [
                                        html.H6(f"Latest Meat Count: {pellet_df.loc[latest_index, 'meat_pellet_count']}", style={"textAlign": "center", "color": "white"}),
                                        html.H6(f"Latest Meat Amount: {round(pellet_df.loc[latest_index, 'meat_total_amount'], 2)}", style={"textAlign": "center", "color": "white"}),
                                        html.H6(f"Latest Meat avg Amount: {round(pellet_df.loc[latest_index, 'meat_pellet_count']/pellet_df.loc[latest_index, 'meat_total_amount'], 2) if pellet_df.loc[latest_index, 'meat_total_amount'] > 0 else 0}", style={"textAlign": "center", "color": "white"}),
                                        html.H6(f"Latest Meat avg Scale: {round(pellet_df.loc[latest_index, 'meat_avg_scale'], 2)}", style={"textAlign": "center", "color": "white"}),
                                    ]
                                ),
                            ]
                        )
                    ])
            )
    return zones_html


def get_zones_tab_content(sim_selected, n_intervals, simulations_base_folder):
    pellet_df = load_pellet_data(sim_selected, simulations_base_folder)
    zone_names = get_zone_list(pellet_df)
    
    return html.Div(
        
        style={
            "flex": "1", 
            "display": "flex", 
            "flexDirection": "column", 
            "gap": "20px",
            'justifyContent': 'center',
        },
        children = [
            html.H3("Zone Data being added soon", style={"textAlign": "center", "color": "white"}),
            html.Div(
                children = build_zone_section(zone_names, pellet_df)
            ),
        ],
    )



def register_zones_tab_callbacks(app):
    pass