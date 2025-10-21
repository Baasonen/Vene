#pragma once // Uuu opin uuden asian
// #ifndef SENSORS_H
// #define SENSORS_h

#include <TinyGPS++.h>
#include <Adafruit_LIS3MDL.h>

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