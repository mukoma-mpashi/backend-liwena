#!/usr/bin/env python3
"""
Script to verify environment variables for deployment
"""

import os
import json
from dotenv import load_dotenv

def check_environment_variables():
    """Check if all required environment variables are set"""
    
    # Load environment variables from .env file (for local testing)
    load_dotenv()
    
    print("🔍 Checking Environment Variables for Deployment...")
    print("=" * 50)
    
    # Check Firebase Database URL
    database_url = os.getenv("FIREBASE_DATABASE_URL")
    if database_url:
        print(f"✅ FIREBASE_DATABASE_URL: {database_url}")
    else:
        print("❌ FIREBASE_DATABASE_URL: Not set")
    
    # Check Firebase Service Account Key
    service_account_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    if service_account_key:
        try:
            # Try to parse as JSON
            service_account_info = json.loads(service_account_key)
            project_id = service_account_info.get("project_id", "Unknown")
            client_email = service_account_info.get("client_email", "Unknown")
            print(f"✅ FIREBASE_SERVICE_ACCOUNT_KEY: Valid JSON")
            print(f"   Project ID: {project_id}")
            print(f"   Client Email: {client_email}")
        except json.JSONDecodeError:
            print("❌ FIREBASE_SERVICE_ACCOUNT_KEY: Invalid JSON format")
    else:
        print("❌ FIREBASE_SERVICE_ACCOUNT_KEY: Not set")
    
    # Check local service account key file (for development)
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
    if service_account_path:
        if os.path.exists(service_account_path):
            print(f"✅ FIREBASE_SERVICE_ACCOUNT_KEY_PATH: {service_account_path} (exists)")
        else:
            print(f"❌ FIREBASE_SERVICE_ACCOUNT_KEY_PATH: {service_account_path} (file not found)")
    else:
        print("ℹ️  FIREBASE_SERVICE_ACCOUNT_KEY_PATH: Not set (OK for deployment)")
    
    print("=" * 50)
    
    # Summary
    if database_url and service_account_key:
        print("🎉 All required environment variables are set for deployment!")
        return True
    else:
        print("⚠️  Missing required environment variables:")
        if not database_url:
            print("   - FIREBASE_DATABASE_URL")
        if not service_account_key:
            print("   - FIREBASE_SERVICE_ACCOUNT_KEY")
        print("\nFor deployment, you need to set these in your Render dashboard.")
        return False

if __name__ == "__main__":
    check_environment_variables()
