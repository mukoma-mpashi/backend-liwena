#!/usr/bin/env python3
"""
Script to help format Firebase service account key for Render deployment
"""

import json
import os

def format_service_account_key():
    """Format Firebase service account key for environment variable"""
    
    # Check for service account key file
    key_files = [
        "firebase-service-account-key.json",
        "cattlemonitor-57c45-firebase-adminsdk-fbsvc-f4ee97e0e5.json"
    ]
    
    key_file = None
    for file in key_files:
        if os.path.exists(file):
            key_file = file
            break
    
    if not key_file:
        print("❌ Firebase service account key file not found!")
        print("Please ensure one of these files exists:")
        for file in key_files:
            print(f"  - {file}")
        return
    
    try:
        with open(key_file, 'r') as f:
            service_account_data = json.load(f)
        
        # Convert to single line JSON string
        service_account_json = json.dumps(service_account_data, separators=(',', ':'))
        
        print("✅ Firebase Service Account Key formatted for Render:")
        print("=" * 60)
        print("Copy this value for FIREBASE_SERVICE_ACCOUNT_KEY environment variable:")
        print()
        print(service_account_json)
        print()
        print("=" * 60)
        print("⚠️  Important: Keep this key secure and don't share it publicly!")
        
    except Exception as e:
        print(f"❌ Error reading service account key: {e}")

if __name__ == "__main__":
    format_service_account_key()
