from fastapi import APIRouter, HTTPException
from temp_firebase_service import temp_firebase_service as firebase_service
from models import Geofence, GeofenceCreate, CattleLocationUpdate, CattleSensorData
from shapely.geometry import Point, Polygon
from datetime import datetime
import uuid
import math

router = APIRouter(tags=["geofence"])

# Create a geofence
@router.post("/geofences")
async def create_geofence(geofence: GeofenceCreate):
    geofence_id = f"geofence_{uuid.uuid4().hex[:8]}"
    data = geofence.model_dump()
    data["id"] = geofence_id
    result = firebase_service.create_document("geofences", geofence_id, data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create geofence"))
    
    print(f"🗺️ New geofence created: {data['name']} with {len(data['coordinates'])} points")
    return result

# Get all geofences
@router.get("/geofences")
async def get_geofences():
    result = firebase_service.get_collection("geofences")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get geofences"))
    
    return result

# =====================
# CATTLE LOCATION UPDATE & GEOFENCE CHECK
# =====================

@router.post("/cattle-location")
async def update_cattle_location(update: CattleLocationUpdate):
    """Legacy endpoint for simple location updates"""
    location_data = {
        "cattle_id": update.cattle_id,
        "latitude": update.location[1],
        "longitude": update.location[0],
        "timestamp": update.timestamp
    }
    path = f"cattle_locations/{update.cattle_id}"
    result = firebase_service.set_realtime_data(path, location_data)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return {"success": True, "message": "Location updated."}

# =====================
# REAL-TIME GEOFENCE MONITORING ENDPOINT
# =====================

@router.get("/monitor/cattle/{cattle_id}")
async def monitor_cattle_geofence_realtime(cattle_id: str):
    """
    Real-time endpoint to check if a specific cattle has stepped out of any geofence.
    This endpoint is designed for frontend to poll for geofence breach alerts.
    """
    try:
        print(f"🔍 Real-time geofence monitoring for cattle {cattle_id}")
        
        # Get latest cattle location from live data
        live_data_result = firebase_service.get_realtime_data(f"cattle_live_data/{cattle_id}")
        
        if not live_data_result.get("success"):
            return {
                "success": False,
                "error": f"No live data found for cattle {cattle_id}",
                "has_breach": False,
                "alerts": []
            }
        
        cattle_data = live_data_result.get("data", {})
        latitude = cattle_data.get("latitude")
        longitude = cattle_data.get("longitude")
        
        if latitude is None or longitude is None:
            return {
                "success": False,
                "error": f"No location data available for cattle {cattle_id}",
                "has_breach": False,
                "alerts": []
            }
        
        print(f"📍 Current location: ({latitude:.6f}, {longitude:.6f})")
        
        # Check geofence status
        geofence_result = check_cattle_geofence_status(cattle_id, latitude, longitude)
        
        if not geofence_result.get("success"):
            return {
                "success": False,
                "error": geofence_result.get("error", "Geofence check failed"),
                "has_breach": False,
                "alerts": []
            }
        
        # Determine if there's a breach
        has_breach = len(geofence_result.get("outside_geofences", [])) > 0
        breach_count = geofence_result.get("total_breaches", 0)
        
        # Format response for frontend
        response = {
            "success": True,
            "cattle_id": cattle_id,
            "timestamp": cattle_data.get("timestamp"),
            "current_location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "has_breach": has_breach,
            "breach_count": breach_count,
            "status": geofence_result.get("status"),
            "geofence_details": {
                "inside": geofence_result.get("inside_geofences", []),
                "outside": geofence_result.get("outside_geofences", []),
                "total_geofences": geofence_result.get("total_geofences", 0)
            },
            "alerts": geofence_result.get("alerts", []),
            "behavior": cattle_data.get("behavior", {}).get("current", "unknown"),
            "is_moving": cattle_data.get("is_moving", False)
        }
        
        if has_breach:
            print(f"🚨 BREACH DETECTED: Cattle {cattle_id} is outside {breach_count} geofence(s)")
        else:
            print(f"✅ All clear: Cattle {cattle_id} is within all geofences")
        
        return response
        
    except Exception as e:
        print(f"❌ Error in real-time geofence monitoring: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "has_breach": False,
            "alerts": []
        }

@router.get("/monitor/all")
async def monitor_all_cattle_geofences():
    """
    Monitor all cattle for geofence breaches in real-time.
    Returns summary of all cattle with breach status.
    """
    try:
        print(f"🔍 Monitoring all cattle for geofence breaches")
        
        # Get all cattle live data
        live_data_result = firebase_service.get_realtime_data("cattle_live_data")
        
        if not live_data_result.get("success"):
            return {
                "success": True,
                "message": "No cattle data found",
                "total_cattle": 0,
                "cattle_with_breaches": 0,
                "cattle_status": []
            }
        
        all_cattle_data = live_data_result.get("data", {})
        cattle_status = []
        breach_count = 0
        
        for cattle_id, cattle_data in all_cattle_data.items():
            if not isinstance(cattle_data, dict):
                continue
                
            latitude = cattle_data.get("latitude")
            longitude = cattle_data.get("longitude")
            
            if latitude is None or longitude is None:
                cattle_status.append({
                    "cattle_id": cattle_id,
                    "has_breach": False,
                    "error": "No location data",
                    "alerts": []
                })
                continue
            
            # Check geofence status for this cattle
            geofence_result = check_cattle_geofence_status(cattle_id, latitude, longitude)
            
            has_breach = len(geofence_result.get("outside_geofences", [])) > 0
            if has_breach:
                breach_count += 1
            
            cattle_status.append({
                "cattle_id": cattle_id,
                "has_breach": has_breach,
                "breach_count": geofence_result.get("total_breaches", 0),
                "current_location": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "timestamp": cattle_data.get("timestamp")
                },
                "behavior": cattle_data.get("behavior", {}).get("current", "unknown"),
                "is_moving": cattle_data.get("is_moving", False),
                "geofence_details": {
                    "outside": geofence_result.get("outside_geofences", []),
                    "inside": geofence_result.get("inside_geofences", [])
                },
                "alerts": geofence_result.get("alerts", [])
            })
        
        print(f"📊 Monitoring complete: {len(cattle_status)} cattle, {breach_count} with breaches")
        
        return {
            "success": True,
            "total_cattle": len(cattle_status),
            "cattle_with_breaches": breach_count,
            "timestamp": datetime.now().isoformat(),
            "cattle_status": cattle_status
        }
        
    except Exception as e:
        print(f"❌ Error monitoring all cattle: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to monitor cattle: {str(e)}")

