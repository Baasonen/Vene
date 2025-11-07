#include <Arduino.h>
#include "lights.h"
#include "common.h"

void lightInit()
{
    ledcSetup(CHR, PWMFREQ, PWMRES);
    ledcSetup(CHG, PWMFREQ, PWMRES);
    ledcSetup(CHB, PWMFREQ, PWMRES);

    ledcAttachPin(LEDR, CHR);
    ledcAttachPin(LEDG, CHG);
    ledcAttachPin(LEDB, CHB);

    ledcWrite(CHR, 255);
    ledcWrite(CHG, 255);
    ledcWrite(CHB, 255);
    Serial.println("LedInit");
}

void setLight(unsigned char colorId)
{
    static unsigned char r = 255;
    static unsigned char g = 0;
    static unsigned char b = 0;

    switch (MODE)
    {
        case 0:
        {
            r = 255;
            g = 0;
            b = 0;
            break;
        }
        case 1:
        {
            r = 0;
            g = 255;
            b = 0;
            break;
        }
        case 2:
        {
            r = 0;
            g = 0;
            b = 255;
            break;
        }
        default:
        {
            r = 255;
            g = 255;
            b = 255;
            break;
        }
    }

    ledcWrite(CHR, r);
    ledcWrite(CHG, g);
    ledcWrite(CHB, b);
}