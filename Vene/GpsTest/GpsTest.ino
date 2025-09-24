#include <TinyGPS++.h>

TinyGPSplus gps;

HardwareSerial gpsSerial(2);

struct GPSData
{
  double lat;
  double lon;
  double speed;
  double hdop;
  bool fix;
};

void setup()
{
  Serial.begin(115200);

  gpsSerial.begin(9600, SERIAL_8N1, 5, 18)
}

GPSData updateGPS()
{
  GPSData data = {0, 0, 0, false};

  while(gpsSerial.available() > 0)
  {
    gps.encode(gpsSerial.read());
  }

  if (gps.location.isValid())
  {
    data.lat = gps.location.lat();
    data.lon = gps.location.lng();
    data.speed = gps.speed.kmph();
    data.hdop = gps.hdop.hdop();
    data.fix = true;
  }
  return data
}

void loop()
{
  GPSData currentGPS = updateGPS();
}