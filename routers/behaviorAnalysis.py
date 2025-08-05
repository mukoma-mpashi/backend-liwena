from datetime import datetime
from temp_firebase_service import temp_firebase_service as firebase_service

def analyze_behavior_and_generate_alerts(cattle_id: str, new_data: dict):
    """
    Analyze new sensor data for a cattle, compare with previous data,
    and generate alerts for suspicious events (e.g., sudden speed change, abnormal motion).
    Returns a list of generated alerts (if any).
    """
    alerts = []

    # 1. Fetch previous live data for this cattle
    prev_result = firebase_service.get_realtime_data(f"cattle_live_data/{cattle_id}")
    prev_data = prev_result.get("data") if prev_result.get("success") else None

    # 2. Sudden speed change detection
    if prev_data:
        prev_speed = prev_data.get("speed_kmh", 0)
        new_speed = new_data.get("speed_kmh", 0)
        speed_diff = abs(new_speed - prev_speed)
        if speed_diff > 5:  # Threshold for sudden speed change (tune as needed)
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

    # 3. Abnormal motion detection (possible intruder or predator)
    accel = new_data.get("acceleration", {})
    if accel:
        accel_magnitude = (accel.get("x", 0)**2 + accel.get("y", 0)**2 + accel.get("z", 0)**2) ** 0.5
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

    # 4. Add more rules as needed (e.g., geofence breach, no movement for long time, etc.)

    # 5. Save alerts to database
    for alert in alerts:
        alert_id = f"alert_{cattle_id}_{int(datetime.now().timestamp())}"
        firebase_service.create_document("alerts", alert_id, alert)
        # Optionally, you can also append the alert to the cattle's live data
        # (e.g., add a 'recent_alerts' field to cattle_live_data)

    return alerts
