#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <TinyGPS++.h>

// WiFi credentials
const char* ssid = "wamulehi";
const char* password = "YOUR_WIFI_PASSWORD";


// Backend configuration
const char* backendUrl = "http://your-backend-url:8001";
const char* cattleId = "cattle_001";  // Unique ID for this cattle
const char* authToken = "your-firebase-auth-token"; // Firebase ID token

// Data sending interval
const unsigned long DATA_SEND_INTERVAL = 10000; // Send data every 10 seconds
unsigned long lastDataSend = 0;

Adafruit_MPU6050 mpu;


#define RXD2 16
#define TXD2 17
#define GPS_BAUD 9600

// GPS objects
TinyGPSPlus gps;
HardwareSerial gpsSerial(2);

// Timing variables
unsigned long lastSensorRead = 0;
unsigned long sensorInterval = 5000; // Read sensors every 1 second

// Motion detection variables
float lastAccelX = 0, lastAccelY = 0, lastAccelZ = 0;
float filteredAccelX = 0, filteredAccelY = 0, filteredAccelZ = 0;
float motionThreshold = 0.5; // Adjust based on cattle movement sensitivity
bool isMoving = false;
unsigned long lastMotionTime = 0;
unsigned long motionTimeout = 5000; 
int motionCount = 0;
unsigned long activityStartTime = 0;
bool wasMoving = false;

// Low-pass filter coefficient 
const float FILTER_ALPHA = 0.8;

// GPS reliability tracking
unsigned long lastValidGPS = 0;
const unsigned long GPS_TIMEOUT = 30000; // 30 seconds

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

struct MovementProfile {
  float avgSpeed;
  float maxSpeed;
  float motionVariance;
  int directionChanges;
  unsigned long profileStartTime;
};

// Behavior detection variables
BehaviorData behavior;
MovementProfile movementProfile;
float speedHistory[10] = {0}; // Rolling speed history
int speedHistoryIndex = 0;
float lastHeading = -1;
int suddenDirectionChanges = 0;
unsigned long lastDirectionChange = 0;

// Thresholds 
const float GRAZING_SPEED_MAX = 0.8;        // km/h
const float WALKING_SPEED_MIN = 0.8;        // km/h  
const float WALKING_SPEED_MAX = 4.0;        // km/h
const float RUNNING_SPEED_MIN = 4.0;        // km/h
const float PREDATOR_SPEED_THRESHOLD = 8.0; // km/h - sudden speed
const float HIGH_MOTION_THRESHOLD = 2.0;    // m/s² - for agitated movement
const int MAX_DIRECTION_CHANGES = 5;        // per minute for alert
const unsigned long BEHAVIOR_MIN_DURATION = 10000; // 10 seconds minimum

// Activity tracking
struct ActivityMetrics {
  unsigned long totalActiveTime;
  unsigned long totalRestTime;
  unsigned long dailySteps;
  float dailyDistance;
  unsigned long lastResetTime;
  unsigned long longestRestPeriod;
  unsigned long longestActivePeriod;
};

ActivityMetrics dailyActivity;

void setup(void) {
  Serial.begin(115200);
  while (!Serial)
    delay(10);

  Serial.println("=== Enhanced Cattle Tracking System ===");
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

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
  dailyActivity.longestRestPeriod = 0;
  dailyActivity.longestActivePeriod = 0;
  
  // Initialize MPU6050
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  Serial.println("MPU6050 Found!");

  // Configure MPU6050
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  Serial.print("Accelerometer range set to: ");
  switch (mpu.getAccelerometerRange()) {
  case MPU6050_RANGE_2_G:
    Serial.println("+-2G");
    break;
  case MPU6050_RANGE_4_G:
    Serial.println("+-4G");
    break;
  case MPU6050_RANGE_8_G:
    Serial.println("+-8G");
    break;
  case MPU6050_RANGE_16_G:
    Serial.println("+-16G");
    break;
  }
  
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  Serial.print("Gyro range set to: ");
  switch (mpu.getGyroRange()) {
  case MPU6050_RANGE_250_DEG:
    Serial.println("+- 250 deg/s");
    break;
  case MPU6050_RANGE_500_DEG:
    Serial.println("+- 500 deg/s");
    break;
  case MPU6050_RANGE_1000_DEG:
    Serial.println("+- 1000 deg/s");
    break;
  case MPU6050_RANGE_2000_DEG:
    Serial.println("+- 2000 deg/s");
    break;
  }

  mpu.setFilterBandwidth(MPU6050_BAND_5_HZ);
  Serial.print("Filter bandwidth set to: ");
  switch (mpu.getFilterBandwidth()) {
  case MPU6050_BAND_260_HZ:
    Serial.println("260 Hz");
    break;
  case MPU6050_BAND_184_HZ:
    Serial.println("184 Hz");
    break;
  case MPU6050_BAND_94_HZ:
    Serial.println("94 Hz");
    break;
  case MPU6050_BAND_44_HZ:
    Serial.println("44 Hz");
    break;
  case MPU6050_BAND_21_HZ:
    Serial.println("21 Hz");
    break;
  case MPU6050_BAND_10_HZ:
    Serial.println("10 Hz");
    break;
  case MPU6050_BAND_5_HZ:
    Serial.println("5 Hz");
    break;
  }

  // Initialize GPS
  gpsSerial.begin(GPS_BAUD, SERIAL_8N1, RXD2, TXD2);
  Serial.println("GPS Serial started at 9600 baud rate");
  
  Serial.println("\n===  Cattle Tracking System Initialized ===");
  Serial.println("Motion Detection: ACTIVE");
  Serial.println("Behavior Analysis: ACTIVE");
  Serial.println("Threshold: " + String(motionThreshold) + " m/s²");
  Serial.println("=== Setup Complete ===\n");
  delay(100);
}

