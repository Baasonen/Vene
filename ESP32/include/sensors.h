#pragma once // Uuu opin uuden asian
// #ifndef SENSORS_H
// #define SENSORS_h

// Sensorit ja niihin liittyvät funktiot

#include <TinyGPS++.h>
#include <Adafruit_LIS3MDL.h>

#define GPSRXPIN 5
#define GPSTXPIN 18

extern double homeLat;
extern double homeLon;

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

// #endif