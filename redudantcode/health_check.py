#!/usr/bin/env python3
"""
Health check script for deployment verification
"""

import os
import sys
from dotenv import load_dotenv

def health_check():
    """Perform basic health checks"""
    print("🏥 Performing Health Check...")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    database_url = os.getenv("FIREBASE_DATABASE_URL")
    service_account_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    
    if not database_url:
        print("❌ FIREBASE_DATABASE_URL not set")
        return False
    
    if not service_account_key:
        print("❌ FIREBASE_SERVICE_ACCOUNT_KEY not set")
        return False
    
    print("✅ Environment variables are set")
    
    # Try to import Firebase service
    try:
        from firebase_service import firebase_service
        print("✅ Firebase service imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Firebase service: {e}")
        return False
    
    # Try to import FastAPI app
    try:
        from main import app
        print("✅ FastAPI app imported successfully")
    except Exception as e:
        print(f"❌ Failed to import FastAPI app: {e}")
        return False
    
    print("🎉 Health check passed!")
    return True

if __name__ == "__main__":
    success = health_check()
    sys.exit(0 if success else 1)
