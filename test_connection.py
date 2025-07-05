"""
Simple Firebase connection test
"""

from firebase_service import firebase_service

def test_firebase_connection():
    print("🔥 Testing Firebase Connection...")
    
    # Test basic connection
    try:
        print("Attempting to connect to Firebase...")
        
        # Try to get a non-existent collection (this will tell us if the connection works)
        result = firebase_service.get_collection("test_connection")
        
        if result["success"]:
            print("✅ Firebase connection successful!")
            print(f"Found {len(result['data'])} documents in test collection")
            return True
        else:
            print("❌ Firebase connection failed:")
            print(f"Error: {result.get('error', 'Unknown error')}")
            
            # Check if it's a Firestore API error
            if "SERVICE_DISABLED" in str(result.get('error', '')):
                print("\n🚨 FIRESTORE API IS NOT ENABLED!")
                print("Please follow these steps:")
                print("1. Go to https://console.firebase.google.com/")
                print("2. Select your project: cattlemonitor-57c45")
                print("3. Click 'Firestore Database' in the left sidebar")
                print("4. Click 'Create database'")
                print("5. Choose 'Start in test mode'")
                print("6. Select a location and click 'Done'")
                print("7. Wait 2-3 minutes for changes to propagate")
                print("\nAlternatively, visit:")
                print("https://console.developers.google.com/apis/api/firestore.googleapis.com/overview?project=cattlemonitor-57c45")
                print("And click 'Enable'")
            
            return False
            
    except Exception as e:
        print(f"❌ Firebase connection failed with exception: {e}")
        return False

if __name__ == "__main__":
    test_firebase_connection()
