// ============================================================
//  Fire Detection System - ESP32-S3 N8R8
//  Sensors : PIR (GPIO15) | LDR (GPIO4) | MQ-7 (GPIO5)
//            Flame D1 (GPIO16) | DHT22 (GPIO14)
//
//  Sends JSON to Python backend every 2 seconds via WiFi.
//  Backend runs sensor_receiver.py on your laptop.
// ============================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <time.h>
#include "DHT.h"

// ── WiFi ─────────────────────────────────────────────────────
const char* WIFI_SSID     = "POCO M6 5G";
const char* WIFI_PASSWORD = "11111111";

// ── Backend ───────────────────────────────────────────────────
// Run ipconfig on your laptop and put your IPv4 address here.
// Must be on same network as ESP32.
const char* BACKEND_URL = "http://172.23.175.67:5000/telemetry";

// ── Pin Definitions ──────────────────────────────────────────
#define PIR_PIN    15
#define LDR_PIN    4
#define MQ7_PIN    5
#define FLAME_PIN  16
#define DHT_PIN    14
#define DHT_TYPE   DHT22
 
DHT dht(DHT_PIN, DHT_TYPE);

// ── Timing ───────────────────────────────────────────────────
#define SEND_INTERVAL_MS   2000UL
#define MQ7_WARMUP_MS     90000UL

// ── LDR flicker sampling ──────────────────────────────────────
// Takes 10 LDR samples over 500ms and returns the std deviation.
// Flame flicker produces high variance (~200-900).
// Stable ambient light produces low variance (~0-75).
#define FLICKER_SAMPLES     10
#define FLICKER_WINDOW_MS  500

float computeLDRFlicker() {
  int samples[FLICKER_SAMPLES];
  int delayMs = FLICKER_WINDOW_MS / FLICKER_SAMPLES;

  for (int i = 0; i < FLICKER_SAMPLES; i++) {
    samples[i] = analogRead(LDR_PIN);
    delay(delayMs);
  }

  // Mean
  float mean = 0;
  for (int i = 0; i < FLICKER_SAMPLES; i++) {
    mean += samples[i];
  }
  mean /= FLICKER_SAMPLES;

  // Std deviation
  float variance = 0;
  for (int i = 0; i < FLICKER_SAMPLES; i++) {
    float diff = samples[i] - mean;
    variance += diff * diff;
  }
  variance /= FLICKER_SAMPLES;

  return sqrt(variance);
}

unsigned long lastSend  = 0;
unsigned long startTime = 0;
bool ntpSynced          = false;

// ── NTP timestamp ─────────────────────────────────────────────
String getTimestamp() {
  if (!ntpSynced) return "1970-01-01T00:00:00Z";
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) return "1970-01-01T00:00:00Z";
  char buf[25];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
  return String(buf);
}

// ── Setup ────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(PIR_PIN,   INPUT);
  pinMode(FLAME_PIN, INPUT);
  pinMode(LDR_PIN,  INPUT);
  pinMode(MQ7_PIN,  INPUT);

  dht.begin();
  startTime = millis();

  // WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());

    // NTP sync
    configTime(19800, 0, "pool.ntp.org", "time.nist.gov"); // UTC+5:30 (IST)
    Serial.print("Syncing NTP");
    struct tm timeinfo;
    int ntpAttempts = 0;
    while (!getLocalTime(&timeinfo) && ntpAttempts < 10) {
      delay(500);
      Serial.print(".");
      ntpAttempts++;
    }
    if (getLocalTime(&timeinfo)) {
      ntpSynced = true;
      Serial.println("\nNTP synced");
    } else {
      Serial.println("\nNTP failed - using fallback timestamp");
    }
  } else {
    Serial.println("\nWiFi FAILED - check SSID/password");
  }

  Serial.println("MQ-7 warming up (90 sec)...");
  Serial.println("System ready\n");
}

// ── Loop ─────────────────────────────────────────────────────
void loop() {
  unsigned long now = millis();

  if (now - lastSend >= SEND_INTERVAL_MS) {
    lastSend = now;

    bool warmedUp = (now - startTime) >= MQ7_WARMUP_MS;

    // ── DHT22 ────────────────────────────────────────────────
    float temperature = dht.readTemperature();
    float humidity    = dht.readHumidity();

    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("[ERROR] DHT22 read failed - check GPIO 14 wiring");
      return;
    }

    // ── MQ-7 (CO) ────────────────────────────────────────────
    int co_adc = analogRead(MQ7_PIN);

    // ── PIR ──────────────────────────────────────────────────
    bool motion = digitalRead(PIR_PIN) == HIGH;

    // ── Flame sensor (active LOW on D1) ──────────────────────
    bool flame = digitalRead(FLAME_PIN) == LOW;

    // ── LDR + flicker computation ─────────────────────────────
    // computeLDRFlicker() takes 500ms internally (10 samples)
    float ldr_flicker = computeLDRFlicker();
    int   ldr_adc     = analogRead(LDR_PIN);   // single snapshot after flicker window

    // ── Serial debug ─────────────────────────────────────────
    Serial.println("--------------------------------------------");
    Serial.print("[DHT22]  Temp     : "); Serial.print(temperature, 1); Serial.println(" C");
    Serial.print("[DHT22]  Humidity : "); Serial.print(humidity, 1);    Serial.println(" %");
    Serial.print("[MQ-7]   CO ADC   : "); Serial.print(co_adc);
    if (!warmedUp) {
      unsigned long rem = (MQ7_WARMUP_MS - (now - startTime)) / 1000;
      Serial.print("  (warming up - "); Serial.print(rem); Serial.print("s left)");
    }
    Serial.println();
    Serial.print("[LDR]    ADC      : "); Serial.println(ldr_adc);
    Serial.print("[LDR]    Flicker  : "); Serial.println(ldr_flicker, 1);
    Serial.print("[PIR]    Motion   : "); Serial.println(motion ? "YES" : "no");
    Serial.print("[FLAME]  D1       : "); Serial.println(flame  ? "*** DETECTED ***" : "none");

    // ── Build JSON ────────────────────────────────────────────
    StaticJsonDocument<300> doc;

    doc["device_id"]    = "esp32_001";
    doc["zone_id"]      = "lab_zone";
    doc["timestamp"]    = getTimestamp();
    doc["mq7_warmed"]   = warmedUp;

    doc["temperature"]  = round(temperature * 10.0) / 10.0;
    doc["humidity"]     = round(humidity    * 10.0) / 10.0;
    doc["co_adc"]       = co_adc;
    doc["ldr_adc"]      = ldr_adc;
    doc["ldr_flicker"]  = round(ldr_flicker * 10.0) / 10.0;
    doc["flame"]        = flame  ? 1 : 0;
    doc["motion"]       = motion ? 1 : 0;

    String json;
    serializeJson(doc, json);

    // ── POST to backend ───────────────────────────────────────
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(BACKEND_URL);
      http.addHeader("Content-Type", "application/json");
      http.setTimeout(3000);

      int code = http.POST(json);

      Serial.print("[HTTP]   Response : ");
      Serial.println(code);

      if (code == 200) {
        String resp = http.getString();
        Serial.print("[ML]     Result   : ");
        Serial.println(resp);
      } else if (code < 0) {
        Serial.println("[HTTP]   Cannot reach backend - check IP and that sensor_receiver.py is running");
      }

      http.end();
    } else {
      Serial.println("[WiFi]   Disconnected - attempting reconnect...");
      WiFi.reconnect();
    }

    Serial.println();
  }
}
