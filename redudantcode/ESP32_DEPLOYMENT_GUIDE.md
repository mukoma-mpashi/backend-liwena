# 🔧 ESP32 Deployment Guide - Cattle Monitoring System

## 📋 Hardware Requirements

### Components Needed
- **ESP32 Development Board** (ESP32-WROOM-32 or similar)
- **MPU6050 Accelerometer/Gyroscope Module**
- **GPS Module** (NEO-6M or NEO-8M recommended)
- **MicroSD Card** (optional, for local data backup)
- **Battery Pack** (Li-Ion 3.7V 2000mAh+ recommended)
- **Waterproof Enclosure**
- **Jumper Wires** and **Breadboard** (for prototyping)

### Wiring Connections

#### MPU6050 Connections
```
MPU6050    →    ESP32
VCC        →    3.3V
GND        →    GND
SCL        →    GPIO 22 (I2C Clock)
SDA        →    GPIO 21 (I2C Data)
```

#### GPS Module Connections
```
GPS Module →    ESP32
VCC        →    3.3V (or 5V if module requires)
GND        →    GND
TX         →    GPIO 16 (RX2)
RX         →    GPIO 17 (TX2)
```

#### Power Connections
```
Battery+   →    VIN (or use USB for development)
Battery-   →    GND
```

## 🔧 Software Setup

### 1. Arduino IDE Configuration

#### Install ESP32 Board Package
1. Open Arduino IDE
2. Go to **File** → **Preferences**
3. Add this URL to "Additional Board Manager URLs":
   ```
   https://dl.espressif.com/dl/package_esp32_index.json
   ```
4. Go to **Tools** → **Board** → **Boards Manager**
5. Search for "ESP32" and install "ESP32 by Espressif Systems"

#### Install Required Libraries
Go to **Tools** → **Manage Libraries** and install:
- **Adafruit MPU6050** by Adafruit
- **Adafruit Unified Sensor** by Adafruit  
- **TinyGPS++** by Mikal Hart
- **ArduinoJson** by Benoit Blanchon

### 2. Upload Code to ESP32

#### Configure Settings
1. Select **Board**: "ESP32 Dev Module"
2. Select **Port**: (your ESP32 COM port)
3. Set **Upload Speed**: 921600
4. Set **Flash Frequency**: 80MHz

#### Update Network Configuration
In `cattle.ino`, update these lines with your network details:
```cpp
// WiFi credentials - UPDATE THESE
const char* ssid = "YOUR_WIFI_NETWORK";
const char* password = "YOUR_WIFI_PASSWORD";

// Backend configuration - UPDATE THIS IP
const String BACKEND_URL = "http://YOUR_SERVER_IP:8001";
```

#### Upload Process
1. Connect ESP32 to computer via USB
2. Open `cattle.ino` in Arduino IDE
3. Press **Upload** button
4. Wait for "Done uploading" message

## 🌐 Network Configuration

### Finding Your Server IP Address

#### Windows (Command Prompt)
```cmd
ipconfig
```
Look for "IPv4 Address" under your active network adapter.

#### Router Method
1. Access your router admin panel (usually 192.168.1.1)
2. Look for "Connected Devices" or "DHCP Client List"
3. Find your server computer's IP address