# =====================
# ADVANCED GEOFENCE CHECK LOGIC
# =====================

def check_cattle_geofence_status(cattle_id: str, latitude: float, longitude: float):
    """
    Check if a cattle is inside or outside all geofences.
    Returns detailed geofence status and generates alerts if needed.
    """
    try:
        print(f"🔍 Checking geofence status for cattle {cattle_id} at ({latitude:.6f}, {longitude:.6f})")
        
        # Create point from cattle location
        cattle_point = Point(longitude, latitude)
        
        # Get all geofences
        geofences_result = firebase_service.get_collection("geofences")
        if not geofences_result.get("success"):
            print(f"❌ Failed to fetch geofences: {geofences_result.get('error')}")
            return {
                "success": False,
                "error": "Failed to fetch geofences",
                "alerts": []
            }
        
        geofences = geofences_result.get("data", [])
        if not geofences:
            print(f"📭 No geofences found")
            return {
                "success": True,
                "status": "no_geofences",
                "inside_geofences": [],
                "outside_geofences": [],
                "alerts": []
            }
        
        print(f"📊 Found {len(geofences)} geofences to check")
        
        inside_geofences = []
        outside_geofences = []
        alerts = []
        
        for geofence_data in geofences:
            if not isinstance(geofence_data, dict):
                continue
                
            geofence_id = geofence_data.get("id", "unknown")
            geofence_name = geofence_data.get("name", geofence_id)
            coordinates = geofence_data.get("coordinates", [])
            
            if not coordinates or len(coordinates) < 3:
                print(f"⚠️ Skipping invalid geofence {geofence_name}: insufficient coordinates")
                continue
            
            try:
                # Create polygon from coordinates
                geofence_poly = Polygon(coordinates)
                
                # Check if cattle is inside the geofence
                is_inside = geofence_poly.contains(cattle_point)
                
                # Calculate distance to geofence boundary
                distance_to_boundary = cattle_point.distance(geofence_poly.boundary)
                distance_km = distance_to_boundary * 111.32  # Rough conversion to km
                
                geofence_info = {
                    "id": geofence_id,
                    "name": geofence_name,
                    "is_inside": is_inside,
                    "distance_to_boundary_km": round(distance_km, 3)
                }
                
                if is_inside:
                    inside_geofences.append(geofence_info)
                    print(f"✅ Cattle {cattle_id} is INSIDE geofence '{geofence_name}'")
                else:
                    outside_geofences.append(geofence_info)
                    print(f"❌ Cattle {cattle_id} is OUTSIDE geofence '{geofence_name}' by {distance_km:.3f} km")
                    
                    # Generate breach alert
                    alert = {
                        "cattleId": cattle_id,
                        "type": "geofence_breach",
                        "severity": "high" if distance_km > 1.0 else "medium",
                        "message": f"🚨 Cattle {cattle_id} is outside geofence '{geofence_name}' by {distance_km:.3f} km",
                        "timestamp": datetime.now().isoformat(),
                        "location": {
                            "latitude": latitude,
                            "longitude": longitude
                        },
                        "geofence": {
                            "id": geofence_id,
                            "name": geofence_name,
                            "distance_km": round(distance_km, 3)
                        }
                    }
                    alerts.append(alert)
                    
            except Exception as e:
                print(f"❌ Error processing geofence {geofence_name}: {str(e)}")
                continue
        
        # Determine overall status
        if inside_geofences and not outside_geofences:
            overall_status = "all_inside"
        elif outside_geofences and not inside_geofences:
            overall_status = "all_outside"
        elif inside_geofences and outside_geofences:
            overall_status = "partial_breach"
        else:
            overall_status = "unknown"
        
        # Save alerts to database
        for alert in alerts:
            try:
                alert_id = f"alert_{cattle_id}_{uuid.uuid4().hex[:8]}"
                result = firebase_service.create_document("alerts", alert_id, alert)
                if result.get("success"):
                    print(f"🚨 Geofence breach alert saved: {alert['message']}")
                else:
                    print(f"❌ Failed to save alert: {result.get('error')}")
            except Exception as e:
                print(f"❌ Error saving alert: {str(e)}")
        
        return {
            "success": True,
            "status": overall_status,
            "inside_geofences": inside_geofences,
            "outside_geofences": outside_geofences,
            "alerts": alerts,
            "total_geofences": len(geofences),
            "total_breaches": len(outside_geofences)
        }
        
    except Exception as e:
        print(f"❌ Critical error in geofence check: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "alerts": []
        }

