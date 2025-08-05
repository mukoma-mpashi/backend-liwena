import sys
import os
import asyncio
import json
from datetime import datetime

# Add project root to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from routers.geofence import monitor_cattle_geofence_realtime
from temp_firebase_service import temp_firebase_service as firebase_service

# Define constants for our test
TEST_CATTLE_ID = "cattle_test_123"
TEST_GEOFENCE_ID = "geofence_test_123"

async def setup_test_data():
    """Create the necessary geofence and cattle data for the test."""
    print("--- Setting up test data ---")
    
    # 1. Create a test geofence
    geofence_data = {
        "id": TEST_GEOFENCE_ID,
        "name": "Farm Boundary Test",
        "coordinates": [
            [28.20, -15.50], [28.30, -15.50],
            [28.30, -15.40], [28.20, -15.40],
            [28.20, -15.50]  # Close the polygon
        ]
    }
    firebase_service.create_document("geofences", TEST_GEOFENCE_ID, geofence_data)
    print(f"✅ Created test geofence: {TEST_GEOFENCE_ID}")

    # 2. Create test cattle data (location OUTSIDE the geofence)
    cattle_data = {
        "cattle_id": TEST_CATTLE_ID,
        "timestamp": datetime.now().isoformat(),
        "latitude": -15.60,  # This latitude is outside the geofence
        "longitude": 28.25,
        "gps_fix": True,
        "speed_kmh": 1.5,
        "heading": 90.0,
        "is_moving": True,
        "behavior": {"current": "walking", "previous": "resting", "duration_seconds": 120, "confidence": 0.95},
        "activity": {"daily_steps": 1500, "daily_distance_km": 2.1, "total_active_time_seconds": 10000, "total_rest_time_seconds": 20000}
    }
    firebase_service.set_realtime_data(f"cattle_live_data/{TEST_CATTLE_ID}", cattle_data)
    print(f"✅ Created live data for cattle '{TEST_CATTLE_ID}' (status: OUTSIDE)")

async def cleanup_test_data():
    """Remove the test data from Firebase."""
    print("\n--- Cleaning up test data ---")
    firebase_service.delete_document("geofences", TEST_GEOFENCE_ID)
    print(f"🗑️ Deleted test geofence: {TEST_GEOFENCE_ID}")
    firebase_service.delete_realtime_data(f"cattle_live_data/{TEST_CATTLE_ID}")
    print(f"🗑️ Deleted live data for cattle: {TEST_CATTLE_ID}")

async def main():
    """Main function to run the test."""
    await setup_test_data()
    
    print(f"\n--- 🧪 Testing endpoint: @router.get('/monitor/cattle/{{cattle_id}}') ---")
    print(f"--- Using Cattle ID: {TEST_CATTLE_ID} ---")
    
    try:
        # Directly call the async function that the endpoint uses
        result = await monitor_cattle_geofence_realtime(TEST_CATTLE_ID)
        
        print("\n--- ✅ TEST COMPLETE ---")
        print("--- API Response Output ---")
        # Pretty-print the JSON result for clear readability
        print(json.dumps(result, indent=2))

        # Key checks to verify the logic
        print("\n--- Verification Checks ---")
        assert result.get("success") is True, "Success should be True"
        print("✅ 'success' field is True")
        
        assert result.get("has_breach") is True, "Cattle should have a breach"
        print("✅ 'has_breach' field is True (Correct)")
        
        assert result.get("breach_count", 0) > 0, "Breach count should be greater than 0"
        print(f"✅ 'breach_count' is {result.get('breach_count')} (Correct)")
        
        assert len(result.get("alerts", [])) > 0, "Alerts should be generated"
        print(f"✅ {len(result.get('alerts'))} alert(s) generated (Correct)")

    except Exception as e:
        print(f"\n--- ❌ TEST FAILED ---")
        print(f"An error occurred during the test: {e}")
    
    finally:
        # Ensure data is cleaned up even if the test fails
        await cleanup_test_data()

if __name__ == "__main__":
    # This allows the async main function to be run
    asyncio.run(main())
