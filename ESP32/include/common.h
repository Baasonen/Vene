#pragma once

// Yleisiä arvoja

#define MAX_WAYPOINTS 255

extern unsigned char MODE;
extern bool waypointUploadComplete;
extern unsigned char waypointCount;
extern unsigned char targetWp;

extern bool RDYFLAG;
extern unsigned char miscError;

void modulesInit();
unsigned short makeError(unsigned char waypoint, unsigned char gps, unsigned char errors);
unsigned char calculateChecksum(unsigned char* data, unsigned char length);

#pragma pack(push, 1) // Ei paddingia structeihin jotta koko matchaa lähetettyjen kanssa
struct ControlPacket
{
  unsigned char mode;
  unsigned char rudder;
  unsigned char throttle1;
  unsigned char checksum;
  unsigned char apThrottle;
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

