#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <TinyGPS++.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "robotics";
const char* password = "cburobotics.";

// Backend configuration
const String BACKEND_URL = "http://10.90.9.105:8001"; // Your laptop's IP address
const String LIVE_DATA_ENDPOINT = "/cattle/live-data";

// Cattle identification
String cattleId = "cattle1"; // This device is for cattle1

// MPU6050 object
Adafruit_MPU6050 mpu;

// GPS configuration
#define RXD2 16
#define TXD2 17
#define GPS_BAUD 9600

// GPS objects
TinyGPSPlus gps;
HardwareSerial gpsSerial(2);

// Timing variables
unsigned long lastSensorRead = 0;
unsigned long lastDataSend = 0;
unsigned long sensorInterval = 1000; // Read sensors every 1 second
unsigned long sendInterval = 30000; // Send data to backend every 30 seconds

// Motion detection variables
float lastAccelX = 0, lastAccelY = 0, lastAccelZ = 0;
float filteredAccelX = 0, filteredAccelY = 0, filteredAccelZ = 0;
float motionThreshold = 0.5; // Adjust based on cattle movement sensitivity
bool isMoving = false;
unsigned long lastMotionTime = 0;
unsigned long motionTimeout = 5000; // 5 seconds - consider stationary after this
int motionCount = 0;
unsigned long activityStartTime = 0;
bool wasMoving = false;

// Low-pass filter coefficient (adjust for more/less smoothing)
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

// Thresholds (adjust based on cattle type/size)
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

  Serial.println("=== Enhanced Cattle Tracking System with Backend Integration ===");
  
  // Connect to WiFi first
  connectToWiFi();
  
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
  
  Serial.println("\n=== Enhanced Cattle Tracking System Initialized ===");
  Serial.println("Motion Detection: ACTIVE");
  Serial.println("Behavior Analysis: ACTIVE");
  Serial.println("Backend Integration: ACTIVE");
  Serial.println("Cattle ID: " + cattleId);
  Serial.println("Backend URL: " + BACKEND_URL + LIVE_DATA_ENDPOINT);
  Serial.println("Threshold: " + String(motionThreshold) + " m/s²");
  Serial.println("=== Setup Complete ===\n");
  delay(100);
}

// WiFi connection function
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
    Serial.println("Signal: " + String(WiFi.RSSI()) + " dBm");
  } else {
    Serial.println("\n❌ WiFi failed. Will retry...");
  }
}

// Send data to backend
void sendDataToBackend() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi not connected, attempting reconnection...");
    connectToWiFi();
    return;
  }
  
  Serial.println("📡 Sending data to backend...");
  
  // Create JSON payload matching CattleSensorData model
  DynamicJsonDocument doc(2048);
  
  // Clear the document first
  doc.clear();
  
  // Add the data
  doc["cattle_id"] = cattleId;
  doc["timestamp"] = getCurrentTimestamp();
  
  // Verify the JSON structure before proceeding
  if (!verifyJson(doc)) {
    Serial.println("❌ Invalid JSON structure - skipping data send");
    return;
  }
  
  // GPS data
  if (gps.location.isValid()) {
    doc["latitude"] = gps.location.lat();
    doc["longitude"] = gps.location.lng();
    doc["gps_fix"] = true;
  } else {
    // Use default Nairobi coordinates if no GPS
    doc["latitude"] = -1.2921;
    doc["longitude"] = 36.8219;
    doc["gps_fix"] = false;
  }
  
  if (gps.speed.isValid()) {
    doc["speed_kmh"] = gps.speed.kmph();
  } else {
    doc["speed_kmh"] = 0.0;
  }
  
  if (gps.course.isValid()) {
    doc["heading"] = gps.course.deg();
  } else {
    doc["heading"] = 0.0;
  }
  
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
  
  // Verify JSON document before sending
  if (!verifyJson(doc)) {
    Serial.println("❌ JSON validation failed, not sending");
    return;
  }

  // Send to backend
  HTTPClient http;
  
  // Print the full URL for debugging
  String fullUrl = BACKEND_URL + LIVE_DATA_ENDPOINT;
  Serial.println("Sending to URL: " + fullUrl);
  Serial.println("JSON payload: " + jsonString);

  // Configure HTTP client
  http.begin(fullUrl);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Accept", "application/json");
  http.addHeader("Connection", "close"); // Important for stability
  
  // Attempt to send the request with timeout
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    if (httpResponseCode == 200) {
      Serial.println("✅ Data sent successfully to backend!");
      Serial.println("Response: " + response);
    } else {
      Serial.println("⚠️ Server response code: " + String(httpResponseCode));
      Serial.println("Response: " + response);
    }
  } else {
    Serial.println("❌ HTTP Error: " + String(httpResponseCode));
    Serial.println("Error: " + http.errorToString(httpResponseCode));
    
    // Additional debug info
    Serial.println("Failed URL: " + fullUrl);
    if (!WiFi.isConnected()) {
      Serial.println("WiFi disconnected - attempting reconnection");
      connectToWiFi();
    }
  }
  
  http.end();
  
  // Print data summary
  Serial.println("📊 Data sent for " + cattleId + ":");
  Serial.println("   Behavior: " + behaviorToString(behavior.currentBehavior));
  Serial.println("   Moving: " + String(isMoving ? "Yes" : "No"));
  Serial.println("   GPS Fix: " + String(gps.location.isValid() ? "Yes" : "No"));
  if (gps.location.isValid()) {
    Serial.println("   Location: " + String(gps.location.lat(), 6) + ", " + String(gps.location.lng(), 6));
  }
  Serial.println("   Daily Steps: " + String((int)dailyActivity.dailySteps));
}

