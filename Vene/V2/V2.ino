#include <WiFi.h>
#include <WiFiUdp.h>

// Use with vcom 2.0

const char* ssid = "VENE";
const char* password = "1234";


WiFiUDP udp;
const unsigned int RXPort = 4211;
const unsigned int TXPort = 4210;
IPAddress lastIP;

unsigned long TXRate = 1;

// Incomming Packets BhBBBh
// Outgoing Packets BhhhBBB

#pragma pack(push, 1)
struct Control_Packet 
{
  unsigned char mode;
  unsigned short int heading;
  unsigned char throttle1;
  unsigned char throttle2;
  unsigned char lightMode;
  unsigned short int timestamp;
};
#pragma pop

#pragma pack(push, 1)
struct Telemetry_packet
{
  unsigned char mode;
  unsigned short int heading;
  unsigned char speed;
  unsigned char tilt;
  unsigned short int gpsLat;
  unsigned short int gpsLon;
  unsigned char battery;
  unsigned char error;
};
#pragma pop

Control_Packet inbound;
Telemetry_packet outbound;

unsigned long TXRMillis = 1000.0 / TXRate;
unsigned long lastTelemetryTime = 0;

void setup() 
{
  Serial.begin(115200);
  delay(1000);

  WiFi.softAP(ssid, password);
  Serial.println("ESP32 AP Started");
  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP());

  udp.begin(RXPort);
  Serial.print("Listening for UDP packets on port ");
  Serial.println(RXPort);
}

void loop() 
{
  // Check for inbound packet
  int packetSize = udp.parsePacket();
  if (packetSize == sizeof(Control_Packet)) {
    udp.read((uint8_t*)&inbound, sizeof(Control_Packet)); // directly cast buffer to struct

    lastIP = udp.remoteIP(); // Save sender ip

    Serial.println("Mode: "); Serial.print(inbound.mode);
    Serial.print(" | Steering: "); Serial.print(inbound.heading);
    Serial.print(" | Throttle1: "); Serial.print(inbound.throttle1);
    //Serial.print(" | Throttle2: "); Serial.print(inbound.throttle2);
    //Serial.print(" | Timestamp: "); Serial.println(inbound.timestamp);
  }

  // Send telemetry
  if (lastIP && (millis() - lastTelemetryTime >= TXRMillis))
  {
    lastTelemetryTime = millis();

    double t = millis() / 1000.0;
    outbound.mode = inbound.mode;
    outbound.heading = (unsigned short)(sin(t) * 180 + 180);
    outbound.speed = (unsigned short)(abs(sin(t)) * 100);
    outbound.tilt = (unsigned short)(sin(t) * 45 + 45);
    outbound.gpsLat = 1111;
    outbound.gpsLon = 2222;
    outbound.battery = 50;
    outbound.error = 0;

    udp.beginPacket(lastIP, TXPort);
    udp.write((uint8_t*)&outbound, sizeof(Telemetry_packet));
    udp.endPacket();

    //Serial.println("Telemetry Sent");
  }
}
