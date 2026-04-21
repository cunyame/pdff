# AGV + Charger Station Monitor

Real-time dashboard running on a Raspberry Pi that combines:
- **AGV fleet data** polled from an ACS server (CSV or HTML)
- **Charger station data** pushed from ESP32 nodes over WiFi
- **Live web UI** served by Flask, auto-refreshes every N seconds

---

## Project structure

```
agv_monitor/
├── app.py                        ← Flask server (main entry point)
├── config.yaml                   ← All settings (edit this first)
├── test_with_mock_data.py        ← Run this to test without real hardware
├── fetchers/
│   ├── acs_fetcher.py            ← Downloads & parses ACS data
│   └── esp32_fetcher.py          ← Polls ESP32 nodes (poll mode)
├── templates/
│   └── dashboard.html            ← Jinja2 dashboard template
└── esp32_firmware/
    └── charger_station.ino       ← Arduino sketch for each ESP32
```

---

## Quick start (Raspberry Pi)

### 1. Install dependencies

All libraries are already available on the Pi (as seen in the app).
No pip install needed. To confirm:

```bash
python3 -c "import flask, requests, bs4, yaml, simplejson, numpy"
```

### 2. Edit config.yaml

```yaml
acs:
  mode: "csv"                          # or "html"
  url:  "http://<acs-server-ip>/agv_status.csv"

esp32:
  mode: "push"                         # ESP32 posts to Pi
```

### 3. Run the server

```bash
cd agv_monitor
python3 app.py
```

Open `http://<pi-ip>:5000` in any browser on the same network.

### 4. Test without hardware first

```bash
python3 test_with_mock_data.py
```

This fills the UI with fake AGV and charger data so you can verify
everything looks correct before connecting real devices.

---

## ESP32 setup

1. Open `esp32_firmware/charger_station.ino` in Arduino IDE.
2. Install **ArduinoJson** via Library Manager.
3. Edit the top section:
   ```cpp
   const char* WIFI_SSID     = "YOUR_WIFI_SSID";
   const char* WIFI_PASS     = "YOUR_WIFI_PASSWORD";
   const char* PI_SERVER_URL = "http://192.168.1.50:5000/api/charger";
   const char* STATION_ID    = "CS-01";   // unique per unit
   ```
4. Calibrate the sensor constants (VOLTAGE_SCALE, ACS_SENSITIVITY, etc.)
   to match your actual hardware divider and sensor model.
5. Flash to each ESP32, changing STATION_ID for each one.

The ESP32 will POST JSON to the Pi every 5 seconds:
```json
{
  "station_id":  "CS-01",
  "voltage":     48.32,
  "current":     12.50,
  "temperature": 34.1,
  "status":      "charging"
}
```

---

## ACS data format

### CSV mode
The CSV file should have headers matching `config.yaml → acs → csv_columns`.
Default expected headers:

| AGV_ID | Status  | Location | Battery_% | Speed_mps | Current_Task   | Error_Code |
|--------|---------|----------|-----------|-----------|----------------|------------|
| AGV-01 | running | Zone-A   | 87.3      | 1.20      | Deliver pallet |            |

### HTML mode
The ACS server must render an HTML page with a `<table id="agv-status">` tag.
The first row or `<thead>` must contain column headers.
Adjust `html_table_selector` in config.yaml if the table has a different id/class.

---

## Dashboard features

- Live charger cards: voltage, current, temperature, power, status badge
- Colour-coded warnings (amber/red) when values exceed thresholds
- AGV table: status pills, battery progress bars, search filter
- CSV export button
- Connection status indicators for ACS and ESP32
- Auto-refresh countdown

---

## Run on boot (systemd)

```ini
# /etc/systemd/system/agv-monitor.service
[Unit]
Description=AGV Monitor
After=network.target

[Service]
WorkingDirectory=/home/pi/agv_monitor
ExecStart=/usr/bin/python3 app.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable agv-monitor
sudo systemctl start  agv-monitor
```
