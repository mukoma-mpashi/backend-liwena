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
    
    print("\n🎉 Database population complete!")
    print("\nYou can now test the API endpoints:")
    print("- GET /cattle - Get all cattle")
    print("- GET /staff - Get all staff")
    print("- GET /alerts - Get all alerts")
    print("- GET /dashboard/summary - Get dashboard summary")

if __name__ == "__main__":
    populate_database()

if __name__ == "__main__":
    populate_database()
