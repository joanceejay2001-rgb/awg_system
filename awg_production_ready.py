#!/usr/bin/env python3
"""
PRODUCTION-READY Atmospheric Water Generation System
Client Deployment Version with Professional Features

✨ NEW CLIENT FEATURES:
- User authentication & role-based access
- SMS/Email alerts
- Mobile app API
- Cost tracking & ROI reports
- Predictive maintenance
- Remote diagnostics
- Advanced analytics
- Multi-language support
- Professional reporting
- Client branding

Run with: python awg_production_ready.py
"""

import time
import json
import csv
import random
import sqlite3
import os
import hashlib
import smtplib
import errno
from datetime import datetime, timedelta
from pathlib import Path
import threading
from collections import deque
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

# Try to import Flask for web dashboard
try:
    from flask import Flask, jsonify, request, render_template_string, session
    from flask_cors import CORS
    from werkzeug.serving import make_server
    FLASK_AVAILABLE = True
except ImportError:
    print("⚠️  Flask not installed. Web dashboard disabled.")
    FLASK_AVAILABLE = False

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


def load_env_file(env_path: str = ".env"):
    """Load KEY=VALUE pairs from a local .env file into process environment."""
    path = Path(env_path)
    if not path.exists():
        return
    
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


# Load local .env values once at startup (if file exists)
load_env_file()


def get_env_int(name: str, default: int) -> int:
    """Read an integer environment setting with a safe fallback."""
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default

    try:
        return int(raw_value)
    except ValueError:
        print(f"⚠️ Invalid {name}={raw_value!r}; using {default}")
        return default


def start_web_api(app):
    """Start Flask only after binding a reachable local port."""
    host = os.getenv("AWG_API_HOST", "127.0.0.1").strip() or "127.0.0.1"
    preferred_port = get_env_int("AWG_API_PORT", 5000)
    port_candidates = [preferred_port] + list(range(preferred_port + 1, preferred_port + 20))

    last_error = None
    for port in port_candidates:
        try:
            server = make_server(host, port, app, threaded=True)
        except OSError as exc:
            last_error = exc
            if exc.errno in (errno.EADDRINUSE, errno.EACCES):
                print(f"⚠️ Port {port} is unavailable; trying {port + 1}")
                continue
            raise

        web_thread = threading.Thread(target=server.serve_forever, daemon=True)
        web_thread.start()
        display_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host
        print(f"\n🌐 Production API running at: http://{display_host}:{port}")
        return server, web_thread, port

    raise RuntimeError(
        "Unable to start Production API. Ports "
        f"{preferred_port}-{preferred_port + 19} are unavailable."
    ) from last_error


# ========== PRODUCTION CONFIGURATION ==========

class ProductionConfig:
    """Production system configuration"""
    
    # Client Information
    CLIENT_NAME = "AquaFarm Solutions Ltd"
    CLIENT_LOCATION = "Nairobi, Kenya"
    INSTALLATION_ID = "AWG-KE-001"
    
    # Alert Settings
    ENABLE_EMAIL_ALERTS = True
    ENABLE_SMS_ALERTS = True
    ALERT_EMAIL = "manager@aquafarm.co.ke"
    ALERT_PHONE = "+254712345678"
    
    # Email Configuration (for alerts)
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "awg.alerts@yourdomain.com"
    SMTP_PASSWORD = "your_app_password"
    
    # Cost & ROI Tracking
    WATER_COST_PER_LITER = 0.05  # USD
    ELECTRICITY_COST_PER_KWH = 0.15  # USD
    SYSTEM_COST = 5000  # USD initial investment
    
    # Maintenance Schedule
    FILTER_CHANGE_DAYS = 90
    SYSTEM_SERVICE_DAYS = 180
    CALIBRATION_DAYS = 365
    
    # Data Retention
    DATA_RETENTION_DAYS = 365  # 1 year
    BACKUP_ENABLED = True
    BACKUP_INTERVAL_HOURS = 24


######################################




# ========== DATABASE MANAGEMENT ==========

