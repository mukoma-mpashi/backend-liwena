#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>
#include <TinyGPSPlus.h>
#include <SoftwareSerial.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <ArduinoJson.h>
#include <time.h>

// Function prototypes
void sendSensorDataToBackend();
String getCurrentISOTimestamp();

// WiFi credentials
const char* ssid PROGMEM = "Google";
const char* password PROGMEM = "Gr33nw377";

// GPS Configuration
static const int RXPin = D5;  // GPIO14
static const int TXPin = D6;  // GPIO12
SoftwareSerial gpsSerial(RXPin, TXPin);
TinyGPSPlus gps;

// MPU6050 Configuration
Adafruit_MPU6050 mpu;

// Backend Configuration (UPDATED)
const char* backendHost PROGMEM = "cattle-monitoring.onrender.com";
// Secondary backend (Uncomment if needed)


// NTP Configuration for timestamp
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 10800;  // 3 hours for East Africa Time (UTC+3)
const int daylightOffset_sec = 0;

// Data transmission control
const unsigned long SEND_INTERVAL = 15000;  // 15 seconds
unsigned long lastSendTime = 0;
bool mpuInitialized = false;
String deviceId;

void setup() {
  Serial.begin(115200);
  gpsSerial.begin(9600);
  
  // Generate unique device ID from MAC address
  deviceId = String(ESP.getChipId(), HEX);
  deviceId.toUpperCase();
  
  // Initialize I2C for MPU6050
  Wire.begin(D2, D1);  // SDA (D2/GPIO4), SCL (D1/GPIO5)
  
  // Initialize WiFi
  WiFi.begin(FPSTR(ssid), FPSTR(password));
  Serial.print(F("Connecting to WiFi"));
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(F("."));
  }
  Serial.print(F("\nConnected! IP: "));
  Serial.println(WiFi.localIP());
  
  // Configure time
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  Serial.println(F("Waiting for NTP time sync..."));
  delay(2000);
  Serial.println(F("Current time: ") + getCurrentISOTimestamp());
  
  // Initialize MPU6050
  if (mpu.begin()) {
    mpuInitialized = true;
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
    Serial.println(F("MPU6050 initialized"));
  } else {
    Serial.println(F("Failed to initialize MPU6050!"));
  }
}

void loop() {
  // Process GPS data
  while (gpsSerial.available() > 0) {
    if (gps.encode(gpsSerial.read())) {
      // Minimal GPS processing
    }
  }

  // Send data at intervals
  if (millis() - lastSendTime >= SEND_INTERVAL) {
    if (WiFi.status() == WL_CONNECTED) {
      sendSensorDataToBackend();
    } else {
      Serial.println(F("WiFi disconnected. Reconnecting..."));
      WiFi.reconnect();
    }
    lastSendTime = millis();
  }
  
  delay(10);
}

