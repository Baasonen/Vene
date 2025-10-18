#include "sensors.h"
#include <HardwareSerial.h>
#include <math.h>

static TinyGPSPlus gps;
static HardwareSerial gpsSerial(2);
static Adafruit_LIS3MDL lis3;
static bool magAvailable = false;
static float xmin = 1e6;
static float xmax = -1e6;
static float ymin = 1e6;
static float ymax = -1e6;

void sensorInit()
{
    gpsSerial.begin(9600, SERIAL_8N1, 5, 18);

    if (lis3.begin_I2C(0x1c))
    {
        magAvailable = true;
        lis3.setPerformanceMode(LIS3MDL_ULTRAHIGHMODE);
        lis3.setOperationMode(LIS3MDL_CONTINUOUSMODE);
        lis3.setDataRate(LIS3MDL_DATARATE_80_HZ);
        lis3.setRange(LIS3MDL_RANGE_4_GAUSS);
    }
}

GPSData getGPS()
{
    GPSData data = {0, 0, 0, 0, false};
    while(gpsSerial.available() > 0) gps.encode(gpsSerial.read());

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

float getHeading()
{
    // Palauta 0 jos magnetometriä ei ole (debuggausta varten)
    if (!magAvailable) {return 0.0;}

    sensors_event_t event;
    lis3.getEvent(&event);

    float x = event.magnetic.x;
    float y = event.magnetic.y;

    // Päivitä maksimit
    xmin = min(xmin, x);
    xmax = max(xmax, x);
    ymin = min(ymin, y);
    ymax = max(ymax, y);

    // Laske keskiarvo tulosten skaalausta varten
    float xof = (xmin + xmax) / 2;
    float yof = (ymin + ymax) / 2;

    // Skaalaa tulokset 
    x -= xof;
    y -= yof;

    // Laske suunta ja muuta asteiksi
    float heading = atan2(y, x) * 180 / M_PI;
    // Muuta -180 ... 180 -> 0 ... 360
    if (heading < 0) {heading += 360.0;}
    
    // Laske geograafinen suunta 
    // Deklinaatio, Otakaari 1, 2.10.2025 
    float declination = 10.0 + 17.0 / 60.0;  
    float geo_heading = heading + declination;
    if (geo_heading >= 360.0) {geo_heading -= 360.0;}

    return geo_heading;
}