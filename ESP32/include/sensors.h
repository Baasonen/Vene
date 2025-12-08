#pragma once 

// Sensoridata 

#include <TinyGPS++.h>
#include <Adafruit_LIS3MDL.h>

#define GPSRXPIN 5
#define GPSTXPIN 18

extern double homeLat;
extern double homeLon;
extern bool homeSaved;

struct GPSData
{
    double lat;
    double lon;
    float speed;
    float hdop;
    bool fix;
};

void sensorInit();

GPSData getGPS();
float getHeading();
unsigned char getGPSStatus();
