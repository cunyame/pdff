"""
test_with_mock_data.py
----------------------
Run this INSTEAD of app.py to test the UI with fake AGV and charger data.
No ACS server or ESP32 needed.

Usage:
    python test_with_mock_data.py
Then open: http://localhost:5000
"""

import time
import random
import threading

# Patch config before importing app
import yaml, os

MOCK_CONFIG = {
    "server_host": "0.0.0.0",
    "server_port": 5000,
    "debug": True,
    "ui_refresh_interval_s": 3,
    "acs": {
        "mode": "csv",
        "url": "http://mock",
        "poll_interval_s": 4,
        "csv_columns": {
            "agv_id":   "AGV_ID",
            "status":   "Status",
            "location": "Location",
            "battery":  "Battery_%",
            "speed":    "Speed_mps",
            "task":     "Current_Task",
            "error":    "Error_Code",
        }
    },
    "esp32": {
        "mode": "push",
        "stations": [],
        "poll_interval_s": 5,
        "timeout_s": 4,
        "thresholds": {
            "voltage_min": 44.0,
            "voltage_max": 56.0,
            "current_max": 20.0,
            "temperature_max": 50.0,
        }
    }
}

with open("config.yaml", "w") as f:
    yaml.dump(MOCK_CONFIG, f)

# Now import the real app
from app import app, data_store, store_lock

AGV_IDS     = ["AGV-001", "AGV-002", "AGV-003", "AGV-004", "AGV-005"]
STATUSES    = ["running", "idle", "running", "running", "error"]
LOCATIONS   = ["Zone-A", "Zone-B", "Dock-1", "Aisle-3", "Charging"]
TASKS       = ["Deliver pallet", "Idle", "Pick item", "Return to dock", "Charging"]
CHARGER_IDS = ["CS-01", "CS-02", "CS-03"]
CS_STATUS   = ["charging", "idle", "charging"]

def mock_agv_loop():
    """Generate random AGV data and push into store every 4 seconds."""
    while True:
        rows = []
        for i, aid in enumerate(AGV_IDS):
            batt = random.uniform(10, 100)
            rows.append({
                "agv_id":   aid,
                "status":   STATUSES[i] if random.random() > 0.1 else "idle",
                "location": LOCATIONS[i],
                "battery":  f"{batt:.1f}",
                "speed":    f"{random.uniform(0, 1.8):.2f}" if STATUSES[i] == "running" else "0.00",
                "task":     TASKS[i],
                "error":    "E-042" if STATUSES[i] == "error" else "",
            })
        with store_lock:
            data_store["agv_list"]        = rows
            data_store["acs_last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
            data_store["acs_error"]       = None
        time.sleep(4)

def mock_charger_loop():
    """Generate random charger station data every 3 seconds."""
    while True:
        with store_lock:
            for i, sid in enumerate(CHARGER_IDS):
                voltage = random.uniform(47.5, 50.5)
                current = random.uniform(8, 18) if CS_STATUS[i] == "charging" else random.uniform(0, 0.3)
                temp    = random.uniform(28, 42)
                data_store["chargers"][sid] = {
                    "station_id":  sid,
                    "voltage":     round(voltage, 2),
                    "current":     round(current, 2),
                    "temperature": round(temp, 1),
                    "status":      CS_STATUS[i],
                    "timestamp":   time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            data_store["esp_last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
            data_store["esp_error"]       = None
        time.sleep(3)

if __name__ == "__main__":
    print("=" * 50)
    print("  AGV Monitor — MOCK DATA MODE")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 50)
    threading.Thread(target=mock_agv_loop,     daemon=True).start()
    threading.Thread(target=mock_charger_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
