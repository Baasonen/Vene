#include "mode.h"
#include "common.h"
#include "lights.h"

// Hieman huono tapa hoitaa modin vaihtamissäännöt
void setMode(unsigned char targetMode)
{
  switch (MODE) 
  {
    case 0:
      if (targetMode == 1) {MODE = 1; setLight(1);}
      if (targetMode == 3) {MODE = 3; setLight(3);}
      break;
    
    case 1:
      if (targetMode == 2)
      {
        if (waypointUploadComplete && waypointCount > 1 && RDYFLAG)
        {
          MODE = 2;  
          targetWp = 1;
          setLight(2);
        }
      }
      if (targetMode == 3) {MODE = 3; setLight(3);}

      if (targetMode == 8) {MODE = 8;}
      if (targetMode == 9) {MODE = 9;}
      break;

    case 2:
      if (targetMode == 1) {MODE = 1; setLight(1);}
      if (targetMode == 3) {MODE = 3; setLight(3);}
      break;

    case 3:
      if (targetMode == 4) {MODE = 1; setLight(1);}
      break;

    // Home WP päivitystä varten
    case 8:
      MODE = 1;
      break;

    // VGUI Home WP päivitys
    case 9:
      MODE = 1;
      break;
  }
}