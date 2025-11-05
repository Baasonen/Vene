#pragma once

// Ohjauslogiikka

#define M1PIN 25
#define M2PIN 26
#define PSERVOPIN 14
#define EARTHRADIUS 6371000.0

void navigationInit();
float distanceToPoint(double lat1, double lon1, double lat2, double lon2);
float headingToPoint(double lat1, double lon1, double lat2, double lon2);
void steerTo(unsigned short targetHeading);
void turnRudder(unsigned char targetAngle);
void setThrottle(unsigned char t1, unsigned char t2);