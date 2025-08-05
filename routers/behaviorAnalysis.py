from datetime import datetime
from temp_firebase_service import temp_firebase_service as firebase_service
import uuid

def analyze_behavior_and_generate_alerts(cattle_id: str, new_data: dict):
    """
    Analyze new sensor data for a cattle, compare with previous data,
    and generate alerts for suspicious events (e.g., sudden speed change, abnormal motion).
    Returns a list of generated alerts (if any).
    """
    alerts = []
    
    try:
        print(f"🔍 Starting behavior analysis for cattle: {cattle_id}")

        # 1. Fetch previous live data for this cattle
        prev_result = firebase_service.get_realtime_data(f"cattle_live_data/{cattle_id}")
        prev_data = prev_result.get("data") if prev_result.get("success") else None
        
        if prev_data:
            print(f"📊 Found previous data for comparison")
        else:
            print(f"📊 No previous data found, skipping comparison-based alerts")

        # 2. Sudden speed change detection
        if prev_data:
            try:
                prev_speed = prev_data.get("speed_kmh", 0)
                new_speed = new_data.get("speed_kmh", 0)
                speed_diff = abs(new_speed - prev_speed)
                
                print(f"🏃 Speed comparison: {prev_speed:.2f} -> {new_speed:.2f} km/h (diff: {speed_diff:.2f})")
                
                if speed_diff > 5:  # Threshold for sudden speed change
                    alert = {
                        "cattleId": cattle_id,
                        "type": "sudden_speed_change",
                        "message": f"⚠️ Sudden speed change detected: {prev_speed:.2f} → {new_speed:.2f} km/h",
                        "timestamp": datetime.now().isoformat(),
                        "location": {
                            "latitude": new_data.get("latitude"),
                            "longitude": new_data.get("longitude")
                        }
                    }
                    alerts.append(alert)
                    print(f"⚠️ Speed change alert created")
            except Exception as e:
                print(f"❌ Error in speed change detection: {str(e)}")

        # 3. Abnormal motion detection (possible intruder or predator)
        try:
            accel = new_data.get("acceleration", {})
            if accel and isinstance(accel, dict):
                accel_x = accel.get("x", 0) or 0
                accel_y = accel.get("y", 0) or 0  
                accel_z = accel.get("z", 0) or 0
                
                accel_magnitude = (accel_x**2 + accel_y**2 + accel_z**2) ** 0.5
                print(f"📈 Acceleration magnitude: {accel_magnitude:.2f} m/s²")
                
                # If acceleration is much higher than normal (e.g., > 15 m/s²), flag as possible panic
                if accel_magnitude > 15:
                    alert = {
                        "cattleId": cattle_id,
                        "type": "abnormal_motion",
                        "message": f"🚨 Abnormal motion detected (possible intruder/predator): Accel={accel_magnitude:.2f} m/s²",
                        "timestamp": datetime.now().isoformat(),
                        "location": {
                            "latitude": new_data.get("latitude"),
                            "longitude": new_data.get("longitude")
                        }
                    }
                    alerts.append(alert)
                    print(f"🚨 Abnormal motion alert created")
        except Exception as e:
            print(f"❌ Error in motion detection: {str(e)}")

        # 5. Save alerts to database
        for alert in alerts:
            try:
                alert_id = f"alert_{cattle_id}_{uuid.uuid4().hex[:8]}"
                result = firebase_service.create_document("alerts", alert_id, alert)
                if result.get("success"):
                    print(f"✅ Alert saved: {alert['type']}")
                else:
                    print(f"❌ Failed to save alert: {result.get('error')}")
            except Exception as e:
                print(f"❌ Error saving alert: {str(e)}")

        print(f"🔍 Behavior analysis completed. Generated {len(alerts)} alerts")
        return alerts
        
    except Exception as e:
        print(f"❌ Critical error in behavior analysis: {str(e)}")
        return []
