from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Position model
class Position(BaseModel):
    x: float
    y: float

# Cattle models
class CattleBase(BaseModel):
    id: str
    type: str
    status: str
    location: str
    lastMovement: str
    position: Position

class CattleCreate(BaseModel):
    type: str
    status: str
    location: str
    lastMovement: str
    position: Position

class CattleUpdate(BaseModel):
    type: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    lastMovement: Optional[str] = None
    position: Optional[Position] = None

# Staff models
class StaffBase(BaseModel):
    id: str
    name: str
    role: str
    status: str
    location: str

class StaffCreate(BaseModel):
    name: str
    role: str
    status: str
    location: str

class StaffUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None

# Alert models
class AlertBase(BaseModel):
    id: str
    cattleId: str
    type: str
    message: str
    timestamp: str

# =================================================
# NEW MODELS FOR ESP32 SENSOR DATA
# =================================================

class Acceleration(BaseModel):
    x: float
    y: float
    z: float

class Behavior(BaseModel):
    current: str
    previous: str
    duration_seconds: int
    confidence: float

class ActivityMetrics(BaseModel):
    total_active_time_seconds: int
    total_rest_time_seconds: int
    daily_steps: int
    daily_distance_km: float

class CattleSensorData(BaseModel):
    """
    Represents the full data payload from IoT sensors (ESP32/ESP8266).
    """
    cattle_id: str
    timestamp: str
    latitude: float
    longitude: float
    gps_fix: bool
    speed_kmh: float
    heading: float
    is_moving: bool
    acceleration: Acceleration
    behavior: Behavior
    activity: ActivityMetrics

class CattleLiveData(CattleSensorData):
    """
    Represents the data stored in Firebase for a cattle's live state.
    Includes an ID field.
    """
    id: str

# =================================================

# Geofence models
from typing import List
class Geofence(BaseModel):
    id: str
    name: str
    coordinates: List[List[float]]  # [[lng, lat], ...] polygon

class GeofenceCreate(BaseModel):
    name: str
    coordinates: List[List[float]]

# Cattle location update model
class CattleLocationUpdate(BaseModel):
    cattle_id: str
    location: List[float]  # [lng, lat]
    timestamp: str

class AlertCreate(BaseModel):
    cattleId: str
    type: str
    message: str
    timestamp: str

class AlertUpdate(BaseModel):
    cattleId: Optional[str] = None
    type: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None

# Response models (can handle both single items and collections)
class CattleResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None  # Can be dict (single item) or list (collection)
    error: Optional[str] = None

class StaffResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None  # Can be dict (single item) or list (collection)
    error: Optional[str] = None

class AlertResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None  # Can be dict (single item) or list (collection)
    error: Optional[str] = None
