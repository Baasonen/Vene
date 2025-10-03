#include <WiFi.h>
#include <WiFiUdp.h>
#include <TinyGPS++.h>
#include <ESP32Servo.h>

// Use with vcom 3.0

const char* ssid = "VENE";
const char* password = "1234";

Servo perasinServo;
int perasinServoPin = 16;

// WIfi config
WiFiUDP udp;
const unsigned int RXPort = 4211;
const unsigned int TXPort = 4210;
IPAddress lastIP;
unsigned long TXRate = 1;
unsigned short packetsReceived = 0;
unsigned long lastPacketTimestamp = 0;

unsigned char MODE = 0;
bool RDYFLAG = false;
// Incomming Packets BhBBBh
// Outgoing Packets BhhhBBB

#pragma pack(push, 1)
struct ControlPacket 
{
  unsigned char mode;
  unsigned char rudder;
  unsigned char throttle1;
  unsigned char throttle2;
  unsigned char lightMode;
  unsigned char controlTxRate;
  unsigned short timestamp;
};
#pragma pop

#pragma pack(push, 1)
struct TelemetryPacket
{
    unsigned char mode;
    unsigned char battery;
    unsigned char pl;
    unsigned char speed;
    unsigned short heading;
    unsigned short error;
    long gpsLat;
    long gpsLon;
};
#pragma pop

struct GPSDataStruct
{
  double lat;
  double lon;
  float speed;
  float hdop;
  bool fix;
};

// Pack errors to long
unsigned long makeError(unsigned char waypoint, unsigned char gps, unsigned short errors)
  {
    return (waypoint & 0x7F) // Bitit 0-6
       | ((gps & 0x03) << 7) // Bitit 7-8
       | ((errors & 0xFFFF) << 9); // Bitit 9->
  }

ControlPacket inbound;
TelemetryPacket outbound;

unsigned long TXRMillis = 1000.0 / TXRate;
unsigned long lastTelemetryTime = 0;

TinyGPSPlus gps;
HardwareSerial gpsSerial(2);
GPSDataStruct gpsData;

// Functions

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
  if (gps.hdop.hdop() >= 1.0)
  {
    RDYFLAG = true;
  }

  return data;
}

void setMode(unsigned char targetMode)
{
  switch (MODE) {
    case 0:
      if (RDYFLAG ) {MODE = 1;}
      break;
    
    case 1:
      if (targetMode == 2) {MODE = 2;}
      if (targetMode == 3) {MODE = 3;}

    case 2:
      if (targetMode == 1) {MODE = 1;}
      if (targetMode == 3) {MODE = 3;}

    case 3:
      if (targetMode == 4) {MODE = 1;}
  }
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

  perasinServo.attach(perasinServoPin);
  perasinServo.write(90);
}

void loop() 
{
  // Check for inbound packet
  int packetSize = udp.parsePacket();
  if (packetSize == sizeof(ControlPacket)) {
    udp.read((uint8_t*)&inbound, sizeof(ControlPacket)); // directly cast buffer to struct

    if (inbound.rudder == 180) RDYFLAG = true;

    lastIP = udp.remoteIP(); // Save sender ip  
    if (lastPacketTimestamp != inbound.timestamp)
    {
      lastPacketTimestamp = inbound.timestamp;
      packetsReceived = 0;
    }
    else packetsReceived++;
  }

  if (inbound.mode != MODE) {setMode(inbound.mode);}

  switch (MODE) {
    case 1:
      perasinServo.write(inbound.rudder);
      break;
  }

  // Send telemetry
  if (lastIP && (millis() - lastTelemetryTime >= TXRMillis))
  {
    lastTelemetryTime = millis();

    gpsData = getGPS();

    double t = millis() / 1000.0;
    outbound.mode = MODE;
    outbound.heading = (unsigned short)(sin(t) * 180 + 180);
    outbound.speed = inbound.throttle1;
    outbound.gpsLat = (long)(gpsData.lat * 100000);
    outbound.gpsLon = (long)(gpsData.lon * 100000);
    outbound.battery = (unsigned char)(gpsData.fix);
    outbound.error = makeError(0, 0, inbound.rudder);
    float pLoss = (float) packetsReceived / (float) inbound.controlTxRate;
    outbound.pl = (unsigned char)(pLoss * 100);

    udp.beginPacket(lastIP, TXPort);
    udp.write((uint8_t*)&outbound, sizeof(TelemetryPacket));
    udp.endPacket();

    //Serial.println("Telemetry Sent");
  }
}
