#include <WiFi.h>
#include "esp_wifi.h"
#include <HTTPClient.h>
#include <ArduinoJson.h>

#define DEVICE_ID 1

const char* ssid = "SENORITA";
const char* password = "mohit2402";
const char* serverUrl = "http://10.181.196.173:5000/endpoint";

typedef struct {
  unsigned frame_ctrl:16;
  unsigned duration_id:16;
  uint8_t addr2[6];
  uint8_t addr3[6];
  unsigned seq_ctrl:16;
} wifi_ieee80211_mac_hdr_t;

struct PacketData {
  char mac[18];
  int rssi;
  bool ready;
};

volatile bool packetAvailable = false;
PacketData latestPacket;

unsigned long lastSend = 0;

void sendToBackend(const char* mac, int rssi) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected");
    return;
  }

  esp_wifi_set_promiscuous(false);
  delay(50);

  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_ID;
  doc["mac"] = mac;
  doc["rssi"] = rssi;
  doc["timestamp"] = millis();

  String body;
  serializeJson(doc, body);

  int code = http.POST(body);
  Serial.printf("Sent: %s | RSSI: %d | HTTP: %d\n", mac, rssi, code);

  http.end();

  delay(50);
  esp_wifi_set_promiscuous(true);
}

void snifferCallback(void* buf, wifi_promiscuous_pkt_type_t type) {
  if (type != WIFI_PKT_MGMT && type != WIFI_PKT_DATA) return;

  wifi_promiscuous_pkt_t *pkt = (wifi_promiscuous_pkt_t *)buf;
  const wifi_ieee80211_mac_hdr_t *hdr = (wifi_ieee80211_mac_hdr_t *) pkt->payload;

  int rssi = pkt->rx_ctrl.rssi;
  if (rssi < -85) return;

  char macStr[18];
  sprintf(macStr, "%02X:%02X:%02X:%02X:%02X:%02X",
          hdr->addr2[0], hdr->addr2[1], hdr->addr2[2],
          hdr->addr2[3], hdr->addr2[4], hdr->addr2[5]);

  if (strcmp(macStr, "FF:FF:FF:FF:FF:FF") == 0) return;
  if (strcmp(macStr, "00:00:00:00:00:00") == 0) return;
  if (strcmp(macStr, "01:00:5E:7F:FF:FA") == 0) return;

  Serial.printf("MAC: %s | RSSI: %d\n", macStr, rssi);

  if (!packetAvailable) {
    strncpy(latestPacket.mac, macStr, sizeof(latestPacket.mac));
    latestPacket.mac[17] = '\0';
    latestPacket.rssi = rssi;
    packetAvailable = true;
  }
}

void setup() {
  Serial.begin(115200);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected!");
  Serial.print("ESP IP: ");
  Serial.println(WiFi.localIP());

  esp_wifi_set_promiscuous(true);
  esp_wifi_set_promiscuous_rx_cb(snifferCallback);

  Serial.println("Sniffer started...");
}

void loop() {
  if (packetAvailable && millis() - lastSend > 1000) {
    packetAvailable = false;
    sendToBackend(latestPacket.mac, latestPacket.rssi);
    lastSend = millis();
  }

  delay(10);
}