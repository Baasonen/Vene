#pragma once

float distanceToPoint(double lat1, double lon1, double lat2, double lon2);
float headingToPoint(double lat1, double lon1, double lat2, double lon2);
void steerTo(unsigned short targetHeading);