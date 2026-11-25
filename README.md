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

On Windows, use **PowerShell** (Windows PowerShell 5.1 or PowerShell 7) or **Command Prompt** (`cmd.exe`). Install [Git for Windows](https://git-scm.com/downloads/win) and [Python](https://www.python.org/downloads/windows/), then open a new terminal so the commands are available. Check `git --version` and `py -3 --version`; Python must be 3.12 or newer. Use the blocks labeled for your shell throughout this guide.

## 1) Clone and Install

Choose the block for your operating system. Run it from the directory where you want to keep the project.

### Windows (PowerShell)

```powershell
git clone https://github.com/joanceejay2001-rgb/awg_system.git
Set-Location awg_system
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Windows (Command Prompt)

```bat
git clone https://github.com/joanceejay2001-rgb/awg_system.git
cd /d awg_system
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

In either Windows shell, if `py` is unavailable but `python --version` shows Python 3.12 or newer, use `python -m venv .venv` for the third command.

### Linux / macOS (Bash)

```bash
git clone https://github.com/joanceejay2001-rgb/awg_system.git
cd awg_system
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

If you already cloned the repository, open a terminal in that checkout and skip the first two commands. The project folder can have any name.

### Working directory and Python environment

For each additional terminal, open it inside the checkout. The root command at the start of each launch block also works from a subfolder, including paths containing spaces. Always run the services at the repository root: `.env`, `awg_production.db`, and `awg_data/hardware_sensors.json` are resolved relative to the working directory.

The Command Prompt blocks are for pasting into an interactive `cmd.exe` window. If you put them in a `.bat` file, change `%R` to `%%R` in the `for` commands, as described in the [Microsoft `for` reference](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/for).

Each command uses the virtual environment's Python directly, so activation is unnecessary. On Windows, you can run these commands without changing PowerShell's execution policy. If you move the checkout or switch operating systems, recreate `.venv` and install the requirements again. See the [Python virtual environment documentation](https://docs.python.org/3/library/venv.html).

## 2) Configure Environment

Copy the supplied configuration without overwriting an existing `.env`:

Windows (PowerShell):

```powershell
Set-Location -LiteralPath (git rev-parse --show-toplevel)
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Windows (Command Prompt):

```bat
for /f "delims=" %R in ('git rev-parse --show-toplevel') do cd /d "%R"
if not exist .env copy .env.example .env
```

Linux / macOS (Bash):

```bash
cd "$(git rev-parse --show-toplevel)"
test -f .env || cp .env.example .env
```

The supplied configuration starts in simulator mode with SQLite and needs no PostgreSQL setup. To use Wokwi/ESP32 telemetry, open `.env` in a text editor and set the following values. These are file contents, not terminal commands:

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

Windows (PowerShell):

```powershell
Set-Location -LiteralPath (git rev-parse --show-toplevel)
.\.venv\Scripts\python.exe bridge_server.py
```

Windows (Command Prompt):

```bat
for /f "delims=" %R in ('git rev-parse --show-toplevel') do cd /d "%R"
.\.venv\Scripts\python.exe bridge_server.py
```

Linux / macOS (Bash):

```bash
cd "$(git rev-parse --show-toplevel)"
.venv/bin/python bridge_server.py
```

Keep the bridge running and check its health in another terminal.

Windows (PowerShell), using [Invoke-RestMethod](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/invoke-restmethod?view=powershell-5.1):

```powershell
Invoke-RestMethod -UseBasicParsing -Uri http://127.0.0.1:8090/health
```

Windows (Command Prompt), from inside the checkout:

```bat
for /f "delims=" %R in ('git rev-parse --show-toplevel') do cd /d "%R"
.\.venv\Scripts\python.exe -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8090/health').read().decode())"
```

Linux / macOS (Bash):

```bash
curl http://127.0.0.1:8090/health
```

## 4) Expose Bridge to Wokwi (Optional)

Install `cloudflared` using the [Cloudflare download instructions](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/) and make sure `cloudflared --version` works in a new terminal. With the bridge still running, run this command in another terminal. It is the same in PowerShell, Command Prompt, and Bash:

```text
cloudflared tunnel --url http://127.0.0.1:8090
```

Copy the generated `https://...trycloudflare.com` URL and set it in `wokwi_esp32_awg_bridge.ino` as:

```cpp
const char* BRIDGE_INGEST_URL = "https://YOUR-URL.trycloudflare.com/ingest";
```

## 5) Start AWG Service

Windows (PowerShell):

```powershell
Set-Location -LiteralPath (git rev-parse --show-toplevel)
.\.venv\Scripts\python.exe awg_production_ready.py
```

Windows (Command Prompt):

```bat
for /f "delims=" %R in ('git rev-parse --show-toplevel') do cd /d "%R"
.\.venv\Scripts\python.exe awg_production_ready.py
```

Linux / macOS (Bash):

```bash
cd "$(git rev-parse --show-toplevel)"
.venv/bin/python awg_production_ready.py
```

For simulator mode, this is the only service you need; skip the bridge and tunnel steps.

Keep the terminal open while using the dashboard. Press `Ctrl+C` in each service terminal to stop it.

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

For Wokwi, open each terminal at the repository root. If you are in a subfolder, use the root command for your shell from the launch blocks above first.

The Windows launch commands are the same in PowerShell and Command Prompt.

| Terminal | Windows (PowerShell or Command Prompt) | Linux / macOS (Bash) |
| --- | --- | --- |
| 1: Bridge | `.\.venv\Scripts\python.exe bridge_server.py` | `.venv/bin/python bridge_server.py` |
| 2: Tunnel | `cloudflared tunnel --url http://127.0.0.1:8090` | `cloudflared tunnel --url http://127.0.0.1:8090` |
| 3: AWG | `.\.venv\Scripts\python.exe awg_production_ready.py` | `.venv/bin/python awg_production_ready.py` |
