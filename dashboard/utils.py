import pandas as pd
import json
import os


def seconds_to_hours(seconds):
    """
    Convert a duration in seconds to hours, rounded to two decimal places.
    """
    try:
        hours = float(seconds) / 3600
        return round(hours, 2)
    except Exception as e:
        print(f"Error converting seconds to hours: {e}")
        return None

def get_config():
    """
    Load and return the configuration from config.json,
    which is located in the parent folder of the dashboard folder.
    """
    # Get the directory containing this file (i.e. dashboard folder)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # config.json is assumed to be one level above the dashboard folder
    config_path = os.path.join(base_dir, "..", "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    return config


def get_base_folder():
    """
    Return the autosave folder path from the configuration.
    """
    config = get_config()
    folder_path = config.get("Path_To_Autosave_Folder")
    if not folder_path:
        raise ValueError("Path_To_Autosave_Folder not found in config.json")
    return folder_path

def get_simulations_base_folder():
    """
    Return the simulation base folder.
    It is assumed that simulation data is stored in a folder named
    'Dibite_Simulation_Data' within the autosave folder.
    """
    base_folder = get_base_folder()
    return os.path.join(base_folder, "Dibite_Simulation_Data")

def load_processed_log(log_path):
    """Load processed ZIP filenames from a log file."""
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def update_processed_log(log_path, processed_set):
    """Update the processed ZIP log file with new entries."""
    with open(log_path, "w") as f:
        for filename in processed_set:
            f.write(filename + "\n")

def load_dataframe(file_path, columns=None):
    """Load a Parquet file into a Pandas DataFrame, returning an empty DataFrame if not found."""
    if os.path.exists(file_path):
        try:
            return pd.read_parquet(file_path)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    return pd.DataFrame(columns=columns) if columns else pd.DataFrame()

def save_dataframe(df, file_path):
    """Save a Pandas DataFrame to a Parquet file."""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        df.to_parquet(file_path, index=False)
    except Exception as e:
        print(f"Error saving data to {file_path}: {e}")

def get_update_frequency():
    """
    Return the update frequency (in seconds) from the configuration.
    Defaults to 600 if not provided.
    """
    config = get_config()
    return config.get("UpdateFrequency", 600)

def load_species_data(sim_selected, simulations_base_folder):
    """
    Load and process species data for the selected simulation.
    - Reads species_data.parquet and species_counts.parquet
    - Determines alive species count from the latest update
    - Sorts species by alive count in descending order
    - Returns a tuple (species_df, sorted_species_list)
    """

    if not sim_selected:
        return pd.DataFrame(), []  # Return empty DataFrame and list if no selection

    sim_folder = os.path.join(simulations_base_folder, sim_selected)
    species_file = os.path.join(sim_folder, "species_data.parquet")
    counts_file = os.path.join(sim_folder, "species_counts.parquet")

    if not os.path.exists(species_file) or not os.path.exists(counts_file):
        print(f"Missing data files: {species_file} or {counts_file}")
        return pd.DataFrame(), []

    try:
        # Load species data
        species_df = pd.read_parquet(species_file)
        counts_df = pd.read_parquet(counts_file)

        if species_df.empty or counts_df.empty:
            return pd.DataFrame(), []

        # Get latest update time
        latest_update = counts_df["update_time"].max()
        latest_counts = counts_df[counts_df["update_time"] == latest_update]

        # Merge to get alive counts per species
        species_df = species_df.merge(
            latest_counts[["speciesID", "count"]], on="speciesID", how="left"
        ).fillna({"count": 0})  # Fill missing values with 0

        # Sort species by the number of alive individuals (descending)
        species_df = species_df.sort_values(by="count", ascending=False)

        # Create list of dropdown options
        species_options = [
            {
                "label": f"{row['speciesID']}: {row['genericName']} {row['specificName']} (Alive: {int(row['count'])})",
                "value": row["speciesID"],
            }
            for _, row in species_df.iterrows()
        ]

        return species_df, species_options

    except Exception as e:
        print(f"Error loading species data: {e}")
        return pd.DataFrame(), []


def getNodeType(type):
    node_types = {
        "0": "Input",
        "1": "Sigmoid",
        "2": "Linear",
        "3": "TanH",
        "4": "Sine",
        "5": "ReLu",
        "6": "Gaussian",
        "7": "Differential",
        "8": "Latch",
        "9": "Abs",
        "10":"Mult",
        "11":"Integrator",
        "12":"Inhibitory",
        "13":"13",
        "14":"14",
        "15":"15",
        "16":"16",
        "17":"17",
        "18":"18",
        "19":"19",
        "20":"20",
    }
    return node_types[type]
