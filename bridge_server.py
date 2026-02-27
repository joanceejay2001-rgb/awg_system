#!/usr/bin/env python3
"""
AWG bridge server for Wokwi/ESP32 sensor ingestion.

Endpoints:
- POST /ingest   : Accept JSON sensor payload from device simulator
- GET  /latest   : Return latest payload (for AWG app AWG_SENSOR_HTTP_URL)
- GET  /health   : Basic health check
"""

import json
import os
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = os.getenv("BRIDGE_HOST", "127.0.0.1")
PORT = int(os.getenv("BRIDGE_PORT", "8090"))
STATE_FILE = Path(os.getenv("BRIDGE_STATE_FILE", "awg_data/hardware_sensors.json"))

_LOCK = threading.Lock()
_LATEST = {
    "humidity": 0.0,
    "temperature": 0.0,
    "battery_percent": 0.0,
    "tank_level": 0.0,
    "soil_moisture": 0.0,
    "water_output": 0.0,
    "energy_used": 0.0,
    "efficiency": 0.0,
    "filter_age_days": 0,
    "received_at": None,
}


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def sanitize_payload(payload):
    """Normalize incoming payload to AWG app-compatible fields."""
    out = {
        "humidity": max(0.0, min(100.0, _to_float(payload.get("humidity")))),
        "temperature": _to_float(payload.get("temperature")),
        "battery_percent": max(0.0, min(100.0, _to_float(payload.get("battery_percent")))),
        "tank_level": max(0.0, min(100.0, _to_float(payload.get("tank_level")))),
        "soil_moisture": max(0.0, min(100.0, _to_float(payload.get("soil_moisture")))),
        "water_output": max(0.0, _to_float(payload.get("water_output"))),
        "energy_used": max(0.0, _to_float(payload.get("energy_used"))),
        "efficiency": max(0.0, min(100.0, _to_float(payload.get("efficiency")))),
        "filter_age_days": max(0, int(_to_float(payload.get("filter_age_days"), 0))),
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
    return out


def update_latest(payload):
    global _LATEST
    clean = sanitize_payload(payload)
    with _LOCK:
        _LATEST = clean
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(clean, indent=2), encoding="utf-8")
    except OSError as exc:
        # Keep service functional even if file persistence is unavailable.
        print(f"Warning: could not persist bridge state file: {exc}")
    return clean


def get_latest():
    with _LOCK:
        return dict(_LATEST)


class BridgeHandler(BaseHTTPRequestHandler):
    server_version = "AWGBridge/1.0"

    def _send_json(self, status_code, body):
        data = json.dumps(body).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self._send_json(200, {"ok": True})

    def do_GET(self):
        if self.path == "/latest":
            self._send_json(200, get_latest())
            return
        if self.path == "/health":
            self._send_json(200, {"ok": True, "service": "awg-bridge"})
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/ingest":
            self._send_json(404, {"error": "not found"})
            return

        length = self.headers.get("Content-Length")
        if not length:
            self._send_json(400, {"error": "missing body"})
            return

        try:
            raw = self.rfile.read(int(length))
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("payload must be JSON object")
            latest = update_latest(payload)
            self._send_json(200, {"ok": True, "latest": latest})
        except Exception as exc:
            self._send_json(400, {"error": "invalid json", "detail": str(exc)})

    def log_message(self, fmt, *args):
        return


def main():
    print(f"Starting AWG bridge at http://{HOST}:{PORT}")
    print(f"State file: {STATE_FILE}")
    server = ThreadingHTTPServer((HOST, PORT), BridgeHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
