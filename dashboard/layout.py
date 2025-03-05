from dash import html, dcc
import dash_bootstrap_components as dbc
from utils import get_simulations_base_folder, get_update_frequency

def get_layout():
    # Header with title, simulation selector, and main tabs
    header = dbc.Row(
        [
            # Logo + Title
            dbc.Col(
                html.Div([
                    html.Img(
                        src="/assets/logo.png",  # Placeholder logo
                        style={'height': '50px', 'marginRight': '15px', 'borderRadius': '5px'}
                    ),
                    html.H1("Dibites", style={
                        'color': '#17a2b8',  # Bootstrap primary color
                        'fontSize': '42px',
                        'fontWeight': 'bold',
                        'textShadow': '2px 2px 5px rgba(0, 0, 0, 0.3)',
                        'letterSpacing': '2px',
                        'display': 'inline-block',
                        'verticalAlign': 'middle',
                        'margin': '0'
                    })
                ], style={'display': 'flex', 'alignItems': 'center'}),
                width="auto"
            ),

            # Simulation Selector
            dbc.Col(
                html.Div([
                    html.Label("Select Simulation:", style={'fontWeight': 'bold', 'color': 'white', 'marginRight': '10px'}),
                    dcc.Dropdown(
                        id="sim-dropdown",
                        options=[],  # Dynamically populated via callback
                        placeholder="Choose a Simulation",
                        clearable=False,
                        style={'backgroundColor': '#343a40', 'color': 'white', 'minWidth': '200px'}
                    )
                ], style={'display': 'flex', 'alignItems': 'center'}),
                width="auto"
            ),

            # Main Tabs (Reduced Height, Preserving Styling)
            dbc.Col(
                dcc.Tabs(
                    id="main-tabs",
                    value="sim",  # Default tab
                    children=[
                        dcc.Tab(
                            label="Sim",
                            value="sim",
                            style={'backgroundColor': '#343a40', 'color': 'white', 'textAlign': 'center',
                                   'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center',
                                   'padding': '5px 15px', 'lineHeight': '25px'},
                            selected_style={'backgroundColor': '#212529', 'color': 'white', 'textAlign': 'center',
                                            'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center',
                                            'padding': '5px 15px', 'lineHeight': '25px'}
                        ),
                        dcc.Tab(
                            label="Bibite Analysis",
                            value="bibite-analysis",
                            style={'backgroundColor': '#343a40', 'color': 'white', 'textAlign': 'center',
                                   'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center',
                                   'padding': '5px 15px', 'lineHeight': '25px'},
                            selected_style={'backgroundColor': '#212529', 'color': 'white', 'textAlign': 'center',
                                            'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center',
                                            'padding': '5px 15px', 'lineHeight': '25px'}
                        ),
                    ],
                    style={'backgroundColor': '#1c1e22', 'marginLeft': '20px'}
                ),
                width="auto"
            ),
        ],
        style={
            'backgroundColor': '#1c1e22',
            'padding': '15px',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'space-between',
            'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.3)',
            'borderBottom': '6px solid #17a2b8'
        }
    )

    # Sub-tabs for Bibite Analysis (Bibites & Lineages, Reduced Height)
    bibite_analysis_tabs = html.Div(
        id="bibite-analysis-tabs-container",
        children=[
            dcc.Tabs(
                id="bibite-tabs",
                value="bibites",  # Default sub-tab
                children=[
                    dcc.Tab(
                        label="Bibites",
                        value="bibites",
                        style={'backgroundColor': '#343a40', 'color': 'white', 'textAlign': 'center',
                               'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center',
                               'padding': '5px 15px', 'lineHeight': '25px'},
                        selected_style={'backgroundColor': '#212529', 'color': 'white', 'textAlign': 'center',
                                        'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center',
                                        'padding': '5px 15px', 'lineHeight': '25px'}
                    ),
                    dcc.Tab(
                        label="Lineages",
                        value="lineages",
                        style={'backgroundColor': '#343a40', 'color': 'white', 'textAlign': 'center',
                               'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center',
                               'padding': '5px 15px', 'lineHeight': '25px'},
                        selected_style={'backgroundColor': '#212529', 'color': 'white', 'textAlign': 'center',
                                        'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center',
                                        'padding': '5px 15px', 'lineHeight': '25px'}
                    )
                ],
                style={'backgroundColor': '#1c1e22', 'marginTop': '10px'}
            )
        ],
        style={'display': 'none'}  # Initially hidden unless "Bibite Analysis" is selected
    )

    # Interval component for auto-refresh
    interval = dcc.Interval(
        id="interval-component",
        interval=get_update_frequency() * 1000,  # Update based on config settings
        n_intervals=0
    )

    # Content area for tab-specific data
    tab_content = html.Div(id="tab-content", style={'padding': '20px'})

    return html.Div([
        header,
        interval,
        bibite_analysis_tabs,  # Add nested sub-tabs here
        tab_content
    ], style={'backgroundColor': '#212529'})

