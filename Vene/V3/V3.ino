#include <Wire.h>
#include <Adafruit_LIS3MDL.h>
#include <math.h>
#include <TinyGPS++.h>
#include <WiFi.h>
#include <WiFiUdp.h>

// Password MUST be atleast 8 char
const char* ssid = "VENE";
const char* password = "12345678";

WiFiUDP udp;
const unsigned short RXPort = 4211;
const unsigned short TXPort = 4210;
unsigned char TXRate = 1;
IPAddress  lastIP;

Adafruit_LIS3MDL lis3;
TinyGPSplus gps;
HardwareSerial gpsSerial(2);

// Error
unsigned char MODE = 0;
bool FATAL_ERROR = false;
unsigned char targetWP = 0;
unsigned char GPSError = 0;
unsigned char wpError = 0;
unsigned char miscError = 0;

inline unsigned short makeError(unsigned short target, unsigned short GPSErr, unsigned short wpErr, unsigned short miscErr)
{
    return ((target & 0x3F) << 0) |
           ((GPSError & 0x07) << 6) |
           ((wpError  & 0x03) << 9) |
           ((miscError & 0x03) << 11);
}

#pragma pack(push, 1)
struct controlPacketStruct
{
    unsigned char mode, rudder, thr1, thr2, lightMode, TXRate, batt, pl;
    unsigned short int timeStamp;
};

struct telemtryPacketStruct
{
    unsigned char mode, batt, pl;
    unsigned short HDG, error;
    int32_t gpsLat, gpsLon;
};

struct waypointPacketStruct
{
    unsigned char amount, order;
    unsigned short lat, lon;
};
#pragma pop

struct magDataStruct
{
    float xmin = 0;
    float ymin = 0;
    float xmax = 0;
    float ymax = 0;

    float xof, yof;;
};

struct GPSDataStruct
{
    double lat;
    double lon;
    float speed;
    float hdop;
    bool fix;
};

// WP parameters
const unsigned char MAX_WAYPOINTS = 25;
waypointPacketStruct waypointList[MAX_WAYPOINTS];
unsigned char waypointsTotal = 1;
unsigned char waypointsRecieved = 1;
bool waypointsReady = false;

magDataStruct magData;
GPSDataStruct GPSData;
float heading;

controlPacketStruct inbound;
//telemtryPacket outbound;

unsigned long TXMillis = 1000.0 / TXRate;
unsigned long lastTelemtryTime = 0;
unsigned long packetCount = 0;
unsigned short packetTimeStamp = 0;

void setHome(unsigned short lat, unsigned short lon)
{
    waypointList[0].lat = lat;
    waypointList[0].lon = lon;
    waypointList[0].order = 0;
    waypointList[0].amount = 1;
}

float getHDG()
{
    sensors_event_t event;
    lis3.getEvent(&event);

    float x = event.magnetic.x;
    float y = event.magnetic.y;

    magData.xmin = min(magData.xmin, x);
    magData.ymin = min(magData.ymin, y);
    magData.xmax = max(magData.xmax, x);
    magData.ymax = max(magData.ymax, y);

    magData.xof = (magData.xmin + magData.xmax) / 2;
    magData.yof = (magData.ymin + magData.ymax) / 2;

    x -= magData.xof;
    y -= magData.yof;

    float hdg = atan2(y, x) * 180 / PI;
    if (hdg < 0) hdg += 360;

    return hdg;
}

GPSDataStruct getGPS()
{
    GPSDataStruct data = {0, 0, 0, 0, false};

    while(gpsSerial.available() > 0)
    {
        gps.encode(gpsSerial.read());
    }

    if(gps.location.isValid())
    {   
        if (gps.hdop.hdop() >= 1)
        {
            GPSError = 2;
        }
        data.lat = gps.location.lat();
        data.lon = gps.location.lng();
        data.speed = gps.speed.kmph();
        data.hdop = gps.hdop.hdop();
        data.fix = true;
    }
    else 
    {
        GPSError = 1;
    }
    return data;
}

void sendTelemetry(telemtryPacketStruct outbound)
{
    udp.beginPacket(lastIP, TXPort);
    udp.write((uint8_t*)&outbound, sizeof(telemtryPacketStruct));
    udp.endPacket();
}

void setup()
{
    Serial.begin(115200);

    if (!lis3.begin_I2C(0x1c))
    {
        Serial.println("No Mag");
        FATAL_ERROR = true;
    }

    // Magnetometer Config
    lis3.setPerformanceMode(LIS3MDL_ULTRAHIGHMODE);
    lis3.setOperationMode(LIS3MDL_CONTINUOUSMODE);
    lis3.setDataRate(LIS3MDL_DATARATE_80_HZ);
    lis3.setRange(LIS3MDL_RANGE_4_GAUSS);

    // GPS UART
    gpsSerial.begin(9600, SERIAL_8N1, 5, 18);


    // Network Setup
    WiFi.softAP(ssid, password);
    udp.begin(RXPort);
}

void loop()
{
    short packetSize = udp.parsePacket();
    if (packetSize == sizeof(controlPacketStruct)) 
    {
        udp.read((uint8_t*)&inbound, sizeof(controlPacketStruct)); // Cast buffer to struct direct (Mahdollinen vittusaatana)
        lastIP = udp.remoteIP(); // Save sender ip
    }
    // Check if waypoint packet
    else if (packetSize == sizeof(waypointPacketStruct))
    {
        waypointPacketStruct temp;
        udp.read((uint8_t*)&temp, sizeof(waypointPacketStruct));
        
        waypointsTotal = temp.amount;

        if (temp.order >= 1 && temp.order < MAX_WAYPOINTS)
        {
            waypointList[temp.order] = temp;
            short recievedCount = 1; // Home is (hopefully) already set
            for (short i = 1; i < waypointsTotal; i++)
            {
                if (waypointList[i].order == i) recievedCount++;
            }
            waypointsRecieved = recievedCount;

            if (waypointsRecieved == waypointsTotal)
            {
                waypointsReady = true;
            }
        }
    }

    if (inbound.timeStamp != packetTimeStamp)
    {
        packetCount = 0;
        packetTimeStamp = inbound.timeStamp;
    }
    else
    {
        packetCount++; 
    }

    heading = getHDG();
    GPSData = getGPS();

    if (lastIP && (millis() - lastTelemtryTime >= TXMillis))
    {
        // Populate outbound struct 
        telemtryPacketStruct outbound;
        outbound.mode = MODE;
        outbound.HDG =  (unsigned short)heading;
        outbound.gpsLat = (int32_t)(GPSData.lat * 100000);
        outbound.gpsLon = (int32_t)(GPSData.lon * 100000);
        outbound.batt = 100;
        outbound.error = makeError(targetWP, GPSError, wpError, miscError);
        outbound.pl = (packetCount * 100) / inbound.TXRate;

        // Send struct
        sendTelemetry(outbound);
        lastTelemetryTime = millis();
    }
}
