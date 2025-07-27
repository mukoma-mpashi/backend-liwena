#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <TinyGPS++.h>

// WiFi credentials
const char* ssid = "robotics club";
const char* password = "cburobotics.";

// Backend configuration
const String BACKEND_URL = "https://your-backend-url.com"; // Replace with your actual backend URL
const String LIVE_DATA_ENDPOINT = "/cattle/live-data";

// MPU6050 object
Adafruit_MPU6050 mpu;

// GPS configuration
#define RXD2 16
#define TXD2 17
#define GPS_BAUD 9600

// GPS objects
TinyGPSPlus gps;
HardwareSerial gpsSerial(2);

// Cattle identification
String cattleId = "cattle_001"; // This should be unique for each device

// Timing variables
unsigned long lastSensorRead = 0;
unsigned long lastDataSend = 0;
const unsigned long SENSOR_INTERVAL = 1000;  // Read sensors every 1 second
const unsigned long SEND_INTERVAL = 30000;   // Send data every 30 seconds

// Motion detection variables
float lastAccelX = 0, lastAccelY = 0, lastAccelZ = 0;
float filteredAccelX = 0, filteredAccelY = 0, filteredAccelZ = 0;
float motionThreshold = 0.5;
bool isMoving = false;
unsigned long lastMotionTime = 0;
unsigned long motionTimeout = 5000;

// Low-pass filter coefficient
const float FILTER_ALPHA = 0.8;

// GPS reliability tracking
unsigned long lastValidGPS = 0;
const unsigned long GPS_TIMEOUT = 30000;

// Behavior classification
enum CattleBehavior {
  RESTING,
  GRAZING,
  WALKING,
  RUNNING,
  ALERT_UNUSUAL,
  ALERT_PREDATOR
};

struct BehaviorData {
  CattleBehavior currentBehavior;
  CattleBehavior previousBehavior;
  unsigned long behaviorStartTime;
  unsigned long behaviorDuration;
  float confidence;
};

struct ActivityMetrics {
  unsigned long totalActiveTime;
  unsigned long totalRestTime;
  unsigned long dailySteps;
  float dailyDistance;
  unsigned long lastResetTime;
  unsigned long longestRestPeriod;
  unsigned long longestActivePeriod;
};

// Current sensor data
BehaviorData behavior;
ActivityMetrics dailyActivity;
float currentLat = -1.2921;  // Default to Nairobi
float currentLng = 36.8219;
float currentSpeed = 0.0;
float currentHeading = 0.0;
bool gpsFixValid = false;

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);

  Serial.println("=== Enhanced Cattle Tracking System for Backend Integration ===");
  
  // Initialize behavior data
  behavior.currentBehavior = RESTING;
  behavior.previousBehavior = RESTING;
  behavior.behaviorStartTime = millis();
  behavior.behaviorDuration = 0;
  behavior.confidence = 50.0;
  
  // Initialize activity metrics
  dailyActivity.totalActiveTime = 0;
  dailyActivity.totalRestTime = 0;
  dailyActivity.dailySteps = 0;
  dailyActivity.dailyDistance = 0;
  dailyActivity.lastResetTime = millis();
  
  // Initialize MPU6050
  if (!mpu.begin()) {
    Serial.println("❌ Failed to find MPU6050 chip");
    while (1) delay(10);
  }
  Serial.println("✅ MPU6050 Found!");

  // Configure MPU6050
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_5_HZ);

  // Initialize GPS
  gpsSerial.begin(GPS_BAUD, SERIAL_8N1, RXD2, TXD2);
  Serial.println("✅ GPS Serial started");
  
  // Connect to WiFi
  connectToWiFi();
  
  Serial.println("🎯 System ready for backend integration!");
}

void loop() {
  unsigned long currentTime = millis();
  
  // Read sensors at regular intervals
  if (currentTime - lastSensorRead >= SENSOR_INTERVAL) {
    readSensors();
    updateBehavior();
    updateActivityMetrics();
    lastSensorRead = currentTime;
  }
  
  // Send data to backend at regular intervals
  if (currentTime - lastDataSend >= SEND_INTERVAL) {
    sendDataToBackend();
    lastDataSend = currentTime;
  }
  
  delay(100);
}

void connectToWiFi() {
  Serial.print("🌐 Connecting to WiFi");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi connected!");
    Serial.println("IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\n❌ WiFi failed. Restarting...");
    ESP.restart();
  }
}

void readSensors() {
  // Read accelerometer
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  
  // Apply low-pass filter
  filteredAccelX = FILTER_ALPHA * filteredAccelX + (1 - FILTER_ALPHA) * a.acceleration.x;
  filteredAccelY = FILTER_ALPHA * filteredAccelY + (1 - FILTER_ALPHA) * a.acceleration.y;
  filteredAccelZ = FILTER_ALPHA * filteredAccelZ + (1 - FILTER_ALPHA) * a.acceleration.z;
  
  // Calculate motion
  float deltaX = abs(filteredAccelX - lastAccelX);
  float deltaY = abs(filteredAccelY - lastAccelY);
  float deltaZ = abs(filteredAccelZ - lastAccelZ);
  float totalMotion = sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
  
  if (totalMotion > motionThreshold) {
    isMoving = true;
    lastMotionTime = millis();
  } else if (millis() - lastMotionTime > motionTimeout) {
    isMoving = false;
  }
  
  lastAccelX = filteredAccelX;
  lastAccelY = filteredAccelY;
  lastAccelZ = filteredAccelZ;
  
  // Read GPS
  while (gpsSerial.available() > 0) {
    if (gps.encode(gpsSerial.read())) {
      if (gps.location.isValid()) {
        currentLat = gps.location.lat();
        currentLng = gps.location.lng();
        gpsFixValid = true;
        lastValidGPS = millis();
        
        if (gps.speed.isValid()) {
          currentSpeed = gps.speed.kmph();
        }
        
        if (gps.course.isValid()) {
          currentHeading = gps.course.deg();
        }
      }
    }
  }
  
  // Check GPS timeout
  if (millis() - lastValidGPS > GPS_TIMEOUT) {
    gpsFixValid = false;
  }
}

