#pragma once

// Yleisiä arvoja

extern unsigned char MODE;
extern bool waypointUploadComplete;
extern unsigned char waypointCount;
extern unsigned char targetWp;

extern long homeLat;
extern long homeLon;

extern bool RDYFLAG;
extern unsigned char miscError;

#pragma pack(push, 1)
struct ControlPacket
{
  unsigned char mode;
  unsigned char rudder;
  unsigned char throttle1;
  unsigned char throttle2;
  unsigned char lightMode;
  unsigned char debugData;
  unsigned short timestamp;
};

struct TelemetryPacket
{
    unsigned char mode;
    unsigned char battery;
    unsigned char pl;
    unsigned char speed;
    unsigned short heading;
    unsigned short error;
    long gpsLat;
    long gpsLon;
};

struct WaypointPacket
{
  unsigned char order;
  long wpLat;
  long wpLon;
  unsigned char wpAmmount;
  unsigned char wpId;
};
#pragma pack(pop)

#define MAX_WAYPOINTS 65