from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from auth import get_current_user, role_required, firebase_auth
from firebase_admin import auth
# from firebase_service import firebase_service  # Commented out due to auth issues
from temp_firebase_service import temp_firebase_service as firebase_service  # Temporary fix
from models import (
    CattleBase, CattleCreate, CattleUpdate, CattleResponse,
    StaffBase, StaffCreate, StaffUpdate, StaffResponse,
    AlertBase, AlertCreate, AlertUpdate, AlertResponse,
    Geofence, GeofenceCreate, CattleLocationUpdate,
    CattleSensorData
)
from pydantic import EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"  # Default role
from shapely.geometry import Point, Polygon
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uuid

# Single FastAPI app instance
app = FastAPI(title="Cattle Monitor API", description="FastAPI backend for cattle monitoring system with Firebase integration")

# CORS configuration - update for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# AUTHENTICATION ENDPOINTS
# =====================

# User registration
@app.post("/auth/register")
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        # Create user in Firebase Auth
        user = auth.create_user(
            email=user_data.email,
            password=user_data.password
        )
        
        # Set custom claims (role)
        auth.set_custom_user_claims(user.uid, {"role": user_data.role})
        
        # Store additional user data in Realtime DB
        user_record = {
            "email": user_data.email,
            "role": user_data.role,
            "created_at": datetime.now().isoformat()
        }
        
        result = firebase_service.create_document("users", user.uid, user_record)
        if not result["success"]:
            # Rollback: delete the created auth user
            auth.delete_user(user.uid)
            raise HTTPException(status_code=500, detail="Failed to create user record")
        
        return {"success": True, "uid": user.uid, "message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get current user info
@app.get("/auth/me", dependencies=[Depends(firebase_auth)])
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user

# Verify Firebase ID token
@app.get("/auth/verify")
async def verify_token(decoded_token: dict = Depends(firebase_auth)):
    """Verify Firebase ID token"""
    return {"success": True, "user": decoded_token}

# List all users (Admin only)
@app.get("/auth/users", dependencies=[Depends(firebase_auth)])
@role_required(["admin"])
async def list_users(current_user: dict):
    """List all users - Admin only"""
    try:
        result = firebase_service.get_collection("users")
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Failed to fetch users")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =====================
# GEOFENCE ENDPOINTS
# =====================

# Create a geofence
@app.post("/geofences")
async def create_geofence(geofence: GeofenceCreate):
    import uuid
    geofence_id = f"geofence_{uuid.uuid4().hex[:8]}"
    data = geofence.model_dump()
    data["id"] = geofence_id
    result = firebase_service.create_document("geofences", geofence_id, data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create geofence"))
    return result

# Get all geofences
@app.get("/geofences")
async def get_geofences():
    result = firebase_service.get_collection("geofences")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get geofences"))
    return result

# =====================
# CATTLE LOCATION UPDATE & GEOFENCE CHECK
# =====================

@app.post("/cattle-location")
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
    
# =================================================
# NEW ENDPOINT FOR ESP32 SENSOR DATA
# =================================================

@app.post("/cattle/live-data", status_code=200, dependencies=[Depends(firebase_auth)])
@role_required(["admin", "staff"])
async def update_cattle_live_data(data: CattleSensorData, current_user: dict):
    """
    Receives and processes live sensor data from an ESP32 device for a specific cattle.
    This is the primary endpoint for hardware integration.
    """
    cattle_id = data.cattle_id
    
    # 1. Store the complete raw sensor data in a new 'cattle_live_data' collection
    live_data_path = f"cattle_live_data/{cattle_id}"
    result_live = firebase_service.set_realtime_data(live_data_path, data.model_dump())
    
    if not result_live["success"]:
        # This is a critical failure, as we are losing raw data.
        raise HTTPException(status_code=500, detail=f"Failed to store live sensor data: {result_live.get('error')}")

    # 2. Update the main 'cattle' document with the latest summary
    update_data = {
        "last_seen": data.timestamp,
        "location": f"{data.latitude},{data.longitude}",
        "status": data.behavior.current,
        "position": {"x": data.longitude, "y": data.latitude},
        "lastMovement": data.timestamp if data.is_moving else "Stationary"
    }
    result_update = firebase_service.update_document("cattle", cattle_id, update_data)
    
    if not result_update["success"]:
        # Log this error but don't block the response to the ESP32.
        # The raw data was saved, which is most important.
        print(f"Warning: Failed to update main cattle document for {cattle_id}: {result_update.get('error')}")

    # 3. Perform geofence check using the new location data
    location_point = Point(data.longitude, data.latitude)
    geofences_result = firebase_service.get_collection("geofences")
    
    if geofences_result.get("success") and geofences_result.get("data"):
        geofences = geofences_result["data"]
        for geofence_data in geofences:
            if isinstance(geofence_data, dict) and 'coordinates' in geofence_data and geofence_data['coordinates']:
                try:
                    geofence_poly = Polygon(geofence_data["coordinates"])
                    if not geofence_poly.contains(location_point):
                        # Cattle is outside the geofence, create an alert
                        alert_message = f"Alert: Cattle {cattle_id} detected outside of geofence '{geofence_data.get('name', geofence_data.get('id'))}'."
                        alert_data = {
                            "cattleId": cattle_id,
                            "type": "geofence_breach",
                            "message": alert_message,
                            "timestamp": datetime.now().isoformat(),
                            "location": {"latitude": data.latitude, "longitude": data.longitude}
                        }
                        alert_id = f"alert_{uuid.uuid4().hex[:10]}"
                        firebase_service.create_document("alerts", alert_id, alert_data)
                        print(f"ALERT CREATED: {alert_message}")
                except Exception as e:
                    print(f"Error processing geofence {geofence_data.get('id')}: {e}")

    return {"success": True, "message": f"Live data for {cattle_id} processed."}


# General models for backward compatibility
class DocumentData(BaseModel):
    data: Dict[str, Any]

class DocumentResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "Cattle Monitor API is running!", "status": "healthy", "version": "1.0.0"}

# CATTLE ENDPOINTS
@app.post("/cattle", response_model=CattleResponse, dependencies=[Depends(firebase_auth)])
@role_required(["admin"])
async def create_cattle(cattle_data: CattleCreate, current_user: dict):
    """Create a new cattle record"""
    cattle_id = f"cattle_{uuid.uuid4().hex[:8]}"
    cattle_dict = cattle_data.model_dump()
    cattle_dict["id"] = cattle_id
    
    result = firebase_service.create_document("cattle", cattle_id, cattle_dict)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create cattle record"))
    return result

@app.get("/cattle", response_model=CattleResponse)
async def get_all_cattle():
    """Get all cattle records"""
    result = firebase_service.get_collection("cattle")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get cattle records"))
    return result

@app.get("/cattle/{cattle_id}", response_model=CattleResponse)
async def get_cattle(cattle_id: str):
    """Get a specific cattle record"""
    result = firebase_service.get_document("cattle", cattle_id)
    if not result["success"]:
        if "not found" in result.get("message", "").lower():
            raise HTTPException(status_code=404, detail=f"Cattle {cattle_id} not found")
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get cattle record"))
    return result

@app.put("/cattle/{cattle_id}", response_model=CattleResponse)
async def update_cattle(cattle_id: str, cattle_data: CattleUpdate):
    """Update a cattle record"""
    # Filter out None values
    update_data = {k: v for k, v in cattle_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided for update")
    
    result = firebase_service.update_document("cattle", cattle_id, update_data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to update cattle record"))
    return result

@app.delete("/cattle/{cattle_id}", response_model=CattleResponse)
async def delete_cattle(cattle_id: str):
    """Delete a cattle record"""
    result = firebase_service.delete_document("cattle", cattle_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to delete cattle record"))
    return result

@app.get("/cattle/status/{status}", response_model=CattleResponse)
async def get_cattle_by_status(status: str):
    """Get cattle by status (Grazing, Resting, Alert, etc.)"""
    result = firebase_service.get_collection("cattle")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get cattle records"))
    
    # Filter by status
    filtered_cattle = [cattle for cattle in result["data"] if cattle.get("status") == status]
    return {"success": True, "data": filtered_cattle}

@app.get("/cattle/location/{location}", response_model=CattleResponse)
async def get_cattle_by_location(location: str):
    """Get cattle by location"""
    result = firebase_service.get_collection("cattle")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get cattle records"))
    
    # Filter by location
    filtered_cattle = [cattle for cattle in result["data"] if cattle.get("location") == location]
    return {"success": True, "data": filtered_cattle}

# STAFF ENDPOINTS
@app.post("/staff", response_model=StaffResponse)
async def create_staff(staff_data: StaffCreate):
    """Create a new staff record"""
    staff_id = f"staff_{uuid.uuid4().hex[:8]}"
    staff_dict = staff_data.model_dump()
    staff_dict["id"] = staff_id
    
    result = firebase_service.create_document("staff", staff_id, staff_dict)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create staff record"))
    return result

@app.get("/staff", response_model=StaffResponse)
async def get_all_staff():
    """Get all staff records"""
    result = firebase_service.get_collection("staff")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get staff records"))
    return result

@app.get("/staff/{staff_id}", response_model=StaffResponse)
async def get_staff(staff_id: str):
    """Get a specific staff record"""
    result = firebase_service.get_document("staff", staff_id)
    if not result["success"]:
        if "not found" in result.get("message", "").lower():
            raise HTTPException(status_code=404, detail=f"Staff {staff_id} not found")
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get staff record"))
    return result

@app.put("/staff/{staff_id}", response_model=StaffResponse)
async def update_staff(staff_id: str, staff_data: StaffUpdate):
    """Update a staff record"""
    # Filter out None values
    update_data = {k: v for k, v in staff_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided for update")
    
    result = firebase_service.update_document("staff", staff_id, update_data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to update staff record"))
    return result

@app.delete("/staff/{staff_id}", response_model=StaffResponse)
async def delete_staff(staff_id: str):
    """Delete a staff record"""
    result = firebase_service.delete_document("staff", staff_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to delete staff record"))
    return result

@app.get("/staff/status/{status}", response_model=StaffResponse)
async def get_staff_by_status(status: str):
    """Get staff by status (Online, Offline)"""
    result = firebase_service.get_collection("staff")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get staff records"))
    
    # Filter by status
    filtered_staff = [staff for staff in result["data"] if staff.get("status") == status]
    return {"success": True, "data": filtered_staff}

# ALERT ENDPOINTS
@app.post("/alerts", response_model=AlertResponse)
async def create_alert(alert_data: AlertCreate):
    """Create a new alert"""
    alert_id = f"alert_{uuid.uuid4().hex[:8]}"
    alert_dict = alert_data.model_dump()
    alert_dict["id"] = alert_id
    
    result = firebase_service.create_document("alerts", alert_id, alert_dict)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create alert"))
    return result

@app.get("/alerts", response_model=AlertResponse)
async def get_all_alerts():
    """Get all alerts"""
    result = firebase_service.get_collection("alerts")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get alerts"))
    return result

@app.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str):
    """Get a specific alert"""
    result = firebase_service.get_document("alerts", alert_id)
    if not result["success"]:
        if "not found" in result.get("message", "").lower():
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get alert"))
    return result

@app.put("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(alert_id: str, alert_data: AlertUpdate):
    """Update an alert"""
    # Filter out None values
    update_data = {k: v for k, v in alert_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided for update")
    
    result = firebase_service.update_document("alerts", alert_id, update_data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to update alert"))
    return result

@app.delete("/alerts/{alert_id}", response_model=AlertResponse)
async def delete_alert(alert_id: str):
    """Delete an alert"""
    result = firebase_service.delete_document("alerts", alert_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to delete alert"))
    return result

@app.get("/alerts/cattle/{cattle_id}", response_model=AlertResponse)
async def get_alerts_for_cattle(cattle_id: str):
    """Get all alerts for a specific cattle"""
    result = firebase_service.get_collection("alerts")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get alerts"))
    
    # Filter by cattle ID
    filtered_alerts = [alert for alert in result["data"] if alert.get("cattleId") == cattle_id]
    return {"success": True, "data": filtered_alerts}

@app.get("/alerts/type/{alert_type}", response_model=AlertResponse)
async def get_alerts_by_type(alert_type: str):
    """Get alerts by type (Health, Location, etc.)"""
    result = firebase_service.get_collection("alerts")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get alerts"))
    
    # Filter by type
    filtered_alerts = [alert for alert in result["data"] if alert.get("type") == alert_type]
    return {"success": True, "data": filtered_alerts}

# =====================
# UTILITY ENDPOINTS
# =====================

@app.get("/dashboard/summary")
async def get_dashboard_summary():
    """Get summary data for dashboard"""
    try:
        # Get cattle data
        cattle_result = firebase_service.get_collection("cattle")
        staff_result = firebase_service.get_collection("staff")
        alerts_result = firebase_service.get_collection("alerts")
        
        if not all([cattle_result["success"], staff_result["success"], alerts_result["success"]]):
            raise HTTPException(status_code=400, detail="Failed to fetch dashboard data")
        
        cattle_data = cattle_result["data"]
        staff_data = staff_result["data"]
        alerts_data = alerts_result["data"]
        
        # Calculate statistics
        total_cattle = len(cattle_data)
        cattle_by_status = {}
        cattle_by_location = {}
        
        for cattle in cattle_data:
            status = cattle.get("status", "Unknown")
            location = cattle.get("location", "Unknown")
            cattle_by_status[status] = cattle_by_status.get(status, 0) + 1
            cattle_by_location[location] = cattle_by_location.get(location, 0) + 1
        
        total_staff = len(staff_data)
        staff_online = len([s for s in staff_data if s.get("status") == "Online"])
        staff_offline = total_staff - staff_online
        
        total_alerts = len(alerts_data)
        recent_alerts = sorted(alerts_data, key=lambda x: x.get("timestamp", ""), reverse=True)[:5]
        
        return {
            "success": True,
            "data": {
                "cattle": {
                    "total": total_cattle,
                    "by_status": cattle_by_status,
                    "by_location": cattle_by_location
                },
                "staff": {
                    "total": total_staff,
                    "online": staff_online,
                    "offline": staff_offline
                },
                "alerts": {
                    "total": total_alerts,
                    "recent": recent_alerts
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard summary: {str(e)}")

# =====================
# ORIGINAL GENERIC ENDPOINTS (for backward compatibility)
# =====================

@app.post("/firestore/{collection_name}/{document_id}", response_model=DocumentResponse)
async def create_document(collection_name: str, document_id: str, document_data: DocumentData):
    """Create a new document in Firestore"""
    result = firebase_service.create_document(collection_name, document_id, document_data.data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create document"))
    return result

@app.get("/firestore/{collection_name}/{document_id}", response_model=DocumentResponse)
async def get_document(collection_name: str, document_id: str):
    """Get a document from Firestore"""
    result = firebase_service.get_document(collection_name, document_id)
    if not result["success"]:
        if "not found" in result.get("message", "").lower():
            raise HTTPException(status_code=404, detail=result.get("message", "Document not found"))
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get document"))
    return result

@app.put("/firestore/{collection_name}/{document_id}", response_model=DocumentResponse)
async def update_document(collection_name: str, document_id: str, document_data: DocumentData):
    """Update a document in Firestore"""
    result = firebase_service.update_document(collection_name, document_id, document_data.data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to update document"))
    return result

@app.delete("/firestore/{collection_name}/{document_id}", response_model=DocumentResponse)
async def delete_document(collection_name: str, document_id: str):
    """Delete a document from Firestore"""
    result = firebase_service.delete_document(collection_name, document_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to delete document"))
    return result

@app.get("/firestore/{collection_name}", response_model=DocumentResponse)
async def get_collection(collection_name: str):
    """Get all documents from a collection"""
    result = firebase_service.get_collection(collection_name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get collection"))
    return result

# =====================
# REALTIME DATABASE ENDPOINTS (Direct path access)
# =====================

@app.post("/realtime/{path:path}", response_model=DocumentResponse)
async def set_realtime_data(path: str, document_data: DocumentData):
    """Set data in Firebase Realtime Database"""
    result = firebase_service.set_realtime_data(path, document_data.data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to set data"))
    return result

@app.get("/realtime/{path:path}", response_model=DocumentResponse)
async def get_realtime_data(path: str):
    """Get data from Firebase Realtime Database"""
    result = firebase_service.get_realtime_data(path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get data"))
    return result

@app.put("/realtime/{path:path}", response_model=DocumentResponse)
async def update_realtime_data(path: str, document_data: DocumentData):
    """Update data in Firebase Realtime Database"""
    result = firebase_service.update_realtime_data(path, document_data.data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to update data"))
    return result

@app.delete("/realtime/{path:path}", response_model=DocumentResponse)
async def delete_realtime_data(path: str):
    """Delete data from Firebase Realtime Database"""
    result = firebase_service.delete_realtime_data(path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to delete data"))
    return result

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Cattle Monitor API", "version": "1.0.0"}

# Debug endpoint for production troubleshooting
@app.get("/debug/firebase")
async def debug_firebase():
    """Debug Firebase connection and environment variables"""
    import os
    
    debug_info = {
        "timestamp": datetime.now().isoformat(),
        "environment_variables": {
            "FIREBASE_DATABASE_URL": os.getenv("FIREBASE_DATABASE_URL") is not None,
            "FIREBASE_SERVICE_ACCOUNT_KEY": os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY") is not None,
            "FIREBASE_SERVICE_ACCOUNT_KEY_PATH": os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH") is not None
        },
        "firebase_status": "checking..."
    }
    
    try:
        # Test Firebase connection
        test_result = firebase_service.get_realtime_data("test")
        debug_info["firebase_status"] = "connected"
        debug_info["firebase_test"] = test_result
    except Exception as e:
        debug_info["firebase_status"] = "error"
        debug_info["firebase_error"] = str(e)
    
    return debug_info

# Debug endpoint for checking data structure
@app.get("/debug/data")
async def debug_data():
    """Debug data structure in Firebase"""
    try:
        # Try to get raw data from Firebase
        cattle_raw = firebase_service.get_realtime_data("cattle")
        staff_raw = firebase_service.get_realtime_data("staff")
        alerts_raw = firebase_service.get_realtime_data("alerts")
        
        return {
            "cattle_raw": cattle_raw,
            "staff_raw": staff_raw,
            "alerts_raw": alerts_raw,
            "cattle_collection": firebase_service.get_collection("cattle"),
            "staff_collection": firebase_service.get_collection("staff"),
            "alerts_collection": firebase_service.get_collection("alerts")
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

@app.get("/cattle-locations")
async def get_all_cattle_locations():
    """Get all cattle locations"""
    result = firebase_service.get_collection("cattle_live_data")
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to fetch cattle locations."))
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)