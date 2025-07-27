from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from firebase_admin import auth
from auth import get_current_user, role_required, firebase_auth
from temp_firebase_service import temp_firebase_service as firebase_service
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["authentication"])

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"  # Default role

# User registration
@router.post("/register")
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
@router.get("/me", dependencies=[Depends(firebase_auth)])
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user

# Verify Firebase ID token
@router.get("/verify")
async def verify_token(decoded_token: dict = Depends(firebase_auth)):
    """Verify Firebase ID token"""
    return {"success": True, "user": decoded_token}

# List all users (Admin only)
@router.get("/users", dependencies=[Depends(firebase_auth)])
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