@router.post("/check/{cattle_id}")
async def check_cattle_geofence(cattle_id: str, location_data: dict):
    """
    Check geofence status for a specific cattle at given coordinates.
    Expected payload: {"latitude": float, "longitude": float}
    """
    try:
        latitude = location_data.get("latitude")
        longitude = location_data.get("longitude")
        
        if latitude is None or longitude is None:
            raise HTTPException(status_code=400, detail="Latitude and longitude are required")
        
        result = check_cattle_geofence_status(cattle_id, latitude, longitude)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check geofence: {str(e)}")

@router.get("/status/{cattle_id}")
async def get_cattle_geofence_status(cattle_id: str):
    """
    Get current geofence status for a cattle based on their latest location.
    """
    try:
        # Get latest cattle location from live data
        live_data_result = firebase_service.get_realtime_data(f"cattle_live_data/{cattle_id}")
        
        if not live_data_result.get("success"):
            raise HTTPException(status_code=404, detail=f"No live data found for cattle {cattle_id}")
        
        cattle_data = live_data_result.get("data", {})
        latitude = cattle_data.get("latitude")
        longitude = cattle_data.get("longitude")
        
        if latitude is None or longitude is None:
            raise HTTPException(status_code=400, detail=f"No location data available for cattle {cattle_id}")
        
        result = check_cattle_geofence_status(cattle_id, latitude, longitude)
        
        # Add timestamp of the location data
        result["location_timestamp"] = cattle_data.get("timestamp")
        result["cattle_behavior"] = cattle_data.get("behavior", {}).get("current", "unknown")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get geofence status: {str(e)}")

