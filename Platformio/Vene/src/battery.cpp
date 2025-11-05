#include "battery.h"
#include <Arduino.h>

void batteryInit()
{
    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);
}

unsigned char getBattery()
{
    float vRef = 3.3;

    float cell1Offset = 1.46;
    float cell2Offset = 3.40;

    float cell1 = analogRead(CELL1PIN);
    float cell2 = analogRead(CELL2PIN);

    cell1 = (cell1 / 4095.0) * vRef;
    cell2 = (cell2 / 4095.0) * vRef;

    cell1 *= cell1Offset;
    cell2 *= cell2Offset;
    cell2 -= cell1;

    return (unsigned char)(min(cell1, cell2) * 10);
}