# ESP8266 Cattle Monitoring System

## Overview
This code configures an ESP8266 to collect data from a GPS module and MPU6050 accelerometer/gyroscope sensor and sends it to our cattle monitoring backend in the exact format expected by the database.

## Hardware Requirements
- ESP8266 (NodeMCU or Wemos D1 Mini)
- NEO-6M GPS module 
- MPU6050 accelerometer/gyroscope
- Power source (LiPo battery + charging circuit recommended)
- Enclosure for field deployment

## Wiring
- **GPS Module**:
  - VCC → 3.3V
  - GND → GND
  - TX → D5 (GPIO14)
  - RX → D6 (GPIO12)

- **MPU6050**:
  - VCC → 3.3V
  - GND → GND
  - SDA → D2 (GPIO4)
  - SCL → D1 (GPIO5)

## Software Dependencies
Install these libraries via the Arduino Library Manager:
- ESP8266WiFi
- ESP8266HTTPClient
- WiFiClientSecure
- TinyGPSPlus
- SoftwareSerial
- Wire
- Adafruit_MPU6050
- Adafruit_Sensor
- ArduinoJson

## Configuration
Before deployment, update these variables:
- WiFi credentials (`ssid`, `password`)
- Backend URL if needed (`backendHost`)
- Data transmission interval (`SEND_INTERVAL`) - currently set to 15 seconds

## Data Format
The device will send data in this format, which exactly matches the expected format in the Firebase database:
```json
{
  "cattle_id": "cattle1",
  "timestamp": "2025-07-28T12:34:56.000Z",
  "latitude": -1.2921,
  "longitude": 36.8219,
  "gps_fix": true,
  "speed_kmh": 2.5,
  "heading": 45.0,
  "is_moving": true,
  "acceleration": {
    "x": 0.1,
    "y": 0.2,
    "z": 9.8
  },
  "behavior": {
    "current": "grazing",
    "previous": "resting",
    "duration_seconds": 300,
    "confidence": 85.5
  },
  "activity": {
    "total_active_time_seconds": 7200,
    "total_rest_time_seconds": 3600,
    "daily_steps": 1250,
    "daily_distance_km": 2.8
  }
}
```

## Behavior Detection
The code includes simple behavior detection logic:
- **Walking**: Detected when the device is moving and has significant gyroscope activity
- **Resting**: Detected when the device is stationary with very little acceleration/gyroscope changes
- **Grazing**: Detected when there is moderate movement with specific acceleration patterns

## Deployment Notes
1. Ensure the device has a clear view of the sky for GPS reception
2. Use a waterproof enclosure for field deployment
3. Test the WiFi signal strength at the deployment location
4. Consider adding a status LED to indicate successful data transmission
5. For long-term deployment, implement deep sleep to conserve battery

## Troubleshooting
- **No GPS Fix**: Make sure the GPS module has a clear view of the sky. It may take several minutes to get an initial fix.
- **Connection Issues**: Check WiFi signal strength and verify backend URL.
- **Sensor Errors**: Verify the I2C connection to the MPU6050.
