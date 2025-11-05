#pragma once

// Statusvalo

#define LEDR 16
#define LEDG 17
#define LEDB 23

#define CHR 0
#define CHG 1
#define CHB 2

#define PWMFREQ 5000
#define PWMRES 8 // 8 bittinen resoluutio (0 ... 255)

void lightInit();
void setLight(unsigned char colorId);