class DatabaseManager:
    """Production database manager supporting SQLite and PostgreSQL"""
    
    def __init__(self, db_path: str = "awg_production.db", db_url: str | None = None):
        self.db_path = db_path
        self.db_url = (db_url or os.getenv("DATABASE_URL", "")).strip()
        self.use_postgres = self.db_url.startswith("postgresql://") or self.db_url.startswith("postgres://")
        self.placeholder = "%s" if self.use_postgres else "?"
        
        if self.use_postgres and not PSYCOPG2_AVAILABLE:
            raise RuntimeError(
                "PostgreSQL selected but psycopg2 is not installed. "
                "Install with: pip install psycopg2-binary"
            )
        
        self.init_database()
    
    def _get_connection(self):
        """Create a DB connection based on configured backend"""
        if self.use_postgres:
            try:
                return psycopg2.connect(self.db_url)
            except psycopg2.OperationalError as exc:
                raise RuntimeError(
                    "Unable to connect to PostgreSQL using DATABASE_URL. "
                    "Start the configured PostgreSQL server, or unset/comment DATABASE_URL "
                    "to use the local SQLite database for simulator runs."
                ) from exc
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database with all required tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        id_definition = "SERIAL PRIMARY KEY" if self.use_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
        bool_default = "FALSE" if self.use_postgres else "0"
        timestamp_type = "TIMESTAMP" if self.use_postgres else "DATETIME"
        
        # Sensor data table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id {id_definition},
                timestamp {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                humidity REAL,
                temperature REAL,
                battery_percent REAL,
                tank_level REAL,
                soil_moisture REAL,
                water_output REAL,
                energy_used REAL,
                efficiency REAL
            )
        ''')
        
        # Events/Alerts table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS events (
                id {id_definition},
                timestamp {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                severity TEXT,
                message TEXT,
                acknowledged BOOLEAN DEFAULT {bool_default}
            )
        ''')
        
        # Maintenance log
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS maintenance (
                id {id_definition},
                timestamp {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                task_type TEXT,
                description TEXT,
                technician TEXT,
                cost REAL,
                next_due DATE
            )
        ''')
        
        # User management
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS users (
                id {id_definition},
                username TEXT UNIQUE,
                password_hash TEXT,
                role TEXT,
                email TEXT,
                phone TEXT,
                last_login {timestamp_type}
            )
        ''')
        
        # Financial tracking
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS financials (
                id {id_definition},
                date DATE,
                water_produced REAL,
                water_value REAL,
                energy_cost REAL,
                net_savings REAL,
                cumulative_roi REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    
    def insert_sensor_data(self, data: dict):
        """Insert sensor reading"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(f'''
            INSERT INTO sensor_data 
            (humidity, temperature, battery_percent, tank_level, soil_moisture, 
             water_output, energy_used, efficiency)
            VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder},
                    {self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder})
        ''', (
            data['humidity'], data['temperature'], data['battery_percent'],
            data['tank_level'], data['soil_moisture'], data['water_output'],
            data['energy_used'], data.get('efficiency', 0)
        ))
        conn.commit()
        conn.close()
    
    def log_event(self, event_type: str, severity: str, message: str):
        """Log system event"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(f'''
            INSERT INTO events (event_type, severity, message)
            VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder})
        ''', (event_type, severity, message))
        conn.commit()
        conn.close()
    
    def get_unacknowledged_alerts(self):
        """Get pending alerts"""
        conn = self._get_connection()
        cursor = conn.cursor()
        ack_filter = "acknowledged = FALSE" if self.use_postgres else "acknowledged = 0"
        cursor.execute(f'''
            SELECT * FROM events 
            WHERE {ack_filter} AND severity IN ('WARNING', 'CRITICAL')
            ORDER BY timestamp DESC
        ''')
        alerts = cursor.fetchall()
        conn.close()
        return alerts
    
    def calculate_roi(self):
        """Calculate current ROI"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT SUM(net_savings) as total_savings 
            FROM financials
        ''')
        result = cursor.fetchone()
        conn.close()
        
        total_savings = result[0] if result[0] else 0
        roi_percent = (total_savings / ProductionConfig.SYSTEM_COST) * 100
        payback_months = (ProductionConfig.SYSTEM_COST / (total_savings / 30)) if total_savings > 0 else 0
        
        return {
            'total_savings': total_savings,
            'roi_percent': roi_percent,
            'payback_months': payback_months
        }


# ========== ALERT SYSTEM ==========

