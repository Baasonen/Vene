#include <WiFi.h>
#include <WiFiUdp.h>
#include <TinyGPS++.h>

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
  long gpsLat;
  long gpsLon;
  unsigned char battery;
  unsigned char error;
};
#pragma pop

struct GPSDataStruct
{
  double lat;
  double lon;
  float speed;
  float hdop;
  bool fix;
}

ControlPacket inbound;
TelemetryPacket outbound;

unsigned long TXRMillis = 1000.0 / TXRate;
unsigned long lastTelemetryTime = 0;

TinyGPSPlus gps;
HardwareSerial gpsSerial(2);

GPSDataStruct gpsData;

GPSDataStruct getGPS()
{
  GPSDataStruct data = {0, 0, 0, 0, false};
  while(gpsSerial.available() > 0)
  {
      gps.encode(gpsSerial.read());
  }
  if(gps.location.isValid())
  {   
      data.lat = gps.location.lat();
      data.lon = gps.location.lng();
      data.speed = gps.speed.kmph();
      data.hdop = gps.hdop.hdop();
      data.fix = true;
  }
  return data;
}

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

  gpsSerial.begin(9600, SERIAL_8N1, 5, 18);
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

    gpsData = getGPS();

    double t = millis() / 1000.0;
    outbound.mode = MODE;
    outbound.heading = (unsigned short)(sin(t) * 180 + 180);
    outbound.speed = (unsigned short)(sin(t) * 180 + 180);
    outbound.tilt = (unsigned short)(sin(t) * 45 + 45);
    outbound.gpsLat = (long)(gpsData.lat * 100000);
    outbound.gpsLon = (long)(gpsData.lon * 100000);
    outbound.battery = (unsigned char)(gpsData.fix);
    outbound.error = 0;

    udp.beginPacket(lastIP, TXPort);
    udp.write((uint8_t*)&outbound, sizeof(TelemetryPacket));
    udp.endPacket();

    //Serial.println("Telemetry Sent");
  }


  // Logiikka tänne ??
}
