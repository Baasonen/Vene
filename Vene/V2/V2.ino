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

unsigned char MODE = 0;
// Incomming Packets BhBBBh
// Outgoing Packets BhhhBBB

#pragma pack(push, 1)
struct ControlPacket 
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
struct TelemetryPacket
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

ControlPacket inbound;
TelemetryPacket outbound;

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
  if (packetSize == sizeof(ControlPacket)) {
    udp.read((uint8_t*)&inbound, sizeof(ControlPacket)); // directly cast buffer to struct

    lastIP = udp.remoteIP(); // Save sender ip  
  }

  // Send telemetry
  if (lastIP && (millis() - lastTelemetryTime >= TXRMillis))
  {
    lastTelemetryTime = millis();

    double t = millis() / 1000.0;
    outbound.mode = MODE;
    outbound.heading = (unsigned short)(sin(t) * 180 + 180);
    outbound.speed = (unsigned short)(sin(t) * 180 + 180);
    outbound.tilt = (unsigned short)(sin(t) * 45 + 45);
    outbound.gpsLat = 1111;
    outbound.gpsLon = 2222;
    outbound.battery = 50;
    outbound.error = 0;

    udp.beginPacket(lastIP, TXPort);
    udp.write((uint8_t*)&outbound, sizeof(TelemetryPacket));
    udp.endPacket();

    //Serial.println("Telemetry Sent");
  }


  // Logiikka tänne ??
}
