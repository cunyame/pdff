"""
fetchers/acs_fetcher.py
-----------------------
Fetches AGV data from the ACS (Automated Control System) server.

Supports two modes:
  • csv  — downloads a CSV file and parses every row into a dict
  • html — scrapes an HTML table using BeautifulSoup

All column names are mapped through config so the rest of the app
always sees the same normalised keys regardless of the source format.
"""

import csv
import io
import requests
from bs4 import BeautifulSoup


class ACSFetcher:
    def __init__(self, cfg: dict):
        self.mode    = cfg.get("mode", "csv")
        self.url     = cfg["url"]
        self.timeout = cfg.get("timeout_s", 8)
        self.columns = cfg.get("csv_columns", {})
        self.selector = cfg.get("html_table_selector", "table")
        auth_user = cfg.get("username", "")
        auth_pass = cfg.get("password", "")
        self.auth = (auth_user, auth_pass) if auth_user else None

    # ── Public ───────────────────────────────────────────────────────────────
    def fetch(self) -> list[dict]:
        """Return a list of normalised AGV dicts."""
        if self.mode == "csv":
            return self._fetch_csv()
        elif self.mode == "html":
            return self._fetch_html()
        else:
            raise ValueError(f"Unknown ACS mode: {self.mode!r}")

    # ── CSV mode ─────────────────────────────────────────────────────────────
    def _fetch_csv(self) -> list[dict]:
        resp = requests.get(
            self.url,
            auth=self.auth,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        content = resp.text

        reader  = csv.DictReader(io.StringIO(content))
        col_map = self.columns   # app_key → csv_header

        rows = []
        for raw in reader:
            # Strip whitespace from all values
            raw = {k.strip(): v.strip() for k, v in raw.items()}
            row = self._normalise_csv_row(raw, col_map)
            rows.append(row)
        return rows

    def _normalise_csv_row(self, raw: dict, col_map: dict) -> dict:
        """Map raw CSV headers to our internal keys, keep extras as-is."""
        result = {}
        used   = set()
        for app_key, csv_header in col_map.items():
            result[app_key] = raw.get(csv_header, "")
            used.add(csv_header)
        # Also keep every unmapped column so the UI can show it
        for k, v in raw.items():
            if k not in used:
                result[k] = v
        return result

    # ── HTML-scrape mode ──────────────────────────────────────────────────────
    def _fetch_html(self) -> list[dict]:
        resp = requests.get(
            self.url,
            auth=self.auth,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        soup  = BeautifulSoup(resp.text, "lxml")
        table = soup.select_one(self.selector)
        if table is None:
            raise ValueError(
                f"No table found with selector {self.selector!r}"
            )
        return self._parse_html_table(table)

    def _parse_html_table(self, table) -> list[dict]:
        rows = []
        headers = []
        for th in table.select("thead th, thead td"):
            headers.append(th.get_text(strip=True))

        if not headers:
            # Fallback: use first <tr> as header row
            first_row = table.find("tr")
            if first_row:
                headers = [
                    td.get_text(strip=True)
                    for td in first_row.find_all(["th", "td"])
                ]

        for tr in table.select("tbody tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(cells) == len(headers):
                raw = dict(zip(headers, cells))
                col_map = self.columns
                rows.append(self._normalise_csv_row(raw, col_map))
        return rows
