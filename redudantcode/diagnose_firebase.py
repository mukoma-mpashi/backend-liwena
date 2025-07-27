"""
Firebase Authentication Diagnostic Script
This script helps diagnose and fix Firebase authentication issues.
"""

import os
import json
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

def diagnose_firebase_auth():
    """Diagnose Firebase authentication issues"""
    
    print("🔍 Firebase Authentication Diagnostic")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    print("\n1. Checking Environment Variables...")
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
    database_url = os.getenv("FIREBASE_DATABASE_URL")
    service_account_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    
    print(f"   FIREBASE_DATABASE_URL: {'✅ Set' if database_url else '❌ Not set'}")
    print(f"   FIREBASE_SERVICE_ACCOUNT_KEY_PATH: {'✅ Set' if service_account_path else '❌ Not set'}")
    print(f"   FIREBASE_SERVICE_ACCOUNT_KEY: {'✅ Set' if service_account_key else '❌ Not set'}")
    
    if database_url:
        print(f"   Database URL: {database_url}")
    
    # Check service account file
    print("\n2. Checking Service Account File...")
    if service_account_path and os.path.exists(service_account_path):
        print(f"   ✅ File exists: {service_account_path}")
        
        try:
            with open(service_account_path, 'r') as f:
                creds = json.load(f)
            
            # Check required fields
            required_fields = ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id", "auth_uri", "token_uri"]
            missing_fields = [field for field in required_fields if field not in creds]
            
            if missing_fields:
                print(f"   ❌ Missing required fields: {missing_fields}")
            else:
                print("   ✅ All required fields present")
                print(f"   Project ID: {creds.get('project_id')}")
                print(f"   Client Email: {creds.get('client_email')}")
                print(f"   Type: {creds.get('type')}")
                
                # Check private key format
                private_key = creds.get('private_key', '')
                if private_key.startswith('-----BEGIN PRIVATE KEY-----') and private_key.endswith('-----END PRIVATE KEY-----\n'):
                    print("   ✅ Private key format looks correct")
                else:
                    print("   ❌ Private key format might be incorrect")
                    print("   Expected format: -----BEGIN PRIVATE KEY-----...-----END PRIVATE KEY-----")
                
        except json.JSONDecodeError as e:
            print(f"   ❌ Invalid JSON format: {e}")
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
    else:
        print(f"   ❌ File not found: {service_account_path}")
    
    # Check system time
    print("\n3. Checking System Time...")
    current_time = datetime.now(timezone.utc)
    print(f"   Current UTC time: {current_time}")
    
    # Check if time is reasonable (not too far in past/future)
    epoch_time = current_time.timestamp()
    if epoch_time < 1600000000:  # Before 2020
        print("   ❌ System time appears to be in the past")
    elif epoch_time > 2000000000:  # After 2033
        print("   ❌ System time appears to be in the future")
    else:
        print("   ✅ System time looks reasonable")
    
    # Test Firebase connection
    print("\n4. Testing Firebase Connection...")
    try:
        import firebase_admin
        from firebase_admin import credentials, db
        
        # Clean up any existing apps
        if firebase_admin._apps:
            for app in firebase_admin._apps.values():
                firebase_admin.delete_app(app)
            firebase_admin._apps.clear()
        
        # Try to initialize Firebase
        if service_account_key:
            print("   Testing with service account key (environment variable)...")
            try:
                service_account_info = json.loads(service_account_key)
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred, {'databaseURL': database_url})
                print("   ✅ Successfully initialized with environment variable")
            except Exception as e:
                print(f"   ❌ Failed with environment variable: {e}")
                return False
                
        elif service_account_path and os.path.exists(service_account_path):
            print("   Testing with service account file...")
            try:
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred, {'databaseURL': database_url})
                print("   ✅ Successfully initialized with file")
            except Exception as e:
                print(f"   ❌ Failed with file: {e}")
                return False
        else:
            print("   ❌ No valid credentials found")
            return False
        
        # Test database access
        print("   Testing database access...")
        try:
            ref = db.reference()
            test_data = {"test": "connection", "timestamp": current_time.isoformat()}
            ref.child("test").set(test_data)
            print("   ✅ Database write test successful")
            
            # Clean up test data
            ref.child("test").delete()
            print("   ✅ Database delete test successful")
            
        except Exception as e:
            print(f"   ❌ Database access failed: {e}")
            return False
            
        print("\n🎉 All Firebase tests passed!")
        return True
        
    except ImportError as e:
        print(f"   ❌ Firebase Admin SDK not installed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def generate_new_service_account_instructions():
    """Generate instructions for creating a new service account"""
    
    print("\n" + "=" * 60)
    print("🔧 HOW TO FIX FIREBASE AUTHENTICATION ISSUES")
    print("=" * 60)
    
    print("\n1. **Download a fresh service account key:**")
    print("   a. Go to Firebase Console: https://console.firebase.google.com/")
    print("   b. Select your project")
    print("   c. Click the gear icon → Project settings")
    print("   d. Go to 'Service accounts' tab")
    print("   e. Click 'Generate new private key'")
    print("   f. Download the JSON file")
    print("   g. Save it as 'firebase-service-account.json' in your project folder")
    
    print("\n2. **Update your .env file:**")
    print("   FIREBASE_SERVICE_ACCOUNT_KEY_PATH=./firebase-service-account.json")
    print("   FIREBASE_DATABASE_URL=https://your-project-default-rtdb.firebaseio.com/")
    
    print("\n3. **Alternative - Use environment variable (for deployment):**")
    print("   Instead of a file, you can set the entire JSON as an environment variable:")
    print("   FIREBASE_SERVICE_ACCOUNT_KEY='{\"type\":\"service_account\",...}'")
    
    print("\n4. **Check system time:**")
    print("   Make sure your computer's clock is accurate.")
    print("   JWT tokens are time-sensitive!")
    
    print("\n5. **Verify Firebase project settings:**")
    print("   - Ensure Firebase Realtime Database is enabled")
    print("   - Check database rules (allow read/write for testing)")
    print("   - Verify the database URL matches your project")

def main():
    """Main diagnostic function"""
    success = diagnose_firebase_auth()
    
    if not success:
        generate_new_service_account_instructions()
        return False
    
    return True

if __name__ == "__main__":
    main()
