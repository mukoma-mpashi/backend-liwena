from fastapi import APIRouter, HTTPException
from temp_firebase_service import temp_firebase_service as firebase_service
from models import AlertCreate, AlertUpdate, AlertResponse
import uuid

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.post("", response_model=AlertResponse)
async def create_alert(alert_data: AlertCreate):
    """Create a new alert"""
    alert_id = f"alert_{uuid.uuid4().hex[:8]}"
    alert_dict = alert_data.model_dump()
    alert_dict["id"] = alert_id
    
    result = firebase_service.create_document("alerts", alert_id, alert_dict)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create alert"))
    return result

@router.get("", response_model=AlertResponse)
async def get_all_alerts():
    """Get all alerts"""
    result = firebase_service.get_collection("alerts")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get alerts"))
    return result

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str):
    """Get a specific alert"""
    result = firebase_service.get_document("alerts", alert_id)
    if not result["success"]:
        if "not found" in result.get("message", "").lower():
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get alert"))
    return result

@router.put("/{alert_id}", response_model=AlertResponse)
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

@router.delete("/{alert_id}", response_model=AlertResponse)
async def delete_alert(alert_id: str):
    """Delete an alert"""
    result = firebase_service.delete_document("alerts", alert_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to delete alert"))
    return result

@router.get("/cattle/{cattle_id}", response_model=AlertResponse)
async def get_alerts_for_cattle(cattle_id: str):
    """Get all alerts for a specific cattle"""
    result = firebase_service.get_collection("alerts")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get alerts"))
    
    # Filter by cattle ID
    filtered_alerts = [alert for alert in result["data"] if alert.get("cattleId") == cattle_id]
    return {"success": True, "data": filtered_alerts}

@router.get("/type/{alert_type}", response_model=AlertResponse)
async def get_alerts_by_type(alert_type: str):
    """Get alerts by type (Health, Location, etc.)"""
    result = firebase_service.get_collection("alerts")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get alerts"))
    
    # Filter by type
    filtered_alerts = [alert for alert in result["data"] if alert.get("type") == alert_type]
    return {"success": True, "data": filtered_alerts}