### WiFi Network Requirements
- **2.4GHz network** (ESP32 doesn't support 5GHz)
- **WPA/WPA2 security** (WEP not recommended)
- **Stable internet connection** for backend communication
- **Good signal strength** at cattle location

## 🔋 Power Management

### Battery Considerations
- **Capacity**: 2000mAh minimum for 8-12 hours operation
- **Voltage**: 3.7V Li-Ion or 5V USB power bank
- **Protection**: Use batteries with built-in protection circuits
- **Charging**: Solar panel option for extended field deployment

### Power Optimization Tips
```cpp
// Add these for better battery life
#include "esp_sleep.h"

// Deep sleep between readings (advanced)
esp_sleep_enable_timer_wakeup(30 * 1000000); // 30 seconds
esp_light_sleep_start();
```

## 📦 Physical Installation

### Enclosure Requirements
- **IP65/IP67 rated** for weather protection
- **Clear GPS reception** (no metal blocking)
- **Ventilation** to prevent condensation
- **Secure mounting** for cattle collar/harness

### Mounting Options
1. **Collar Mount**: Attach to cattle collar with zip ties
2. **Ear Tag**: Smaller ESP32 variant in ear tag housing
3. **Halter Mount**: Integrated into halter system
4. **Backpack Style**: Small backpack for larger batteries

### GPS Antenna Placement
- **Clear sky view** for optimal satellite reception
- **Away from metal objects** that block signals
- **Upward facing** when cattle is standing normally
- **Consider cattle behavior** (head down for grazing)

## 🔍 Testing and Verification

### Pre-Deployment Tests

#### 1. Indoor Testing
```
✅ WiFi Connection: Check serial monitor for IP address
✅ Sensor Reading: Verify accelerometer values
✅ GPS Fix: May take time indoors, test outdoors
✅ Backend Communication: Check for "Data sent successfully" messages
```

#### 2. Outdoor GPS Test
- Take device outside for 2-3 minutes
- Monitor serial output for GPS coordinates
- Verify latitude/longitude are reasonable for your location
- Check GPS fix status and satellite count

#### 3. Range Testing
- Test WiFi connection at intended deployment location
- Walk around with device to check coverage
- Verify backend receives data consistently
- Test during different times of day

### Serial Monitor Output
When working correctly, you should see:
```
🌐 Connecting to WiFi...
✅ WiFi connected!
IP: 192.168.1.105
📍 LAT: -1.292100
📍 LONG: 36.821900
🛰️ Satellites: 8
📡 Sending data to backend...
✅ Data sent successfully to backend!
```

## 🚨 Troubleshooting

### Common Issues and Solutions

#### WiFi Connection Problems
```
❌ WiFi failed. Will retry...
```
**Solutions:**
- Check SSID and password spelling
- Ensure 2.4GHz network (not 5GHz)
- Move closer to router
- Check if network uses captive portal (unsupported)

#### GPS Not Working
```
❌ GPS: No valid location data
🛰️ Satellites: 0
```
**Solutions:**
- Move to open outdoor area
- Wait 2-5 minutes for cold start
- Check GPS module wiring
- Verify GPS module power (3.3V or 5V)

#### Backend Communication Errors
```
❌ HTTP Error: -1
Error: connection refused
```
**Solutions:**
- Verify server IP address
- Check if backend server is running
- Test with curl/browser from another device
- Check firewall settings

#### Sensor Reading Issues
```
⚠️ Suspicious acceleration reading
```
**Solutions:**
- Check MPU6050 wiring (I2C connections)
- Verify power supply stability
- Try different I2C pins if needed
- Check for loose connections

### Debug Mode
Add this to enable verbose output:
```cpp
#define DEBUG_MODE 1  // Add at top of file

#if DEBUG_MODE
  Serial.println("Debug: " + debugMessage);
#endif
```

## 📊 Monitoring and Maintenance

### Daily Checks
- [ ] Battery level monitoring
- [ ] GPS signal quality
- [ ] WiFi connection status
- [ ] Data transmission success rate

### Weekly Maintenance
- [ ] Clean GPS antenna
- [ ] Check physical mounting
- [ ] Verify enclosure sealing
- [ ] Review data in Firebase database

### Battery Life Estimation
```
Typical Power Consumption:
- ESP32 active: ~160mA
- GPS module: ~30mA  
- MPU6050: ~3.5mA
- WiFi transmission: ~200mA (brief)

With 2000mAh battery:
- Continuous operation: ~8-10 hours
- With sleep mode: 24+ hours
```

## 🎯 Deployment Checklist

### Pre-Deployment
- [ ] Code uploaded and tested
- [ ] WiFi credentials configured
- [ ] Server IP address updated
- [ ] GPS getting fix outdoors
- [ ] Sensors reading correctly
- [ ] Backend receiving data
- [ ] Battery fully charged
- [ ] Enclosure waterproof
- [ ] Mounting secure

### During Deployment
- [ ] Attach to cattle safely
- [ ] Verify continued operation
- [ ] Check signal strength at location
- [ ] Monitor first few data transmissions
- [ ] Document deployment location/time

### Post-Deployment
- [ ] Monitor data flow in Firebase
- [ ] Check for regular updates (every 30 seconds)
- [ ] Verify behavior classification accuracy
- [ ] Set up alerts for connection loss
- [ ] Plan battery replacement schedule

## 📞 Support and Resources

### Useful Links
- **ESP32 Documentation**: https://docs.espressif.com/projects/esp32/
- **Arduino ESP32 Core**: https://github.com/espressif/arduino-esp32
- **TinyGPS++ Library**: https://github.com/mikalhart/TinyGPSPlus
- **Adafruit MPU6050**: https://github.com/adafruit/Adafruit_MPU6050

### Contact Information
For technical support with this cattle monitoring system:
- **Backend Issues**: Check Firebase and API logs
- **Hardware Issues**: Review wiring and power connections  
- **Software Issues**: Monitor serial output for error messages

---

*Deployment Guide v1.0 - Updated December 28, 2024*  
*Compatible with cattle.ino ESP32 code*
