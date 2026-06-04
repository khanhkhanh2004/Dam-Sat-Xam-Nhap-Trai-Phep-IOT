/*
 * esp8266_alarm.ino
 * Firmware ESP8266 NodeMCU - Còi báo động xâm nhập YOLOv5
 *
 * API:
 *   GET /                  -> kiểm tra ESP8266
 *   GET /alarm             -> bật còi 3 giây
 *   GET /alarm?duration=5  -> bật còi 5 giây
 *
 * Kết nối:
 *   D5  -> chân (+) buzzer
 *   GND -> chân (-) buzzer
 */

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

// ===== WIFI =====
const char* WIFI_SSID = "Khanh";
const char* WIFI_PASSWORD = "88888888";

// ===== BUZZER =====
#define BUZZER_PIN D5

// Nếu buzzer của bạn là passive mà digitalWrite không kêu,
// đổi dòng dưới thành true
bool USE_TONE = false;

// ===== SERVER =====
ESP8266WebServer server(80);

// ===== TRẠNG THÁI CÒI =====
bool buzzerActive = false;
unsigned long buzzerEndTime = 0;

// ============================================================
// BẬT / TẮT CÒI
// ============================================================
void buzzerOn() {
  if (USE_TONE) {
    tone(BUZZER_PIN, 1000);
  } else {
    digitalWrite(BUZZER_PIN, HIGH);
  }
}

void buzzerOff() {
  if (USE_TONE) {
    noTone(BUZZER_PIN);
  } else {
    digitalWrite(BUZZER_PIN, LOW);
  }
}

// ============================================================
// ROUTE: /
// ============================================================
void handleRoot() {
  String response = "";
  response += "ESP8266 Alarm Ready\n";
  response += "IP: ";
  response += WiFi.localIP().toString();
  response += "\n";
  response += "API: /alarm?duration=3\n";
  response += "Status: ";
  response += buzzerActive ? "ALARM ACTIVE" : "STANDBY";

  server.send(200, "text/plain", response);

  Serial.println("[HTTP] GET /");
}

// ============================================================
// ROUTE: /alarm
// ============================================================
void handleAlarm() {
  int duration = 3;

  if (server.hasArg("duration")) {
    duration = server.arg("duration").toInt();
  }

  if (duration < 1) duration = 1;
  if (duration > 30) duration = 30;

  Serial.print("[ALARM] Bat coi trong ");
  Serial.print(duration);
  Serial.println(" giay");

  buzzerOn();

  buzzerActive = true;
  buzzerEndTime = millis() + duration * 1000UL;

  String json = "{";
  json += "\"status\":\"ok\",";
  json += "\"message\":\"alarm_on\",";
  json += "\"duration\":";
  json += duration;
  json += ",\"ip\":\"";
  json += WiFi.localIP().toString();
  json += "\"";
  json += "}";

  server.send(200, "application/json", json);
}

// ============================================================
// ROUTE: 404
// ============================================================
void handleNotFound() {
  server.send(404, "text/plain", "404 Not Found. Use /alarm?duration=3");
}

// ============================================================
// SETUP
// ============================================================
void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(BUZZER_PIN, OUTPUT);
  buzzerOff();

  Serial.println();
  Serial.println("========================================");
  Serial.println(" ESP8266 IOT ALARM - YOLOv5 INTRUSION");
  Serial.println("========================================");

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("[WIFI] Dang ket noi toi: ");
  Serial.println(WIFI_SSID);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("[WIFI] Ket noi thanh cong!");
  Serial.print("[WIFI] IP cua ESP8266: ");
  Serial.println(WiFi.localIP());

  server.on("/", handleRoot);
  server.on("/alarm", handleAlarm);
  server.onNotFound(handleNotFound);

  server.begin();

  Serial.println("[SERVER] HTTP server da san sang.");
  Serial.println("[TEST] Mo trinh duyet va nhap:");
  Serial.print("       http://");
  Serial.print(WiFi.localIP());
  Serial.println("/alarm?duration=3");
  Serial.println("========================================");
}

// ============================================================
// LOOP
// ============================================================
void loop() {
  server.handleClient();

  if (buzzerActive && millis() >= buzzerEndTime) {
    buzzerOff();
    buzzerActive = false;
    Serial.println("[ALARM] Da tat coi.");
  }
}