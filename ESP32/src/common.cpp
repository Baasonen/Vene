#include "common.h"
#include "battery.h"
#include "sensors.h"
#include "navigation.h"
#include "lights.h"

unsigned char MODE = 0;
bool waypointUploadComplete = false;
unsigned char waypointCount = 0;
unsigned char targetWp = 0;

bool RDYFLAG = false;
unsigned char miscError = 0;

void modulesInit()
{
  batteryInit();
  sensorInit();
  navigationInit();
  lightInit();
}

// Muuta virheet yhdeksi 16 bittiseksi luvuksi
unsigned short makeError(unsigned char waypoint, unsigned char gps, unsigned char errors)
  {
    return (waypoint & 0x3FF) // Bitit 0-9 (1023)
       | ((gps & 0x03) << 10) // Bitit 10-11 (3)
       | ((errors & 0x0F) << 12); // Bitit 12 - 15
  }