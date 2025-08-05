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

        # 3. 🔥 GEOFENCING LOGIC 🔥
        print(f"🗺️ Checking geofences for cattle {cattle_id}...")
        geofence_alerts = []
        
        try:
            location_point = Point(data.longitude, data.latitude)
            geofences_result = firebase_service.get_collection("geofences")
            
            if geofences_result.get("success") and geofences_result.get("data"):
                geofences = geofences_result["data"]
                print(f"📊 Found {len(geofences)} geofences to check")
                
                for geofence_data in geofences:
                    if isinstance(geofence_data, dict) and 'coordinates' in geofence_data and geofence_data['coordinates']:
                        try:
                            geofence_name = geofence_data.get('name', geofence_data.get('id', 'Unknown'))
                            geofence_poly = Polygon(geofence_data["coordinates"])
                            
                            is_inside = geofence_poly.contains(location_point)
                            print(f"🎯 Geofence '{geofence_name}': {'✅ INSIDE' if is_inside else '❌ OUTSIDE'}")
                            
                            if not is_inside:
                                # Cattle is outside the geofence, create an alert
                                alert_message = f"🚨 GEOFENCE BREACH: Cattle {cattle_id} detected outside of geofence '{geofence_name}'"
                                alert_data = {
                                    "cattleId": cattle_id,
                                    "type": "geofence_breach",
                                    "message": alert_message,
                                    "timestamp": datetime.now().isoformat(),
                                    "location": {"latitude": data.latitude, "longitude": data.longitude},
                                    "geofence_name": geofence_name
                                }
                                alert_id = f"alert_{uuid.uuid4().hex[:10]}"
                                alert_result = firebase_service.create_document("alerts", alert_id, alert_data)
                                
                                if alert_result["success"]:
                                    print(f"🚨 ALERT CREATED: {alert_message}")
                                    geofence_alerts.append(alert_message)
                                else:
                                    print(f"❌ Failed to create alert: {alert_result.get('error')}")
                                    
                        except Exception as e:
                            print(f"❌ Error processing geofence {geofence_data.get('id')}: {e}")
            else:
                print("📭 No geofences found or geofence query failed")
                
        except Exception as e:
            print(f"❌ Error in geofence processing: {str(e)}")

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
