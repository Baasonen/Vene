#include "esp_camera.h"
#include <WiFi.h>
#include <ESPAsyncWebServer.h>

const char* ssid = "VENE";
const char* password = "12345678";

// Globals
AsyncWebServer server(80);
bool streamEnabled = true;
int streamFps = 15;

IPAddress subnetMask(255, 255, 0, 0);
IPAddress gateway(192, 168, 4, 1);
IPAddress camIp(192, 168, 4, 2);

// Kopioitu EspCamera esimerkistä
#define PWDN_GPIO_NUM    32
#define RESET_GPIO_NUM   -1
#define XCLK_GPIO_NUM     0
#define SIOD_GPIO_NUM    26
#define SIOC_GPIO_NUM    27

#define Y9_GPIO_NUM      35
#define Y8_GPIO_NUM      34
#define Y7_GPIO_NUM      39
#define Y6_GPIO_NUM      36
#define Y5_GPIO_NUM      21
#define Y4_GPIO_NUM      19
#define Y3_GPIO_NUM      18
#define Y2_GPIO_NUM       5
#define VSYNC_GPIO_NUM   25
#define HREF_GPIO_NUM    23
#define PCLK_GPIO_NUM    22


// Myös kopioitu
void startCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 12;
  config.fb_count = 2;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t * s = esp_camera_sensor_get();
  if (s->id.PID == OV5640_PID) {
    Serial.println("Detected OV5640 sensor.");
  } else {
    Serial.println("WARNING: This may not be an OV5640 sensor.");
  }
}

void Stream(AsyncWebServerRequest *request) {
    if (!streamEnabled) {
        request->send(200, "text/plain", "Stream Not Enabled");
        return;
    }

    AsyncResponseStream *response = request->beginResponseStream("multipart/x-mixed-replace; boundary=frame");
    response->addHeader("Cache-Control", "no-cache");
    request->send(response);

    while (streamEnabled) {
        camera_fb_t *fb = esp_camera_fb_get();
        if (!fb) continue;

        String header = "--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + String(fb->len) + "\r\n\r\n";
        response->write((uint8_t*)header.c_str(), header.length());
        response->write(fb->buf, fb->len);
        response->write((uint8_t*)"\r\n", 2);

        esp_camera_fb_return(fb);
        delay(1000 / streamFps); // FPS limit
    }
}


void Config(AsyncWebServerRequest *request) {
  if (request->hasParam("enabled")) {
    streamEnabled = request->getParam("enabled")->value().toInt() > 0;
  }
  if (request->hasParam("fps")) {
    streamFps = request->getParam("fps")->value().toInt();
    if (streamFps < 1) streamFps = 1;
    if (streamFps > 60) streamFps = 60;
  }
  request->send(200, "text/plain", "Config updated");
}


void setup()
{
  Serial.begin(115200);

  WiFi.config(camIp, gateway, subnetMask);
  WiFi.begin(ssid, password);
  Serial.println("Connecting to wifi");

  while (WiFi.status() != WL_CONNECTED)
  {
    Serial.println(".");
    delay(500);
  }
  Serial.println(WiFi.localIP());

  startCamera();

  server.on("/stream", HTTP_GET, Stream);
  server.on("/config", HTTP_GET, Config);
  server.begin();

  Serial.println("Server Started");
}

void loop()
{

}


