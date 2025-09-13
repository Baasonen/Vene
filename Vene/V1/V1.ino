#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>

// WiFi AP
const char *ssid = "ESP32_AP";
const char *password = "12345678";

WiFiUDP udp;
unsigned int rxPort = 4210; // receive joystick commands
unsigned int txPort = 4211; // send potentiometer data
char incomingPacket[255];
IPAddress laptopIP;

// Servo setup
Servo myServo;
int servoPin = 13;

// Potentiometer pin
int potPin = 34;  // ADC pin
int lastPotValue = -1;

// Timing
unsigned long lastReport = 0;

void setup() {
  Serial.begin(115200);

  // WiFi AP
  WiFi.softAP(ssid, password);
  Serial.println("AP started");
  Serial.print("IP: ");
  Serial.println(WiFi.softAPIP());

  udp.begin(rxPort);
  Serial.printf("Listening on UDP port %d\n", rxPort);

  // Servo
  myServo.attach(servoPin);
  myServo.write(90);
}

void loop() {
  // 1. Receive joystick commands
  int packetSize = udp.parsePacket();
  if (packetSize > 0) {
    int len = udp.read(incomingPacket, 255);
    if (len > 0) {
      incomingPacket[len] = '\0'; // null-terminate
    }

    // Save laptop IP for feedback
    laptopIP = udp.remoteIP();

    // Convert to String for parsing
    String data = String(incomingPacket);

    // Split by comma
    int commaIndex = data.indexOf(',');
    if (commaIndex > 0) {
      String angleStr = data.substring(1, commaIndex); // skip '('
      String throttleStr = data.substring(commaIndex + 2, data.length() - 1);

      int angle = angleStr.toFloat();
      int throttle = throttleStr.toFloat();

      Serial.print("Angle: "); Serial.print(angle);
      Serial.print("   Throttle: "); Serial.println(throttle);

      // Move servo
      myServo.write(angle);
    }
  }

  // 2. Read potentiometer
  int potValue = analogRead(potPin); // 0..4095
  if (potValue != lastPotValue) {
    lastPotValue = potValue;
  }

  // 3. Periodically send value back
  if (millis() - lastReport > 200) { // every 200 ms
    if (laptopIP) {
      char msg[50];
      sprintf(msg, "POT:%d", lastPotValue);
      udp.beginPacket(laptopIP, txPort);
      udp.write((uint8_t*)msg, strlen(msg));
      udp.endPacket();
      //Serial.println(msg);
    }
    lastReport = millis();
  }
}
