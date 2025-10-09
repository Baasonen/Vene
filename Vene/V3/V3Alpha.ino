#include <WiFi.h>
#include <WiFiUdp.h> 
#include <TinyGPS++.h> // Tulkitsee gps moduulilta tulleita NEMA lauseita
#include <ESP32Servo.h> // Sero moottorielle ja peräsimelle
#include <Wire.h> // I2C magnetometrille
#include <Adafruit_LIS3MDL.h> // Magnetometrin kirjasto
#include <math.h> // Kompassilaskuja varten
#include <list> 

// Vcom 3.0

const char* ssid = "VENE";
const char* password = "1234";

Servo perasinServo;
int perasinServoPin = 14;

Servo motor1;
Servo motor2;

int motor1Pin = 25;
int motor2Pin = 26;

int gpsRxPin = 5;
int gpsTxPin = 18;

// WIFI asetukset
WiFiUDP udp;
const unsigned int RXPort = 4211;
const unsigned int TXPort = 4210;
IPAddress lastIP;
unsigned long TXRate = 2;
unsigned short packetsThisSecond = 0;
unsigned long lastPacketCountTime = 0;
unsigned char packetsPerSecond = 0;

unsigned char MODE = 0;
bool RDYFLAG = false;

#pragma pack(push, 1)  // Estä kääntäjää lisäämästä paddingia
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
#pragma pop

struct GPSDataStruct
{
  double lat;
  double lon;
  float speed;
  float hdop;
  bool fix;
};

// Virhemuuttujat
unsigned char gpsError = 0;
unsigned char targetWp = 0;
unsigned char miscError = 0;

// Muuta virheet yhdeksi 16 bittiseksi luvuksi
unsigned short makeError(unsigned char waypoint, unsigned char gps, unsigned char errors)
  {
    return (waypoint & 0x7F) // Bits 0-6
       | ((gps & 0x03) << 7) // Bits 7-8
       | ((errors & 0xFFFF) << 9); // Bits 9->
  }

ControlPacket inbound;
TelemetryPacket outbound;
std::list<WaypointPacket> waypointList;

unsigned char currentWpId = 0;
unsigned char currentTargetWp = 0;

long homeLat;
long homeLon;

// Telemetrian lähetystaajuuden muutos millisekunneiksi
unsigned long TXRMillis = 1000.0 / TXRate;
unsigned long lastTelemetryTime = 0;

// Gps
TinyGPSPlus gps;
HardwareSerial gpsSerial(2);
GPSDataStruct gpsData;
float heading = 0;

// Magnetometrin kalibrointimuuttujat
float xmin = 0;
float xmax = 0;
float ymin = 0;
float ymax = 0;

Adafruit_LIS3MDL lis3;

// Funktiot

void steerTo(unsigned short targetHeading)
{
  float Kp = 1.0;
  int error = targetHeading - heading;

  if (error > 180) error -= 360;
  if (error < -180) error += 360;

  float rudderOffset = error * Kp;

  if (rudderOffset > 90.0f) rudderOffset = 90.0f;
  if (rudderOffset < -90.0f) rudderOffset = -90.0f; 

  int rudder = 90 + rudderOffset;

  if (rudder > 180) rudder = 180;
  if (rudder < 0) rudder = 0;

  turnRudder(rudder);
}

void turnRudder(unsigned char target_angle)
{
  int Llimit = 10;
  int Ulimit = 170;
  
  if (target_angle < Llimit) {target_angle = Llimit;}
  if (target_angle > Ulimit) {target_angle = Ulimit;}

  perasinServo.write(target_angle);
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
      data.lat = gps.location.lat();
      data.lon = gps.location.lng();
      data.speed = gps.speed.kmph();
      data.hdop = gps.hdop.hdop();
      data.fix = true;

      if (gps.hdop.hdop() <= 1.0)
      {
        if (!RDYFLAG)
        {
          homeLat = gps.location.lat();
          homeLon = gps.location.lng();
        }
        RDYFLAG = true;
        gpsError = 0; // Gps ok
      }
      else gpsError = 1; // Gps liian epätarkka
  }
  else gpsError = 2; // Ei gps sijanintia

  return data;
}

float getHDG()
{
  sensors_event_t event;
  lis3.getEvent(&event);

  float x = event.magnetic.x;
  float y = event.magnetic.y;

  // Päivitä minimit ja maksimit
  xmin = min(xmin, x);
  xmax = max(xmax, x);
  ymin = min(ymin, y);
  ymax = max(ymax, y);

  float xof = (xmin + xmax) / 2;
  float yof = (ymax + ymin) / 2;

  x -= xof;
  y -= yof;

  float heading = atan2(y, x) * 180.0 / PI;
  if (heading < 0) heading += 360.0;

  float declination = 10.0 + (17.0 / 60.0);
  float true_heading = heading + declination;
  if (true_heading >= 360.0) true_heading -= 360.0;

  return true_heading;
}