// Data validation function
bool isValidAccelerationReading(float x, float y, float z) {
  return (abs(x) <= 20 && abs(y) <= 20 && abs(z) <= 20);
}

// Activity tracking function
void updateActivityMetrics(bool isCurrentlyMoving, float speed, unsigned long currentTime) {
  static unsigned long lastUpdate = 0;
  static bool wasActive = false;
  static unsigned long currentActivityStart = 0;
  static unsigned long currentRestStart = 0;
  
  if (lastUpdate == 0) {
    lastUpdate = currentTime;
    return;
  }
  
  unsigned long deltaTime = currentTime - lastUpdate;
  lastUpdate = currentTime;
  
  // Reset daily metrics at midnight (24 hours)
  if (currentTime - dailyActivity.lastResetTime > 86400000) { // 24 hours
    Serial.println("📊 DAILY RESET - Previous day stats:");
    printDailyActivitySummary();
    
    dailyActivity.totalActiveTime = 0;
    dailyActivity.totalRestTime = 0;
    dailyActivity.dailySteps = 0;
    dailyActivity.dailyDistance = 0;
    dailyActivity.longestRestPeriod = 0;
    dailyActivity.longestActivePeriod = 0;
    dailyActivity.lastResetTime = currentTime;
  }
  
  // Track activity periods
  if (isCurrentlyMoving) {
    dailyActivity.totalActiveTime += deltaTime;
    
    if (!wasActive) {
      currentActivityStart = currentTime;
      // End rest period
      if (currentRestStart > 0) {
        unsigned long restDuration = currentTime - currentRestStart;
        if (restDuration > dailyActivity.longestRestPeriod) {
          dailyActivity.longestRestPeriod = restDuration;
        }
      }
    }
    
    // Estimate steps and distance
    if (speed > 0.5) { // Only count if moving with reasonable speed
      dailyActivity.dailyDistance += (speed * deltaTime / 3600000.0); // Convert to km
      // Rough step estimation (cattle: ~0.7m per step at walking pace)
      if (speed > 1.0 && speed < 5.0) {
        dailyActivity.dailySteps += (deltaTime / 1000.0) * (speed / 2.52); // Rough step rate
      }
    }
  } else {
    dailyActivity.totalRestTime += deltaTime;
    
    if (wasActive) {
      // End activity period
      if (currentActivityStart > 0) {
        unsigned long activityDuration = currentTime - currentActivityStart;
        if (activityDuration > dailyActivity.longestActivePeriod) {
          dailyActivity.longestActivePeriod = activityDuration;
        }
      }
      currentRestStart = currentTime;
    }
  }
  
  wasActive = isCurrentlyMoving;
}

// Print daily activity summary
void printDailyActivitySummary() {
  Serial.println("\n--- DAILY ACTIVITY SUMMARY ---");
  Serial.print("Total Active Time: ");
  Serial.print(dailyActivity.totalActiveTime / 3600000.0, 1);
  Serial.println(" hours");
  
  Serial.print("Total Rest Time: ");
  Serial.print(dailyActivity.totalRestTime / 3600000.0, 1);
  Serial.println(" hours");
  
  Serial.print("Estimated Steps: ");
  Serial.println((int)dailyActivity.dailySteps);
  
  Serial.print("Estimated Distance: ");
  Serial.print(dailyActivity.dailyDistance, 2);
  Serial.println(" km");
  
  Serial.print("Longest Rest Period: ");
  Serial.print(dailyActivity.longestRestPeriod / 3600000.0, 1);
  Serial.println(" hours");
  
  Serial.print("Longest Active Period: ");
  Serial.print(dailyActivity.longestActivePeriod / 3600000.0, 1);
  Serial.println(" hours");
  
  // Activity percentage
  unsigned long totalTime = dailyActivity.totalActiveTime + dailyActivity.totalRestTime;
  if (totalTime > 0) {
    float activityPercentage = (dailyActivity.totalActiveTime * 100.0) / totalTime;
    Serial.print("Activity Percentage: ");
    Serial.print(activityPercentage, 1);
    Serial.println("%");
  }
}

