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
        
        # Convert to single line JSON string (compact format)
        service_account_json = json.dumps(service_account_data, separators=(',', ':'))
        
        # Validate the JSON by parsing it again
        json.loads(service_account_json)
        
        print("✅ Firebase Service Account Key formatted for Render:")
        print("=" * 60)
        print("Environment Variable Name: FIREBASE_SERVICE_ACCOUNT_KEY")
        print("Environment Variable Value (copy everything below):")
        print()
        print(service_account_json)
        print()
        print("=" * 60)
        print("✅ JSON validation: PASSED")
        print("⚠️  Important: Copy the ENTIRE line above, with no extra spaces or line breaks!")
        print("⚠️  The value should start with { and end with }")
        
        # Show key information
        print("\n📋 Key Information:")
        print(f"   Project ID: {service_account_data.get('project_id', 'Unknown')}")
        print(f"   Client Email: {service_account_data.get('client_email', 'Unknown')}")
        print(f"   Key ID: {service_account_data.get('private_key_id', 'Unknown')[:10]}...")
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in service account key: {e}")
    except Exception as e:
        print(f"❌ Error reading service account key: {e}")

if __name__ == "__main__":
    format_service_account_key()
