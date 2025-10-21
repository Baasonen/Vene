#include "navigation.h"
#include <math.h>
#include "sensors.h"

const float degToRad = M_PI / 180.0;
const float radToDeg = 180.0 / M_PI;
const float earthRadius = 6371000.0;

float distanceToPoint(double lat1, double lon1, double lat2, double lon2)
{
    float dLat = (lat2 - lat1) * degToRad;
    float dLon = (lon2 - lon1) * degToRad;

    float latMean = (lat1 + lat2) * 0.5 * degToRad;

    dLon *= cos(latMean);

    return sqrt(dLon * dLon + dLat * dLat) * earthRadius;
}

float headingToPoint(double lat1, double lon1, double lat2, double lon2)
{
    float dLat = (lat2 - lat1) * degToRad;
    float dLon = (lon2 - lon1) * degToRad;

    float latMean = (lat1 + lat2) * 0.5 * degToRad;

    dLon *= cos(latMean);

    float heading = atan2(dLon, dLat) * radToDeg;
    if (heading < 0) {heading += 360.0;}

    return heading;
}

void steerTo(unsigned short targetHeading)
{
    float Kp = 1.0;
    int error = targetHeading - getHeading();
}