#include "common.h"

unsigned char MODE = 0;
bool waypointUploadComplete = false;
unsigned char waypointCount = 0;
unsigned char targetWp = 0;

long homeLat = 1;
long homeLon = 1;

bool RDYFLAG = false;
unsigned char miscError = 0;