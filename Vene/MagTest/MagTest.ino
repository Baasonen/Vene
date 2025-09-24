#include <Wire.h>
#include <Adafruit_LIS3MDL.h>
#include <math.h>


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

  float heading = atan2(y, x) * 180.0 / PI;
  if (heading < 0) heading += 360.0;

  Serial.print("X: ");
  Serial.print(x);
  Serial.print("Y: ");
  Serial.print(y);
  Serial.print("Z: ");
  Serial.print(z);
  Serial.println(heading);
}