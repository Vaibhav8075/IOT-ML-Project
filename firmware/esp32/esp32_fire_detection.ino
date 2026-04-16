// ============================================================
// Fire Detection System - ESP32 Sender for Flask ML Receiver
// Sends live sensor data to sensor_receiver.py every 2 seconds.
//
// Board        : ESP32 DevKit V1
// PIR (HC-SR501)        -> GPIO 27  (digital)
// LDR (LM393 AO)        -> GPIO 34  (analog)
// MQ-7 CO (AO)          -> GPIO 35  (analog)
// Flame Sensor D1       -> GPIO 26  (digital, active LOW)
// DHT22 (AM2302)        -> GPIO 14  (data)
// ============================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <time.h>
#include <math.h>
#include "DHT.h"

// ---- Wi-Fi / backend config --------------------------------
const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* DEVICE_ID = "esp32_001";
const char* BACKEND_URL = "http://192.168.137.1:5000/telemetry";

// ---- NTP config --------------------------------------------
const long GMT_OFFSET_SEC = 19800;  // IST = UTC+5:30
const int DAYLIGHT_OFFSET_SEC = 0;

// ---- Pin definitions ---------------------------------------
#define PIR_PIN    27
#define LDR_PIN    34
#define MQ7_PIN    35
#define FLAME_PIN  26
#define DHT_PIN    14

// ---- DHT setup ---------------------------------------------
#define DHT_TYPE   DHT22
DHT dht(DHT_PIN, DHT_TYPE);

// ---- Timing ------------------------------------------------
#define INTERVAL_MS     2000UL
#define MQ7_WARMUP_MS  90000UL

unsigned long lastSend = 0;
unsigned long startTime = 0;

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("Wi-Fi connected. IP: ");
  Serial.println(WiFi.localIP());
}

void initTime() {
  configTime(GMT_OFFSET_SEC, DAYLIGHT_OFFSET_SEC, "pool.ntp.org", "time.nist.gov");
  Serial.print("Syncing NTP time");

  struct tm timeInfo;
  int attempts = 0;
  while (!getLocalTime(&timeInfo) && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  Serial.println();
  if (attempts < 20) {
    Serial.println("NTP time synced.");
  } else {
    Serial.println("NTP sync failed. Timestamps may fall back to uptime.");
  }
}

String isoTimestamp() {
  struct tm timeInfo;
  if (getLocalTime(&timeInfo)) {
    char buffer[32];
    strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &timeInfo);
    return String(buffer);
  }

  unsigned long seconds = millis() / 1000;
  return "1970-01-01T00:00:" + String(seconds) + "Z";
}

float computeLDRFlicker() {
  const int sampleCount = 10;
  float samples[sampleCount];
  float sum = 0.0;

  for (int i = 0; i < sampleCount; i++) {
    samples[i] = analogRead(LDR_PIN);
    sum += samples[i];
    delay(50);
  }

  float mean = sum / sampleCount;
  float varianceSum = 0.0;
  for (int i = 0; i < sampleCount; i++) {
    float delta = samples[i] - mean;
    varianceSum += delta * delta;
  }

  return sqrt(varianceSum / sampleCount);
}

void sendTelemetry(
  float temperature,
  float humidity,
  int coAdc,
  int ldrAdc,
  float ldrFlicker,
  int flame,
  int motion,
  bool mq7Warmed
) {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  HTTPClient http;
  http.begin(BACKEND_URL);
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<384> doc;
  doc["device_id"] = DEVICE_ID;
  doc["timestamp"] = isoTimestamp();
  doc["temperature"] = isnan(temperature) ? 0.0 : temperature;
  doc["humidity"] = isnan(humidity) ? 0.0 : humidity;
  doc["co_adc"] = coAdc;
  doc["ldr_adc"] = ldrAdc;
  doc["ldr_flicker"] = ldrFlicker;
  doc["flame"] = flame;
  doc["motion"] = motion;
  doc["mq7_warmed"] = mq7Warmed;

  String payload;
  serializeJson(doc, payload);

  int statusCode = http.POST(payload);
  String response = http.getString();

  Serial.println("--------------------------------------------");
  Serial.println("[POST] Payload sent to Flask receiver");
  Serial.print("[POST] Status code : ");
  Serial.println(statusCode);
  Serial.print("[POST] Response    : ");
  Serial.println(response);

  http.end();
}

void setup() {
  Serial.begin(115200);
  delay(300);

  pinMode(PIR_PIN, INPUT);
  pinMode(FLAME_PIN, INPUT);
  pinMode(LDR_PIN, INPUT);
  pinMode(MQ7_PIN, INPUT);

  dht.begin();
  startTime = millis();

  Serial.println("============================================");
  Serial.println("  ESP32 Fire Detection Sender");
  Serial.println("  Target: Flask ML receiver on port 5000");
  Serial.println("============================================");

  connectWiFi();
  initTime();
}

void loop() {
  unsigned long now = millis();
  if (now - lastSend < INTERVAL_MS) {
    return;
  }
  lastSend = now;

  int motion = digitalRead(PIR_PIN) == HIGH ? 1 : 0;
  int ldrAdc = analogRead(LDR_PIN);
  int coAdc = analogRead(MQ7_PIN);
  int flame = digitalRead(FLAME_PIN) == LOW ? 1 : 0;

  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  bool mq7Warmed = (now - startTime) >= MQ7_WARMUP_MS;
  float ldrFlicker = computeLDRFlicker();

  Serial.println("--------------------------------------------");
  Serial.print("[PIR] Motion      : ");
  Serial.println(motion ? "DETECTED" : "none");

  Serial.print("[LDR] Raw ADC     : ");
  Serial.println(ldrAdc);

  Serial.print("[LDR] Flicker SD  : ");
  Serial.println(ldrFlicker, 1);

  Serial.print("[MQ7] Raw ADC     : ");
  Serial.print(coAdc);
  Serial.print("  ");
  Serial.println(mq7Warmed ? "READY" : "WARMING UP");

  Serial.print("[FLAME] Status    : ");
  Serial.println(flame ? "DETECTED" : "none");

  Serial.print("[DHT22] Temp/Hum  : ");
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("READ ERROR");
  } else {
    Serial.print(temperature, 1);
    Serial.print(" C / ");
    Serial.print(humidity, 1);
    Serial.println(" %");
  }

  sendTelemetry(
    temperature,
    humidity,
    coAdc,
    ldrAdc,
    ldrFlicker,
    flame,
    motion,
    mq7Warmed
  );
}
