/*
  Wokwi ESP32 -> AWG Bridge sender

  1) Set WIFI_SSID / WIFI_PASS for Wokwi-GUEST.
  2) Set BRIDGE_INGEST_URL to your public tunnel URL + /ingest
     Example: https://abc123.trycloudflare.com/ingest
*/

#if defined(ESP32)
#include <WiFi.h>
#include <HTTPClient.h>
#elif defined(ESP8266)
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#else
#error "This sketch requires ESP32 or ESP8266. In Wokwi, choose an ESP32 board."
#endif
#include <ArduinoJson.h>

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASS = "";

// Replace with your tunnel URL:
const char* BRIDGE_INGEST_URL = "https://REPLACE-ME.trycloudflare.com/ingest";

float waterOutput = 0.0f;
float energyUsed = 0.0f;
int filterAgeDays = 21;

void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
  }
}

float clampf(float v, float lo, float hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

void setup() {
  Serial.begin(115200);
  delay(500);
  connectWiFi();
  randomSeed(esp_random());
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  // Simulated telemetry
  float humidity = clampf(65.0f + (random(-80, 80) / 10.0f), 20.0f, 100.0f);
  float temperature = 24.0f + (random(-50, 50) / 10.0f);
  float battery = clampf(82.0f + (random(-30, 30) / 10.0f), 0.0f, 100.0f);
  float tank = clampf(45.0f + (random(-40, 40) / 10.0f), 0.0f, 100.0f);
  float soil = clampf(42.0f + (random(-30, 30) / 10.0f), 0.0f, 100.0f);
  float efficiency = clampf((humidity * 0.9f), 0.0f, 100.0f);

  waterOutput += 0.15f;
  energyUsed += 0.03f;

  StaticJsonDocument<512> doc;
  doc["humidity"] = humidity;
  doc["temperature"] = temperature;
  doc["battery_percent"] = battery;
  doc["tank_level"] = tank;
  doc["soil_moisture"] = soil;
  doc["water_output"] = waterOutput;
  doc["energy_used"] = energyUsed;
  doc["efficiency"] = efficiency;
  doc["filter_age_days"] = filterAgeDays;

  String body;
  serializeJson(doc, body);

  HTTPClient http;
  http.begin(BRIDGE_INGEST_URL);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(body);
  String resp = http.getString();
  http.end();

  Serial.print("POST ");
  Serial.print(code);
  Serial.print(" -> ");
  Serial.println(resp);

  delay(5000);
}
