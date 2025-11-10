#include "mode.h"
#include "common.h"

void setMode(unsigned char targetMode)
{
  switch (MODE) 
  {
    case 0:
      if (RDYFLAG) {MODE = 1; miscError = 1;}
      break;
    
    case 1:
      if (targetMode == 2)
      {
        if (waypointUploadComplete && waypointCount > 1)
        {
          MODE = 2;
          targetWp = 1;
        }
      }
      if (targetMode == 3) {MODE = 3;}

      if (targetMode == 9) {MODE = 9;}
      break;

    case 2:
      if (targetMode == 1) {MODE = 1;}
      if (targetMode == 3) {MODE = 3;}
      break;

    case 3:
      if (targetMode == 4) {MODE = 1;}
      break;

    // Vaan home WP päivitystä varten, ei ohjausta
    case 9:
      MODE = 1;
      break;
  }
}