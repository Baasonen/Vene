    #include "sensors.h"
    #include "common.h"
    #include <HardwareSerial.h>
    #include <math.h>

    static TinyGPSPlus gps;
    static HardwareSerial gpsSerial(2);
    static Adafruit_LIS3MDL lis3;
    static bool magAvailable = false;

    static const float magOffset[2] = {-12.05, -25.96}; // X, Y offsets
    static const float magSoftIron[2][2] = 
    {
        {1.017, -0.108}, // row 0
        {-0.108, 1.006}   // row 1
    };

    static unsigned char gpsStatus = 2;

    double homeLat = 1.0;
    double homeLon = 1.0;

    void sensorInit()
    {
        gpsSerial.begin(9600, SERIAL_8N1, GPSRXPIN, GPSTXPIN);

        if (lis3.begin_I2C(0x1c)) // Estää I2C errorit
        {
            magAvailable = true;
            lis3.setPerformanceMode(LIS3MDL_ULTRAHIGHMODE);
            lis3.setOperationMode(LIS3MDL_CONTINUOUSMODE);
            lis3.setDataRate(LIS3MDL_DATARATE_40_HZ);
            lis3.setRange(LIS3MDL_RANGE_4_GAUSS);
        }
    }

    GPSData getGPS()
    {
        GPSData data = {0, 0, 0, 0, false}; // Pohjusta structi
        while(gpsSerial.available() > 0) gps.encode(gpsSerial.read());

        if(gps.location.isValid())
        {
            data.lat = gps.location.lat();
            data.lon = gps.location.lng();
            data.speed = gps.speed.kmph();
            data.hdop = gps.hdop.hdop();
            data.fix = true;

            if (gps.hdop.hdop() <= 1.3) 
            {   
                // Oikee tapa määrittää RDYFLAG ilman debugmode
                if (!RDYFLAG)
                {
                    homeLat = gps.location.lat();
                    homeLon = gps.location.lng();
                }
                gpsStatus = 0;
            }
            else {gpsStatus = 1;}
        }
        else {gpsStatus = 2;}

        return data;
    }

    unsigned char getGPSStatus()
    {
        return gpsStatus;
    }

    float getHeading()
    {
        if (!magAvailable) {Serial.println("MAGERROR"); return 0.0;}

        sensors_event_t event;
        lis3.getEvent(&event);

        // Raw magnetometer readings
        float mx = event.magnetic.x;
        float my = event.magnetic.y;

        // Apply 2D calibration (offset + soft-iron)
        float vx = mx - magOffset[0];
        float vy = my - magOffset[1];

        float mx_cal = magSoftIron[0][0]*vx + magSoftIron[0][1]*vy;
        float my_cal = magSoftIron[1][0]*vx + magSoftIron[1][1]*vy;

        // Compute heading in degrees
        float heading = atan2(my_cal, mx_cal) * 180.0 / M_PI;
        if (heading < 0) heading += 360.0;

        // Apply declination (example: 10°17')
        float declination = 10.0 + 17.0 / 60.0;
        float geoHeading = heading + declination;
        if (geoHeading >= 360.0) geoHeading -= 360.0;

        return geoHeading;
}   