void ICACHE_FLASH_ATTR sendSensorDataToBackend() {
  // Use ArduinoJson to build the JSON payload in the EXACT format needed by the Firebase DB
  StaticJsonDocument<1024> doc;
  
  // Hardcoded cattle_id for this specific device
  doc["cattle_id"] = "cattle1";
  
  // Add timestamp in ISO 8601 format
  doc["timestamp"] = getCurrentISOTimestamp();
  
  // Add GPS data if valid
  float latitude = -1.2921; // Default Nairobi location
  float longitude = 36.8219;
  bool gps_fix = false;
  
  if (gps.location.isValid() && gps.location.age() < 2000) {
    latitude = gps.location.lat();
    longitude = gps.location.lng();
    gps_fix = true;
    Serial.println(F("Valid GPS data added"));
  } else {
    Serial.println(F("No valid GPS data, using default location"));
  }
  
  doc["latitude"] = latitude;
  doc["longitude"] = longitude;
  doc["gps_fix"] = gps_fix;
  
  // Movement data
  bool is_moving = false;
  float speed_kmh = 0.0;
  float heading = 0.0;
  
  if (gps.speed.isValid()) {
    speed_kmh = gps.speed.kmph();
    is_moving = speed_kmh > 0.5; // Moving if speed > 0.5 km/h
  }
  
  if (gps.course.isValid()) {
    heading = gps.course.deg();
  } else {
    // Default heading (east)
    heading = 90.0;
  }
  
  doc["speed_kmh"] = speed_kmh;
  doc["heading"] = heading;
  doc["is_moving"] = is_moving;
  
  // Add MPU6050 data in the format expected by the DB
  JsonObject acceleration = doc.createNestedObject("acceleration");
  JsonObject behavior = doc.createNestedObject("behavior");
  JsonObject activity = doc.createNestedObject("activity");
  
  // Default activity metrics
  activity["daily_distance_km"] = 2.8;
  activity["daily_steps"] = 1250;
  activity["total_active_time_seconds"] = 7200;
  activity["total_rest_time_seconds"] = 3600;
  
  if (mpuInitialized) {
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    
    // Set acceleration values
    acceleration["x"] = a.acceleration.x;
    acceleration["y"] = a.acceleration.y;
    acceleration["z"] = a.acceleration.z;
    
    // Calculate acceleration magnitude for behavior detection
    float accel_magnitude = sqrt(
      a.acceleration.x * a.acceleration.x +
      a.acceleration.y * a.acceleration.y +
      a.acceleration.z * a.acceleration.z
    );
    
    // Calculate gyro magnitude for behavior detection
    float gyro_magnitude = sqrt(
      g.gyro.x * g.gyro.x +
      g.gyro.y * g.gyro.y +
      g.gyro.z * g.gyro.z
    );
    
    // Determine behavior based on sensor data
    const char* current_behavior;
    float confidence;
    
    if (is_moving && gyro_magnitude > 0.5) {
      current_behavior = "walking";
      confidence = 85.5;
    } else if (abs(a.acceleration.z - 9.8) < 0.5 && gyro_magnitude < 0.2) {
      current_behavior = "resting";
      confidence = 92.0;
    } else {
      current_behavior = "grazing";
      confidence = 85.5;
    }
    
    // Set behavior values
    behavior["current"] = current_behavior;
    behavior["previous"] = "resting";
    behavior["duration_seconds"] = 300;
    behavior["confidence"] = confidence;
    
    Serial.print(F("Behavior detected: "));
    Serial.println(current_behavior);
  } else {
    // Default values if MPU not initialized
    acceleration["x"] = 0.1;
    acceleration["y"] = 0.2;
    acceleration["z"] = 9.8;
    
    behavior["current"] = "unknown";
    behavior["previous"] = "unknown";
    behavior["duration_seconds"] = 0;
    behavior["confidence"] = 50.0;
    
    Serial.println(F("MPU6050 not initialized, using default values"));
  }

  // Serialize JSON to String
  String jsonPayload;
  serializeJson(doc, jsonPayload);

  Serial.print(F("JSON Payload: "));
  Serial.println(jsonPayload);

  // Create secure client
  WiFiClientSecure client;
  HTTPClient http;

  // Configure WiFiClientSecure to skip certificate verification
  client.setInsecure(); // Skip verification (use with caution)
  
  // Construct Backend URL - Direct to Firebase option
  // String url = "https://cattlemonitor-57c45-default-rtdb.firebaseio.com/cattle_live_data/cattle1.json?auth=" + String(FPSTR(firebaseSecret));
  
  // Construct Backend URL - Using your FastAPI backend
  String url = "https://" + String(FPSTR(backendHost)) + "/cattle/live-data";
  
  Serial.print(F("Sending to: "));
  Serial.println(url);

  // Send to Backend
  if (http.begin(client, url)) {
    http.addHeader("Content-Type", "application/json");
    
    int httpCode = http.POST(jsonPayload);
    
    if (httpCode > 0) {
      Serial.printf("HTTP code: %d\n", httpCode);
      if (httpCode == HTTP_CODE_OK || httpCode == HTTP_CODE_CREATED) {
        String response = http.getString();
        Serial.print(F("Backend response: "));
        Serial.println(response);
      }
    } else {
      Serial.printf("HTTP failed, error: %s\n", http.errorToString(httpCode).c_str());
    }
    http.end();
  } else {
    Serial.println(F("Failed to connect to backend"));
  }
}

// Helper function to get ISO timestamp
String getCurrentISOTimestamp() {
  time_t now;
  struct tm timeinfo;
  
  time(&now);
  localtime_r(&now, &timeinfo);
  
  char timestamp[25];
  
  // Format: YYYY-MM-DDThh:mm:ss.000Z
  sprintf(timestamp, "%04d-%02d-%02dT%02d:%02d:%02d.000Z", 
          timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
          timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
  
  return String(timestamp);
}
