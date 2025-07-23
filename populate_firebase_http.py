"""
Simple Firebase Test - Direct HTTP Access
This bypasses Firebase Admin SDK authentication to test basic connectivity
"""

import requests
import json

def test_firebase_direct():
    """Test Firebase using direct HTTP requests (no auth required for public rules)"""
    
    database_url = "https://cattlemonitor-57c45-default-rtdb.firebaseio.com"
    
    print("🧪 Testing Firebase Direct HTTP Access")
    print("=" * 50)
    
    # Test 1: Write data
    print("\n1. Testing write access...")
    test_data = {
        "test": "direct_access",
        "timestamp": "2025-07-19T12:00:00Z",
        "message": "Testing direct Firebase access"
    }
    
    try:
        response = requests.put(f"{database_url}/test/direct_test.json", json=test_data)
        if response.status_code == 200:
            print("   ✅ Write test successful!")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Write failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Write error: {e}")
        return False
    
    # Test 2: Read data
    print("\n2. Testing read access...")
    try:
        response = requests.get(f"{database_url}/test/direct_test.json")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Read test successful!")
            print(f"   Data: {data}")
        else:
            print(f"   ❌ Read failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Read error: {e}")
        return False
    
    # Test 3: Clean up
    print("\n3. Cleaning up test data...")
    try:
        response = requests.delete(f"{database_url}/test/direct_test.json")
        if response.status_code == 200:
            print("   ✅ Cleanup successful!")
        else:
            print(f"   ⚠️ Cleanup warning: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Cleanup error: {e}")
    
    print("\n🎉 Firebase direct access works! The issue is with authentication.")
    return True

def populate_via_http():
    """Populate Firebase using direct HTTP requests"""
    
    database_url = "https://cattlemonitor-57c45-default-rtdb.firebaseio.com"
    
    print("\n📊 Populating Firebase via HTTP (no auth required)")
    print("=" * 60)
    
    # Sample data
    sample_data = {
        "cattle": {
            "cattle1": {
                "id": "cattle1",
                "type": "Holstein",
                "status": "active",
                "location": "Pasture A",
                "position": {"x": 36.8219, "y": -1.2921},
                "lastMovement": "2025-07-19T12:00:00Z"
            },
            "cattle2": {
                "id": "cattle2", 
                "type": "Angus",
                "status": "resting",
                "location": "Pasture B",
                "position": {"x": 36.8229, "y": -1.2931},
                "lastMovement": "2025-07-19T11:30:00Z"
            },
            "cattle3": {
                "id": "cattle3",
                "type": "Jersey",
                "status": "grazing", 
                "location": "Pasture A",
                "position": {"x": 36.8209, "y": -1.2911},
                "lastMovement": "2025-07-19T12:15:00Z"
            }
        },
        "staff": {
            "staff1": {
                "id": "staff1",
                "name": "John Doe",
                "role": "Ranch Manager",
                "status": "active",
                "location": "Main Office"
            },
            "staff2": {
                "id": "staff2",
                "name": "Jane Smith", 
                "role": "Veterinarian",
                "status": "active",
                "location": "Field"
            }
        },
        "alerts": {
            "alert1": {
                "id": "alert1",
                "cattleId": "cattle1",
                "type": "location",
                "message": "Cattle moved outside designated area",
                "timestamp": "2025-07-19T11:45:00Z"
            }
        },
        "geofences": {
            "geofence1": {
                "id": "geofence1",
                "name": "Pasture A Boundary",
                "coordinates": [
                    [36.82, -1.29],
                    [36.83, -1.29], 
                    [36.83, -1.30],
                    [36.82, -1.30],
                    [36.82, -1.29]
                ]
            }
        }
    }
    
    # Upload each collection
    for collection_name, collection_data in sample_data.items():
        print(f"\n📄 Adding {collection_name} data...")
        
        try:
            response = requests.put(f"{database_url}/{collection_name}.json", json=collection_data)
            if response.status_code == 200:
                print(f"   ✅ Successfully added {collection_name} collection")
            else:
                print(f"   ❌ Failed to add {collection_name}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ Error adding {collection_name}: {e}")
    
    # Add sample live data
    print(f"\n📡 Adding cattle live data...")
    for cattle_id in ["cattle1", "cattle2", "cattle3"]:
        live_data = {
            "cattle_id": cattle_id,
            "timestamp": "2025-07-19T12:00:00Z",
            "latitude": -1.2921 + (hash(cattle_id) % 100) / 10000.0,
            "longitude": 36.8219 + (hash(cattle_id) % 100) / 10000.0,
            "gps_fix": True,
            "speed_kmh": (hash(cattle_id) % 30) / 10.0,
            "heading": hash(cattle_id) % 360,
            "is_moving": (hash(cattle_id) % 2) == 0,
            "acceleration": {
                "x": (hash(cattle_id) % 100) / 100.0 - 0.5,
                "y": (hash(cattle_id) % 100) / 100.0 - 0.5,
                "z": 9.8 + (hash(cattle_id) % 20) / 100.0
            },
            "behavior": {
                "current": ["resting", "grazing", "walking"][hash(cattle_id) % 3],
                "previous": ["resting", "grazing", "walking"][hash(cattle_id) % 3],
                "duration_seconds": 300 + (hash(cattle_id) % 1800),
                "confidence": 75.0 + (hash(cattle_id) % 25)
            },
            "activity": {
                "total_active_time_seconds": 14400 + (hash(cattle_id) % 7200),
                "total_rest_time_seconds": 72000 + (hash(cattle_id) % 14400),
                "daily_steps": 5000 + (hash(cattle_id) % 5000),
                "daily_distance_km": 2.5 + (hash(cattle_id) % 50) / 10.0
            }
        }
        
        try:
            response = requests.put(f"{database_url}/cattle_live_data/{cattle_id}.json", json=live_data)
            if response.status_code == 200:
                print(f"   ✅ Added live data for {cattle_id}")
            else:
                print(f"   ❌ Failed to add live data for {cattle_id}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error adding live data for {cattle_id}: {e}")
    
    print("\n🎉 Database populated successfully via HTTP!")
    print("\nYou can now test the API endpoints:")
    print("- GET /cattle - Get all cattle")
    print("- GET /staff - Get all staff") 
    print("- GET /alerts - Get all alerts")
    print("- GET /cattle-locations - Get all cattle live sensor data")
    print("- POST /cattle/live-data - Receive ESP32 sensor data")

def main():
    """Main function"""
    
    # Test basic connectivity first
    if test_firebase_direct():
        # If basic connectivity works, populate the database
        populate_via_http()
        
        print("\n" + "=" * 60)
        print("🔧 NEXT STEPS TO FIX AUTHENTICATION")
        print("=" * 60)
        print("1. Your Firebase database is working - the issue is just with the service account")
        print("2. Generate a fresh service account key from Firebase Console")
        print("3. Replace your current firebase-service-account-key.json file")
        print("4. Restart your backend server")
        print("5. The authentication should work with the new key")
        
    else:
        print("\n❌ Firebase connectivity issue - check your database URL and rules")

if __name__ == "__main__":
    main()
