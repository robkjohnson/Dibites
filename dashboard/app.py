import dash
import dash_bootstrap_components as dbc
from layout import get_layout
from callbacks import register_callbacks
from utils import get_simulations_base_folder

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
app.layout = get_layout()

# Store the simulations base folder in a custom attribute if needed:
app.my_config = {}
app.my_config["SIMULATIONS_BASE_FOLDER"] = get_simulations_base_folder()

register_callbacks(app)

if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
