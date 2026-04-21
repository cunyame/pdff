"""
AGV + Charger Station Monitor
Raspberry Pi Flask server — main entry point.

Run with:  python app.py
Then open: http://<pi-ip>:5000
"""

import threading
import time
import simplejson as json
from flask import Flask, render_template, jsonify, request, Response
import yaml
import csv
import io

from fetchers.acs_fetcher import ACSFetcher
from fetchers.esp32_fetcher import ESP32Fetcher

# ── Load config ──────────────────────────────────────────────────────────────
with open("config.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

# ── Shared in-memory data store ──────────────────────────────────────────────
data_store = {
    "agv_list":        [],   # list of dicts, one per AGV
    "chargers":        {},   # station_id → latest reading dict
    "acs_last_update": None,
    "esp_last_update": None,
    "acs_error":       None,
    "esp_error":       None,
}
store_lock = threading.Lock()

# ── Flask app ────────────────────────────────────────────────────────────────
app = Flask(__name__)

# ── Background ACS polling thread ────────────────────────────────────────────
def acs_poll_loop():
    fetcher  = ACSFetcher(CONFIG["acs"])
    interval = CONFIG["acs"].get("poll_interval_s", 10)
    while True:
        try:
            agv_rows = fetcher.fetch()
            with store_lock:
                data_store["agv_list"]        = agv_rows
                data_store["acs_last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
                data_store["acs_error"]       = None
        except Exception as exc:
            with store_lock:
                data_store["acs_error"] = str(exc)
        time.sleep(interval)

# ── Background ESP32 active-poll thread ──────────────────────────────────────
def esp32_poll_loop():
    fetcher  = ESP32Fetcher(CONFIG["esp32"])
    interval = CONFIG["esp32"].get("poll_interval_s", 5)
    if CONFIG["esp32"].get("mode", "push") != "poll":
        return                    # push mode: ESP32 calls us, no polling needed
    while True:
        try:
            charger_data = fetcher.fetch_all()
            with store_lock:
                data_store["chargers"].update(charger_data)
                data_store["esp_last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
                data_store["esp_error"]       = None
        except Exception as exc:
            with store_lock:
                data_store["esp_error"] = str(exc)
        time.sleep(interval)

# ── HTTP endpoint: ESP32 pushes charger data here (push mode) ────────────────
@app.route("/api/charger", methods=["POST"])
def receive_charger():
    """
    ESP32 POSTs JSON payload:
    {
      "station_id":  "CS-01",
      "voltage":     48.3,
      "current":     12.5,
      "temperature": 34.2,
      "status":      "charging"   // "idle" | "charging" | "fault"
    }
    """
    try:
        payload = request.get_json(force=True)
        if not payload or "station_id" not in payload:
            return jsonify({"ok": False, "error": "missing station_id"}), 400
        payload["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with store_lock:
            data_store["chargers"][payload["station_id"]] = payload
            data_store["esp_last_update"]                 = payload["timestamp"]
            data_store["esp_error"]                       = None
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

# ── Dashboard page ────────────────────────────────────────────────────────────
@app.route("/")
def dashboard():
    with store_lock:
        snapshot = {
            "agv_list":         list(data_store["agv_list"]),
            "chargers":         dict(data_store["chargers"]),
            "acs_last_update":  data_store["acs_last_update"],
            "esp_last_update":  data_store["esp_last_update"],
            "acs_error":        data_store["acs_error"],
            "esp_error":        data_store["esp_error"],
            "refresh_interval": CONFIG.get("ui_refresh_interval_s", 5),
        }
    return render_template("dashboard.html", **snapshot)

# ── JSON API — polled by JS auto-refresh ─────────────────────────────────────
@app.route("/api/data")
def api_data():
    with store_lock:
        return jsonify({
            "agv_list":        data_store["agv_list"],
            "chargers":        data_store["chargers"],
            "acs_last_update": data_store["acs_last_update"],
            "esp_last_update": data_store["esp_last_update"],
            "acs_error":       data_store["acs_error"],
            "esp_error":       data_store["esp_error"],
        })

# ── Export AGV table as CSV download ─────────────────────────────────────────
@app.route("/export/agv.csv")
def export_agv_csv():
    with store_lock:
        rows = list(data_store["agv_list"])
    if not rows:
        return "No data yet", 204
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=agv_export.csv"},
    )

# ── Start ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    threading.Thread(target=acs_poll_loop,  daemon=True).start()
    threading.Thread(target=esp32_poll_loop, daemon=True).start()

    host  = CONFIG.get("server_host", "0.0.0.0")
    port  = CONFIG.get("server_port",  5000)
    debug = CONFIG.get("debug",        False)
    print(f"[AGV Monitor] Running on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, use_reloader=False)