@router.get("/status/all")
async def get_all_cattle_geofence_status():
    """
    Get geofence status for all cattle based on their latest locations.
    """
    try:
        # Get all cattle live data
        live_data_result = firebase_service.get_realtime_data("cattle_live_data")
        
        if not live_data_result.get("success"):
            return {
                "success": True,
                "message": "No cattle data found",
                "cattle_status": []
            }
        
        all_cattle_data = live_data_result.get("data", {})
        cattle_status = []
        
        for cattle_id, cattle_data in all_cattle_data.items():
            if not isinstance(cattle_data, dict):
                continue
                
            latitude = cattle_data.get("latitude")
            longitude = cattle_data.get("longitude")
            
            if latitude is None or longitude is None:
                cattle_status.append({
                    "cattle_id": cattle_id,
                    "status": "no_location_data",
                    "error": "Missing location coordinates"
                })
                continue
            
            # Check geofence status for this cattle
            geofence_result = check_cattle_geofence_status(cattle_id, latitude, longitude)
            
            cattle_status.append({
                "cattle_id": cattle_id,
                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "timestamp": cattle_data.get("timestamp")
                },
                "behavior": cattle_data.get("behavior", {}).get("current", "unknown"),
                "geofence_status": geofence_result
            })
        
        # Calculate summary statistics
        total_cattle = len(cattle_status)
        cattle_with_breaches = sum(1 for c in cattle_status if c.get("geofence_status", {}).get("total_breaches", 0) > 0)
        total_alerts = sum(len(c.get("geofence_status", {}).get("alerts", [])) for c in cattle_status)
        
        return {
            "success": True,
            "summary": {
                "total_cattle": total_cattle,
                "cattle_with_breaches": cattle_with_breaches,
                "total_alerts_generated": total_alerts
            },
            "cattle_status": cattle_status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get all cattle geofence status: {str(e)}")

@router.get("/alerts/recent")
async def get_recent_geofence_alerts(limit: int = 50):
    """
    Get recent geofence breach alerts for frontend display.
    Returns alerts sorted by timestamp (newest first).
    """
    try:
        # Get all alerts from database
        alerts_result = firebase_service.get_collection("alerts")
        
        if not alerts_result.get("success"):
            return {
                "success": True,
                "message": "No alerts found",
                "alerts": []
            }
        
        all_alerts = alerts_result.get("data", [])
        
        # Filter for geofence breach alerts only
        geofence_alerts = [
            alert for alert in all_alerts 
            if isinstance(alert, dict) and alert.get("type") == "geofence_breach"
        ]
        
        # Sort by timestamp (newest first)
        geofence_alerts.sort(
            key=lambda x: x.get("timestamp", ""), 
            reverse=True
        )
        
        # Limit results
        limited_alerts = geofence_alerts[:limit]
        
        print(f"📋 Retrieved {len(limited_alerts)} recent geofence alerts")
        
        return {
            "success": True,
            "total_alerts": len(geofence_alerts),
            "returned_alerts": len(limited_alerts),
            "alerts": limited_alerts
        }
        
    except Exception as e:
        print(f"❌ Error getting recent alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@router.get("/alerts/cattle/{cattle_id}")
async def get_cattle_geofence_alerts(cattle_id: str, limit: int = 20):
    """
    Get geofence breach alerts for a specific cattle.
    """
    try:
        # Get all alerts from database
        alerts_result = firebase_service.get_collection("alerts")
        
        if not alerts_result.get("success"):
            return {
                "success": True,
                "message": f"No alerts found for cattle {cattle_id}",
                "alerts": []
            }
        
        all_alerts = alerts_result.get("data", [])
        
        # Filter for this cattle's geofence breach alerts
        cattle_alerts = [
            alert for alert in all_alerts 
            if isinstance(alert, dict) and 
            alert.get("type") == "geofence_breach" and
            alert.get("cattleId") == cattle_id
        ]
        
        # Sort by timestamp (newest first)
        cattle_alerts.sort(
            key=lambda x: x.get("timestamp", ""), 
            reverse=True
        )
        
        # Limit results
        limited_alerts = cattle_alerts[:limit]
        
        print(f"📋 Retrieved {len(limited_alerts)} alerts for cattle {cattle_id}")
        
        return {
            "success": True,
            "cattle_id": cattle_id,
            "total_alerts": len(cattle_alerts),
            "returned_alerts": len(limited_alerts),
            "alerts": limited_alerts
        }
        
    except Exception as e:
        print(f"❌ Error getting cattle alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cattle alerts: {str(e)}")

@router.delete("/geofences/{geofence_id}")
async def delete_geofence(geofence_id: str):
    """Delete a geofence"""
    try:
        result = firebase_service.delete_document("geofences", geofence_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to delete geofence"))
        
        print(f"🗑️ Geofence {geofence_id} deleted")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete geofence: {str(e)}")

@router.get("/geofences/{geofence_id}")
async def get_geofence(geofence_id: str):
    """Get a specific geofence by ID"""
    try:
        result = firebase_service.get_document("geofences", geofence_id)
        if not result["success"]:
            if "not found" in result.get("message", "").lower():
                raise HTTPException(status_code=404, detail=f"Geofence {geofence_id} not found")
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get geofence"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get geofence: {str(e)}")
