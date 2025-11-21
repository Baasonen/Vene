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

    // Jännittenjakajan skaala (mitattu)
    float cell1Offset = 1.46;
    float cell2Offset = 3.40;

    // HUOM! ADC data, ei jännite
    float cell1 = analogRead(CELL1PIN);
    float cell2 = analogRead(CELL2PIN);

    // Muuta jännitteeksi
    cell1 = (cell1 / 4095.0) * vRef;
    cell2 = (cell2 / 4095.0) * vRef;

    // Kennojen oikeat jännitteet
    cell1 *= cell1Offset;
    cell2 *= cell2Offset;
    cell2 -= cell1;

    // Kiinnostaa kennoista pienempi jännite
    float cellMin = min(cell1, cell2);

    // 2,5 ... 5,0 -> 0 ... 250
    int limited = (unsigned char) round((cellMin - 2.5) * 100);
    
    // Rajoita palautusarvo 
    return (unsigned char)min(max(limited, 0), 255);
}