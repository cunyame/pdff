"""
fetchers/esp32_fetcher.py
--------------------------
Fetches charger station data from ESP32 nodes.

Poll mode:  Pi actively GETs http://<esp32-ip>/data  every N seconds.
Push mode:  This file is not called — ESP32 pushes to /api/charger in app.py.

Expected JSON from ESP32 /data endpoint:
{
  "station_id":  "CS-01",
  "voltage":     48.3,
  "current":     12.5,
  "temperature": 34.2,
  "status":      "charging"    // "idle" | "charging" | "fault"
}
"""

import requests
import simplejson as json


class ESP32Fetcher:
    def __init__(self, cfg: dict):
        self.stations  = cfg.get("stations", [])   # list of {id, ip}
        self.poll_path = cfg.get("poll_path", "/data")
        self.timeout   = cfg.get("timeout_s", 4)

    # ── Public ───────────────────────────────────────────────────────────────
    def fetch_all(self) -> dict:
        """
        Poll every configured ESP32 station.
        Returns {station_id: data_dict}.
        Stations that time out are skipped (error logged per-station).
        """
        result = {}
        for station in self.stations:
            sid = station["id"]
            ip  = station["ip"]
            try:
                data = self._fetch_one(ip)
                data.setdefault("station_id", sid)   # fill in if ESP32 omits it
                result[sid] = data
            except Exception as exc:
                # Store an error entry so the UI can show "offline"
                result[sid] = {
                    "station_id": sid,
                    "status":     "offline",
                    "error":      str(exc),
                }
        return result

    # ── Private ──────────────────────────────────────────────────────────────
    def _fetch_one(self, ip: str) -> dict:
        url  = f"http://{ip}{self.poll_path}"
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()
