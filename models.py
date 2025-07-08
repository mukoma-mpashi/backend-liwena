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