// Behavior analysis function
CattleBehavior analyzeCattleBehavior(float currentSpeed, float motionMagnitude, bool hasValidGPS) {
  
  // Update speed history
  speedHistory[speedHistoryIndex] = currentSpeed;
  speedHistoryIndex = (speedHistoryIndex + 1) % 10;
  
  // Calculate speed statistics
  float avgSpeed = 0;
  float maxSpeed = 0;
  for(int i = 0; i < 10; i++) {
    avgSpeed += speedHistory[i];
    if(speedHistory[i] > maxSpeed) maxSpeed = speedHistory[i];
  }
  avgSpeed /= 10;
  
  // Calculate speed variance for erratic behavior detection
  float variance = 0;
  for(int i = 0; i < 10; i++) {
    variance += pow(speedHistory[i] - avgSpeed, 2);
  }
  variance /= 10;
  
  // Direction change detection (if GPS valid and has course data)
  if(hasValidGPS && gps.course.isValid()) {
    float currentHeading = gps.course.deg();
    if(lastHeading >= 0) {
      float headingDiff = abs(currentHeading - lastHeading);
      if(headingDiff > 180) headingDiff = 360 - headingDiff; // Handle wrap-around
      
      if(headingDiff > 45) { // Significant direction change
        suddenDirectionChanges++;
        lastDirectionChange = millis();
      }
    }
    lastHeading = currentHeading;
  }
  
  // Reset direction change counter every minute
  if(millis() - lastDirectionChange > 60000) {
    suddenDirectionChanges = 0;
  }
  
  // PREDATOR/DANGER DETECTION (Highest Priority)
  if(currentSpeed > PREDATOR_SPEED_THRESHOLD || 
     (motionMagnitude > HIGH_MOTION_THRESHOLD && currentSpeed > RUNNING_SPEED_MIN) ||
     (suddenDirectionChanges > MAX_DIRECTION_CHANGES && variance > 2.0)) {
    return ALERT_PREDATOR;
  }
  
  // UNUSUAL BEHAVIOR DETECTION
  if(variance > 1.5 || // Highly erratic speed
     (suddenDirectionChanges > 3 && currentSpeed > WALKING_SPEED_MIN) ||
     (motionMagnitude > HIGH_MOTION_THRESHOLD && currentSpeed < GRAZING_SPEED_MAX)) {
    return ALERT_UNUSUAL;
  }
  
  // NORMAL BEHAVIOR CLASSIFICATION
  if(currentSpeed < GRAZING_SPEED_MAX && motionMagnitude < 1.0) {
    if(motionMagnitude < 0.3) {
      return RESTING;
    } else {
      return GRAZING; // Low speed, moderate motion (head movement while eating)
    }
  } else if(currentSpeed >= WALKING_SPEED_MIN && currentSpeed < WALKING_SPEED_MAX) {
    return WALKING;
  } else if(currentSpeed >= RUNNING_SPEED_MIN && currentSpeed < PREDATOR_SPEED_THRESHOLD) {
    return RUNNING; // Normal running, not panic
  } else {
    return RESTING; // Default fallback
  }
}

// Get behavior description
String getBehaviorDescription(CattleBehavior behavior, float confidence) {
  switch(behavior) {
    case RESTING:
      return "🛌 RESTING (Confidence: " + String(confidence, 1) + "%)";
    case GRAZING:
      return "🌱 GRAZING (Confidence: " + String(confidence, 1) + "%)";
    case WALKING:
      return "🚶 WALKING (Confidence: " + String(confidence, 1) + "%)";
    case RUNNING:
      return "🏃 RUNNING (Confidence: " + String(confidence, 1) + "%)";
    case ALERT_UNUSUAL:
      return "⚠️ UNUSUAL BEHAVIOR (Confidence: " + String(confidence, 1) + "%)";
    case ALERT_PREDATOR:
      return "🚨 PREDATOR ALERT! (Confidence: " + String(confidence, 1) + "%)";
    default:
      return "❓ UNKNOWN";
  }
}

