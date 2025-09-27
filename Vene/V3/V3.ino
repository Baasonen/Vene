#include <Wire.h>
#include <Adafruit_LIS3MDL.h>
#include <math.h>
#include <TinyGPS++.h>

Adafruit_LIS3MDL lis3;
TinyGPSplus gps;

struct magData
{
    float xmin = 0;
    float ymin = 0;
    float xmax = 0;
    float ymax = 0;

    float xof, yof;;
};

struct GPSData
{
    double lat;
    double lon;
    float speed;
    float hdop;
    bool fix;
};

magData magData;
GPSData GPSData;
float heading;

float getHDG()
{
    sensors_event_t event;
    lis3.getEvent(&event);

    float x = event.magnetic.x;
    float y = event.magnetic.y;

    magData.xmin = min(xmin, x);
    magData.ymin = min(ymin, y);
    magData.xmax = max(xmax, x);
    magData.ymax = max(ymax, y);

    magData.xof(xmin + xmax) / 2;
    magData.yof(ymin + ymax) / 2;

    x -= xof;
    y -= yof;

    float hdg = atan2(y, x) * 180 / PI;
    if (hdg < 0) hdg += 360;

    return hdg
}

GPSData getGPS()
{
    GPSData data = {0, 0, 0, 0, false};

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
    return data
}

void setup()
{
    Serial.begin(115200);

    if (!lis3.begin_I2C(0x1c))
    {
        Serial.println("No Mag");
    }

    // Magnetometer Config
    lis3.setPerformanceMode(LIS3MDL_ULTRAHIGHMODE);
    lis3.setOperationMode(LIS3MDL_CONTINUOUSMODE);
    lis3.setDataRate(LIS3MDL_DATARATE_80_HZ);
    lis3.setRange(LIS3MDL_RANGE_4_GAUSS);

    // GPS UART
    gpsSerial.begin(9600, SERIAL_8N1, 5, 18);
}

void loop()
{
    heading = getHDG();
    GPSData = getGPS();
}