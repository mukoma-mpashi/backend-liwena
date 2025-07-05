#!/usr/bin/env python3
"""
Test Firebase connection and generate new service account key instructions
"""

import json
import os
from datetime import datetime

def check_firebase_key_validity():
    """Check if the Firebase service account key is valid"""
    
    key_files = [
        "firebase-service-account-key.json",
        "cattlemonitor-57c45-firebase-adminsdk-fbsvc-f4ee97e0e5.json"
    ]
    
    for key_file in key_files:
        if os.path.exists(key_file):
            try:
                with open(key_file, 'r') as f:
                    key_data = json.load(f)
                
                print(f"📋 Key file: {key_file}")
                print(f"   Project ID: {key_data.get('project_id')}")
                print(f"   Client Email: {key_data.get('client_email')}")
                print(f"   Key ID: {key_data.get('private_key_id')}")
                print(f"   Type: {key_data.get('type')}")
                print()
                
                # Check if key has all required fields
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if not key_data.get(field)]
                
                if missing_fields:
                    print(f"❌ Missing fields in {key_file}: {missing_fields}")
                else:
                    print(f"✅ All required fields present in {key_file}")
                
            except Exception as e:
                print(f"❌ Error reading {key_file}: {e}")
    
    print("\n" + "="*60)
    print("🔧 SOLUTION: Generate a New Service Account Key")
    print("="*60)
    print("The 'Invalid JWT Signature' error usually means:")
    print("1. The service account key is expired or invalid")
    print("2. The private key is corrupted")
    print("3. The key doesn't have the right permissions")
    print()
    print("To fix this, generate a new service account key:")
    print()
    print("1. Go to Firebase Console: https://console.firebase.google.com/")
    print("2. Select your project: cattlemonitor-57c45")
    print("3. Go to Project Settings → Service accounts")
    print("4. Click 'Generate new private key'")
    print("5. Download the new JSON file")
    print("6. Replace your current key file with the new one")
    print("7. Update the FIREBASE_SERVICE_ACCOUNT_KEY environment variable in Render")
    print()
    print("Alternative: Check Firebase Database Rules")
    print("Make sure your Firebase Realtime Database rules allow access:")
    print('{\n  "rules": {\n    ".read": true,\n    ".write": true\n  }\n}')

if __name__ == "__main__":
    check_firebase_key_validity()
