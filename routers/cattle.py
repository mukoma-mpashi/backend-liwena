from fastapi import APIRouter, HTTPException, Body
from temp_firebase_service import temp_firebase_service as firebase_service
from models import CattleSensorData
from shapely.geometry import Point, Polygon
from datetime import datetime
import uuid
import math
from routers.behaviorAnalysis import analyze_behavior_and_generate_alerts

router = APIRouter(prefix="/cattle", tags=["cattle"])

# =================================================
# NEW ENDPOINT FOR ESP32 SENSOR DATA (No Auth Required)
# =================================================

@router.post("/live-data", status_code=200)
async def update_cattle_live_data(data: CattleSensorData):
    """
    Receives and processes live sensor data from ESP32/ESP8266 devices for cattle.
    This is the primary endpoint for hardware integration.
    Note: Authentication removed for ESP32/ESP8266 compatibility.
    """
    try:
        cattle_id = data.cattle_id
        
        print(f"📡 Received data from IoT device for cattle: {cattle_id}")
        print(f"📍 Location: {data.latitude}, {data.longitude}")
        print(f"🐄 Behavior: {data.behavior.current}")
        print(f"🚶 Moving: {data.is_moving}")
        
        # 1. Store the complete raw sensor data in 'cattle_live_data' collection
        print(f"💾 Storing live data for {cattle_id}")
        live_data_path = f"cattle_live_data/{cattle_id}"
        result_live = firebase_service.set_realtime_data(live_data_path, data.model_dump())
        
        if not result_live["success"]:
            print(f"❌ Failed to store live data: {result_live.get('error')}")
            raise HTTPException(status_code=500, detail=f"Failed to store live sensor data: {result_live.get('error')}")
        else:
            print(f"✅ Live data stored successfully")

        # 2. Update the main 'cattle' document with the latest summary
        print(f"📝 Updating cattle document for {cattle_id}")
        update_data = {
            "last_seen": data.timestamp,
            "location": f"{data.latitude},{data.longitude}",
            "status": data.behavior.current,
            "position": {"x": data.longitude, "y": data.latitude},
            "lastMovement": data.timestamp if data.is_moving else "Stationary"
        }
        result_update = firebase_service.update_document("cattle", cattle_id, update_data)
        
        if not result_update["success"]:
            print(f"⚠️ Warning: Failed to update main cattle document for {cattle_id}: {result_update.get('error')}")
        else:
            print(f"✅ Cattle document updated successfully")

        # 3. 🔥 ENHANCED GEOFENCING LOGIC 🔥
        print(f"🗺️ Checking geofences for cattle {cattle_id}...")
        
        # Use the enhanced geofence checking logic from geofence router
        from routers.geofence import check_cattle_geofence_status
        
        try:
            geofence_result = check_cattle_geofence_status(cattle_id, data.latitude, data.longitude)
            
            if geofence_result.get("success"):
                geofence_alerts = geofence_result.get("alerts", [])
                breach_count = geofence_result.get("total_breaches", 0)
                
                if breach_count > 0:
                    print(f"🚨 GEOFENCE BREACHES DETECTED: {breach_count} breaches for cattle {cattle_id}")
                else:
                    print(f"✅ Cattle {cattle_id} is within all geofences")
            else:
                print(f"⚠️ Geofence check failed: {geofence_result.get('error')}")
                geofence_alerts = []
                
        except Exception as e:
            print(f"❌ Error in enhanced geofence processing: {str(e)}")
            geofence_alerts = []

        # Prepare response with geofence status
        response_message = f"Live data for {cattle_id} processed successfully."
        if geofence_alerts:
            response_message += f" Generated {len(geofence_alerts)} geofence alerts."

        # --- Behavior-based alert analysis ---
        try:
            alerts = analyze_behavior_and_generate_alerts(cattle_id, data.model_dump())
            print(f"🔍 Generated {len(alerts)} behavior alerts")
        except Exception as e:
            print(f"⚠️ Warning: Behavior analysis failed: {str(e)}")
            alerts = []

        # Update response message with behavior alerts
        if alerts:
            response_message += f" Generated {len(alerts)} behavior alerts."

        print(f"✅ Successfully processed data for {cattle_id}")
        return {
            "success": True, 
            "message": response_message,
            "cattle_id": cattle_id,
            "location": {"latitude": data.latitude, "longitude": data.longitude},
            "behavior": data.behavior.current,
            "geofence_alerts": geofence_alerts,
            "behavior_alerts": alerts
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"❌ Unexpected error in update_cattle_live_data: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/live-data/{cattle_id}")
async def get_cattle_live_data(cattle_id: str):
    """Get live data for a specific cattle"""
    try:
        result = firebase_service.get_realtime_data(f"cattle_live_data/{cattle_id}")
        if not result["success"]:
            raise HTTPException(status_code=404, detail=f"No live data found for cattle {cattle_id}")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get live data: {str(e)}")