// Convert behavior enum to string
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

// Get current timestamp (simple implementation)
String getCurrentTimestamp() {
  if (gps.date.isValid() && gps.time.isValid()) {
    // Use GPS time if available
    char timestamp[64];
    sprintf(timestamp, "%04d-%02d-%02dT%02d:%02d:%02dZ", 
            gps.date.year(), gps.date.month(), gps.date.day(),
            gps.time.hour(), gps.time.minute(), gps.time.second());
    return String(timestamp);
  } else {
    // Fallback to millis-based timestamp
    return String(millis());
  }
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
  // Continuously read GPS data
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }
  
  // Read and display sensor data at specified interval
  if (millis() - lastSensorRead >= sensorInterval) {
    lastSensorRead = millis();
    
    // Read MPU6050 data
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    
    // Data validation
    if (!isValidAccelerationReading(a.acceleration.x, a.acceleration.y, a.acceleration.z)) {
      Serial.println("⚠️ Suspicious acceleration reading - sensor check needed");
      return; // Skip this reading
    }
    
    // Motion Detection Algorithm with Low-Pass Filtering
    float accelX = a.acceleration.x;
    float accelY = a.acceleration.y;
    float accelZ = a.acceleration.z;
    
    // Apply low-pass filter to reduce noise
    filteredAccelX = FILTER_ALPHA * filteredAccelX + (1 - FILTER_ALPHA) * accelX;
    filteredAccelY = FILTER_ALPHA * filteredAccelY + (1 - FILTER_ALPHA) * accelY;
    filteredAccelZ = FILTER_ALPHA * filteredAccelZ + (1 - FILTER_ALPHA) * accelZ;
    
    // Calculate motion magnitude using filtered data
    float motionMagnitude = sqrt(pow(filteredAccelX - lastAccelX, 2) + 
                                pow(filteredAccelY - lastAccelY, 2) + 
                                pow(filteredAccelZ - lastAccelZ, 2));
    
    // Calculate total acceleration magnitude for additional analysis
    float totalAccelMagnitude = sqrt(pow(filteredAccelX, 2) + pow(filteredAccelY, 2) + pow(filteredAccelZ, 2));
    
    // Update motion status
    if (motionMagnitude > motionThreshold) {
      if (!isMoving) {
        isMoving = true;
        activityStartTime = millis();
        Serial.println("🐄 CATTLE MOTION DETECTED!");
      }
      lastMotionTime = millis();
      motionCount++;
    } else {
      // Check if motion has stopped
      if (isMoving && (millis() - lastMotionTime > motionTimeout)) {
        isMoving = false;
        unsigned long activityDuration = (millis() - activityStartTime) / 1000;
        Serial.println("🛑 CATTLE STOPPED - Activity duration: " + String(activityDuration) + " seconds");
      }
    }
    
    // Store current readings for next comparison (use filtered values)
    lastAccelX = filteredAccelX;
    lastAccelY = filteredAccelY;
    lastAccelZ = filteredAccelZ;
    
    // Get current GPS data
    float currentSpeed = 0;
    bool hasValidGPS = gps.location.isValid();
    if (hasValidGPS) {
      currentSpeed = gps.speed.kmph();
      lastValidGPS = millis();
    }
    
    // Activity tracking
    updateActivityMetrics(isMoving, currentSpeed, millis());
    
    // Update behavior analysis
    updateBehaviorAnalysis(currentSpeed, motionMagnitude, hasValidGPS);
    
    Serial.println("==========================================");
    Serial.println("ENHANCED CATTLE TRACKING DATA:");
    Serial.println("==========================================");
    
    // Behavior Status (New primary status)
    printBehaviorStatus();
    
    // Traditional Motion Status (Secondary)
    Serial.println("\n--- MOTION DETECTION ---");
    Serial.print("Raw Motion: ");
    if (isMoving) {
      Serial.println("🚶 DETECTED");
      Serial.print("Activity Duration: ");
      Serial.print((millis() - activityStartTime) / 1000);
      Serial.println(" seconds");
    } else {
      Serial.println("🛑 STATIONARY");
    }
    Serial.print("Motion Magnitude: ");
    Serial.print(motionMagnitude, 3);
    Serial.println(" m/s²");
    Serial.print("Motion Events (last interval): ");
    Serial.println(motionCount);
    
    // Reset motion counter
    motionCount = 0;
    
    // Print MPU6050 data
    Serial.println("\n--- ACCELEROMETER DATA ---");
    Serial.print("Raw Acceleration X: ");
    Serial.print(a.acceleration.x, 2);
    Serial.print(", Y: ");
    Serial.print(a.acceleration.y, 2);
    Serial.print(", Z: ");
    Serial.print(a.acceleration.z, 2);
    Serial.println(" m/s²");
    
    Serial.print("Filtered Acceleration X: ");
    Serial.print(filteredAccelX, 2);
    Serial.print(", Y: ");
    Serial.print(filteredAccelY, 2);
    Serial.print(", Z: ");
    Serial.print(filteredAccelZ, 2);
    Serial.println(" m/s²");
    
    Serial.print("Total Acceleration: ");
    Serial.print(totalAccelMagnitude, 2);
    Serial.println(" m/s²");
    
    Serial.print("Rotation X: ");
    Serial.print(g.gyro.x, 2);
    Serial.print(", Y: ");
    Serial.print(g.gyro.y, 2);
    Serial.print(", Z: ");
    Serial.print(g.gyro.z, 2);
    Serial.println(" rad/s");
    
    Serial.print("Temperature: ");
    Serial.print(temp.temperature, 1);
    Serial.println(" °C");
    
    // Print GPS data
    Serial.println("\n--- LOCATION DATA ---");
    if (hasValidGPS) {
      Serial.print("📍 LAT: ");
      Serial.println(gps.location.lat(), 6);
      Serial.print("📍 LONG: ");
      Serial.println(gps.location.lng(), 6);
      Serial.print("🏃 SPEED: ");
      Serial.print(currentSpeed, 1);
      Serial.println(" km/h");
      Serial.print("⛰️  ALT: ");
      Serial.print(gps.altitude.meters(), 1);
      Serial.println(" m");
      Serial.print("📶 HDOP: ");
      Serial.println(gps.hdop.value() / 100.0, 2);
      Serial.print("🛰️  Satellites: ");
      Serial.println(gps.satellites.value());
      
      if (gps.course.isValid()) {
        Serial.print("🧭 Course: ");
        Serial.print(gps.course.deg(), 1);
        Serial.println("°");
      }
      
      if (gps.date.isValid() && gps.time.isValid()) {
        Serial.print("🕐 Time (UTC): ");
        Serial.println(String(gps.date.year()) + "/" + String(gps.date.month()) + "/" + String(gps.date.day()) + " " + String(gps.time.hour()) + ":" + String(gps.time.minute()) + ":" + String(gps.time.second()));
      }
      
      // Enhanced movement correlation
      if (behavior.currentBehavior == WALKING || behavior.currentBehavior == RUNNING) {
        if (currentSpeed > 0.5) {
          Serial.println("✅ Behavior and GPS speed correlated");
        } else {
          Serial.println("⚠️  Motion detected but low GPS speed");
        }
      } else if (behavior.currentBehavior == GRAZING && currentSpeed < 1.0) {
        Serial.println("✅ Grazing behavior confirmed by GPS");
      }
    } else {
      Serial.println("❌ GPS: No valid location data");
      if (gps.satellites.isValid()) {
        Serial.print("🛰️  Satellites: ");
        Serial.println(gps.satellites.value());
      }
      Serial.println("🔍 Searching for GPS signal...");
      
      // Check for GPS timeout
      if (millis() - lastValidGPS > GPS_TIMEOUT && lastValidGPS != 0) {
        Serial.println("⚠️ GPS signal lost for > 30s");
      }
    }
    
    // Print periodic activity summary (every 10 minutes)
    static unsigned long lastActivitySummary = 0;
    if (millis() - lastActivitySummary > 600000) { // 10 minutes
      lastActivitySummary = millis();
      Serial.println("\n--- PERIODIC ACTIVITY SUMMARY ---");
      Serial.print("Session Active Time: ");
      Serial.print(dailyActivity.totalActiveTime / 60000.0, 1);
      Serial.println(" minutes");
      Serial.print("Estimated Distance Today: ");
      Serial.print(dailyActivity.dailyDistance, 2);
      Serial.println(" km");
      Serial.print("Estimated Steps Today: ");
      Serial.println((int)dailyActivity.dailySteps);
    }
    
    Serial.println("==========================================\n");
  }
  
  // Send data to backend every 30 seconds
  if (millis() - lastDataSend >= sendInterval) {
    lastDataSend = millis();
    sendDataToBackend();
  }
}

// Verify JSON document before sending
bool verifyJson(const JsonDocument& doc) {
  if (doc.isNull()) {
    Serial.println("❌ JSON document is null");
    return false;
  }
  
  // Check required fields
  if (!doc.containsKey("cattle_id") || 
      !doc.containsKey("timestamp") ||
      !doc.containsKey("latitude") ||
      !doc.containsKey("longitude")) {
    Serial.println("❌ Missing required fields in JSON");
    return false;
  }
  
  // Check nested objects
  if (!doc.containsKey("acceleration") ||
      !doc["acceleration"].is<JsonObject>()) {
    Serial.println("❌ Missing or invalid acceleration data");
    return false;
  }
  
  if (!doc.containsKey("behavior") ||
      !doc["behavior"].is<JsonObject>()) {
    Serial.println("❌ Missing or invalid behavior data");
    return false;
  }
  
  return true;
}