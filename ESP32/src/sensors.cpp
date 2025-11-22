#include "sensors.h"
#include "common.h"
#include <HardwareSerial.h>
#include <math.h>

static TinyGPSPlus gps;
static HardwareSerial gpsSerial(2);
static Adafruit_LIS3MDL lis3;
static bool magAvailable = false;


// Arvot saatu adafruitin kalibraatiotyökalulla
static const float magOffset[2] = {-12.05, -25.96}; // X ja Y offsetit
static const float magSoftIron[2][2] = 
{
    {1.017, -0.108}, // Rivi 0
    {-0.108, 1.006}   // Rivi 1
};


static unsigned char gpsStatus = 2;
double homeLat = 1.0;
double homeLon = 1.0;


void sensorInit()
{
    gpsSerial.begin(9600, SERIAL_8N1, GPSRXPIN, GPSTXPIN);
    if (lis3.begin_I2C(0x1c)) // Estää I2C errorit
    {
        magAvailable = true;
        lis3.setPerformanceMode(LIS3MDL_ULTRAHIGHMODE);
        lis3.setOperationMode(LIS3MDL_CONTINUOUSMODE);
        lis3.setDataRate(LIS3MDL_DATARATE_40_HZ);
        lis3.setRange(LIS3MDL_RANGE_4_GAUSS);
    }
}


GPSData getGPS()
{
    GPSData data = {0, 0, 0, 0, false}; // Pohjusta structi
    while(gpsSerial.available() > 0) gps.encode(gpsSerial.read());
    if(gps.location.isValid())
    {
        data.lat = gps.location.lat();
        data.lon = gps.location.lng();
        data.speed = gps.speed.kmph();
        data.hdop = gps.hdop.hdop();
        data.fix = true;
        if (gps.hdop.hdop() <= 1.3) 
        {   
            // Oikee tapa määrittää RDYFLAG ilman debugmode
            if (!RDYFLAG)
            {
                homeLat = gps.location.lat();
                homeLon = gps.location.lng();
            }
            gpsStatus = 0;
        }
        else {gpsStatus = 1;}
    }
    else {gpsStatus = 2;}
    return data;
}


unsigned char getGPSStatus()
{
    return gpsStatus;
}


float getHeading()
{
    if (!magAvailable) {miscError = 6; return 0.0;} // Tarkista 

    static unsigned long lastMagRead = 0;
    static float lastHeading = 0;

    if (millis() - lastMagRead < 100)
    {
        return lastHeading;
    }

    lastMagRead = millis();

    sensors_event_t event;
    lis3.getEvent(&event);
    
    // Data magnetometriltä
    float magX = event.magnetic.x;
    float magY = event.magnetic.y;

    // Kalibroi (offset ja soft iron)
    float offsetX = magX - magOffset[0];
    float offsetY = magY - magOffset[1];

    float calibratedX = magSoftIron[0][0]* offsetX + magSoftIron[0][1]* offsetY;
    float calibratedY = magSoftIron[1][0]* offsetX + magSoftIron[1][1]* offsetY;

    // Laske suunta asteissa
    float heading = atan2(calibratedY, calibratedX) * 180.0 / M_PI;
    if (heading < 0) heading += 360.0;

    // Deklinaatio  
    float declination = 10.0 + 17.0 / 60.0;  // Otakaari 1   27.10.2025
    float geoHeading = heading + declination;
    if (geoHeading >= 360.0) geoHeading -= 360.0;

    return geoHeading;
}   