void updateBehavior() {
  CattleBehavior newBehavior = behavior.currentBehavior;
  
  // Simple behavior classification based on motion and speed
  if (!isMoving) {
    newBehavior = RESTING;
  } else if (currentSpeed < 0.8) {
    newBehavior = GRAZING;
  } else if (currentSpeed < 4.0) {
    newBehavior = WALKING;
  } else {
    newBehavior = RUNNING;
  }
  
  // Update behavior if changed
  if (newBehavior != behavior.currentBehavior) {
    behavior.previousBehavior = behavior.currentBehavior;
    behavior.currentBehavior = newBehavior;
    behavior.behaviorStartTime = millis();
  }
  
  behavior.behaviorDuration = millis() - behavior.behaviorStartTime;
  behavior.confidence = 75.0 + random(0, 25); // Simulate confidence
}

void updateActivityMetrics() {
  unsigned long currentTime = millis();
  unsigned long deltaTime = currentTime - dailyActivity.lastResetTime;
  
  if (isMoving) {
    dailyActivity.totalActiveTime += deltaTime;
    dailyActivity.dailySteps += random(0, 3); // Simulate step counting
    dailyActivity.dailyDistance += (currentSpeed * deltaTime) / 3600000.0; // Convert to km
  } else {
    dailyActivity.totalRestTime += deltaTime;
  }
  
  dailyActivity.lastResetTime = currentTime;
}

void sendDataToBackend() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi not connected, skipping data send");
    return;
  }
  
  Serial.println("📡 Sending data to backend...");
  
  // Create JSON payload matching CattleSensorData model
  DynamicJsonDocument doc(2048);
  
  doc["cattle_id"] = cattleId;
  doc["timestamp"] = getCurrentTimestamp();
  doc["latitude"] = currentLat;
  doc["longitude"] = currentLng;
  doc["gps_fix"] = gpsFixValid;
  doc["speed_kmh"] = currentSpeed;
  doc["heading"] = currentHeading;
  doc["is_moving"] = isMoving;
  
  // Acceleration data
  JsonObject accel = doc.createNestedObject("acceleration");
  accel["x"] = filteredAccelX;
  accel["y"] = filteredAccelY;
  accel["z"] = filteredAccelZ;
  
  // Behavior data
  JsonObject behaviorObj = doc.createNestedObject("behavior");
  behaviorObj["current"] = behaviorToString(behavior.currentBehavior);
  behaviorObj["previous"] = behaviorToString(behavior.previousBehavior);
  behaviorObj["duration_seconds"] = behavior.behaviorDuration / 1000;
  behaviorObj["confidence"] = behavior.confidence;
  
  // Activity data
  JsonObject activity = doc.createNestedObject("activity");
  activity["total_active_time_seconds"] = dailyActivity.totalActiveTime / 1000;
  activity["total_rest_time_seconds"] = dailyActivity.totalRestTime / 1000;
  activity["daily_steps"] = dailyActivity.dailySteps;
  activity["daily_distance_km"] = dailyActivity.dailyDistance;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  // Send to backend
  HTTPClient http;
  http.begin(BACKEND_URL + LIVE_DATA_ENDPOINT);
  http.addHeader("Content-Type", "application/json");
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    if (httpResponseCode == 200) {
      Serial.println("✅ Data sent successfully!");
      Serial.println("Response: " + response);
    } else {
      Serial.println("⚠️ Server response: " + String(httpResponseCode));
      Serial.println("Response: " + response);
    }
  } else {
    Serial.println("❌ HTTP Error: " + String(httpResponseCode));
  }
  
  http.end();
  
  // Print summary
  Serial.println("📊 Current Status:");
  Serial.println("   Location: " + String(currentLat, 6) + ", " + String(currentLng, 6));
  Serial.println("   GPS Fix: " + String(gpsFixValid ? "Yes" : "No"));
  Serial.println("   Speed: " + String(currentSpeed) + " km/h");
  Serial.println("   Moving: " + String(isMoving ? "Yes" : "No"));
  Serial.println("   Behavior: " + behaviorToString(behavior.currentBehavior));
  Serial.println("   Daily Steps: " + String(dailyActivity.dailySteps));
  Serial.println("   Daily Distance: " + String(dailyActivity.dailyDistance, 2) + " km");
}

String behaviorToString(CattleBehavior behavior) {
  switch (behavior) {
    case RESTING: return "resting";
    case GRAZING: return "grazing";
    case WALKING: return "walking";
    case RUNNING: return "running";
    case ALERT_UNUSUAL: return "alert_unusual";
    case ALERT_PREDATOR: return "alert_predator";
    default: return "unknown";
  }
}

String getCurrentTimestamp() {
  // For simplicity, using millis(). In production, use NTP time
  return String(millis());
}