@router.get("/live-data")
async def get_all_cattle_live_data():
    """Get live data for all cattle"""
    try:
        result = firebase_service.get_realtime_data("cattle_live_data")
        if not result["success"]:
            raise HTTPException(status_code=404, detail="No live data found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get live data: {str(e)}")

@router.get("/geofence-status/{cattle_id}")
async def get_cattle_geofence_breach_status(cattle_id: str):
    """
    Quick endpoint for frontend to check if a cattle has breached any geofences.
    Returns simple boolean status for easy frontend integration.
    """
    try:
        # Get latest cattle location
        result = firebase_service.get_realtime_data(f"cattle_live_data/{cattle_id}")
        if not result["success"]:
            return {
                "success": False,
                "cattle_id": cattle_id,
                "has_breach": False,
                "error": f"No live data found for cattle {cattle_id}"
            }
        
        cattle_data = result.get("data", {})
        latitude = cattle_data.get("latitude")
        longitude = cattle_data.get("longitude")
        
        if latitude is None or longitude is None:
            return {
                "success": False,
                "cattle_id": cattle_id,
                "has_breach": False,
                "error": "No location data available"
            }
        
        # Use enhanced geofence checking
        from routers.geofence import check_cattle_geofence_status
        geofence_result = check_cattle_geofence_status(cattle_id, latitude, longitude)
        
        if not geofence_result.get("success"):
            return {
                "success": False,
                "cattle_id": cattle_id,
                "has_breach": False,
                "error": geofence_result.get("error", "Geofence check failed")
            }
        
        has_breach = len(geofence_result.get("outside_geofences", [])) > 0
        breach_details = geofence_result.get("outside_geofences", [])
        
        return {
            "success": True,
            "cattle_id": cattle_id,
            "has_breach": has_breach,
            "breach_count": len(breach_details),
            "timestamp": cattle_data.get("timestamp"),
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "breach_details": breach_details,
            "behavior": cattle_data.get("behavior", {}).get("current", "unknown")
        }
        
    except Exception as e:
        return {
            "success": False,
            "cattle_id": cattle_id,
            "has_breach": False,
            "error": f"Error checking geofence status: {str(e)}"
        }

@router.get("/locations")
async def get_all_cattle_locations():
    """Get all cattle locations in format expected by frontend"""
    try:
        result = firebase_service.get_realtime_data("cattle_live_data")
        if not result["success"]:
            return {"success": True, "data": []}
        
        cattle_data = result.get("data", {})
        locations = []
        
        for cattle_id, data in cattle_data.items():
            if isinstance(data, dict) and "latitude" in data and "longitude" in data:
                locations.append({
                    "cattle_id": cattle_id,
                    "latitude": data["latitude"],
                    "longitude": data["longitude"],
                    "timestamp": data.get("timestamp"),
                    "behavior": data.get("behavior", {}).get("current", "unknown"),
                    "is_moving": data.get("is_moving", False)
                })
        
        return {"success": True, "data": locations}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cattle locations: {str(e)}")
