# Enhanced Cattle Monitoring System - Backend Integration Guide

## Overview

Your cattle monitoring system has been upgraded to handle rich sensor data from ESP32 devices. The system now supports detailed behavior analysis, activity tracking, and real-time monitoring with proper Firebase structure.

## New Architecture

### 1. Data Flow
```
ESP32 Sensor Device
    ↓ (Rich sensor data every 30 seconds)
FastAPI Backend (/cattle/live-data endpoint)
    ↓ (Processes and stores data)
Firebase Realtime Database
    ↓ (Provides data to)
Vue.js Frontend / Mobile Apps
```

### 2. Firebase Database Structure

#### New Collections:

**`cattle_live_data/{cattle_id}`** - Real-time sensor data
```json
{
  "cattle_id": "cattle_001",
  "timestamp": "2025-07-19T12:00:00Z",
  "latitude": -1.2921,
  "longitude": 36.8219,
  "gps_fix": true,
  "speed_kmh": 2.5,
  "heading": 45.0,
  "is_moving": true,
  "acceleration": {
    "x": 0.1,
    "y": -0.3,
    "z": 9.9
  },
  "behavior": {
    "current": "grazing",
    "previous": "walking",
    "duration_seconds": 300,
    "confidence": 85.0
  },
  "activity": {
    "total_active_time_seconds": 14400,
    "total_rest_time_seconds": 72000,
    "daily_steps": 7500,
    "daily_distance_km": 4.2
  }
}
```

**`cattle/{cattle_id}`** - Summary data (updated from live data)
```json
{
  "id": "cattle_001",
  "type": "Holstein",
  "status": "grazing",
  "location": "-1.2921,36.8219",
  "position": {"x": 36.8219, "y": -1.2921},
  "lastMovement": "2025-07-19T12:00:00Z",
  "last_seen": "2025-07-19T12:00:00Z"
}
```

## API Endpoints

### New Primary Endpoint

**POST `/cattle/live-data`** - Primary endpoint for ESP32 data
- Receives complete `CattleSensorData` payload
- Stores raw data in `cattle_live_data` collection
- Updates summary in `cattle` collection
- Performs geofence checks and creates alerts
- Returns success/failure status to ESP32

### Updated Endpoints

**GET `/cattle-locations`** - Now returns live sensor data
- Sources data from `cattle_live_data` collection
- Provides real-time location and behavior information

**POST `/cattle-location`** - Legacy endpoint (still supported)
- For simple location updates
- Stores data in `cattle_locations` collection

## ESP32 Implementation

### Required Libraries
```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <TinyGPS++.h>
```

### Key Features in ESP32 Code
1. **Sensor Data Collection**: MPU6050 accelerometer + GPS
2. **Behavior Analysis**: Real-time classification (resting, grazing, walking, running)
3. **Activity Tracking**: Steps, distance, active/rest time
4. **Data Transmission**: JSON payload every 30 seconds to backend
5. **Error Handling**: WiFi reconnection, sensor validation

### Hardware Setup
- **ESP32 Development Board**
- **MPU6050 Accelerometer/Gyroscope** (I2C: SDA=21, SCL=22)
- **GPS Module** (UART: RX=16, TX=17)
- **Power Management** (Battery + charging circuit)
- **Enclosure** (Weatherproof for cattle collar)

## Setup Instructions

### 1. Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Populate database with new structure
python populate_database.py

# Start the backend
python main.py
```

### 2. ESP32 Setup
1. Install Arduino IDE with ESP32 board package
2. Install required libraries via Library Manager
3. Update WiFi credentials and backend URL in code
4. Upload `esp32_cattle_backend_integration.ino`
5. Monitor Serial output for status

### 3. Hardware Assembly
1. Connect MPU6050 to ESP32 (VCC, GND, SDA=21, SCL=22)
2. Connect GPS module to ESP32 (VCC, GND, RX=16, TX=17)
3. Add power management circuit
4. Enclose in weatherproof housing
5. Attach securely to cattle collar

## Testing

### 1. Test Backend Endpoints
```bash
# Test live data endpoint
curl -X POST "http://localhost:8000/cattle/live-data" \
  -H "Content-Type: application/json" \
  -d '{
    "cattle_id": "test_cattle",
    "timestamp": "2025-07-19T12:00:00Z",
    "latitude": -1.2921,
    "longitude": 36.8219,
    "gps_fix": true,
    "speed_kmh": 2.5,
    "heading": 45.0,
    "is_moving": true,
    "acceleration": {"x": 0.1, "y": -0.3, "z": 9.9},
    "behavior": {"current": "grazing", "previous": "walking", "duration_seconds": 300, "confidence": 85.0},
    "activity": {"total_active_time_seconds": 14400, "total_rest_time_seconds": 72000, "daily_steps": 7500, "daily_distance_km": 4.2}
  }'

# Get all cattle locations
curl "http://localhost:8000/cattle-locations"
```

### 2. Test ESP32 Communication
1. Open Serial Monitor (115200 baud)
2. Verify WiFi connection
3. Check sensor readings
4. Confirm data transmission to backend
5. Monitor Firebase console for incoming data

## Monitoring & Analytics

### Real-time Monitoring
- Live location tracking on map
- Behavior classification in real-time
- Activity metrics dashboard
- Geofence breach alerts

### Historical Analysis
- Movement patterns over time
- Behavior trend analysis
- Health indicators from activity data
- Predictive analytics for unusual behavior

## Production Considerations

### 1. Security
- Use HTTPS for backend communication
- Implement authentication for API endpoints
- Secure Firebase database rules
- Add device authentication tokens

### 2. Scalability
- Implement data compression for large herds
- Add database indexing for efficient queries
- Consider data archiving strategies
- Implement rate limiting on API endpoints

### 3. Reliability
- Add ESP32 watchdog timers
- Implement automatic restart on failures
- Add offline data buffering
- Include battery monitoring and alerts

### 4. Power Management
- Optimize sensor reading intervals
- Implement sleep modes between transmissions
- Add solar charging capabilities
- Monitor battery health

## Troubleshooting

### Common Issues

1. **ESP32 Not Connecting to WiFi**
   - Check WiFi credentials
   - Ensure 2.4GHz network (ESP32 doesn't support 5GHz)
   - Verify network accessibility

2. **Sensor Data Not Accurate**
   - Calibrate MPU6050 accelerometer
   - Check GPS antenna placement
   - Verify sensor connections

3. **Backend Not Receiving Data**
   - Check backend URL in ESP32 code
   - Verify API endpoint accessibility
   - Monitor backend logs for errors

4. **Firebase Connection Issues**
   - Verify Firebase credentials
   - Check database rules
   - Monitor Firebase usage quotas

### Debug Commands
```bash
# Check backend health
curl "http://localhost:8000/health"

# Debug Firebase connection
curl "http://localhost:8000/debug/firebase"

# View current data structure
curl "http://localhost:8000/debug/data"
```

## Future Enhancements

1. **Advanced Analytics**
   - Machine learning for anomaly detection
   - Predictive health monitoring
   - Automated alert severity classification

2. **Hardware Improvements**
   - Add heart rate monitoring
   - Implement temperature sensors
   - Include camera for visual confirmation

3. **System Features**
   - Mobile app for ranch managers
   - SMS alerts for critical situations
   - Integration with veterinary systems

This enhanced system provides a robust foundation for comprehensive cattle monitoring with real-time data processing and intelligent behavior analysis.
