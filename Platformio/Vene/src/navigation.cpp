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

    float latMean = (lat1 + lat2) * 0.5 * degToRad; // About tällä korkeusasteella ollaan

    // Maapallo on (kai) pyöreä, ota huomioon pituusasteiden välisen matkan ero eri korkeusasteilla
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
    // Atan2 => -pi ... pi => -180 ... 180 joka muutetaan 0 ... 360
    if (heading < 0) {heading += 360.0;}

    return heading;
}

float smoothHeading()
{
    static float smoothedHeading = 0.0; // HUOM! static
    static bool headingInit = false;

    // a => 0 ... 1,  pieni a pehmeempi mutta reagoi hitaammin
    float a = 0.1; 

    float heading = getHeading();

    if (!headingInit)  // Ei vielä edellistä arvoa
    {
        smoothedHeading = heading;
        headingInit = true;
    }
    else
    {
        float dif = heading - smoothedHeading;
        if (dif > 180) {dif -= 360;}
        if (dif < -180) {dif += 360;}

        smoothedHeading += dif * a;

        if (smoothedHeading < 0) {smoothedHeading += 360;}
        if (smoothedHeading >= 360) {smoothedHeading -= 360;} 
    }

    return smoothedHeading;
}

void steerTo(unsigned short targetHeading)
{
    float Kp = 1.0;
    float deadzone = 5.0;

    int currentHeading = smoothHeading();
    int error = targetHeading - currentHeading;

    // Lyhin kiertosuunta
    if (error > 180) {error -= 360;}
    if (error < -180) {error += 360;}

    // Jätä pienet muutokset huomioimatta
    if (abs(error) < deadzone) {return;}

    // Muuta peräsimen kulmaksi
    int angle = 90 + (int)(error * Kp);

    // Rajoita välill 0 ... 180
    if (angle > 180) {angle = 180;}
    if (angle < 0) { angle = 0;}

    turnRudder(angle);
}

void turnRudder(unsigned char targetAngle)
{
    // TODO: map targetAngle accurately to real rudder movement

    perasinServo.write(targetAngle);
}

void setThrottle(unsigned char t1, unsigned char t2)
{
    // Throttle 0 .. 200 => 1 000 ... 2 000
    unsigned short throttle1 = ((t1 - 100) * 5) + 1500;
    unsigned short throttle2 = ((t2 - 100) * 5) + 1500;

    motor1.writeMicroseconds(throttle1);
    motor2.writeMicroseconds(throttle2);
}