// Update behavior analysis
void updateBehaviorAnalysis(float currentSpeed, float motionMagnitude, bool hasValidGPS) {
  
  // Analyze current behavior
  CattleBehavior newBehavior = analyzeCattleBehavior(currentSpeed, motionMagnitude, hasValidGPS);
  
  // Calculate confidence based on data quality and consistency
  float confidence = 50.0; // Base confidence
  if(hasValidGPS) confidence += 30.0;
  if(gps.hdop.isValid() && gps.hdop.value() < 200) confidence += 10.0; // Good GPS accuracy
  if(gps.satellites.value() > 6) confidence += 10.0;
  confidence = min(confidence, 99.0f);
  
  // Check for behavior change
  if(newBehavior != behavior.currentBehavior) {
    // Only change if minimum duration has passed (avoid rapid switching)
    if(millis() - behavior.behaviorStartTime > BEHAVIOR_MIN_DURATION) {
      behavior.previousBehavior = behavior.currentBehavior;
      behavior.currentBehavior = newBehavior;
      behavior.behaviorStartTime = millis();
      behavior.confidence = confidence;
      
      Serial.println("🔄 BEHAVIOR CHANGE DETECTED!");
      Serial.println("Previous: " + getBehaviorDescription(behavior.previousBehavior, behavior.confidence));
      Serial.println("Current: " + getBehaviorDescription(behavior.currentBehavior, confidence));
      
      // CRITICAL ALERTS - Send immediately to backend/farmer
      if(newBehavior == ALERT_PREDATOR || newBehavior == ALERT_UNUSUAL) {
        Serial.println("🚨🚨🚨 CRITICAL ALERT - IMMEDIATE NOTIFICATION REQUIRED! 🚨🚨🚨");
        // Here you would trigger immediate notification
        // sendCriticalAlert(behavior.currentBehavior, gps.location.lat(), gps.location.lng());
      }
    }
  } else {
    // Update confidence for current behavior
    behavior.confidence = (behavior.confidence * 0.8) + (confidence * 0.2); // Smooth confidence
  }
  
  // Update behavior duration
  behavior.behaviorDuration = millis() - behavior.behaviorStartTime;
}

// Print behavior status
void printBehaviorStatus() {
  Serial.println("--- BEHAVIOR ANALYSIS ---");
  Serial.println("Current: " + getBehaviorDescription(behavior.currentBehavior, behavior.confidence));
  Serial.print("Duration: ");
  Serial.print(behavior.behaviorDuration / 1000);
  Serial.println(" seconds");
  
  if(behavior.previousBehavior != behavior.currentBehavior) {
    Serial.println("Previous: " + getBehaviorDescription(behavior.previousBehavior, behavior.confidence));
  }
  
  // Calculate current speed variance for diagnostics
  float avgSpeed = 0;
  for(int i = 0; i < 10; i++) {
    avgSpeed += speedHistory[i];
  }
  avgSpeed /= 10;
  
  float variance = 0;
  for(int i = 0; i < 10; i++) {
    variance += pow(speedHistory[i] - avgSpeed, 2);
  }
  variance /= 10;
  
  // Additional diagnostic info for alerts
  if(behavior.currentBehavior == ALERT_PREDATOR || behavior.currentBehavior == ALERT_UNUSUAL) {
    Serial.print("⚡ Direction changes (last min): ");
    Serial.println(suddenDirectionChanges);
    Serial.print("📊 Speed variance: ");
    Serial.println(sqrt(variance), 3);
    Serial.print("📈 Avg Speed (10s): ");
    Serial.print(avgSpeed, 1);
    Serial.println(" km/h");
  }
}

void loop() {
  if (millis() - lastDataSend >= DATA_SEND_INTERVAL) {
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    
    float activity_level = sqrt(pow(a.acceleration.x, 2) + 
                              pow(a.acceleration.y, 2) + 
                              pow(a.acceleration.z, 2));
    
    // Using dummy GPS values for testing
    float latitude = -15.3875;
    float longitude = 28.3228;
    
    sendDataToBackend(temp.temperature, activity_level, latitude, longitude);
    lastDataSend = millis();
  }
  
  delay(100);
}

// Function to send sensor data to backend
void sendDataToBackend(float temperature, float activity_level, float latitude, float longitude) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(backendUrl) + "/cattle/live-data";
    http.begin(url);
    
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", String("Bearer ") + authToken);
    
    StaticJsonDocument<200> doc;
    doc["cattle_id"] = cattleId;
    doc["temperature"] = temperature;
    doc["activity_level"] = activity_level;
    doc["location"] = {
      "latitude": latitude,
      "longitude": longitude
    };
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    int httpResponseCode = http.POST(jsonString);
    
    if (httpResponseCode > 0) {
      Serial.println("HTTP Response code: " + String(httpResponseCode));
    } else {
      Serial.println("Error sending data. Error code: " + String(httpResponseCode));
    }
    
    http.end();
  }
}