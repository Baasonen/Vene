#include <Wire.h>
#include <Adafruit_LIS3MDL.h>
#include <math.h>
#include <TinyGPS++.h>
#include <WiFi.h>
#include <WiFiUdp.h>
// Password MUST be atleast 8 char
const char* ssid "VENE";
const char* password = "12345678";

WiFiUDP udp;
const unsigned short RXPort = 4211;
const unsigned short TXPort = 4210;
unsigned char TXRate = 1;
IPAdress lastIP;

Adafruit_LIS3MDL lis3;
TinyGPSplus gps;

unsigned char MODE = 0;
unsigned short ERROR = 00100;
bool FATAL_ERROR = false;

#pragma pack(push, 1)
struct controlPacketStruct
{
    unsigned char mode, rudder, thr1, thr2, lightMode, TXRate, batt, pl;
    unsigned short int timeStamp;
};

struct telemtryPacketStruct
{
    unsigned char mode, batt, pl;
    unsigned short HDG, gpsLat, gpsLon, error;
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

magDataStruct magData;
GPSDataStruct GPSData;
float heading;

controlPacketStruct inbound;
//telemtryPacket outbound;

unsigned long TXMillis = 1000.0 / TXRate;
unsigned long lastTelemtryTime = 0;
unsigned long packetCount = 0;
unsigned short packetTimeStamp = 0;

float getHDG()
{
    sensors_event_t event;
    lis3.getEvent(&event);

    float x = event.magnetic.x;
    float y = event.magnetic.y;

    magData.xmin = min(xmin, x);
    magData.ymin = min(ymin, y);
    magData.xmax = max(xmax, x);
    magData.ymax = max(ymax, y);

    magData.xof(xmin + xmax) / 2;
    magData.yof(ymin + ymax) / 2;

    x -= xof;
    y -= yof;

    float hdg = atan2(y, x) * 180 / PI;
    if (hdg < 0) hdg += 360;

    return hdg
}

GPSDataStruct getGPS()
{
    GPSData data = {0, 0, 0, 0, false};

    while(gpsSerial.available() > 0)
    {
        gps.encode(gpsSerial.read());
    }

    if(gps.location.isValid())
    {
        data.lat = gps.location.lat();
        data.lon = gps.location.lng();
        data.speed = gps.speed.kmph();
        data.hdop = gps.hdop.hdop();
        data.fix = true;
    }
    return data
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
    if packetSize = udp.parsePacket();
    if (packetSize == sizeof(controlPacketStruct)) 
    {
        udp.read((uint8_t*)&inbound, sizeof(controlPacketStruct)); // Cast buffer to struct direct (Mahdollinen vittusaatana)
        lastIP = udp.remoteIP(); // Save sender ip
    }

    if inbound.timeStamp != packetTimeStamp
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
        outbound.HDG = heading;
        outbound.gpsLat = GPSData.lat;
        outbound.gpsLon = GPSData.lon;
        outbound.batt = 100;
        outbound.error = ERROR;
        outbound.pl = packetCount / inbound.TXRate;

        // Send struct
        sendTelemetry(outbound);
    }
}
