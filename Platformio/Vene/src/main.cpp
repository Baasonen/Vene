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
#include "navigation.h"
#include "common.h"
#include "mode.h"

// Vcom 3.5
// Vene 4.0

const char* ssid = "VENE";
const char* password = "12345678";

int gpsRxPin = 5; // Pitäis siirtää sensors.cpp kuha (heh) muistaa
int gpsTxPin = 18;

// WIFI asetukset & siihen liittyvät muuttujat
WiFiUDP udp;
const unsigned int RXPort = 4211;
const unsigned int TXPort = 4210;
IPAddress lastIP;
unsigned long TXRate = 10;
unsigned short packetsThisSecond = 0;
unsigned long lastPacketCountTime = 0;
unsigned char packetsPerSecond = 0;

bool AP_ACTIVE = false;

// Muuta virheet yhdeksi 16 bittiseksi luvuksi
unsigned short makeError(unsigned char waypoint, unsigned char gps, unsigned char errors)
  {
    return (waypoint & 0x7F) // Bitit 0-6
       | ((gps & 0x03) << 7) // Bitit 7-8
       | ((errors & 0xFFFF) << 9); // Bitit 9->
  }

ControlPacket inbound;
TelemetryPacket outbound;
WaypointPacket waypointList[MAX_WAYPOINTS];
unsigned char currentWpId = 0;

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



void setup() 
{
  // Käynnistä UART-kanava serial monitorille (vaan debug)
  Serial.begin(115200);
  delay(2000);
  Serial.println("Boot...");
  delay(2000); // Vähän taukoa, muuten wifi ei välttämättä toimi

  // Käynnistä WIFI
  WiFi.softAP(ssid, password);
  udp.begin(RXPort);
  delay(2000);
  Serial.print("VENE started on: ");
  Serial.println(WiFi.softAPIP());

  sensorInit();
  navigationInit();
}

void loop() 
{
  // Normaali ohjauspaketti
  int packetSize = udp.parsePacket();
  if (packetSize == sizeof(ControlPacket)) {
    udp.read((uint8_t*)&inbound, sizeof(ControlPacket)); // Dumppaa koko bufferi suoraan muistiin (huom. kommentti alempana)

    RDYFLAG = (inbound.debugData != 0); // Debuggausta varten, pitäs muistaa (ei tuu tapahtuu) poistaa ku suht valmis
    if (inbound.debugData == 2) targetWp++;
    // Pitäis varmaan tarkistaa et sisältö ok (jos jaksaa...)

    if (udp.remoteIP() != lastIP) {Serial.print("New Connection: "); Serial.println(udp.remoteIP());} // Lisää debuggausta

    lastIP = udp.remoteIP(); // Tallenna IP osoita telemetrian lähetystä varten
    packetsThisSecond++;
  }
  // WP paketti
  else if (packetSize == sizeof(WaypointPacket))
  {
    WaypointPacket wp;
    udp.read((uint8_t*)&wp, sizeof(WaypointPacket));

    if (wp.wpId != currentWpId) // Uus WP sarja, nollaa asetukset
    {
      waypointCount = 0; 
      currentWpId = wp.wpId;
      targetWp = 0;
      waypointUploadComplete = false;

      WaypointPacket homeWp = {0, homeLat, homeLon, wp.wpAmmount, wp.wpId};
      waypointList[waypointCount++] = homeWp;
    }
    
    // Älä ota samoja huomioon uudestaan
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
      
      // Pelkästään debuggausta varten
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

  // Laske pakettia / sekuntti
  if (millis() - lastPacketCountTime >= 1000) 
  {
    lastPacketCountTime = millis();
    packetsPerSecond = packetsThisSecond;
    packetsThisSecond = 0;
  }

  // Tarkista onko gps tarkka
  if (getGPSStatus() == 0 && !RDYFLAG) {RDYFLAG = true;}

  // Päiuvitä gps ja heading
  GPSData gps = getGPS();
  heading = getHeading();

  if (inbound.mode != MODE) {setMode(inbound.mode);}  // Tarvitseeko modia vaihtaa

  switch (MODE)  // Ohjaus riippuen modesta
  {
    // Manuaalinen ohjaus (aika yksinkertanen)
    case 1:
      turnRudder(inbound.rudder);
      setThrottle(inbound.throttle1, inbound.throttle2);
      break;

    // Autopilotti
    case 2: 
    {
      WaypointPacket target = waypointList[targetWp];
      double tLat = target.wpLat / 100000.0;
      double tLon = target.wpLon / 100000.0;

      setThrottle(inbound.lightMode, inbound.lightMode);

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
    // Pelkästään kotisijainnin lähettämistä varten
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
    outbound.error = makeError(targetWp, getGPSStatus(), miscError);
    outbound.pl = packetsPerSecond;

    udp.beginPacket(lastIP, TXPort);
    udp.write((uint8_t*)&outbound, sizeof(TelemetryPacket));
    udp.endPacket();
  }
}
