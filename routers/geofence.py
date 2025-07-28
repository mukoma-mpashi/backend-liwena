from fastapi import APIRouter, HTTPException
from temp_firebase_service import temp_firebase_service as firebase_service
from models import Geofence, GeofenceCreate, CattleLocationUpdate, CattleSensorData
from shapely.geometry import Point, Polygon
from datetime import datetime
import uuid

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
