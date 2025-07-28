from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth, credentials, initialize_app
import firebase_admin
from functools import wraps
import os
import json
from pydantic import BaseModel, EmailStr
from temp_firebase_service import temp_firebase_service as firebase_service
from datetime import datetime

# Create the router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Initialize Firebase Admin with your service account
if not firebase_admin._apps:
    # Check for environment variable first (for deployment)
    service_account_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
    database_url = os.getenv('FIREBASE_DATABASE_URL')
    
    if service_account_key:
        try:
            service_account_info = json.loads(service_account_key)
            cred = credentials.Certificate(service_account_info)
            initialize_app(cred, {'databaseURL': database_url})
        except json.JSONDecodeError:
            # Fall back to file
            cred = credentials.Certificate(os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', 'firebase-service-account-key.json'))
            initialize_app(cred, {'databaseURL': database_url})
    else:
        # Use file for local development
        cred = credentials.Certificate(os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', 'firebase-service-account-key.json'))
        initialize_app(cred, {'databaseURL': database_url})

# Security scheme for Swagger UI
security = HTTPBearer()

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"  # Default role

class FirebaseAuth:
    def __init__(self):
        self.bearer = HTTPBearer()

    async def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        if not credentials:
            raise HTTPException(status_code=403, detail="No credentials provided")
        
        if credentials.scheme != "Bearer":
            raise HTTPException(status_code=403, detail="Invalid authentication scheme")
        
        try:
            decoded_token = auth.verify_id_token(credentials.credentials)
            return decoded_token
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# Instance of FirebaseAuth to be used as a dependency
firebase_auth = FirebaseAuth()

def get_current_user(decoded_token: dict = Depends(firebase_auth)):
    """Dependency to get current authenticated user"""
    try:
        return {
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "role": decoded_token.get("role", "user")
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Failed to get user: {str(e)}")

def role_required(allowed_roles: list):
    """Decorator to check if user has required role"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user=Depends(get_current_user), **kwargs):
            if user.get("role") not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to perform this action"
                )
            return await func(*args, current_user=user, **kwargs)
        return wrapper
    return decorator

# Authentication routes
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
@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user

# Verify Firebase ID token
@router.get("/verify")
async def verify_token(decoded_token: dict = Depends(firebase_auth)):
    """Verify Firebase ID token"""
    return {"success": True, "user": decoded_token}

# List all users (Admin only)
@router.get("/users")
@role_required(["admin"])
async def list_users(current_user: dict = Depends(get_current_user)):
    """List all users - Admin only"""
    try:
        result = firebase_service.get_collection("users")
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Failed to fetch users")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
