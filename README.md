# Dibites

A Dash-powered visualization tool for analyzing Bibites simulations.

## Features

- View species evolution trends
- Analyze population changes over time
- Visualize neural networks of Bibites

## Installation

To install the necessary dependencies, ensure you have **Python 3.8+** installed, then run:

```sh
pip install -r requirements.txt
```

## Configuration

Before running the application, you need to create a `config.json` file in the project directory. This file should specify the location where Bibites saves its autosaves.

1. Create a file named `config.json` in the root of the project.
2. Add the following structure:

```json
{
    "Path_To_Autosave_Folder": "C:\\Users\\<YOUR-USERNAME>\\AppData\\LocalLow\\The Bibites\\The Bibites\\Savefiles\\Autosaves",
    "UpdateFrequency": 600
}
```

- Replace `<YOUR-USERNAME>` with your Windows username.
- The `Path_To_Autosave_Folder` should point to the directory where Bibites saves autosaves.
- `UpdateFrequency` defines how often (in seconds) the application checks for new data.

## Running the Application

Once dependencies are installed and the configuration file is set up, start the application with:

```sh
python app.py
```

## Usage

1. **Select a simulation** – Choose a dataset to analyze.
2. **Explore the tabs**:
   - **Bibites Tab**: Analyze neural networks and genetic attributes.
   - **Simulation Tab**: Observe population trends over time.
   - **Lineages Tab**: Trace the evolutionary lineage of species.

## Contributing

If you’d like to contribute, feel free to fork this repository and submit a pull request.
