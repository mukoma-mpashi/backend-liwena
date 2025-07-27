"""
Script to populate Firebase with sample cattle monitoring data
"""

import json
from firebase_service import firebase_service

def populate_database():
    """Populate Firebase with sample data"""
    
    # Load data from cattle.json file
    try:
        with open('cattle.json', 'r') as f:
            sample_data = json.load(f)
    except FileNotFoundError:
        print("❌ cattle.json file not found. Make sure it exists in the current directory.")
        return
    except json.JSONDecodeError:
        print("❌ Error reading cattle.json file. Please check the JSON format.")
        return
    
    print("Populating Firebase with sample cattle monitoring data...")
    
    # Populate cattle data
    print("\n📄 Adding cattle data...")
    for cattle_id, cattle_data in sample_data["cattle"].items():
        result = firebase_service.create_document("cattle", cattle_id, cattle_data)
        if result["success"]:
            print(f"✅ Added cattle: {cattle_id}")
        else:
            print(f"❌ Failed to add cattle {cattle_id}: {result.get('error', 'Unknown error')}")
    
    # Populate staff data
    print("\n👥 Adding staff data...")
    for staff_id, staff_data in sample_data["staff"].items():
        result = firebase_service.create_document("staff", staff_id, staff_data)
        if result["success"]:
            print(f"✅ Added staff: {staff_id}")
        else:
            print(f"❌ Failed to add staff {staff_id}: {result.get('error', 'Unknown error')}")
    
    # Populate alerts data
    print("\n🚨 Adding alerts data...")
    for alert_id, alert_data in sample_data["alerts"].items():
        result = firebase_service.create_document("alerts", alert_id, alert_data)
        if result["success"]:
            print(f"✅ Added alert: {alert_id}")
        else:
            print(f"❌ Failed to add alert {alert_id}: {result.get('error', 'Unknown error')}")
    
    # Populate geofences data (if available)
    if "geofences" in sample_data:
        print("\n🔒 Adding geofences data...")
        for geofence_id, geofence_data in sample_data["geofences"].items():
            result = firebase_service.create_document("geofences", geofence_id, geofence_data)
            if result["success"]:
                print(f"✅ Added geofence: {geofence_id}")
            else:
                print(f"❌ Failed to add geofence {geofence_id}: {result.get('error', 'Unknown error')}")
    
    # Populate cattle live data (simulated sensor data)
    print("\n📡 Adding simulated cattle live sensor data...")
    for cattle_id in sample_data["cattle"].keys():
        # Create realistic sensor data for each cattle
        live_data = {
            "cattle_id": cattle_id,
            "timestamp": "2025-07-19T12:00:00Z",
            "latitude": -1.2921 + (hash(cattle_id) % 100) / 10000.0,  # Nairobi area with small variations
            "longitude": 36.8219 + (hash(cattle_id) % 100) / 10000.0,
            "gps_fix": True,
            "speed_kmh": (hash(cattle_id) % 30) / 10.0,  # 0-3 km/h
            "heading": hash(cattle_id) % 360,
            "is_moving": (hash(cattle_id) % 2) == 0,
            "acceleration": {
                "x": (hash(cattle_id) % 100) / 100.0 - 0.5,
                "y": (hash(cattle_id) % 100) / 100.0 - 0.5,
                "z": 9.8 + (hash(cattle_id) % 20) / 100.0  # Gravity + small variation
            },
            "behavior": {
                "current": ["resting", "grazing", "walking"][hash(cattle_id) % 3],
                "previous": ["resting", "grazing", "walking"][hash(cattle_id) % 3],
                "duration_seconds": 300 + (hash(cattle_id) % 1800),  # 5-35 minutes
                "confidence": 75.0 + (hash(cattle_id) % 25)  # 75-100%
            },
            "activity": {
                "total_active_time_seconds": 14400 + (hash(cattle_id) % 7200),  # 4-6 hours
                "total_rest_time_seconds": 72000 + (hash(cattle_id) % 14400),   # 20-24 hours
                "daily_steps": 5000 + (hash(cattle_id) % 5000),  # 5000-10000 steps
                "daily_distance_km": 2.5 + (hash(cattle_id) % 50) / 10.0  # 2.5-7.5 km
            }
        }
        
        result = firebase_service.set_realtime_data(f"cattle_live_data/{cattle_id}", live_data)
        if result["success"]:
            print(f"✅ Added live data for cattle: {cattle_id}")
        else:
            print(f"❌ Failed to add live data for {cattle_id}: {result.get('error', 'Unknown error')}")

    print("\n🎉 Database population complete!")
    print("\nYou can now test the API endpoints:")
    print("- GET /cattle - Get all cattle")
    print("- GET /staff - Get all staff")
    print("- GET /alerts - Get all alerts")
    print("- GET /cattle-locations - Get all cattle live sensor data")
    print("- POST /cattle/live-data - Receive ESP32 sensor data")
    print("- GET /dashboard/summary - Get dashboard summary")

if __name__ == "__main__":
    populate_database()
