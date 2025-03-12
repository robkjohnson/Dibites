# Dibites

A Dash-powered visualization tool for analyzing Bibites simulations.
This is a work in progess with more features coming.

Only tested for Windows versions:
 - 0.6.1a7
 - Steam 0.6.1

## Features

- View species evolution trends
- Analyze population changes over time
- Visualize neural networks of Bibites

## Installation

To install the necessary dependencies, ensure you have **Python 3.8+** installed, navigate to the folder where Dibits is saved within a command prompt, then run:

```sh
pip install -r requirements.txt
```

## Configuration

Before running the application, you need to update the `config.json` file in the project directory. This file should specify the location where Bibites saves its autosaves.

1. Open the config.json file.
2. Update the Path_To_Autosave_Folder value to be the path to your autosave folder. Below is the default folder location, you just need to replace **robkj** with your user name.

```json
{
    "Path_To_Autosave_Folder": "C:\\Users\\\<YOUR USER NAME HERE\>\\AppData\\LocalLow\\The Bibites\\The Bibites\\Savefiles\\Autosaves",
    "UpdateFrequency": 600
}
```

- The `Path_To_Autosave_Folder` should point to the directory where Bibites saves autosaves.
    - Note: You will need the double \\\ in between folders in the path. Replace the "\<YOUR USER NAME HERE\>" with your user folder name.
- `UpdateFrequency` defines how often (in seconds) the application checks for new data.

## Simulation Naming and Data Storage

### How Simulations Are Named

When a simulation is run, its name is extracted from the **settings.bb8settings** file inside the autosave ZIP archives. 

The name is taken from the name of the first zone. In order to create a new *sim* in Dibites, you will need to name the first zone of your sim something unique.

### Where Data Is Saved

Extracted simulation data is stored in the **Dibite_Simulation_Data** directory within the configured autosave folder. The relevant data files include:

- `species_data.parquet` – Contains species details extracted from `speciesData.json`.
- `species_counts.parquet` – Tracks population counts over time, derived from `.bb8` files inside the ZIP archives.

Each simulation has its own subfolder within `Dibite_Simulation_Data`, named according to the simulation's extracted name.

## Running the Application

Once dependencies are installed and the configuration file is set up, start the application with:

```sh
python Dibites.py
```

## Viewing the Dash

Once you've run Dibites.py you'll be able go to https:\\\localhost:8050 or https:\\\127.0.0.1:8050 to view the dashboard.

## Usage

1. **Select a simulation** – Choose a dataset to analyze.
2. **Explore the tabs**:
   - **Simulation Tab**: Observe population trends over time.
   - **Bibites Analysis**: Gives more insight into species of Bibites.
       - **Bibites Tab**: Analyze genetic attributes and neural network of a species.
       - **Lineages Tab**: Trace the evolutionary lineage of species and see how genes have changed over time.

## Contributing

If you’d like to contribute, feel free to fork this repository and submit a pull request.

I make no promises on speedy replies but I will try to keep up with this.
