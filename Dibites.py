import subprocess
import time
import sys

def main():
    try:
        # Start the file monitoring process
        file_monitor_proc = subprocess.Popen(["python", "Save_File_Monitor.py"])
        print("File monitor process started (Save_File_Monitor.py).")
        
        # Start the dashboard process from the dashboard folder
        dashboard_proc = subprocess.Popen(["python", "dashboard/app.py"])
        print("Dashboard process started (dashboard/app.py).")
        
        print("Both processes are running. Press Ctrl+C to exit.")
        
        # Keep the main process running to keep child processes alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down processes...")
        file_monitor_proc.terminate()
        dashboard_proc.terminate()
        file_monitor_proc.wait()
        dashboard_proc.wait()
        print("Processes terminated.")
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
