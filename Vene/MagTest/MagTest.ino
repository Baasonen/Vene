#include <Wire.h>
#include <Adafruit_LIS3MDL.h>
#include <math.h>


float xmin = 0;
float ymin = 0;
float zmin = 0;
float xmax = 0;
float ymax = 0;
float zmax = 0; 

float xof, yof, zof;

Adafruit_LIS3MDL lis3;

void setup()
{
  Serial.begin(115200);

  if (!lis3.begin_I2C(0x1c))
  {
    Serial.println("Not Found");
  }

  // Config 
  lis3.setPerformanceMode(LIS3MDL_ULTRAHIGHMODE);
  lis3.setOperationMode(LIS3MDL_CONTINUOUSMODE);
  lis3.setDataRate(LIS3MDL_DATARATE_80_HZ);
  lis3.setRange(LIS3MDL_RANGE_4_GAUSS);

  Serial.println("RDY");
}

void loop()
{
  sensors_event_t event;
  lis3.getEvent(&event);

  float x = event.magnetic.x;
  float y = event.magnetic.y;
  float z = event.magnetic.z;

  xmin = min(xmin, x);
  ymin = min(ymin, y);
  zmin = min(zmin, z);
  xmax = max(xmax, x);
  ymax = max(ymax, y);
  zmax = max(zmax, z);

  xof = (xmin + xmax) / 2;
  yof = (ymin + ymax) / 2;
  zof = (zmin + zmax) / 2;

  x -= xof;
  y -= yof;
  z -= zof;


  float heading = atan2(y,x) * 180.0 / PI;
  if (heading < 0) heading += 360.0;


  //Serial.print("X: ");
  //Serial.print(x);
  //Serial.print(" Xof: ");
  //Serial.print(xof);
  //Serial.print(" Y: ");
  //Serial.print(y);
  //Serial.print(" Yof: ");
  //Serial.print(yof);
  //Serial.print("Z: ");
  //Serial.print(z);
  //Serial.print(" Heading: ");
  Serial.println(heading);
  delay(70);
}
