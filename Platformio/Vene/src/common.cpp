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