# AWG1

Atmospheric Water Generation (AWG) control service with:
- Rule-based controller
- PostgreSQL logging
- Flask API/dashboard
- Wokwi ESP32 bridge ingestion

## Prerequisites

- Git and Python 3.12+
- Local PostgreSQL only if you set `DATABASE_URL` (simulator mode can use SQLite)
- Optional: `cloudflared` for Wokwi internet bridge

## 1) Clone and Install

The commands below use Bash on Linux or macOS. Run the first block from the directory where you want to keep the project:

```bash
git clone https://github.com/joanceejay2001-rgb/awg_system.git
cd awg_system
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

If you already cloned the repository, open a terminal in that checkout and skip the first two commands. The project folder can have any name.

For each additional terminal, open it inside the checkout. `cd "$(git rev-parse --show-toplevel)"` returns to the repository root even from a subfolder. Always run the services there: `.env`, `awg_production.db`, and `awg_data/hardware_sensors.json` are resolved relative to the working directory. Using `.venv/bin/python` also avoids having to activate the environment in every terminal.

On Windows PowerShell, create the environment with `py -3 -m venv .venv` and use `.\.venv\Scripts\python.exe` instead of `.venv/bin/python`. Return to the root with `Set-Location (git rev-parse --show-toplevel)` instead of the Bash `cd` command.

## 2) Configure Environment

Copy the supplied configuration without overwriting an existing `.env`:

```bash
cd "$(git rev-parse --show-toplevel)"
test -f .env || cp .env.example .env
```

On Windows PowerShell, use `if (-not (Test-Path .env)) { Copy-Item .env.example .env }` from the repository root.

The supplied configuration starts in simulator mode with SQLite and needs no PostgreSQL setup. To use Wokwi/ESP32 telemetry, edit `.env` to set:

```env
AWG_MODE=hardware
AWG_SENSOR_SOURCE=http
AWG_SENSOR_HTTP_URL=http://127.0.0.1:8090/latest
AWG_API_HOST=127.0.0.1
AWG_API_PORT=5000
```

For simulator mode, keep:

```env
AWG_MODE=simulator
# Leave DATABASE_URL unset/commented to use awg_production.db via SQLite.
```

Set `DATABASE_URL` only if you have a running PostgreSQL server and use its actual connection details. Variables already exported in your terminal override `.env` values.

## 3) Start Bridge Service (for Wokwi/ESP32)

```bash
cd "$(git rev-parse --show-toplevel)"
.venv/bin/python bridge_server.py
```

Health check:

```bash
curl http://127.0.0.1:8090/health
```

## 4) Expose Bridge to Wokwi (Optional)

```bash
cloudflared tunnel --url http://127.0.0.1:8090
```

Copy the generated `https://...trycloudflare.com` URL and set it in `wokwi_esp32_awg_bridge.ino` as:

```cpp
const char* BRIDGE_INGEST_URL = "https://YOUR-URL.trycloudflare.com/ingest";
```

## 5) Start AWG Service

```bash
cd "$(git rev-parse --show-toplevel)"
.venv/bin/python awg_production_ready.py
```

For simulator mode, this is the only service you need; skip the bridge and tunnel steps.

API:
- `http://127.0.0.1:5000/api/status`
- `http://127.0.0.1:5000/api/data`
- `http://127.0.0.1:5000/api/reports/daily`
- `http://127.0.0.1:5000/api/reports/roi`

Dashboard:
- `http://127.0.0.1:5000/`

If port `5000` is already in use, the service prints the alternate port it selected, for example `http://127.0.0.1:5001/`.

## Wokwi Notes

- Use an ESP32 board in Wokwi.
- If `ArduinoJson` is required, add `libraries.txt` with:

```txt
ArduinoJson
```

## Suggested Run Order (3 terminals)

Open each terminal inside the checkout and return to the root with `cd "$(git rev-parse --show-toplevel)"` first.

1. `.venv/bin/python bridge_server.py`
2. `cloudflared tunnel --url http://127.0.0.1:8090`
3. `.venv/bin/python awg_production_ready.py`