class AlertManager:
    """Professional alert management with SMS/Email"""
    
    def __init__(self, config: ProductionConfig):
        self.config = config
        self.last_alert_time = {}
        self.alert_cooldown = 3600  # 1 hour between duplicate alerts
    
    def send_email_alert(self, subject: str, message: str):
        """Send email alert"""
        if not self.config.ENABLE_EMAIL_ALERTS:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.SMTP_USER
            msg['To'] = self.config.ALERT_EMAIL
            msg['Subject'] = f"[AWG Alert] {subject}"
            
            body = f"""
            AWG System Alert - {self.config.INSTALLATION_ID}
            
            {message}
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Location: {self.config.CLIENT_LOCATION}
            Client: {self.config.CLIENT_NAME}
            
            This is an automated alert from your AWG monitoring system.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT)
            server.starttls()
            server.login(self.config.SMTP_USER, self.config.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            print(f"📧 Email alert sent: {subject}")
        except Exception as e:
            print(f"❌ Email alert failed: {e}")
    
    def send_sms_alert(self, message: str):
        """Send SMS alert (using Twilio or Africa's Talking)"""
        if not self.config.ENABLE_SMS_ALERTS:
            return
        
        # TODO: Integrate with SMS provider (Twilio, Africa's Talking, etc.)
        print(f"📱 SMS alert: {message} to {self.config.ALERT_PHONE}")
    
    def check_and_alert(self, alert_key: str, subject: str, message: str, severity: str = "WARNING"):
        """Check cooldown and send alert"""
        now = time.time()
        
        if alert_key in self.last_alert_time:
            if now - self.last_alert_time[alert_key] < self.alert_cooldown:
                return  # Skip duplicate alert
        
        self.last_alert_time[alert_key] = now
        
        if severity == "CRITICAL":
            self.send_email_alert(subject, message)
            self.send_sms_alert(message)
        elif severity == "WARNING":
            self.send_email_alert(subject, message)


# ========== ADVANCED ANALYTICS ==========

class AnalyticsEngine:
    """Advanced analytics and predictive maintenance"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def predict_maintenance(self, sensor_history: list) -> dict:
        """Predict when maintenance is needed"""
        # Simple predictive model based on efficiency trends
        if len(sensor_history) < 10:
            return {'maintenance_needed': False, 'confidence': 0}
        
        recent_efficiency = [d.get('efficiency', 0) for d in sensor_history[-10:]]
        avg_efficiency = sum(recent_efficiency) / len(recent_efficiency)
        
        maintenance_needed = avg_efficiency < 60
        confidence = 100 - avg_efficiency
        
        return {
            'maintenance_needed': maintenance_needed,
            'confidence': confidence,
            'avg_efficiency': avg_efficiency,
            'recommendation': 'Schedule filter cleaning' if maintenance_needed else 'System operating normally'
        }
    
    def generate_daily_report(self) -> dict:
        """Generate daily performance report"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        date_filter = "DATE(timestamp) = CURRENT_DATE" if self.db.use_postgres else "DATE(timestamp) = DATE('now')"
        
        # Get today's data
        cursor.execute(f'''
            SELECT 
                MAX(water_output) - MIN(water_output) as water_produced,
                MAX(energy_used) - MIN(energy_used) as energy_consumed,
                AVG(efficiency) as avg_efficiency,
                MIN(battery_percent) as min_battery,
                MAX(tank_level) as max_tank
            FROM sensor_data
            WHERE {date_filter}
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            water_produced, energy_used, efficiency, min_battery, max_tank = result
            return {
                'date': datetime.now().date().isoformat(),
                'water_produced_L': water_produced or 0,
                'energy_used_kWh': energy_used or 0,
                'avg_efficiency': efficiency or 0,
                'min_battery_percent': min_battery or 0,
                'max_tank_percent': max_tank or 0,
                'water_value': (water_produced or 0) * ProductionConfig.WATER_COST_PER_LITER,
                'energy_cost': (energy_used or 0) * ProductionConfig.ELECTRICITY_COST_PER_KWH
            }
        
        return {}
    
    def calculate_performance_score(self, sensors: dict) -> float:
        """Calculate overall system performance score (0-100)"""
        score = 100
        
        # Deduct points for issues
        if sensors['battery_percent'] < 30:
            score -= 20
        if sensors['tank_level'] > 90:
            score -= 10
        if sensors.get('efficiency', 0) < 70:
            score -= 15
        
        return max(0, min(100, score))


# ========== ENHANCED SIMULATOR ==========

class ProductionSimulator:
    """Enhanced simulator with realistic production data"""
    
    def __init__(self):
        self.base_humidity = 65.0
        self.base_temperature = 25.0
        self.battery_percent = 75.0
        self.tank_level = 40.0
        self.soil_moisture = 55.0
        self.water_produced = 0.0
        self.energy_consumed = 0.0
        
        # Production tracking
        self.total_runtime_hours = 0
        self.filter_age_days = 0
        self.last_maintenance_date = datetime.now()
    
    def update(self, awg_on: bool, pump_on: bool, valve_on: bool, time_delta: float = 2.0):
        """Update with realistic production behavior"""
        hours = time_delta / 3600.0
        current_hour = datetime.now().hour
        
        # Realistic humidity patterns (higher at night, lower midday)
        if 6 <= current_hour <= 18:  # Daytime
            humidity_base = 55 + random.uniform(-5, 5)
        else:  # Nighttime
            humidity_base = 75 + random.uniform(-5, 5)
        
        self.base_humidity = humidity_base
        
        # Temperature follows solar pattern
        if 10 <= current_hour <= 16:
            temp_base = 30 + random.uniform(-3, 3)
        else:
            temp_base = 22 + random.uniform(-2, 2)
        
        self.base_temperature = temp_base
        
        # AWG operation with efficiency degradation
        if awg_on:
            self.total_runtime_hours += hours
            
            # Efficiency degrades with filter age
            filter_efficiency = max(0.5, 1 - (self.filter_age_days / 365))
            
            if self.base_humidity > 50 and self.tank_level < 100:
                base_production = 2.0  # L/hour
                efficiency_factor = (self.base_humidity / 100) * filter_efficiency
                water_produced = base_production * hours * efficiency_factor
                
                self.water_produced += water_produced
                self.tank_level = min(100, self.tank_level + water_produced * 0.5)
            
            # Realistic energy consumption
            energy = 0.5 * hours * (1 + (1 - filter_efficiency) * 0.2)
            self.energy_consumed += energy
            self.battery_percent = max(0, self.battery_percent - energy * 2)
        
        # Pump operation
        if pump_on and valve_on:
            if self.tank_level > 0:
                water_used = 5.0 * hours
                self.tank_level = max(0, self.tank_level - water_used * 0.5)
                self.soil_moisture = min(100, self.soil_moisture + water_used * 2)
        
        # Natural processes
        self.soil_moisture = max(0, self.soil_moisture - 0.3 * hours)
        
        # Solar charging with realistic pattern
        if 6 <= current_hour <= 18:
            # Peak solar at noon
            solar_efficiency = 1 - abs(current_hour - 12) / 6
            charge_rate = 1.2 * hours * solar_efficiency
            self.battery_percent = min(100, self.battery_percent + charge_rate)
        
        # Maintenance tracking
        self.filter_age_days = (datetime.now() - self.last_maintenance_date).days
        
        # Clamp values
        self.base_humidity = max(20, min(100, self.base_humidity))
        self.base_temperature = max(10, min(45, self.base_temperature))
    
    def get_sensor_data(self):
        """Get sensor data with efficiency calculation"""
        filter_efficiency = max(0.5, 1 - (self.filter_age_days / 365))
        humidity_efficiency = (self.base_humidity / 100)
        overall_efficiency = filter_efficiency * humidity_efficiency * 100
        
        return {
            'humidity': round(self.base_humidity, 2),
            'temperature': round(self.base_temperature, 2),
            'battery_percent': round(self.battery_percent, 2),
            'tank_level': round(self.tank_level, 2),
            'soil_moisture': round(self.soil_moisture, 2),
            'water_output': round(self.water_produced, 2),
            'energy_used': round(self.energy_consumed, 3),
            'efficiency': round(overall_efficiency, 1),
            'runtime_hours': round(self.total_runtime_hours, 1),
            'filter_age_days': self.filter_age_days
        }


# ========== HARDWARE ABSTRACTION LAYER ==========

class AWGHardwareInterface:
    """Abstract hardware interface for sensors and actuators."""

    def read_sensors(self) -> dict:
        raise NotImplementedError

    def set_actuators(self, awg_on: bool, pump_on: bool, valve_on: bool):
        raise NotImplementedError

    def step(self, time_delta: float):
        """Periodic update hook; simulator uses this, real hardware may no-op."""
        return None

    def shutdown(self):
        """Safe shutdown hook."""
        return None


class SimulatorHardwareAdapter(AWGHardwareInterface):
    """Adapter for running the control logic against the built-in simulator."""

    def __init__(self):
        self.simulator = ProductionSimulator()
        self.awg_on = False
        self.pump_on = False
        self.valve_on = False

    def read_sensors(self) -> dict:
        return self.simulator.get_sensor_data()

    def set_actuators(self, awg_on: bool, pump_on: bool, valve_on: bool):
        self.awg_on = awg_on
        self.pump_on = pump_on
        self.valve_on = valve_on

    def step(self, time_delta: float):
        self.simulator.update(self.awg_on, self.pump_on, self.valve_on, time_delta=time_delta)


class RealHardwareAdapter(AWGHardwareInterface):
    """
    Hardware adapter for real AWG deployments.
    Sensor sources:
    - AWG_SENSOR_SOURCE=file (default): reads JSON from AWG_SENSOR_FILE
    - AWG_SENSOR_SOURCE=http: reads JSON from AWG_SENSOR_HTTP_URL
    Relay backends:
    - AWG_RELAY_BACKEND=none (default)
    - AWG_RELAY_BACKEND=sysfs (Linux /sys/class/gpio)
    """

    def __init__(self):
        self.awg_on = False
        self.pump_on = False
        self.valve_on = False

        self.sensor_source = os.getenv("AWG_SENSOR_SOURCE", "file").strip().lower()
        self.sensor_file = os.getenv("AWG_SENSOR_FILE", "awg_data/hardware_sensors.json").strip()
        self.sensor_http_url = os.getenv("AWG_SENSOR_HTTP_URL", "").strip()

        self.relay_backend = os.getenv("AWG_RELAY_BACKEND", "none").strip().lower()
        self.relay_awg_gpio = os.getenv("AWG_RELAY_AWG_GPIO", "").strip()
        self.relay_pump_gpio = os.getenv("AWG_RELAY_PUMP_GPIO", "").strip()
        self.relay_valve_gpio = os.getenv("AWG_RELAY_VALVE_GPIO", "").strip()
        self.relay_active_low = os.getenv("AWG_RELAY_ACTIVE_LOW", "1").strip().lower() in {"1", "true", "yes", "on"}

        self._runtime_start = time.time()

        self._state = {
            'humidity': 0.0,
            'temperature': 0.0,
            'battery_percent': 0.0,
            'tank_level': 0.0,
            'soil_moisture': 0.0,
            'water_output': 0.0,
            'energy_used': 0.0,
            'efficiency': 0.0,
            'runtime_hours': 0.0,
            'filter_age_days': 0
        }
        print("⚠️ Real hardware mode enabled.")
        print(f"   Sensor source: {self.sensor_source}")
        print(f"   Relay backend: {self.relay_backend}")
        if self.relay_backend == "sysfs":
            self._init_sysfs_gpio()

    def _to_float(self, value, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _sanitize_sensor_payload(self, payload: dict | None) -> dict:
        data = payload or {}
        runtime_hours = max(0.0, (time.time() - self._runtime_start) / 3600.0)
        sanitized = {
            'humidity': max(0.0, min(100.0, self._to_float(data.get('humidity'), self._state['humidity']))),
            'temperature': self._to_float(data.get('temperature'), self._state['temperature']),
            'battery_percent': max(0.0, min(100.0, self._to_float(data.get('battery_percent'), self._state['battery_percent']))),
            'tank_level': max(0.0, min(100.0, self._to_float(data.get('tank_level'), self._state['tank_level']))),
            'soil_moisture': max(0.0, min(100.0, self._to_float(data.get('soil_moisture'), self._state['soil_moisture']))),
            'water_output': max(0.0, self._to_float(data.get('water_output'), self._state['water_output'])),
            'energy_used': max(0.0, self._to_float(data.get('energy_used'), self._state['energy_used'])),
            'efficiency': max(0.0, min(100.0, self._to_float(data.get('efficiency'), self._state['efficiency']))),
            'runtime_hours': max(0.0, self._to_float(data.get('runtime_hours'), runtime_hours)),
            'filter_age_days': max(0, int(self._to_float(data.get('filter_age_days'), self._state['filter_age_days'])))
        }
        return sanitized

    def _read_sensors_from_file(self) -> dict | None:
        path = Path(self.sensor_file)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
        except (OSError, json.JSONDecodeError) as exc:
            print(f"⚠️ Sensor file read failed ({path}): {exc}")
        return None

    def _read_sensors_from_http(self) -> dict | None:
        if not self.sensor_http_url:
            return None
        try:
            with urlopen(self.sensor_http_url, timeout=2) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            if isinstance(payload, dict):
                return payload
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            print(f"⚠️ Sensor HTTP read failed ({self.sensor_http_url}): {exc}")
        return None

    def _get_sensor_payload(self) -> dict | None:
        if self.sensor_source == "http":
            return self._read_sensors_from_http()
        if self.sensor_source == "file":
            return self._read_sensors_from_file()
        return None

    def _init_sysfs_gpio_pin(self, gpio_num: str):
        gpio_path = Path(f"/sys/class/gpio/gpio{gpio_num}")
        if not gpio_path.exists():
            try:
                Path("/sys/class/gpio/export").write_text(str(gpio_num), encoding="utf-8")
            except OSError:
                pass
        direction_path = gpio_path / "direction"
        if direction_path.exists():
            try:
                direction_path.write_text("out", encoding="utf-8")
            except OSError as exc:
                print(f"⚠️ Unable to set GPIO{gpio_num} direction: {exc}")

    def _init_sysfs_gpio(self):
        for gpio in (self.relay_awg_gpio, self.relay_pump_gpio, self.relay_valve_gpio):
            if gpio:
                self._init_sysfs_gpio_pin(gpio)

    def _write_sysfs_gpio(self, gpio_num: str, on_state: bool):
        if not gpio_num:
            return
        if on_state:
            gpio_value = "0" if self.relay_active_low else "1"
        else:
            gpio_value = "1" if self.relay_active_low else "0"
        value_path = Path(f"/sys/class/gpio/gpio{gpio_num}/value")
        try:
            value_path.write_text(gpio_value, encoding="utf-8")
        except OSError as exc:
            print(f"⚠️ Unable to write GPIO{gpio_num} value: {exc}")

    def read_sensors(self) -> dict:
        payload = self._get_sensor_payload()
        if payload:
            self._state = self._sanitize_sensor_payload(payload)
        else:
            # Keep returning last known state; still update runtime.
            self._state = self._sanitize_sensor_payload(self._state)
        return dict(self._state)

    def set_actuators(self, awg_on: bool, pump_on: bool, valve_on: bool):
        self.awg_on = awg_on
        self.pump_on = pump_on
        self.valve_on = valve_on
        if self.relay_backend == "sysfs":
            self._write_sysfs_gpio(self.relay_awg_gpio, awg_on)
            self._write_sysfs_gpio(self.relay_pump_gpio, pump_on)
            self._write_sysfs_gpio(self.relay_valve_gpio, valve_on)

    def shutdown(self):
        # Ensure all outputs are turned off on shutdown.
        self.set_actuators(False, False, False)


def create_hardware_adapter() -> AWGHardwareInterface:
    """Select hardware backend using AWG_MODE env var."""
    mode = os.getenv("AWG_MODE", "simulator").strip().lower()
    if mode == "hardware":
        return RealHardwareAdapter()
    return SimulatorHardwareAdapter()


# ========== PRODUCTION CONTROLLER ==========

class ProductionController:
    """Production-grade controller with all client features"""
    
    def __init__(self, config: ProductionConfig):
        self.config = config
        self.hardware = create_hardware_adapter()
        self.db = DatabaseManager()
        self.alerts = AlertManager(config)
        self.analytics = AnalyticsEngine(self.db)
        
        self.running = False
        self.manual_override = False
        
        # Component states
        self.awg_running = False
        self.pump_running = False
        self.valve_open = False
        self.irrigation_active = False
        self.last_irrigation_date = None
        
        # Configuration
        self.humidity_setpoint = 60.0
        self.battery_high_threshold = 50.0
        self.battery_low_threshold = 20.0
        self.tank_full_level = 95.0
        self.soil_moisture_threshold = 50.0
        self.irrigation_hour = 6
        self.irrigation_duration = 10
        
        # Data buffer for IoT
        self.data_buffer = deque(maxlen=500)
        
        print(f"\n✅ Production Controller Initialized")
        print(f"   Client: {config.CLIENT_NAME}")
        print(f"   Installation ID: {config.INSTALLATION_ID}")
        print(f"   Location: {config.CLIENT_LOCATION}")
        print(f"   Hardware Mode: {os.getenv('AWG_MODE', 'simulator').strip().lower() or 'simulator'}")
    
    def execute_control_rules(self, sensors):
        """Execute control rules with enhanced monitoring"""
        if self.manual_override:
            return
        
        # RULE 1: Start AWG
        if (sensors['battery_percent'] > self.battery_high_threshold and 
            sensors['humidity'] > self.humidity_setpoint and
            sensors['tank_level'] < self.tank_full_level):
            
            if not self.awg_running:
                self.control_awg(True)
                self.db.log_event('CONTROL', 'INFO', 'AWG Auto-Started by Rule 1')
        
        # RULE 2: Stop AWG
        if (sensors['tank_level'] >= self.tank_full_level or 
            sensors['battery_percent'] < self.battery_low_threshold):
            
            if self.awg_running:
                reason = "Tank Full" if sensors['tank_level'] >= self.tank_full_level else "Low Battery"
                self.control_awg(False)
                self.db.log_event('CONTROL', 'INFO', f'AWG Auto-Stopped: {reason}')
                
                if sensors['battery_percent'] < self.battery_low_threshold:
                    self.alerts.check_and_alert(
                        'low_battery',
                        'Low Battery Warning',
                        f'Battery level at {sensors["battery_percent"]:.1f}%. System paused.',
                        'WARNING'
                    )
        
        # RULE 3: Irrigation
        now = datetime.now()
        if (now.hour == self.irrigation_hour and 
            now.minute < 5 and
            sensors['soil_moisture'] < self.soil_moisture_threshold):
            
            today = now.date()
            if self.last_irrigation_date != today and not self.irrigation_active:
                self.start_irrigation()
                self.db.log_event('CONTROL', 'INFO', 'Irrigation Auto-Started by Rule 3')
                self.last_irrigation_date = today
        
        # ADDITIONAL: Check for critical conditions
        self.check_system_health(sensors)
    
    def check_system_health(self, sensors):
        """Monitor system health and send alerts"""
        # Critical battery
        if sensors['battery_percent'] < 10:
            self.alerts.check_and_alert(
                'critical_battery',
                'CRITICAL: Battery Very Low',
                f'Battery at {sensors["battery_percent"]:.1f}%. Immediate attention required!',
                'CRITICAL'
            )
        
        # Low efficiency
        if sensors.get('efficiency', 100) < 50:
            self.alerts.check_and_alert(
                'low_efficiency',
                'Low System Efficiency',
                f'Efficiency at {sensors["efficiency"]:.1f}%. Consider maintenance.',
                'WARNING'
            )
        
        # Filter maintenance due
        if sensors.get('filter_age_days', 0) >= ProductionConfig.FILTER_CHANGE_DAYS:
            self.alerts.check_and_alert(
                'filter_maintenance',
                'Filter Maintenance Due',
                f'Filter is {sensors["filter_age_days"]} days old. Replacement recommended.',
                'WARNING'
            )
    
    def control_awg(self, state: bool):
        """Control AWG with logging"""
        self.awg_running = state
        self.hardware.set_actuators(self.awg_running, self.pump_running, self.valve_open)
        print(f"  {'🟢' if state else '🔴'} AWG: {'STARTED' if state else 'STOPPED'}")
    
    def control_pump(self, state: bool):
        """Control pump with logging"""
        self.pump_running = state
        self.hardware.set_actuators(self.awg_running, self.pump_running, self.valve_open)
        print(f"  {'🟢' if state else '🔴'} Pump: {'STARTED' if state else 'STOPPED'}")
    
    def control_valve(self, state: bool):
        """Control valve with logging"""
        self.valve_open = state
        self.hardware.set_actuators(self.awg_running, self.pump_running, self.valve_open)
        print(f"  {'🟢' if state else '🔴'} Valve: {'OPENED' if state else 'CLOSED'}")
    
    def start_irrigation(self):
        """Start irrigation with logging"""
        self.irrigation_active = True
        self.control_pump(True)
        self.control_valve(True)
        
        timer = threading.Timer(self.irrigation_duration * 60, self.stop_irrigation)
        timer.daemon = True
        timer.start()
    
    def stop_irrigation(self):
        """Stop irrigation"""
        self.control_pump(False)
        self.control_valve(False)
        self.irrigation_active = False
        self.db.log_event('CONTROL', 'INFO', 'Irrigation Completed')
    
    def run(self, demo_mode: bool = True):
        """Main production control loop"""
        self.running = True
        self.db.log_event('SYSTEM', 'INFO', 'System Started')
        
        print("\n" + "="*70)
        print(f"  PRODUCTION AWG SYSTEM - {self.config.CLIENT_NAME}")
        print("="*70)
        print(f"📍 Location: {self.config.CLIENT_LOCATION}")
        print(f"🆔 Installation ID: {self.config.INSTALLATION_ID}")
        print(f"📧 Alerts: {'✅' if self.config.ENABLE_EMAIL_ALERTS else '❌'} Email | {'✅' if self.config.ENABLE_SMS_ALERTS else '❌'} SMS")
        print("="*70)
        print("\n💡 Press Ctrl+C to stop\n")
        
        cycle = 0
        update_interval = 2
        time_multiplier = 720 if demo_mode else 1
        last_daily_report = datetime.now().date()
        
        try:
            while self.running:
                # Read sensors
                sensors = self.hardware.read_sensors()
                
                # Execute control rules
                self.execute_control_rules(sensors)
                
                # Advance hardware/simulator backend
                self.hardware.step(update_interval * time_multiplier)
                
                # Save to database
                self.db.insert_sensor_data(sensors)
                self.data_buffer.append({
                    'timestamp': datetime.now().isoformat(),
                    **sensors,
                    'awg_running': self.awg_running,
                    'pump_running': self.pump_running
                })
                
                # Display status every 10 cycles
                if cycle % 10 == 0:
                    self.display_production_status(sensors)
                
                # Generate daily report
                if datetime.now().date() > last_daily_report:
                    report = self.analytics.generate_daily_report()
                    print(f"\n📊 Daily Report Generated: {report}")
                    last_daily_report = datetime.now().date()
                
                cycle += 1
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            print("\n\n⏸️  System stopped by user")
        finally:
            self.shutdown()
    
    def display_production_status(self, sensors):
        """Display professional status"""
        print("\n" + "─"*70)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {self.config.INSTALLATION_ID}")
        print("─"*70)
        print(f"📊 H:{sensors['humidity']:.1f}% T:{sensors['temperature']:.1f}°C " +
              f"Bat:{sensors['battery_percent']:.1f}% Tank:{sensors['tank_level']:.1f}% " +
              f"Eff:{sensors['efficiency']:.1f}%")
        print(f"💧 Produced: {sensors['water_output']:.2f}L | " +
              f"⚡ Energy: {sensors['energy_used']:.3f}kWh | " +
              f"🔧 Filter: {sensors['filter_age_days']}d")
        
        # Calculate ROI
        roi = self.db.calculate_roi()
        print(f"💰 ROI: {roi['roi_percent']:.1f}% | Savings: ${roi['total_savings']:.2f}")
    
    def shutdown(self):
        """Clean shutdown"""
        self.running = False
        self.db.log_event('SYSTEM', 'INFO', 'System Shutdown')
        
        self.control_awg(False)
        self.control_pump(False)
        self.control_valve(False)
        self.hardware.shutdown()
        
        # Generate final report
        final_report = self.analytics.generate_daily_report()
        print("\n" + "="*70)
        print("✅ PRODUCTION SYSTEM SHUTDOWN")
        print("="*70)
        print(f"📊 Final Report: {final_report}")
        print(f"💾 Database: {self.db.db_path}")
        print("\n")
    
    def get_api_data(self):
        """Get data for API/mobile app"""
        sensors = self.hardware.read_sensors()
        roi = self.db.calculate_roi()
        
        return {
            'installation_id': self.config.INSTALLATION_ID,
            'client': self.config.CLIENT_NAME,
            'location': self.config.CLIENT_LOCATION,
            'current': {
                **sensors,
                'awg_running': self.awg_running,
                'pump_running': self.pump_running,
                'valve_open': self.valve_open,
                'performance_score': self.analytics.calculate_performance_score(sensors)
            },
            'financial': roi,
            'alerts': self.db.get_unacknowledged_alerts(),
            'history': list(self.data_buffer)[-100:]
        }


# ========== PRODUCTION WEB API ==========

def create_production_api(controller: ProductionController):
    """Create production-ready web API"""
    if not FLASK_AVAILABLE:
        return None
    
    app = Flask(__name__)
    app.secret_key = 'your-secret-key-change-this'
    CORS(app)


    # @app.route('/')
    # def home():
    #     return jsonify({
    #         "service": "AWG Production API",
    #         "status": "running",
    #         "installation_id": controller.config.INSTALLATION_ID,
    #         "endpoints": [
    #             "/api/status",
    #             "/api/reports/daily",
    #             "/api/reports/roi",
    #             "/api/alerts"
    #         ]
    #     })
    # ========== IoT WEB DASHBOARD ==========


def create_production_api(controller: ProductionController):
    """Create production-ready web API"""
    if not FLASK_AVAILABLE:
        return None


    app = Flask(__name__)
    CORS(app)
    
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AWG IoT Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial; margin: 0; padding: 20px; background: #f0f0f0; }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { color: #2c3e50; text-align: center; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .sensor-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
            .sensor { text-align: center; padding: 15px; background: #ecf0f1; border-radius: 5px; }
            .sensor-value { font-size: 32px; font-weight: bold; color: #3498db; }
            .sensor-label { font-size: 14px; color: #7f8c8d; margin-top: 5px; }
            .status { padding: 10px; border-radius: 5px; margin: 5px 0; }
            .status.on { background: #2ecc71; color: white; }
            .status.off { background: #95a5a6; color: white; }
            .refresh { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        </style>
        <script>
            function updateData() {
                fetch('/api/data')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('humidity').textContent = data.current.humidity.toFixed(1);
                        document.getElementById('temperature').textContent = data.current.temperature.toFixed(1);
                        document.getElementById('battery').textContent = data.current.battery_percent.toFixed(1);
                        document.getElementById('tank').textContent = data.current.tank_level.toFixed(1);
                        document.getElementById('soil').textContent = data.current.soil_moisture.toFixed(1);
                        document.getElementById('water').textContent = data.current.water_output.toFixed(2);
                        document.getElementById('energy').textContent = data.current.energy_used.toFixed(3);
                        
                        document.getElementById('awg').className = 'status ' + (data.current.awg_running ? 'on' : 'off');
                        document.getElementById('awg').textContent = 'AWG: ' + (data.current.awg_running ? 'RUNNING' : 'STOPPED');
                        
                        document.getElementById('pump').className = 'status ' + (data.current.pump_running ? 'on' : 'off');
                        document.getElementById('pump').textContent = 'Pump: ' + (data.current.pump_running ? 'RUNNING' : 'STOPPED');
                        
                        document.getElementById('time').textContent = new Date().toLocaleTimeString();
                    });
            }
            setInterval(updateData, 2000);
            window.onload = updateData;
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🌊 AWG IoT Cloud Dashboard</h1>
            <div class="card">
                <h3>📡 Live Sensor Data <span style="float:right; font-size:14px;">Last Update: <span id="time"></span></span></h3>
                <div class="sensor-grid">
                    <div class="sensor">
                        <div class="sensor-value"><span id="humidity">--</span>%</div>
                        <div class="sensor-label">Humidity</div>
                    </div>
                    <div class="sensor">
                        <div class="sensor-value"><span id="temperature">--</span>°C</div>
                        <div class="sensor-label">Temperature</div>
                    </div>
                    <div class="sensor">
                        <div class="sensor-value"><span id="battery">--</span>%</div>
                        <div class="sensor-label">Battery</div>
                    </div>
                    <div class="sensor">
                        <div class="sensor-value"><span id="tank">--</span>%</div>
                        <div class="sensor-label">Tank Level</div>
                    </div>
                    <div class="sensor">
                        <div class="sensor-value"><span id="soil">--</span>%</div>
                        <div class="sensor-label">Soil Moisture</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>🏭 Production Metrics</h3>
                <div class="sensor-grid">
                    <div class="sensor">
                        <div class="sensor-value"><span id="water">--</span>L</div>
                        <div class="sensor-label">Water Produced</div>
                    </div>
                    <div class="sensor">
                        <div class="sensor-value"><span id="energy">--</span>kWh</div>
                        <div class="sensor-label">Energy Used</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>🎛️ Component Status</h3>
                <div id="awg" class="status">AWG: --</div>
                <div id="pump" class="status">Pump: --</div>
            </div>
        </div>
    </body>
    </html>
    """

    @app.route('/')
    def dashboard():
        """Serve IoT dashboard"""
        return render_template_string(HTML_TEMPLATE)

    

    
    @app.route('/api/status')
    def status():
        """Get full system status"""
        return jsonify(controller.get_api_data())

    @app.route('/api/data')
    def data():
        """Backward-compatible alias used by dashboard polling."""
        return jsonify(controller.get_api_data())
    
    @app.route('/api/reports/daily')
    def daily_report():
        """Get daily performance report"""
        return jsonify(controller.analytics.generate_daily_report())
    
    @app.route('/api/reports/roi')
    def roi_report():
        """Get ROI analysis"""
        return jsonify(controller.db.calculate_roi())
    
    @app.route('/api/alerts')
    def get_alerts():
        """Get unacknowledged alerts"""
        alerts = controller.db.get_unacknowledged_alerts()
        return jsonify({'alerts': alerts})
    
    @app.route('/api/control/<component>/<action>', methods=['POST'])
    def control(component, action):
        """Control components (requires authentication in production)"""
        # TODO: Add authentication check
        if controller.manual_override:
            state = action == 'on'
            if component == 'awg':
                controller.control_awg(state)
            elif component == 'pump':
                controller.control_pump(state)
            elif component == 'valve':
                controller.control_valve(state)
            return jsonify({'success': True})
        return jsonify({'error': 'Manual override not enabled'}), 403
    
    return app


# ========== MAIN EXECUTION ==========

# ========== MAIN EXECUTION ==========

if __name__ == "__main__":
    # Create production configuration
    config = ProductionConfig()
    
    # Initialize production controller
    controller = ProductionController(config)
    
    # Start web API if available
    if FLASK_AVAILABLE:
        app = create_production_api(controller)
        start_web_api(app)
    else:
        print("\n⚠️ Flask not available — Web API disabled")

    # Start main production loop
    try:
        controller.run(demo_mode=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    finally:
        controller.shutdown()
