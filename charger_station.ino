/*
 * ESP32 Charger Station Firmware
 * ================================
 * Reads voltage, current, and temperature sensors then
 * POSTs JSON to the Raspberry Pi Flask server every N seconds.
 *
 * Libraries needed in Arduino IDE:
 *   - WiFi          (built-in ESP32)
 *   - HTTPClient    (built-in ESP32)
 *   - ArduinoJson   (install via Library Manager)
 *
 * Wiring (example — adjust pins to your PCB):
 *   Voltage divider  → GPIO 34  (ADC1_CH6)
 *   ACS712 current   → GPIO 35  (ADC1_CH7)
 *   NTC thermistor   → GPIO 32  (ADC1_CH4)
 *   Status LED       → GPIO 2
 *
 * HOW VOLTAGE IS MEASURED:
 *   Use a resistor divider to step the charger bus voltage down to 0-3.3V.
 *   Example for a 48 V nominal bus:
 *     R1 = 100kΩ (top), R2 = 10kΩ (bottom)
 *     Vout = Vin × R2/(R1+R2) → 48V × 0.0909 = 4.36 V  ← too high for 3.3V ADC
 *     Use R1=47kΩ, R2=3.3kΩ → scale factor = 15.24
 *   Adjust VOLTAGE_SCALE below to match YOUR divider.
 *
 * HOW CURRENT IS MEASURED:
 *   ACS712-20A: sensitivity = 100 mV/A, zero = Vcc/2 (1.65V on 3.3V supply)
 *   Adjust ACS_SENSITIVITY and ACS_ZERO_VOLTAGE below.
 *
 * HOW TEMPERATURE IS MEASURED:
 *   10 kΩ NTC thermistor in series with a 10 kΩ pull-up to 3.3V.
 *   Uses Steinhart-Hart simplified (B-coefficient method).
 *   Adjust THERMISTOR_B and THERMISTOR_NOMINAL to match your part.
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ── Configuration — edit these ───────────────────────────────────────────────
const char* WIFI_SSID      = "YOUR_WIFI_SSID";
const char* WIFI_PASS      = "YOUR_WIFI_PASSWORD";
const char* PI_SERVER_URL  = "http://192.168.1.50:5000/api/charger";
const char* STATION_ID     = "CS-01";          // unique ID for this unit
const int   POST_INTERVAL_MS = 5000;           // 5 seconds

// ── Pin assignments ───────────────────────────────────────────────────────────
const int PIN_VOLTAGE  = 34;
const int PIN_CURRENT  = 35;
const int PIN_TEMP     = 32;
const int PIN_LED      = 2;

// ── Calibration ───────────────────────────────────────────────────────────────
const float VOLTAGE_SCALE      = 15.24f;   // ADC reading × scale = real bus voltage
const float ACS_SENSITIVITY    = 0.100f;   // V per A  (ACS712-20A = 100 mV/A)
const float ACS_ZERO_VOLTAGE   = 1.65f;    // V when current = 0  (Vcc/2)
const float ADC_VREF           = 3.3f;
const int   ADC_RESOLUTION     = 4095;
const float THERMISTOR_B       = 3950.0f;  // Beta coefficient of your NTC
const float THERMISTOR_NOMINAL = 10000.0f; // Resistance at 25°C
const float TEMP_NOMINAL       = 25.0f;    // Reference temperature (°C)
const float SERIES_RESISTOR    = 10000.0f; // Pull-up resistor value (Ω)

// ── Charge detection thresholds ───────────────────────────────────────────────
const float CURRENT_CHARGE_THRESHOLD = 0.5f;  // A — above this = "charging"
const float FAULT_VOLTAGE_MIN        = 20.0f; // V — below this = "fault"
const float FAULT_VOLTAGE_MAX        = 60.0f; // V — above this = "fault"
const float FAULT_TEMP_MAX           = 70.0f; // °C — above this = "fault"

// ── Globals ───────────────────────────────────────────────────────────────────
unsigned long lastPost = 0;

// ─────────────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);

  analogReadResolution(12);      // ESP32 has 12-bit ADC

  Serial.printf("[%s] Connecting to WiFi: %s\n", STATION_ID, WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.printf("\n[%s] Connected. IP: %s\n", STATION_ID, WiFi.localIP().toString().c_str());
  digitalWrite(PIN_LED, HIGH);
}

// ─────────────────────────────────────────────────────────────────────────────
void loop() {
  unsigned long now = millis();
  if (now - lastPost >= POST_INTERVAL_MS) {
    lastPost = now;

    float voltage     = readVoltage();
    float current     = readCurrent();
    float temperature = readTemperature();
    String status     = determineStatus(voltage, current, temperature);

    Serial.printf("[%s] V=%.2fV  I=%.2fA  T=%.1f°C  Status=%s\n",
                  STATION_ID, voltage, current, temperature, status.c_str());

    postToServer(voltage, current, temperature, status);
  }
}

// ── Sensor reading functions ──────────────────────────────────────────────────

float readVoltage() {
  // Average 16 samples to reduce noise
  long sum = 0;
  for (int i = 0; i < 16; i++) sum += analogRead(PIN_VOLTAGE);
  float adcVoltage = (sum / 16.0f) * ADC_VREF / ADC_RESOLUTION;
  return adcVoltage * VOLTAGE_SCALE;
}

float readCurrent() {
  long sum = 0;
  for (int i = 0; i < 16; i++) sum += analogRead(PIN_CURRENT);
  float adcVoltage = (sum / 16.0f) * ADC_VREF / ADC_RESOLUTION;
  float current = (adcVoltage - ACS_ZERO_VOLTAGE) / ACS_SENSITIVITY;
  return max(0.0f, current);   // clamp negative noise to 0
}

float readTemperature() {
  long sum = 0;
  for (int i = 0; i < 16; i++) sum += analogRead(PIN_TEMP);
  float adcValue = sum / 16.0f;
  if (adcValue <= 0 || adcValue >= ADC_RESOLUTION) return -99.0f;  // open/short
  float resistance = SERIES_RESISTOR * (ADC_RESOLUTION / adcValue - 1.0f);
  // Steinhart-Hart B-coefficient equation
  float steinhart = resistance / THERMISTOR_NOMINAL;
  steinhart = log(steinhart);
  steinhart /= THERMISTOR_B;
  steinhart += 1.0f / (TEMP_NOMINAL + 273.15f);
  return (1.0f / steinhart) - 273.15f;
}

// ── Status logic ──────────────────────────────────────────────────────────────

String determineStatus(float v, float i, float t) {
  if (v < FAULT_VOLTAGE_MIN || v > FAULT_VOLTAGE_MAX || t > FAULT_TEMP_MAX)
    return "fault";
  if (i > CURRENT_CHARGE_THRESHOLD)
    return "charging";
  return "idle";
}

// ── HTTP POST ─────────────────────────────────────────────────────────────────

void postToServer(float voltage, float current, float temperature, String status) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Not connected, skipping POST");
    return;
  }

  StaticJsonDocument<256> doc;
  doc["station_id"]  = STATION_ID;
  doc["voltage"]     = serialized(String(voltage, 2));
  doc["current"]     = serialized(String(current, 2));
  doc["temperature"] = serialized(String(temperature, 1));
  doc["status"]      = status;

  String body;
  serializeJson(doc, body);

  HTTPClient http;
  http.begin(PI_SERVER_URL);
  http.addHeader("Content-Type", "application/json");

  int httpCode = http.POST(body);
  if (httpCode == 200) {
    digitalWrite(PIN_LED, HIGH);
  } else {
    Serial.printf("[HTTP] POST failed, code: %d\n", httpCode);
    // Blink LED to indicate error
    for (int i = 0; i < 3; i++) {
      digitalWrite(PIN_LED, LOW);  delay(100);
      digitalWrite(PIN_LED, HIGH); delay(100);
    }
  }
  http.end();
}
