import os
import time
import zipfile
import json
import re
import pandas as pd
from datetime import datetime
from dashboard.utils import get_simulations_base_folder, get_update_frequency, load_dataframe, save_dataframe, load_processed_log, update_processed_log, get_base_folder

folder_path = get_base_folder()
poll_interval = get_update_frequency()
simulations_base_folder = os.path.join(folder_path, "Dibite_Simulation_Data")
os.makedirs(folder_path, exist_ok=True)
processed_log_file = os.path.join(simulations_base_folder, "processed_zips.txt")

def process_zip(zip_path):
    print(f"Processing {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # --- Extract simulation name from settings.bb8settings ---
            try:
                with z.open("settings.bb8settings") as f:
                    file_bytes = f.read()
                    input_str = file_bytes.decode('utf-8', errors='ignore')
                    cleaned_str = re.sub(r'[^\x20-\x7E]', '', input_str)
                    settings_data = json.loads(cleaned_str)
                zones = settings_data.get("zones", [])
                zone_groups = settings_data.get("zoneGroups", [])
                if zones and isinstance(zones, list):
                    sim_name = zones[0].get("name", "default_sim")
                else:
                    sim_name = "default_sim"
                #print(f"Simulation name extracted: {sim_name}")
            except Exception as e:
                print(f"Error processing settings.bb8settings: {e}")
                sim_name = "default_sim"

            # Determine simulation folder and file paths
            sim_folder = os.path.join(simulations_base_folder, sim_name)
            species_data_file = os.path.join(sim_folder, "species_data.parquet")
            species_counts_file = os.path.join(sim_folder, "species_counts.parquet")
            
            # --- Load existing data for this simulation ---
            species_df = load_dataframe(species_data_file)
            counts_df = load_dataframe(species_counts_file, columns=["update_time", "speciesID", "count"])
            
            # --- Process speciesData.json for species details ---
            try:
                with z.open("speciesData.json") as f:
                    data = json.load(f)
                new_species = data.get("recordedSpecies", [])
                if new_species:
                    new_species_df = pd.DataFrame(new_species)
                    if not species_df.empty:
                        species_df = pd.concat([species_df, new_species_df])
                    else:
                        species_df = new_species_df
                    species_df = species_df.drop_duplicates(subset=["speciesID"]).reset_index(drop=True)
                    #print(f"Species details updated: {len(species_df)} records total.")
                else:
                    print("No recordedSpecies data found in speciesData.json.")
            except Exception as e:
                print(f"Error processing speciesData.json: {e}")
            
            # --- Process scene.bb8scene for simulatedTime ---
            try:
                with z.open("scene.bb8scene") as f:
                    file_bytes = f.read()
                    input_str = file_bytes.decode('utf-8', errors='ignore')
                    cleaned_str = re.sub(r'[^\x20-\x7E]', '', input_str)
                    scene_data = json.loads(cleaned_str)
                simulated_time = scene_data.get("simulatedTime")
                if simulated_time is None:
                    raise ValueError("simulatedTime not found")
                update_time = simulated_time  # Use the raw simulatedTime value as is
                #print(f"Simulated time extracted: {update_time}")
            except Exception as e:
                print(f"Error processing scene.bb8scene: {e}")
                update_time = "Unknown"

            # --- Process bibites folder for species counts ---
            bb8_files = [f for f in z.namelist() if f.lower().startswith("bibites/") and f.lower().endswith(".bb8")]
            species_ids = []
            for bb8 in bb8_files:
                try:
                    with z.open(bb8) as f:
                        file_bytes = f.read()
                        input_str = file_bytes.decode('utf-8', errors='ignore')
                        cleaned_str = re.sub(r'[^\x20-\x7E]', '', input_str)
                        bb8_data = json.loads(cleaned_str)
                        species_id = bb8_data.get("genes", {}).get("speciesID")
                        if species_id is not None:
                            species_ids.append(species_id)
                        else:
                            print(f"'speciesID' not found in {bb8}.")
                except Exception as e:
                    print(f"Error processing file {bb8}: {e}")
            
            if species_ids:
                count_series = pd.Series(species_ids).value_counts()
                new_counts = pd.DataFrame({
                    "update_time": [update_time] * len(count_series),
                    "speciesID": count_series.index,
                    "count": count_series.values
                })
                counts_df = pd.concat([counts_df, new_counts], ignore_index=True)
                #print(f"Species counts for simulated time {update_time} processed: {new_counts.shape[0]} species.")
            else:
                print("No .bb8 files found or no speciesIDs extracted in bibites folder.")
            
            # --- Save the updated data for this simulation ---
            save_dataframe(species_df, species_data_file)
            save_dataframe(counts_df, species_counts_file)
            
            return sim_name  # Optionally return the sim_name for logging
    except Exception as e:
        print(f"Error processing {zip_path}: {e}")
        return None

def main():
    processed_zips = load_processed_log(processed_log_file)
    
    while True:
        zip_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".zip")]
        
        # print(folder_path)
        new_files_found = False
        for filename in zip_files:
            if filename not in processed_zips:
                zip_path = os.path.join(folder_path, filename)
                sim_name = process_zip(zip_path)
                processed_zips.add(filename)
                new_files_found = True
        if new_files_found:
            update_processed_log(processed_log_file, processed_zips)
        else:
            print("No new ZIP files found. Waiting...")
        
        # Use poll_interval from the config (in seconds)
        time.sleep(poll_interval)

if __name__ == "__main__":
    main()
