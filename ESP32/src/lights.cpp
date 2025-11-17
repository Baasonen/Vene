#include <Arduino.h>
#include "lights.h"
#include "common.h"

void lightInit()
{
    pinMode(LEDR, OUTPUT);
    pinMode(LEDG, OUTPUT);
    pinMode(LEDB, OUTPUT);
    Serial.println("LedInit");

    digitalWrite(LEDR, HIGH);
    digitalWrite(LEDG, LOW);
    digitalWrite(LEDB, LOW);
}

void setLight(unsigned char colorId)
{
    switch (colorId)
    {
        case 0:
        {
            digitalWrite(LEDR, HIGH);
            digitalWrite(LEDG, LOW);
            digitalWrite(LEDB, LOW);
            break;
        }
        case 1:
        {
            digitalWrite(LEDR, LOW);
            digitalWrite(LEDG, LOW);
            digitalWrite(LEDB, HIGH);
            break;
        }
        case 2:
        {
            digitalWrite(LEDR, LOW);
            digitalWrite(LEDG, HIGH);
            digitalWrite(LEDB, LOW);
            break;
        }
        case 3:
        {
            digitalWrite(LEDR, HIGH);
            digitalWrite(LEDG, LOW);
            digitalWrite(LEDB, HIGH);
            break;
        }
        case 9:
        {
            digitalWrite(LEDR, HIGH);
            digitalWrite(LEDG, LOW);
            digitalWrite(LEDB, LOW);
        }
    }
}