from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth, credentials, initialize_app
import firebase_admin
from functools import wraps
import os

# Initialize Firebase Admin with your service account
if not firebase_admin._apps:
    cred = credentials.Certificate(os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', 'firebase-service-account-key.json'))
    initialize_app(cred)

# Security scheme for Swagger UI
security = HTTPBearer()

class FirebaseAuth:
    def __init__(self):
        self.bearer = HTTPBearer()

    async def __call__(self, credentials: HTTPAuthorizationCredentials = Security(security)):
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
