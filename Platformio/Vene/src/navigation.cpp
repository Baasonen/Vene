#include "navigation.h"
#include <math.h>
#include "sensors.h"
#include <ESP32Servo.h>

const float degToRad = M_PI / 180.0;
const float radToDeg = 180.0 / M_PI;
const float earthRadius = 6371000.0;
static Servo perasinServo;
static const int perasinServoPin = 14;

static Servo motor1;
static Servo motor2;

static const int m1Pin = 25;
static const int m2Pin = 26;

void navigationInit()
{
    perasinServo.attach(perasinServoPin);
    perasinServo.write(90);

    motor1.attach(m1Pin);
    motor2.attach(m2Pin);

    motor1.writeMicroseconds(1500);
    motor2.writeMicroseconds(1500);
}

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

void turnRudder(unsigned char targetAngle)
{
    perasinServo.write(targetAngle);
}

void setThrottle(unsigned char t1, unsigned char t2)
{
    motor1.writeMicroseconds(t1);
    motor2.writeMicroseconds(t2);
}