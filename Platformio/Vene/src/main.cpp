#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h> 
#include <TinyGPS++.h> // Tulkitsee gps moduulilta tulleita NEMA lauseita
#include <ESP32Servo.h> // Sero moottorielle ja peräsimelle
#include <Wire.h> // I2C magnetometrille
#include <Adafruit_LIS3MDL.h> // Magnetometrin kirjasto
#include <math.h> // Kompassilaskuja varten
#include <algorithm> // Min() ja Max()

#include "sensors.h"

// Vcom 3.5
// Vene 4.0

const char* ssid = "VENE";
const char* password = "12345678";

Servo perasinServo;
int perasinServoPin = 14;

Servo motor1;
Servo motor2;

int motor1Pin = 25;
int motor2Pin = 26;

int gpsRxPin = 5;
int gpsTxPin = 18;

// WIFI asetukset
WiFiUDP udp;
const unsigned int RXPort = 4211;
const unsigned int TXPort = 4210;
IPAddress lastIP;
unsigned long TXRate = 4;
unsigned short packetsThisSecond = 0;
unsigned long lastPacketCountTime = 0;
unsigned char packetsPerSecond = 0;

unsigned char MODE = 0;
bool RDYFLAG = false;
bool AP_ACTIVE = false;

#pragma pack(push, 1)  // Estä kääntäjää lisäämästä paddingia
struct ControlPacket 
{
  unsigned char mode;
  unsigned char rudder;
  unsigned char throttle1;
  unsigned char throttle2;
  unsigned char lightMode;
  unsigned char debugData;
  unsigned short timestamp;
};

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

struct WaypointPacket
{
  unsigned char order;
  long wpLat;
  long wpLon;
  unsigned char wpAmmount;
  unsigned char wpId;
};
#pragma pack(pop)

// Virhemuuttujat
unsigned char gpsError = 0;
unsigned char miscError = 0;

// Muuta virheet yhdeksi 16 bittiseksi luvuksi
unsigned short makeError(unsigned char waypoint, unsigned char gps, unsigned char errors)
  {
    return (waypoint & 0x7F) // Bits 0-6
       | ((gps & 0x03) << 7) // Bits 7-8
       | ((errors & 0xFFFF) << 9); // Bits 9->
  }

ControlPacket inbound;
TelemetryPacket outbound;
#define MAX_WAYPOINTS 65
WaypointPacket waypointList[MAX_WAYPOINTS];
unsigned char waypointCount = 0;

unsigned char currentWpId = 0;
unsigned char targetWp = 0;
bool waypointUploadComplete = false;

long homeLat = 1;
long homeLon = 1;

// Telemetrian lähetystaajuuden muutos millisekunneiksi
unsigned long TXRMillis = 1000.0 / TXRate;
unsigned long lastTelemetryTime = 0;

// Gps
TinyGPSPlus gps;
HardwareSerial gpsSerial(2);
float heading = 0;

// Magnetometrin kalibrointimuuttujat
float xmin = 1e6;
float xmax = -1e6;
float ymin = 1e6;
float ymax = -1e6;

Adafruit_LIS3MDL lis3;
bool magAvailable = false;

// Func Dec
void setup();
void loop();
void turnRudder(unsigned char target_angle);

// Funktiot
void steerTo(unsigned short targetHeading)
{
  float Kp = 1.0;
  int error = targetHeading - heading;

  if (error > 180) error -= 360;
  if (error < -180) error += 360;

  float rudderOffset = error * Kp;

  if (rudderOffset > 90.0) rudderOffset = 90.0;
  if (rudderOffset < -90.0) rudderOffset = -90.0; 

  int rudder = 90 + rudderOffset;

  if (rudder > 180) rudder = 180;
  if (rudder < 0) rudder = 0;

  turnRudder(rudder);
}

void turnRudder(unsigned char target_angle)
{
  int Llimit = 10;
  int Ulimit = 170;
  
  if (target_angle < Llimit) {target_angle = Llimit;}
  if (target_angle > Ulimit) {target_angle = Ulimit;}

  perasinServo.write(target_angle);
}

float headingToPoint(double lat1, double lon1, double lat2, double lon2)
{
  float degToRad = PI / 180.0;
  // Kooridinaatit deg -> rad jotta trig. toimii
  // Muutos
  float dLat = (lat2 - lat1) * degToRad;
  float dLon = (lon2 - lon1) * degToRad;

  // Keskiarvo länsi-itä korrektiota varten
  float lat_mean = (lat1 + lat2) * 0.5 * degToRad;

  // Maapallo on pyöreä(kai?), ota huomioon länsi-itä etäisyyden muutos eri korkeusasteilla
  dLon *= cos(lat_mean);

  float hdg = atan2(dLon, dLat) * 180.0 / PI;
  if (hdg < 0) hdg += 360.0;

  return hdg;
}

float distanceToPoint(double lat1, double lon1, double lat2, double lon2)
{
  float degToRad = PI / 180.0;
  float earthRadius = 6371000.0;

  float dLat = (lat2 - lat1) * degToRad;
  float dLon = (lon2 - lon1) * degToRad;

  float lat_mean = (lat1 + lat2) * 0.5 * degToRad;
  
  dLon *= cos(lat_mean);

  return sqrt(dLon * dLon + dLat * dLat) * earthRadius;
}

// Tarkista, onko modin vaihto sallittua
void setMode(unsigned char targetMode)
{
  switch (MODE) 
  {
    case 0:
      if (RDYFLAG) {MODE = 1; miscError = 1;}
      break;
    
    case 1:
      if (targetMode == 2)
      {
        if (waypointUploadComplete && waypointCount > 1)
        {
          MODE = 2;
          targetWp = 1;
          Serial.println("Mode 2");
        }
      }
      if (targetMode == 3) {MODE = 3;}

      if (targetMode == 9) {MODE = 9;}
      break;

    case 2:
      if (targetMode == 1) {MODE = 1;}
      if (targetMode == 3) {MODE = 3;}
      break;

    case 3:
      if (targetMode == 4) {MODE = 1;}
      break;

    case 9:
      MODE = 1;
      break;
  }
}

