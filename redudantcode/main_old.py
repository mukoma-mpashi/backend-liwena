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
    
    print(f"🗺️ New geofence created: {data['name']} with {len(data['coordinates'])} points")
    return result

# Create a simple test geofence (for testing purposes)
@app.post("/geofences/create-test")
async def create_test_geofence():
    """Create a test geofence around Nairobi area for testing"""
    test_geofence = {
        "name": "Test Geofence - Nairobi Area",
        "coordinates": [
            [36.8, -1.3],    # Northwest corner
            [36.9, -1.3],    # Northeast corner  
            [36.9, -1.25],   # Southeast corner
            [36.8, -1.25],   # Southwest corner
            [36.8, -1.3]     # Close the polygon
        ]
    }
    
    geofence_id = f"geofence_{uuid.uuid4().hex[:8]}"
    data = test_geofence
    data["id"] = geofence_id
    
    result = firebase_service.create_document("geofences", geofence_id, data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create test geofence"))
    
    print(f"🧪 Test geofence created: {data['name']}")
    return {
        "success": True,
        "message": "Test geofence created successfully",
        "geofence": data,
        "note": "This geofence covers coordinates around Nairobi. Cattle outside this area will trigger alerts."
    }

# Create test cattle data (for testing the map)
@app.post("/cattle/create-test-data")
async def create_test_cattle_data():
    """Create test cattle data for map visualization"""
    test_cattle = [
        {
            "cattle_id": "cattle1",
            "timestamp": datetime.now().isoformat(),
            "latitude": -1.2921,  # Nairobi coordinates
            "longitude": 36.8219,
            "gps_fix": True,
            "speed_kmh": 2.5,
            "heading": 45.0,
            "is_moving": True,
            "acceleration": {"x": 0.1, "y": 0.2, "z": 9.8},
            "behavior": {
                "current": "grazing",
                "previous": "resting", 
                "duration_seconds": 300,
                "confidence": 85.5
            },
            "activity": {
                "total_active_time_seconds": 7200,
                "total_rest_time_seconds": 3600,
                "daily_steps": 1250,
                "daily_distance_km": 2.8
            }
        },
        {
            "cattle_id": "cattle2", 
            "timestamp": datetime.now().isoformat(),
            "latitude": -1.2925,  # Slightly different location
            "longitude": 36.8225,
            "gps_fix": True,
            "speed_kmh": 0.0,
            "heading": 0.0,
            "is_moving": False,
            "acceleration": {"x": 0.0, "y": 0.0, "z": 9.8},
            "behavior": {
                "current": "resting",
                "previous": "walking",
                "duration_seconds": 1800,
                "confidence": 92.0
            },
            "activity": {
                "total_active_time_seconds": 5400,
                "total_rest_time_seconds": 5400,
                "daily_steps": 890,
                "daily_distance_km": 1.2
            }
        }
    ]
    
    created_cattle = []
    for cattle_data in test_cattle:
        cattle_id = cattle_data["cattle_id"]
        live_data_path = f"cattle_live_data/{cattle_id}"
        result = firebase_service.set_realtime_data(live_data_path, cattle_data)
        
        if result["success"]:
            created_cattle.append(cattle_id)
            print(f"🐄 Test cattle data created for: {cattle_id}")
        else:
            print(f"❌ Failed to create test data for: {cattle_id}")
    
    return {
        "success": True,
        "message": f"Created test data for {len(created_cattle)} cattle",
        "cattle_created": created_cattle,
        "note": "You can now view these cattle on the map and test geofencing"
    }

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
# NEW ENDPOINT FOR ESP32 SENSOR DATA (No Auth Required)
# =================================================

@app.post("/cattle/live-data", status_code=200)
async def update_cattle_live_data(data: CattleSensorData):
    """
    Receives and processes live sensor data from an ESP32 device for a specific cattle.
    This is the primary endpoint for hardware integration.
    Note: Authentication removed for ESP32 compatibility.
    """
    cattle_id = data.cattle_id
    
    print(f"📡 Received data from ESP32 for cattle: {cattle_id}")
    print(f"📍 Location: {data.latitude}, {data.longitude}")
    print(f"🐄 Behavior: {data.behavior.current}")
    print(f"🚶 Moving: {data.is_moving}")
    
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

    # 3. 🔥 GEOFENCING LOGIC 🔥
    print(f"🗺️ Checking geofences for cattle {cattle_id}...")
    location_point = Point(data.longitude, data.latitude)
    geofences_result = firebase_service.get_collection("geofences")
    
    geofence_alerts = []
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

    # Prepare response with geofence status
    response_message = f"Live data for {cattle_id} processed successfully."
    if geofence_alerts:
        response_message += f" Generated {len(geofence_alerts)} geofence alerts."
    
    return {
        "success": True, 
        "message": response_message,
        "cattle_id": cattle_id,
        "location": {"latitude": data.latitude, "longitude": data.longitude},
        "behavior": data.behavior.current,
        "geofence_alerts": geofence_alerts
    }


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

# =====================
# STAFF ENDPOINTS
# =====================

@app.post("/staff", response_model=StaffResponse)
async def create_staff(staff_data: StaffCreate):
    """Create a new staff record"""
    staff_id = f"staff_{uuid.uuid4().hex[:8]}"
    staff_dict = staff_data.model_dump()
    staff_dict["id"] = staff_id
    
    result = firebase_service.create_document("staff", staff_id, staff_dict)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create staff record"))
    
    print(f"👤 New staff created: {staff_dict['name']} ({staff_dict['role']})")
    return result

@app.get("/staff", response_model=StaffResponse)
async def get_all_staff():
    """Get all staff records"""
    try:
        result = firebase_service.get_collection("staff")
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get staff records"))
        
        # Transform the data to match the expected format
        staff_data = result.get("data", [])
        if isinstance(staff_data, dict):
            # If data is returned as a dict (Firebase realtime DB format), convert to list
            staff_list = []
            for staff_id, staff_info in staff_data.items():
                if isinstance(staff_info, dict):
                    staff_info["id"] = staff_id  # Ensure ID is included
                    staff_list.append(staff_info)
            result["data"] = staff_list
        
        print(f"📋 Retrieved {len(result['data'])} staff records")
        return result
        
    except Exception as e:
        print(f"Error fetching staff: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch staff records: {str(e)}")

@app.get("/staff/{staff_id}", response_model=StaffResponse)
async def get_staff(staff_id: str):
    """Get a specific staff record"""
    try:
        result = firebase_service.get_document("staff", staff_id)
        if not result["success"]:
            if "not found" in result.get("message", "").lower():
                raise HTTPException(status_code=404, detail=f"Staff {staff_id} not found")
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get staff record"))
        
        # Ensure the ID is included in the response
        if isinstance(result["data"], dict):
            result["data"]["id"] = staff_id
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch staff {staff_id}: {str(e)}")

@app.put("/staff/{staff_id}", response_model=StaffResponse)
async def update_staff(staff_id: str, staff_data: StaffUpdate):
    """Update a staff record"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in staff_data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No data provided for update")
        
        result = firebase_service.update_document("staff", staff_id, update_data)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to update staff record"))
        
        print(f"✏️ Staff {staff_id} updated: {update_data}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update staff {staff_id}: {str(e)}")

@app.delete("/staff/{staff_id}", response_model=StaffResponse)
async def delete_staff(staff_id: str):
    """Delete a staff record"""
    try:
        result = firebase_service.delete_document("staff", staff_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to delete staff record"))
        
        print(f"🗑️ Staff {staff_id} deleted")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete staff {staff_id}: {str(e)}")

@app.get("/staff/status/{status}", response_model=StaffResponse)
async def get_staff_by_status(status: str):
    """Get staff by status (active, inactive, etc.)"""
    try:
        result = firebase_service.get_collection("staff")
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get staff records"))
        
        # Transform and filter by status
        staff_data = result.get("data", [])
        if isinstance(staff_data, dict):
            # Convert dict to list and filter
            filtered_staff = []
            for staff_id, staff_info in staff_data.items():
                if isinstance(staff_info, dict) and staff_info.get("status", "").lower() == status.lower():
                    staff_info["id"] = staff_id
                    filtered_staff.append(staff_info)
        else:
            # If already a list, filter directly
            filtered_staff = [staff for staff in staff_data if staff.get("status", "").lower() == status.lower()]
        
        print(f"🔍 Found {len(filtered_staff)} staff with status: {status}")
        return {"success": True, "data": filtered_staff}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch staff by status: {str(e)}")

@app.get("/staff/location/{location}", response_model=StaffResponse)
async def get_staff_by_location(location: str):
    """Get staff by location"""
    try:
        result = firebase_service.get_collection("staff")
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get staff records"))
        
        # Transform and filter by location
        staff_data = result.get("data", [])
        if isinstance(staff_data, dict):
            # Convert dict to list and filter
            filtered_staff = []
            for staff_id, staff_info in staff_data.items():
                if isinstance(staff_info, dict) and staff_info.get("location", "").lower() == location.lower():
                    staff_info["id"] = staff_id
                    filtered_staff.append(staff_info)
        else:
            # If already a list, filter directly
            filtered_staff = [staff for staff in staff_data if staff.get("location", "").lower() == location.lower()]
        
        print(f"📍 Found {len(filtered_staff)} staff at location: {location}")
        return {"success": True, "data": filtered_staff}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch staff by location: {str(e)}")

# Create test staff data (for testing)
@app.post("/staff/create-test-data")
async def create_test_staff_data():
    """Create test staff data matching your database structure"""
    test_staff = [
        {
            "id": "staff1",
            "name": "liwena",
            "role": "farm Manager",
            "status": "active",
            "location": "north"
        },
        {
            "id": "staff2",
            "name": "melu", 
            "role": "Veterinarian",
            "status": "active",
            "location": "Field"
        },
        {
            "id": "staff3",
            "name": "john",
            "role": "Field Worker",
            "status": "active", 
            "location": "south"
        }
    ]
    
    created_staff = []
    for staff_data in test_staff:
        staff_id = staff_data["id"]
        result = firebase_service.create_document("staff", staff_id, staff_data)
        
        if result["success"]:
            created_staff.append(staff_id)
            print(f"👤 Test staff created: {staff_data['name']} ({staff_data['role']})")
        else:
            print(f"❌ Failed to create test staff: {staff_id}")
    
    return {
        "success": True,
        "message": f"Created test data for {len(created_staff)} staff members",
        "staff_created": created_staff,
        "note": "Test staff data has been added to the database"
    }

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
@app.get("/cattle-locations")
async def get_all_cattle_locations():
    """Get all cattle locations in format expected by frontend"""
    try:
        # Get live data from cattle_live_data collection
        result = firebase_service.get_realtime_data("cattle_live_data")
        if not result["success"]:
            return {"success": True, "data": []}  # Return empty array if no data
        
        cattle_data = result.get("data", {})
        if not cattle_data:
            return {"success": True, "data": []}
        
        # Transform data for frontend
        locations = []
        for cattle_id, live_data in cattle_data.items():
            if isinstance(live_data, dict):
                locations.append({
                    "id": cattle_id,
                    "cattle_id": cattle_id,
                    "location": [live_data.get("latitude", 0), live_data.get("longitude", 0)],  # [lat, lng]
                    "timestamp": live_data.get("timestamp", ""),
                    "behavior": live_data.get("behavior", {}).get("current", "unknown"),
                    "is_moving": live_data.get("is_moving", False)
                })
        
        return {"success": True, "data": locations}
        
    except Exception as e:
        print(f"Error fetching cattle locations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch cattle locations: {str(e)}")

@app.get("/cattle-live-data/{cattle_id}")
async def get_cattle_live_data(cattle_id: str):
    """Get live sensor data for a specific cattle"""
    try:
        # Try to get live data from the cattle_live_data collection
        result = firebase_service.get_realtime_data(f"cattle_live_data/{cattle_id}")
        if not result["success"]:
            raise HTTPException(status_code=404, detail=f"No live data found for cattle {cattle_id}")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch live data for cattle {cattle_id}: {str(e)}")

@app.get("/cattle-live-data")
async def get_all_cattle_live_data():
    """Get live sensor data for all cattle"""
    try:
        result = firebase_service.get_realtime_data("cattle_live_data")
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Failed to fetch cattle live data")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch cattle live data: {str(e)}")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)