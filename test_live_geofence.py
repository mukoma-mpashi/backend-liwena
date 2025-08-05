import sys
import os
import asyncio
import json
from datetime import datetime

# Add project root to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from routers.geofence import monitor_cattle_geofence_realtime

# The ID of the cattle to test, as seen in your screenshot
TARGET_CATTLE_ID = "cattle1"

async def main():
    """
    Tests the geofence monitoring endpoint using live data for a specific cattle
    as requested. This script does not create or delete any test data.
    It uses the existing state of the database.
    """
    print("--- 🚀 LIVE GEOFENCE TEST ---")
    print(f"--- 🎯 Testing endpoint for: {TARGET_CATTLE_ID} ---")
    print("--- (Using existing data from your Firebase Realtime Database) ---")

    try:
        # Directly call the async function that the endpoint uses
        result = await monitor_cattle_geofence_realtime(TARGET_CATTLE_ID)

        print("\n--- ✅ TEST COMPLETE ---")
        print("--- API Response ---")
        # Pretty-print the JSON result for clear readability
        print(json.dumps(result, indent=2, default=str))

        # Provide a summary of the result
        print("\n--- 📊 Summary ---")
        if result.get("success"):
            print(f"Cattle ID: {result.get('cattle_id')}")
            print(f"Location Timestamp: {result.get('timestamp')}")
            print(f"Current Location: {result.get('current_location')}")
            print(f"Behavior: {result.get('behavior')}")
            print(f"Is Moving: {result.get('is_moving')}")
            print("-" * 20)
            if result.get("has_breach"):
                print(f"🚨 STATUS: BREACH DETECTED")
                print(f"   - Breached {result.get('breach_count')} geofence(s).")
                print("   - Details of breached geofences:")
                for detail in result.get("geofence_details", {}).get("outside", []):
                    print(f"     - Name: {detail.get('name')}, Distance: {detail.get('distance_to_boundary_km')} km")
            else:
                print("✅ STATUS: All clear. Cattle is within all geofences.")
        else:
            print(f"❌ Test failed. Error: {result.get('error')}")

    except Exception as e:
        print(f"\n--- ❌ TEST FAILED ---")
        print(f"An error occurred during the test: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
