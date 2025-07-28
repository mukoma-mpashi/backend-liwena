from fastapi import APIRouter, HTTPException
from temp_firebase_service import temp_firebase_service as firebase_service
from models import StaffCreate, StaffUpdate, StaffResponse
import uuid

router = APIRouter(prefix="/staff", tags=["staff"])

@router.post("", response_model=StaffResponse)
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

@router.get("", response_model=StaffResponse)
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

@router.get("/{staff_id}", response_model=StaffResponse)
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

@router.put("/{staff_id}", response_model=StaffResponse)
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

@router.delete("/{staff_id}", response_model=StaffResponse)
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

@router.get("/status/{status}", response_model=StaffResponse)
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

@router.get("/location/{location}", response_model=StaffResponse)
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