void setup() 
{
  // Käynnistä UART-kanava serial monitorille (vaan debug)
  Serial.begin(115200);
  delay(4000);
  Serial.println("Boot...");

  // Käynnistä WIFI
  WiFi.softAP(ssid, password);
  udp.begin(RXPort);
  delay(2000);
  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP());

  // Peräsimen servo
  perasinServo.attach(perasinServoPin);
  perasinServo.write(90);

  // Moottorit
  motor1.attach(motor1Pin);
  motor2.attach(motor2Pin);

}

void loop() 
{
  int packetSize = udp.parsePacket();
  if (packetSize == sizeof(ControlPacket)) {
    udp.read((uint8_t*)&inbound, sizeof(ControlPacket)); // Dumppaa koko bufferi suoraan muistiin

    RDYFLAG = (inbound.debugData != 0); 
    if (inbound.debugData == 2) targetWp++;
    // Pitäis varmaan tarkistaa et sisältö ok (jos jaksaa...)

    if (udp.remoteIP() != lastIP) {Serial.print("New Connection: "); Serial.println(udp.remoteIP());}

    lastIP = udp.remoteIP(); // Tallenna IP osoita telemetrian lähetystä varten
    packetsThisSecond++;
  }
  else if (packetSize == sizeof(WaypointPacket))
  {
    WaypointPacket wp;
    udp.read((uint8_t*)&wp, sizeof(WaypointPacket));

    if (wp.wpId != currentWpId)
    {
      waypointCount = 0; 
      currentWpId = wp.wpId;
      targetWp = 0;
      waypointUploadComplete = false;

      WaypointPacket homeWp = {0, homeLat, homeLon, wp.wpAmmount, wp.wpId};
      waypointList[waypointCount++] = homeWp;
    }
    
    // Älä huomioi samoja uudestaan
    bool duplicate = false;
    for (unsigned char i = 0; i < waypointCount; i++)
    {
      if (waypointList[i].wpId == wp.wpId && waypointList[i].order == wp.order)
      {
        duplicate = true;
        break;
      }
    }
    if (!duplicate && waypointCount < MAX_WAYPOINTS)
    {
      waypointList[waypointCount++] = wp;
      
      Serial.print(wp.wpId);
      Serial.print("ID ");
      Serial.print(wp.wpAmmount);
      Serial.print("AMMNT ");
      Serial.print(wp.order);
      Serial.print("ORDER ");
      Serial.print(wp.wpLat, wp.wpLon);
      Serial.println("WP Stored");
    }
    else if (!duplicate) Serial.println("WP Buffer Full");

    // Tarkista onko kaikki vastaanotettu
    unsigned char expected = waypointList[0].wpAmmount;
    unsigned char receivedCount = 0;

    for (unsigned char i = 0; i < waypointCount; i++)
    {
      if (waypointList[i].wpId == currentWpId && waypointList[i].order > 0)
      {
        receivedCount++;
      }
    }

    if (!waypointUploadComplete && receivedCount >= expected)
    {
      waypointUploadComplete = true;
      Serial.println("All WP Received");
    }
  }

  if (millis() - lastPacketCountTime >= 1000) // Laske pakettia / sekuntti
  {
    lastPacketCountTime = millis();
    packetsPerSecond = packetsThisSecond;
    packetsThisSecond = 0;
  }

  GPSData gps = getGPS();
  heading = getHeading();

  if (inbound.mode != MODE) {setMode(inbound.mode);}  // Tarvitseeko modia vaihtaa

  switch (MODE)  // Ohjaus riippuen modesta
  {
    case 1:
      turnRudder(inbound.rudder);
      motor1.writeMicroseconds(1);
      motor2.writeMicroseconds(1);
      break;

    case 2: 
    {
      WaypointPacket target = waypointList[targetWp];
      double tLat = target.wpLat / 100000.0;
      double tLon = target.wpLon / 100000.0;

      if (distanceToPoint(gps.lat, gps.lon, tLat, tLon) < 4.0)
      {
        if((targetWp + 1) < waypointCount) targetWp++;
        else targetWp = 0;
      }
      else
      {
        steerTo(headingToPoint(gps.lat, gps.lon, tLat, tLon));
      }
      break;
    }

    case 9:
      outbound.gpsLat = (long)(homeLat * 100000);
      outbound.gpsLon = (long)(homeLon * 100000);

      udp.beginPacket(lastIP, TXPort);
      udp.write((uint8_t*)&outbound, sizeof(TelemetryPacket));
      udp.endPacket();
      break;
  }

  // Lähetä telemetriaa
  if (lastIP && (millis() - lastTelemetryTime >= TXRMillis))
  {
    lastTelemetryTime = millis();

    double t = millis() / 1000.0;
    outbound.mode = MODE;
    outbound.heading = (unsigned short)(heading);
    outbound.speed = (unsigned char) (gps.speed);
    outbound.gpsLat = (long)(gps.lat * 100000);
    outbound.gpsLon = (long)(gps.lon * 100000);
    outbound.battery = (unsigned char)(gps.fix);
    outbound.error = makeError(targetWp, gpsError, miscError);
    outbound.pl = packetsPerSecond;

    udp.beginPacket(lastIP, TXPort);
    udp.write((uint8_t*)&outbound, sizeof(TelemetryPacket));
    udp.endPacket();

    //Serial.println("Telemetry Sent");
  }
}
