#pragma once

// Statusvalo

#define LEDR 15
#define LEDG 23
#define LEDB 2

#define CHR 0
#define CHG 1
#define CHB 2

#define PWMFREQ 5000
#define PWMRES 8 // 8 bittinen resoluutio (0 ... 255)

void lightInit();
void setLight(unsigned char colorId);