// Tarkista, onko modin vaihto sallittua
void setMode(unsigned char targetMode)
{
  switch (MODE) 
  {
    case 0:
      if (RDYFLAG) {MODE = 1; miscError = 1;}
      break;
    
    case 1:
      if (targetMode == 2) {MODE = 2;}
      if (targetMode == 3) {MODE = 3;}

    case 2:
      if (targetMode == 1) {MODE = 1;}
      if (targetMode == 3) {MODE = 3;}

    case 3:
      if (targetMode == 4) {MODE = 1;}
  }
}

void setup() 
{
  // Käynnistä UART-kanava serial monitorille (vaan debug)
  Serial.begin(115200);
  delay(1000);

  // Käynnistä WIFI
  WiFi.softAP(ssid, password);
  Serial.println("AP Started");
  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP());

  udp.begin(RXPort);

  // Käynnistä UART-kanava gps moduulille
  gpsSerial.begin(9600, SERIAL_8N1, gpsRxPin, gpsTxPin);

  // Peräsimen servo
  perasinServo.attach(perasinServoPin);
  perasinServo.write(90);

  // Moottorit
  motor1.attach(motor1Pin);
  motor2.attach(motor2Pin);

  // Magnetometri
  if (!lis3.begin_I2C(0x1c)) {miscError = 2;}
  lis3.setPerformanceMode(LIS3MDL_ULTRAHIGHMODE);
  lis3.setOperationMode(LIS3MDL_CONTINUOUSMODE);
  lis3.setDataRate(LIS3MDL_DATARATE_80_HZ);
  lis3.setRange(LIS3MDL_RANGE_4_GAUSS);
}

void loop() 
{
  int packetSize = udp.parsePacket();
  if (packetSize == sizeof(ControlPacket)) {
    udp.read((uint8_t*)&inbound, sizeof(ControlPacket)); // Dumppaa koko bufferi suoraan muistiin

    RDYFLAG = (inbound.debugData == 1);

    // Pitäis varmaan tarkistaa et sisältö ok (jos jaksaa...)

    lastIP = udp.remoteIP(); // Tallenna IP osoita telemetrian lähetystä varten
    packetsThisSecond++;
  }
  else if (packetSize == sizeof(WaypointPacket))
  {
    WaypointPacket wp;
    udp.read((uint8_t*)&wp, sizeof(WaypointPacket));

    Serial.println(wp.wpId);

    if (!wp.wpId == currentWpId)
    {
      waypointList.clear();
      WaypointPacket homeWp = {0, homeLat, homeLon, 0, 0};

      waypointList.push_back(homeWp);
      currentWpId = wp.wpId;
      currentTargetWp = 0;
    }
    waypointList.push_back(wp);
  }

  if (millis() - lastPacketCountTime >= 1000) // Laske pakettia / sekuntti
  {
    lastPacketCountTime = millis();
    packetsPerSecond = packetsThisSecond;
    packetsThisSecond = 0;
  }

  gpsData = getGPS();
  heading = getHDG();

  if (inbound.mode != MODE) {setMode(inbound.mode);}  // Tarvitseeko modia vaihtaa

  switch (MODE)  // Ohjaus riippuen modesta
  {
    case 1:
      turnRudder(inbound.rudder);
      motor1.writeMicroseconds(1);
      motor2.writeMicroseconds(1);
      break;
    case 2:
      steerTo(180);
      break;
  }

  // Lähetä telemetriaa
  if (lastIP && (millis() - lastTelemetryTime >= TXRMillis))
  {
    lastTelemetryTime = millis();

    double t = millis() / 1000.0;
    outbound.mode = MODE;
    outbound.heading = (unsigned short)(sin(t) * 180 + 180);
    outbound.speed = inbound.throttle1;
    outbound.gpsLat = (long)(gpsData.lat * 100000);
    outbound.gpsLon = (long)(gpsData.lon * 100000);
    outbound.battery = (unsigned char)(gpsData.fix);
    outbound.error = makeError(targetWp, gpsError, miscError);
    outbound.pl = packetsPerSecond;

    udp.beginPacket(lastIP, TXPort);
    udp.write((uint8_t*)&outbound, sizeof(TelemetryPacket));
    udp.endPacket();

    //Serial.println("Telemetry Sent");
  }
}
