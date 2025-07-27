from fastapi import APIRouter, HTTPException
from temp_firebase_service import temp_firebase_service as firebase_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary")
async def get_dashboard_summary():
    """Get summary data for dashboard"""
    try:
        # Get cattle data
        cattle_result = firebase_service.get_collection("cattle")
        staff_result = firebase_service.get_collection("staff")
        alerts_result = firebase_service.get_collection("alerts")
        
        if not all([cattle_result["success"], staff_result["success"], alerts_result["success"]]):
            raise HTTPException(status_code=500, detail="Failed to fetch dashboard data")
        
        cattle_data = cattle_result["data"]
        staff_data = staff_result["data"]
        alerts_data = alerts_result["data"]
        
        # Calculate statistics
        total_cattle = len(cattle_data)
        cattle_by_status = {}
        cattle_by_location = {}
        
        for cattle in cattle_data:
            status = cattle.get("status", "unknown")
            location = cattle.get("location", "unknown")
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
