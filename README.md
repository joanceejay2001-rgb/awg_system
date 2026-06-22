# AWG1

Atmospheric Water Generation (AWG) control service with:
- Rule-based controller
- PostgreSQL logging
- Flask API/dashboard
- Wokwi ESP32 bridge ingestion

## Prerequisites

- Python 3.12+
- Virtual environment at `venv/`
- Local PostgreSQL only if you set `DATABASE_URL` (simulator mode can use SQLite)
- Optional: `cloudflared` for Wokwi internet bridge

## 1) Activate Environment

```bash
source /home/sir-sang/Documents/AWG/venv/bin/activate
```

## 2) Configure Environment

Use `.env`:

```env
AWG_MODE=hardware
DATABASE_URL=postgresql://postgres:postgres@localhost:55432/businessintelligence
AWG_SENSOR_SOURCE=http
AWG_SENSOR_HTTP_URL=http://127.0.0.1:8090/latest
AWG_API_HOST=127.0.0.1
AWG_API_PORT=5000
```

For simulator mode, set:

```env
AWG_MODE=simulator
# Leave DATABASE_URL unset/commented to use awg_production.db via SQLite.
```

## 3) Start Bridge Service (for Wokwi/ESP32)

```bash
python /home/sir-sang/Documents/AWG/bridge_server.py
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
python /home/sir-sang/Documents/AWG/awg_production_ready.py
```

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

1. `python bridge_server.py`
2. `cloudflared tunnel --url http://127.0.0.1:8090`
3. `python awg_production_ready.py`
