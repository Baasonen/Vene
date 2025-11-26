// Copyright (C) 2025 Henri Paasonen - GPLv3
// See LICENSE for details

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h> 
#include <algorithm> // Min() ja Max()
#include "esp_system.h"
#include "esp_task_wdt.h"

#include "sensors.h"
#include "navigation.h"
#include "common.h"
#include "mode.h"
#include "battery.h"
#include "lights.h"

// Vene 4.1

unsigned long lastLoopTime = 0;
unsigned long loopDuration = 0;

const char* ssid = "VENE";
const char* password = "12345678";

// WIFI asetukset & siihen liittyvät muuttujat
WiFiUDP udp;
const unsigned int RXPort = 4211;
const unsigned int TXPort = 4210;
IPAddress lastIP;
unsigned long TXRate = 8;
unsigned short packetsThisSecond = 0;
unsigned long lastPacketCountTime = 0;
unsigned char packetsPerSecond = 0;

ControlPacket inbound;
TelemetryPacket outbound;
WaypointPacket waypointList[MAX_WAYPOINTS];
unsigned char currentWpId = 0;

// Telemetrian lähetystaajuuden muutos millisekunneiksi
unsigned long TXRMillis = 1000.0 / TXRate;
unsigned long lastTelemetryTime = 0;

unsigned short lastControlTimestamp = 0;
unsigned long lastControlTime = 0;
const unsigned short controlTimeout = 2000;

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

  // 5 sec reset timeout
  esp_task_wdt_init(5, true);
  esp_task_wdt_add(NULL);

  // Käynnistä WIFI
  WiFi.softAP(ssid, password);
  WiFi.setTxPower(WIFI_POWER_19_5dBm);
  udp.begin(RXPort);
  delay(1000);
  Serial.print("VENE started on: ");
  Serial.println(WiFi.softAPIP());

  // common.cpp:n init funktio, listää tänne kaikkien muiden modulien init funktiot
  modulesInit();
}

void loop() 
{
  unsigned long start = micros();
  esp_task_wdt_reset();

  int packetSize = udp.parsePacket();

  if (packetSize > 0)
  {
    // Normaali ohjauspaketti
    if (packetSize == sizeof(ControlPacket)) 
    {
      udp.read((unsigned char*)&inbound, sizeof(ControlPacket));

      RDYFLAG = (inbound.debugData != 0); // Debuggausta varten, pitäs muistaa (ei tuu tapahtuu) poistaa ku suht valmis
      if (inbound.debugData == 2) {targetWp++;}
      if (inbound.timestamp != lastControlTimestamp)
      {
        lastControlTimestamp = inbound.timestamp;
        lastControlTime = millis();
      }

      if (udp.remoteIP() != lastIP) // Lisää debuggausta
      {
        Serial.print("New Connection: "); 
        Serial.println(udp.remoteIP());
      }

      lastIP = udp.remoteIP(); // Tallenna IP osoita telemetrian lähetystä varten
      packetsThisSecond++;
    }

    // WP paketti
    else if (packetSize == sizeof(WaypointPacket))
    {
      WaypointPacket wp;
      udp.read((unsigned char*)&wp, sizeof(WaypointPacket));

      if (wp.wpId != currentWpId) // Uus WP sarja, nollaa asetukset
      {
        waypointCount = 0; 
        currentWpId = wp.wpId;
        targetWp = 0;
        waypointUploadComplete = false;
        WaypointPacket homeWp = {0, (long)homeLat * 100000, (long)homeLon * 100000, wp.wpAmmount, wp.wpId};
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

    // Ei validi paketti, tyhjennä
    else
    {
      int x;
      while ((x = udp.parsePacket()) > 0)
      {
        unsigned char y[256];
        udp.read(y, min(x, 256));
      }
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
  if (getGPSStatus() == 0 && !RDYFLAG) 
  {
    RDYFLAG = true; 
    miscError = 1;
  }

  // Päiuvitä gps
  GPSData gps = getGPS();

  // Modin vaihto tarvittaessa
  if (inbound.mode != MODE) {setMode(inbound.mode);}

  // Ei uusia control packet
  if ((millis() - lastControlTime) > controlTimeout)
  {
    inbound.throttle1 = 100;
    inbound.throttle2 = 100;
    miscError = 3;
    Serial.println(inbound.timestamp);
    setLight(9);
  }
  else if (miscError == 3)
  {
    miscError = 0;
    setLight(MODE);
  }


  // OHJAUS
  switch (MODE)
  {
    // Manuaalinen ohjaus (aika yksinkertanen)
    case 1:
      turnRudder(inbound.rudder);
      setThrottle(inbound.throttle1, inbound.throttle2);
      break;

    // Autopilotti
    case 2: 
    {
      // Tarkista että targetWp on mahdollinen
      if (targetWp >= waypointCount) {targetWp = 0;}
      WaypointPacket target = waypointList[targetWp];
      double tLat = target.wpLat / 100000.0;
      double tLon = target.wpLon / 100000.0;

      setThrottle(inbound.apThrottle, inbound.apThrottle);

      if (distanceToPoint(gps.lat, gps.lon, tLat, tLon) < 3.0)
      {
        if((targetWp + 1) < waypointCount) {targetWp++;}
        else targetWp = 0;
      }
      else
      {
        steerTo(headingToPoint(gps.lat, gps.lon, tLat, tLon));
      }
      break;

    }
    case 3:
      setThrottle(100, 100);
      break;

    // Pelkästään kotisijainnin lähettämistä varten
    case 9:
      outbound.gpsLat = (long)(homeLat * 100000);
      outbound.gpsLon = (long)(homeLon * 100000);

      udp.beginPacket(lastIP, TXPort);
      udp.write((unsigned char*)&outbound, sizeof(TelemetryPacket));
      udp.endPacket();
      break;
  
    default:
    {
      setThrottle(100, 100);
      break;
    }
  }


  // TELEMTRIA
  if ((lastIP != IPAddress()) && (WiFi.softAPgetStationNum() > 0) && (millis() - lastTelemetryTime >= TXRMillis))
  {
    lastTelemetryTime = millis();
    double t = millis() / 1000.0;
    outbound.mode = MODE;
    outbound.heading = (unsigned short)(smoothHeading());
    outbound.speed = (unsigned char) (gps.speed);
    outbound.gpsLat = (long)(gps.lat * 100000);
    outbound.gpsLon = (long)(gps.lon * 100000);
    outbound.battery = (unsigned char)(getBattery());
    outbound.error = makeError(targetWp, getGPSStatus(), miscError);
    outbound.pl = packetsPerSecond;

    udp.beginPacket(lastIP, TXPort);
    udp.write((uint8_t*)&outbound, sizeof(TelemetryPacket));
    udp.endPacket();
  }

  loopDuration = micros() - start;

  static unsigned long lastDebugPrint = 0;
  if (millis() - lastDebugPrint > 1000)
  {
    lastDebugPrint = millis();
    Serial.print("Loop time (microseconds): ");
    Serial.print(loopDuration);
    Serial.print(" (");
    Serial.print(1000000.0  / loopDuration);
    Serial.println(" hz)");
  }
}
